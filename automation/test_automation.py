"""Buy Box Check Automation - isolated test suite.

Every test runs against a temporary SQLite history and SYNTHETIC fixtures. Synthetic
records use the TEST- prefix and are never written to 04_DATA or any dashboard.

    python test_automation.py            all tests
    python test_automation.py -v         show each assertion
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
import traceback
from pathlib import Path

import config
import sources
from sources import CheckResult
from history import History
from engine import Engine, _Lock, RunLocked, load_eligible
from alerts import AlertEngine

PASS, FAIL = [], []
VERBOSE = '-v' in sys.argv


def check(name, cond, info=''):
    (PASS if cond else FAIL).append((name, info))
    if VERBOSE or not cond:
        print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f'   [{info}]' if info else ''))


def tmp_hist() -> History:
    return History(Path(tempfile.mkdtemp()) / 'test_history.db')


# --- synthetic source --------------------------------------------------------
class FakeSource(sources.BuyBoxSource):
    """Deterministic source for isolated tests. Clearly synthetic."""
    name = 'TEST-fake'
    gives_live_ownership = True

    def __init__(self, plan: dict, live=True):
        self.plan = plan            # asin -> status
        self.calls = 0
        self._live = live

    def available(self):
        return True, 'ok'

    def check(self, rec):
        self.calls += 1
        st = self.plan.get(rec['asin'], 'NOT VERIFIED')
        now = dt.datetime.now().astimezone().isoformat(timespec='seconds')
        return CheckResult(
            asin=rec['asin'], seller_account=rec['seller_account'],
            marketplace=rec['marketplace'], sku=rec.get('sku'),
            buy_box_status=st,
            verification_status='live' if self._live else 'historical',
            evidence_source=self.name, checked_at=now,
            live_verified_at=now if self._live else None,
            seller_id=config.SELLER_IDS.get(rec['seller_account']),
            official_reason='Unknown' if st == 'NO' else 'Unknown',
            error_code='TEST_ERR' if st == 'CHECK ERROR' else None)


def recs(n, prefix='TEST-ASIN'):
    return [{'asin': f'{prefix}{i:04d}', 'seller_account': 'LEDSone',
             'marketplace': 'UK', 'sku': f'TEST-SKU{i}'} for i in range(n)]


# --- 1-3: execution modes ----------------------------------------------------
def t_modes():
    h = tmp_hist()
    e = Engine(h, log=lambda m: None)
    src = FakeSource({'TEST-ASIN0000': 'YES', 'TEST-ASIN0001': 'NO'})
    sources.REGISTRY['TEST-fake'] = src
    orig = sources.resolve
    sources.resolve = lambda live: (src, [])
    try:
        r1 = e.run('manual_single', recs(1))
        check('1. single-ASIN execution', r1['checked'] == 1 and r1['status'] == 'completed', r1['status'])

        r2 = e.run('full_daily', recs(5))
        check('2. full-list retrieval', r2['checked'] == 5 and r2['total_eligible'] == 5)

        rows = h.latest_results()
        row = [x for x in rows if x['asin'] == 'TEST-ASIN0000'][0]
        check('3. correct seller/marketplace mapping',
              row['seller_account'] == 'LEDSone' and row['marketplace'] == 'UK'
              and row['seller_id'] == config.SELLER_IDS['LEDSone'], row['seller_id'])
    finally:
        sources.resolve = orig
    return h


# --- 4: duplicate handling ---------------------------------------------------
def t_duplicates():
    h = tmp_hist()
    e = Engine(h, log=lambda m: None)
    src = FakeSource({'TEST-ASIN0000': 'YES'})
    orig = sources.resolve
    sources.resolve = lambda live: (src, [])
    try:
        dupes = recs(3) + recs(3)                      # same 3 records twice
        r = e.run('full_daily', dupes, run_id='dup-run')
        stored = h.cx.execute("SELECT COUNT(*) FROM results WHERE run_id='dup-run'").fetchone()[0]
        check('4a. duplicate inputs collapse at the grain', stored == 3, f'{stored} rows')

        e.run('full_daily', recs(3), run_id='dup-run')   # same run_id again
        stored2 = h.cx.execute("SELECT COUNT(*) FROM results WHERE run_id='dup-run'").fetchone()[0]
        check('4b. re-running the same run_id is idempotent', stored2 == 3, f'{stored2} rows')

        e.run('full_daily', recs(3), run_id='dup-run-2')
        total = h.cx.execute('SELECT COUNT(*) FROM results').fetchone()[0]
        check('4c. a new run_id preserves prior history', total == 6, f'{total} rows')
    finally:
        sources.resolve = orig


# --- 5: missing Buy Box source ----------------------------------------------
def t_missing_source():
    h = tmp_hist()
    e = Engine(h, log=lambda m: None)
    orig = sources.resolve

    def boom(live):
        raise sources.SourceUnavailable('TEST: no source')
    sources.resolve = boom
    try:
        r = e.run('full_daily', recs(2))
        check('5a. missing source fails the run', r['status'] == 'failed', r['status'])
        check('5b. failure is recorded transparently',
              'TEST: no source' in (h.get_run(r['run_id']) or {}).get('detail', ''))
    finally:
        sources.resolve = orig

    ok, why = sources.SpApiPricingSource().available()
    check('5c. SP-API reports unavailable, not fabricated', not ok and 'not approved' in why, why)
    res = sources.SpApiPricingSource().check({'asin': 'TEST-A', 'seller_account': 'LEDSone',
                                              'marketplace': 'UK'})
    check('5d. unavailable source yields CHECK ERROR, never YES/NO',
          res.buy_box_status == 'CHECK ERROR' and res.error_code == 'INTEGRATION_NOT_AVAILABLE')


# --- 6: stale reports --------------------------------------------------------
def t_stale():
    r = sources.HistoricalReportSource()
    check('6a. historical source never claims live ownership', not r.gives_live_ownership)
    fake = CheckResult(asin='TEST-A', seller_account='LEDSone', marketplace='UK',
                       buy_box_status='NO', verification_status='historical',
                       evidence_source='x', source_observed_at='2026-10-05',
                       checked_at='2026-10-14T00:00:00+05:30')
    check('6b. source_observed_at and checked_at are distinct',
          fake.source_observed_at != fake.checked_at[:10])
    check('6c. historical result sets no live_verified_at', fake.live_verified_at is None)


# --- 7: CHECK ERROR handling -------------------------------------------------
def t_check_error():
    h = tmp_hist()
    e = Engine(h, log=lambda m: None)
    src = FakeSource({'TEST-ASIN0000': 'CHECK ERROR', 'TEST-ASIN0001': 'YES'})
    orig = sources.resolve
    sources.resolve = lambda live: (src, [])
    try:
        r = e.run('full_daily', recs(2))
        check('7a. CHECK ERROR is counted', r.get('CHECK ERROR') == 1)
        check('7b. a run with errors is NOT reported completed',
              r['status'] == 'completed_with_errors', r['status'])
        row = [x for x in h.latest_results() if x['asin'] == 'TEST-ASIN0000'][0]
        check('7c. error_code is preserved', row['error_code'] == 'TEST_ERR')
    finally:
        sources.resolve = orig


# --- 8: checkpoint / resume --------------------------------------------------
def t_resume():
    """Simulate a genuine interruption: batch 1 succeeds, batch 2 dies, then resume.

    A run that completed cleanly has its checkpoint cleared, so there is nothing to
    resume - that is why this test interrupts the run rather than re-running a clean one.
    """
    h = tmp_hist()
    e = Engine(h, log=lambda m: None)

    class DiesOnSecondBatch(FakeSource):
        def __init__(self):
            super().__init__({})
            self.batches = 0

        def check_batch(self, batch):
            self.batches += 1
            if self.batches >= 2:
                raise RuntimeError('TEST: interrupted')
            return super().check_batch(batch)

    broken = DiesOnSecondBatch()
    orig = sources.resolve
    sources.resolve = lambda live: (broken, [])
    try:
        r1 = e.run('full_daily', recs(10), run_id='rs-1', batch_size=5)
        check('8a. interrupted run is not reported completed',
              r1['status'] == 'completed_with_errors', r1['status'])
        check('8b. partial work was saved', r1['checked'] == 5, f"checked={r1['checked']}")
        check('8c. checkpoint survives an incomplete run',
              e._ckpt_path('rs-1').exists())
    finally:
        sources.resolve = orig

    good = FakeSource({})
    sources.resolve = lambda live: (good, [])
    try:
        r2 = e.run('full_daily', recs(10), run_id='rs-1', resume=True, batch_size=5)
        check('8d. resume only re-checks the outstanding records',
              good.calls == 5, f'{good.calls} calls (expected 5)')
        check('8e. resumed run reaches full coverage', r2['checked'] == 10, r2['checked'])
        stored = h.cx.execute("SELECT COUNT(*) FROM results WHERE run_id='rs-1'").fetchone()[0]
        check('8f. resume produced no duplicate rows', stored == 10, f'{stored} rows')
        check('8g. checkpoint cleared once the run is clean',
              not e._ckpt_path('rs-1').exists())
    finally:
        sources.resolve = orig


# --- 9: concurrent-run prevention -------------------------------------------
def t_lock():
    p = Path(tempfile.mkdtemp()) / 'run.lock'
    a, b = _Lock(p), _Lock(p)
    a.acquire('run-a')
    try:
        b.acquire('run-b')
        check('9a. second concurrent run is refused', False, 'lock did not hold')
    except RunLocked:
        check('9a. second concurrent run is refused', True)
    a.release()
    try:
        b.acquire('run-b')
        check('9b. lock is released for the next run', True)
        b.release()
    except RunLocked:
        check('9b. lock is released for the next run', False)
    p.write_text(json.dumps({'run_id': 'dead', 'pid': 999999}), encoding='utf-8')
    try:
        _Lock(p).acquire('run-c')
        check('9c. a stale lock from a dead PID is reclaimed', True)
    except RunLocked as e:
        check('9c. a stale lock from a dead PID is reclaimed', False, str(e))


# --- 10: scheduler configuration --------------------------------------------
def t_scheduler():
    check('10a. no run hour is silently defaulted', config.SCHEDULE_CRON is None)
    check('10b. timezone follows the house convention',
          config.SCHEDULE_TIMEZONE == 'Asia/Colombo', config.SCHEDULE_TIMEZONE)
    check('10c. schedule gate is closed', not config.gate('daily_schedule_approved'))
    ps = (config.AUTO / 'scheduler.ps1').read_text(encoding='utf-8')
    check('10d. scheduler template requires -Confirm to register', '-Confirm to register' in ps)
    check('10e. scheduler template refuses without an approved RunTime',
          'BLOCKED: -RunTime is required' in ps)
    check('10f. scheduler uses IgnoreNew for overlap prevention',
          'MultipleInstances IgnoreNew' in ps)
    check('10g. upstream dependency is documented',
          config.UPSTREAM_DEPENDENCY['task'] == 'overall_asin_daily')


# --- 11: manual backend interface -------------------------------------------
def t_api():
    import api
    for ep in ('/api/buy-box/health', '/api/buy-box/check', '/api/buy-box/check-all',
               '/api/buy-box/runs/', '/api/buy-box/results/latest', '/api/buy-box/history'):
        check(f'11. endpoint present {ep}', ep in api.__doc__ or ep in open(
            config.AUTO / 'api.py', encoding='utf-8').read())
    src = open(config.AUTO / 'api.py', encoding='utf-8').read()
    check('11z. backend binds to localhost by default', "default='127.0.0.1'" in src)
    check('11y. no credential is sent to the browser',
          'PGPASSWORD' not in src and 'WLP_SOURCE_DB_URL' not in src.split('config.')[0])


# --- 12: history persistence -------------------------------------------------
def t_history():
    h = tmp_hist()
    now = dt.datetime.now().astimezone().isoformat(timespec='seconds')
    h.start_run('h1', 'full_daily', 'TEST-fake', 1)
    h.save_results('h1', [CheckResult(asin='TEST-A', seller_account='LEDSone', marketplace='UK',
                                      buy_box_status='YES', verification_status='live',
                                      evidence_source='TEST', checked_at=now)])
    h.finish_run('h1', 'completed', {'checked': 1, 'YES': 1})
    check('12a. run record persists', h.get_run('h1')['status'] == 'completed')
    check('12b. latest results retrievable', len(h.latest_results()) == 1)
    check('12c. history retrievable', len(h.history_for('TEST-A', 'LEDSone', 'UK')) == 1)
    check('12d. daily history retrievable', len(h.daily_history()) >= 1)
    check('12e. last successful run retrievable', h.last_successful_run()['run_id'] == 'h1')

    sql = (config.MIGRATIONS / '001_buy_box_history.sql').read_text(encoding='utf-8')
    check('12f. Postgres migration is marked NOT APPLIED', 'STATUS: NOT APPLIED' in sql)
    check('12g. migration has a rollback section', 'Rollback' in sql)
    check('12h. history write gate is closed', not config.gate('history_write_approved'))


# --- 13-14: alerts -----------------------------------------------------------
def t_alerts():
    h = tmp_hist()
    now = dt.datetime.now().astimezone().isoformat(timespec='seconds')
    # previous run: we HELD the buy box, verified live
    h.start_run('a0', 'full_daily', 'TEST-fake', 1)
    h.save_results('a0', [CheckResult(asin='TEST-A', seller_account='LEDSone', marketplace='UK',
                                      buy_box_status='YES', verification_status='live',
                                      evidence_source='TEST', checked_at=now)])
    h.finish_run('a0', 'completed', {'checked': 1})
    # current run: lost it, verified live
    h.start_run('a1', 'full_daily', 'TEST-fake', 1)
    h.save_results('a1', [CheckResult(asin='TEST-A', seller_account='LEDSone', marketplace='UK',
                                      buy_box_status='NO', verification_status='live',
                                      evidence_source='TEST', checked_at=now)])
    h.finish_run('a1', 'completed', {'checked': 1})

    ae = AlertEngine(h, log=lambda m: None)
    res = ae.dispatch('a1', dry_run=True)
    check('13a. dry run transmits nothing', res['dry_run'] is True)
    check('13b. no alert without an approved priority rule',
          res['alerted'] == 0 and not res['priority_rule_approved'])
    check('13c. rejection reason is explicit',
          any('high-priority' in w for r in res['rejection_sample'] for w in r['why_not']))

    ev = ae.evaluate('a1')
    rej = {r['asin']: r['why_not'] for r in ev['rejected']}
    check('13d. the only blocker is the priority rule (transition was valid)',
          all('no approved high-priority rule' in w or 'not high-priority' in w
              for w in rej.get('TEST-A', [])), str(rej.get('TEST-A')))

    # a stale historical NO must never alert
    h2 = tmp_hist()
    h2.start_run('b0', 'full_daily', 'x', 1)
    h2.save_results('b0', [CheckResult(asin='TEST-B', seller_account='LEDSone', marketplace='UK',
                                       buy_box_status='YES', verification_status='live',
                                       evidence_source='TEST', checked_at=now)])
    h2.finish_run('b0', 'completed', {})
    h2.start_run('b1', 'full_daily', 'x', 1)
    h2.save_results('b1', [CheckResult(asin='TEST-B', seller_account='LEDSone', marketplace='UK',
                                       buy_box_status='NO', verification_status='historical',
                                       evidence_source='TEST', checked_at=now)])
    h2.finish_run('b1', 'completed', {})
    ev2 = AlertEngine(h2, log=lambda m: None).evaluate('b1')
    why = [w for r in ev2['rejected'] if r['asin'] == 'TEST-B' for w in r['why_not']]
    check('13e. a stale historical NO is never a loss event',
          any('stale historical reading is not a loss event' in w for w in why), str(why))

    # dedupe
    r1 = {'asin': 'TEST-A', 'seller_account': 'LEDSone', 'marketplace': 'UK',
          'checked_at': now}
    k = AlertEngine.alert_key(r1)
    h.record_alert(k, 'a1', r1, 'dry-run', True, {})
    check('14. duplicate alerts are suppressed', h.alert_already_sent(k))
    check('14b. alert delivery gate is closed', not config.gate('alert_delivery_approved'))


# --- 15: failure recovery ----------------------------------------------------
def t_recovery():
    h = tmp_hist()
    e = Engine(h, log=lambda m: None)

    class Flaky(FakeSource):
        def __init__(self):
            super().__init__({})
            self.n = 0

        def check_batch(self, batch):
            self.n += 1
            if self.n == 1:
                raise RuntimeError('TEST: transient')
            return super().check_batch(batch)

    f = Flaky()
    orig = sources.resolve
    sources.resolve = lambda live: (f, [])
    try:
        r = e.run('full_daily', recs(3), batch_size=3)
        check('15a. a transient failure is retried and recovers',
              r['checked'] == 3 and f.n >= 2, f'{f.n} attempts')
    finally:
        sources.resolve = orig

    class Refuser(FakeSource):
        def check_batch(self, batch):
            raise sources.SourceUnavailable('TEST: refusal (cap exceeded)')

    sources.resolve = lambda live: (Refuser({}), [])
    try:
        r = e.run('full_daily', recs(3), batch_size=3)
        check('15b. a refusal is not retried and is reported as skipped',
              r['skipped'] == 3 and r['status'] == 'completed_with_errors', str(r))
    finally:
        sources.resolve = orig

    check('15c. browser source refuses bulk rather than scraping',
          sources.LiveBrowserSource.MAX_RECORDS <= 25)
    try:
        sources.LiveBrowserSource().check_batch(recs(50))
        check('15d. browser bulk cap is enforced', False)
    except sources.SourceUnavailable as ex:
        check('15d. browser bulk cap is enforced', 'not authorised' in str(ex))


# --- 16-17: real data + dashboard integrity ---------------------------------
def t_real_data():
    try:
        elig = load_eligible()
    except FileNotFoundError as e:
        check('16. eligible records load', False, str(e))
        return
    check('16a. eligible record count matches the dashboard grain', len(elig) == 20821, len(elig))
    keys = {(r['asin'], r['seller_account'], r['marketplace']) for r in elig}
    check('16b. no duplicates at the grain', len(keys) == len(elig))
    check('16c. only approved accounts', {r['seller_account'] for r in elig} <= set(config.SELLER_IDS))
    check('16d. only approved marketplaces',
          {r['marketplace'] for r in elig} <= set(config.MARKETPLACES.values()))

    v3 = config.OUTPUT / '2026-10-14_tharsi_buy_box_monitor_v003.html'
    check('17a. v003 dashboard still present', v3.exists())
    for old in ('v001', 'v002'):
        p = config.OUTPUT / f'2026-10-14_tharsi_buy_box_monitor_{old}.html'
        check(f'17b. {old} preserved', p.exists())
    body = v3.read_text(encoding='utf-8', errors='replace')
    check('17c. dashboard has no external asset', '<script src' not in body and '<link href' not in body)
    check('17d. no synthetic TEST- record reached the dashboard', 'TEST-ASIN' not in body)


def main():
    print('Buy Box Check Automation - test suite\n')
    for fn in (t_modes, t_duplicates, t_missing_source, t_stale, t_check_error, t_resume,
               t_lock, t_scheduler, t_api, t_history, t_alerts, t_recovery, t_real_data):
        try:
            fn()
        except Exception:
            check(f'{fn.__name__} raised', False, traceback.format_exc(limit=2))
    print(f'\n{len(PASS)}/{len(PASS) + len(FAIL)} passed')
    if FAIL:
        print('\nFAILURES:')
        for n, i in FAIL:
            print(f'  {n}  {i}')
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
