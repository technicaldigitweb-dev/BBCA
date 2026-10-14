"""Buy Box check engine - three execution modes, with reliability controls.

Modes
-----
    full_daily     every eligible PH record, scheduled
    manual_single  one ASIN / account / marketplace, on demand
    manual_full    the whole eligible list, on demand

Guarantees
----------
* A run is only `completed` when nothing was skipped and nothing errored. Any skip or
  CHECK ERROR downgrades it to `completed_with_errors`. A full run is never reported
  successful while records were missed.
* Checkpoint after every batch, so an interrupted run resumes instead of restarting.
* A lock file prevents overlapping runs.
* Retries are bounded and are NEVER applied to an access-control response.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
import uuid
from collections import Counter

import config
import sources
from history import History


class RunLocked(Exception):
    pass


class _Lock:
    """Cross-process run lock. A stale lock (dead PID) is reclaimed, not honoured."""

    def __init__(self, path=None):
        self.path = config.RUNLOCK_FILE if path is None else path

    def _alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError):
            return False
        except PermissionError:
            return True
        return True

    def acquire(self, run_id: str) -> None:
        if self.path.exists():
            try:
                prev = json.loads(self.path.read_text(encoding='utf-8'))
            except Exception:
                prev = {}
            pid = prev.get('pid')
            if pid and self._alive(int(pid)):
                raise RunLocked(f"another run is active (run_id={prev.get('run_id')}, pid={pid})")
        self.path.write_text(json.dumps(
            {'run_id': run_id, 'pid': os.getpid(),
             'started_at': dt.datetime.now().astimezone().isoformat(timespec='seconds')}),
            encoding='utf-8')

    def release(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def load_eligible() -> list[dict]:
    """The eligible PH Dashboard records, deduplicated at the correct grain."""
    if not config.PH_SPINE_FILE.exists():
        raise FileNotFoundError(
            f'{config.PH_SPINE_FILE} is missing. The PH spine is staged from ph_dashboard '
            'via the read-only MCP route (see README).')
    spine = json.loads(config.PH_SPINE_FILE.read_text(encoding='utf-8'))
    seen, out = set(), []
    for r in spine:
        acct = r.get('account')
        mkt = r.get('marketplace')
        if acct not in config.SELLER_IDS or mkt not in config.MARKETPLACES.values():
            continue
        key = (r['asin'], acct, mkt)
        if key in seen:
            continue
        seen.add(key)
        out.append({'asin': r['asin'], 'seller_account': acct, 'marketplace': mkt,
                    'sku': r.get('sku'), 'stock': r.get('uk_stock'),
                    'listing_status': r.get('listing_status')})
    return out


class Engine:
    def __init__(self, hist: History | None = None, log=print):
        self.h = hist or History()
        self.log = log

    # -----------------------------------------------------------------------
    def run(self, mode: str, records: list[dict] | None = None, prefer_live: bool = False,
            run_id: str | None = None, resume: bool = False,
            batch_size: int | None = None) -> dict:
        assert mode in ('full_daily', 'manual_single', 'manual_full')
        run_id = run_id or f"{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"
        batch_size = batch_size or config.BATCH_SIZE
        lock = _Lock()
        lock.acquire(run_id)
        try:
            return self._run(mode, records, prefer_live, run_id, resume, batch_size)
        finally:
            lock.release()

    def _run(self, mode, records, prefer_live, run_id, resume, batch_size) -> dict:
        try:
            src, notes = sources.resolve(prefer_live)
        except sources.SourceUnavailable as e:
            self.h.start_run(run_id, mode, 'none', 0)
            self.h.finish_run(run_id, 'failed', {}, str(e))
            self.log(f'[{run_id}] FAILED: {e}')
            return {'run_id': run_id, 'status': 'failed', 'detail': str(e)}

        for n in notes:
            self.log(f'[{run_id}] source note: {n}')

        recs = records if records is not None else load_eligible()
        done: set = set()
        if resume:
            done = self._load_checkpoint(run_id)
            if done:
                self.log(f'[{run_id}] resuming - {len(done)} record(s) already done')
        todo = [r for r in recs
                if (r['asin'], r['seller_account'], r['marketplace']) not in done]

        self.h.start_run(run_id, mode, src.name, len(recs))
        self.log(f'[{run_id}] mode={mode} source={src.name} eligible={len(recs)} todo={len(todo)}')

        tally = Counter({'checked': len(done)})
        failed_requests = skipped = 0

        for i in range(0, len(todo), batch_size):
            batch = todo[i:i + batch_size]
            try:
                results = self._with_retry(src, batch, run_id)
            except sources.SourceUnavailable as e:
                # A refusal (e.g. browser cap) is not retried and not partially faked.
                skipped += len(batch)
                self.log(f'[{run_id}] batch skipped: {e}')
                continue
            except Exception as e:
                failed_requests += len(batch)
                self.log(f'[{run_id}] batch error: {type(e).__name__}: {str(e)[:120]}')
                continue

            self.h.save_results(run_id, results)
            for r in results:
                tally[r.buy_box_status] += 1
                tally['checked'] += 1
                if r.buy_box_status == 'NO' and r.official_reason == 'Unknown':
                    tally['reason_unknown'] += 1
                done.add((r.asin, r.seller_account, r.marketplace))
            self._save_checkpoint(run_id, done)
            self.log(f'[{run_id}] batch {i // batch_size + 1}: '
                     f'{len(results)} saved ({tally["checked"]}/{len(recs)})')

        tally['failed_requests'] = failed_requests
        tally['skipped'] = skipped
        clean = (tally['checked'] == len(recs) and failed_requests == 0 and skipped == 0
                 and tally['CHECK ERROR'] == 0)
        status = 'completed' if clean else 'completed_with_errors'
        detail = '' if clean else (f'checked={tally["checked"]}/{len(recs)} '
                                   f'errors={tally["CHECK ERROR"]} failed={failed_requests} '
                                   f'skipped={skipped}')
        self.h.finish_run(run_id, status, tally, detail)
        if clean:
            self._clear_checkpoint(run_id)
        self.log(f'[{run_id}] {status} {dict(tally)}')
        return {'run_id': run_id, 'status': status, 'source': src.name,
                'total_eligible': len(recs), **{k: v for k, v in tally.items()}}

    # -----------------------------------------------------------------------
    def _with_retry(self, src, batch, run_id):
        last = None
        for attempt in range(1, config.MAX_RETRIES + 2):
            try:
                results = src.check_batch(batch)
            except sources.SourceUnavailable:
                raise                      # refusal - never retry
            except Exception as e:
                last = e
                if attempt > config.MAX_RETRIES:
                    raise
                self.log(f'[{run_id}] attempt {attempt} failed ({type(e).__name__}), retrying')
                time.sleep(config.RETRY_BACKOFF_S)
                continue
            # An access-control error is a transparent terminal state, never retried.
            if any(r.error_code == 'ACCESS_CONTROL' for r in results):
                self.log(f'[{run_id}] access control encountered - halting, no retry')
            return results
        raise last  # pragma: no cover

    # --- checkpoints --------------------------------------------------------
    def _ckpt_path(self, run_id):
        return config.STATE / f'checkpoint-{run_id}.json'

    def _save_checkpoint(self, run_id, done):
        self._ckpt_path(run_id).write_text(
            json.dumps({'run_id': run_id, 'done': ['|'.join(k) for k in sorted(done)]}),
            encoding='utf-8')

    def _load_checkpoint(self, run_id) -> set:
        p = self._ckpt_path(run_id)
        if not p.exists():
            return set()
        try:
            return {tuple(s.split('|')) for s in json.loads(p.read_text(encoding='utf-8'))['done']}
        except Exception:
            return set()

    def _clear_checkpoint(self, run_id):
        try:
            self._ckpt_path(run_id).unlink()
        except FileNotFoundError:
            pass

    # --- convenience --------------------------------------------------------
    def check_single(self, asin: str, seller_account: str, marketplace: str,
                     prefer_live: bool = True) -> dict:
        rec = {'asin': asin, 'seller_account': seller_account, 'marketplace': marketplace}
        return self.run('manual_single', [rec], prefer_live=prefer_live)
