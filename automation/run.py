"""Buy Box Check Automation - entry point.

    python run.py --preflight                     environment + approval gate check
    python run.py                                 full daily check (historical source)
    python run.py --live                          full check, live source (will refuse: no SP-API)
    python run.py --asin B07VFV228J --account LEDSone --marketplace UK
    python run.py --manual-full                   on-demand full check
    python run.py --resume <run_id>               resume an interrupted run
    python run.py --alerts <run_id>               alert dry run for a completed run
    python run.py --status                        recent runs + last successful run

The Windows scheduled task calls this file with no arguments, so a manual run and the
scheduled run execute identical code - there is no separate scheduled pipeline.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback

import config
import sources
from engine import Engine, RunLocked, load_eligible
from history import History
from alerts import AlertEngine
import publisher

LOG_FILE = config.LOGS / f"run_{dt.datetime.now().strftime('%Y%m%d')}.log"


def log(msg: str) -> None:
    line = f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')}  {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def spine_freshness(max_age_hours: float = 26.0) -> tuple[bool, str]:
    """Verify the upstream PH ASIN refresh actually completed before we run.

    The upstream job is ph_dashboard's `overall_asin_daily` (cron 35 7 * * * Asia/Colombo),
    but its CRON TIME IS NOT ITS COMPLETION TIME - it has run as late as 08:15 local.
    So freshness is judged on the staged spine's own `snapshot_at`, which is the
    observed completion, not the schedule.
    """
    import datetime as _dt
    if not config.PH_SPINE_FILE.exists():
        return False, f'{config.PH_SPINE_FILE} is missing'
    try:
        rows = json.loads(config.PH_SPINE_FILE.read_text(encoding='utf-8'))
        snap = rows[0]['snapshot_at']
        age = (_dt.datetime.now(_dt.timezone.utc)
               - _dt.datetime.fromisoformat(snap)).total_seconds() / 3600.0
    except Exception as e:
        return False, f'spine unreadable: {type(e).__name__}: {e}'
    if age > max_age_hours:
        return False, (f'spine snapshot_at {snap} is {age:.1f}h old (limit {max_age_hours}h) '
                       '- the upstream refresh has not completed, or the spine was not restaged')
    return True, f'spine snapshot_at {snap} ({age:.1f}h old)'


def preflight() -> int:
    log('--- preflight ---')
    problems = []

    ok = config.source_db_available()
    log(f"  source db (${config.SOURCE_DB_ENV}) : {'available' if ok else 'NOT SET'}")
    if not ok:
        problems.append(f'${config.SOURCE_DB_ENV} is not set')

    sp = config.PH_SPINE_FILE
    log(f"  PH spine                            : "
        f"{'present' if sp.exists() else 'MISSING'} ({sp})")
    if not sp.exists():
        problems.append('PH spine file is missing')
    else:
        try:
            log(f'  eligible records                    : {len(load_eligible())}')
        except Exception as e:
            problems.append(f'spine unreadable: {e}')

    log('  sources:')
    for name, src in sources.REGISTRY.items():
        avail, why = src.available()
        log(f"    {name:24} {'available' if avail else 'unavailable'} - {why}")

    log('  approval gates:')
    for g in config.GATES:
        log(f"    {g:34} {'APPROVED' if config.gate(g) else 'not approved'}")

    log(f'  schedule                            : '
        f"cron={config.SCHEDULE_CRON or 'UNSET (awaiting approval)'} tz={config.SCHEDULE_TIMEZONE}")
    log(f"  upstream dependency                 : {config.UPSTREAM_DEPENDENCY['task']} "
        f"at {config.UPSTREAM_DEPENDENCY['cron']} {config.UPSTREAM_DEPENDENCY['timezone']}")
    fresh, detail = spine_freshness()
    log(f"  upstream freshness                  : {'OK' if fresh else 'STALE'} - {detail}")
    if not fresh:
        problems.append('upstream spine is stale')
    log(f'  history (sqlite)                    : {config.HISTORY_SQLITE}')
    pf = publisher.preflight('') if False else None
    log(f'  publish destination                 : {publisher.PUBLISH_TABLE} '
        f"(order_management_copy) - {'approved' if config.gate('publish_approved') else 'NOT approved'}")
    log(f'  publish audience                    : {[a.get("assigned_user") for a in publisher.audience()] or "not configured"}')

    if problems:
        log('  PROBLEMS: ' + '; '.join(problems))
        return 1
    log('  preflight OK')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--preflight', action='store_true')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--live', action='store_true', help='require a live ownership source')
    ap.add_argument('--manual-full', action='store_true')
    ap.add_argument('--asin')
    ap.add_argument('--account')
    ap.add_argument('--marketplace')
    ap.add_argument('--resume')
    ap.add_argument('--alerts')
    ap.add_argument('--batch-size', type=int)
    ap.add_argument('--publish', action='store_true',
                    help='publish the run to the PH Dashboard (refused unless approved)')
    ap.add_argument('--skip-freshness', action='store_true',
                    help='run even if the upstream spine is stale (recorded in the log)')
    ap.add_argument('--dry-run', action='store_true',
                    help='resolve the source and count work, but write no results')
    a = ap.parse_args()

    if a.preflight:
        return preflight()

    h = History()

    if a.status:
        last = h.last_successful_run()
        log(f'last successful run: {json.dumps(last, indent=1) if last else "none"}')
        for r in h.recent_runs(10):
            log(f"  {r['run_id']}  {r['mode']:13} {r['status']:22} "
                f"checked={r['checked']}/{r['total_eligible']} "
                f"YES={r['buy_box_yes']} NO={r['buy_box_no']} NV={r['not_verified']} "
                f"ERR={r['check_error']}")
        return 0

    if a.alerts:
        res = AlertEngine(h, log=log).dispatch(a.alerts, dry_run=True)
        log(json.dumps({k: v for k, v in res.items() if k != 'payloads'}, indent=1))
        return 0

    eng = Engine(h, log=log)

    if a.asin:
        if not (a.account and a.marketplace):
            log('--asin requires --account and --marketplace')
            return 2
        try:
            res = eng.check_single(a.asin, a.account, a.marketplace, prefer_live=True)
        except sources.SourceUnavailable as e:
            log(f'no live source available: {e}')
            log('falling back is NOT automatic - re-run without --live to use historical data')
            return 1
        log(json.dumps(res, indent=1))
        return 0

    if a.dry_run:
        try:
            src, notes = sources.resolve(a.live)
            log(f'would use source: {src.name}')
        except sources.SourceUnavailable as e:
            log(f'no source: {e}')
            return 1
        log(f'eligible records: {len(load_eligible())}')
        log('dry run - nothing written')
        return 0

    mode = 'manual_full' if a.manual_full else 'full_daily'

    fresh, detail = spine_freshness()
    log(f"upstream freshness: {'OK' if fresh else 'STALE'} - {detail}")
    if not fresh and not a.skip_freshness:
        log('REFUSED: upstream ASIN refresh has not completed. '
            'Restage the PH spine, or pass --skip-freshness to override deliberately.')
        return 5

    try:
        res = eng.run(mode, prefer_live=a.live, run_id=a.resume,
                      resume=bool(a.resume), batch_size=a.batch_size)
    except RunLocked as e:
        log(f'REFUSED: {e}')
        return 3
    except sources.SourceUnavailable as e:
        log(f'REFUSED: {e}')
        return 1
    log(json.dumps(res, indent=1))

    pub = publisher.publish(res['run_id'],
                            dry_run=None if a.publish else True, log=log)
    log(f"publish: {'DRY RUN' if pub['dry_run'] else 'LIVE'} -> {pub['destination']} "
        f"({pub['published']} row(s))")

    alert = AlertEngine(h, log=log).dispatch(res['run_id'], dry_run=True)
    log(f"alerts (dry run): {alert['alerted']} would fire, {alert['rejected']} rejected "
        f"- {alert['priority_detail']}")
    return 0 if res['status'] == 'completed' else 4


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        log('UNHANDLED:\n' + traceback.format_exc())
        sys.exit(9)
