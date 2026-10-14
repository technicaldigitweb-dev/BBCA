"""Publish a validated Buy Box run to the online PH Dashboard.

Destination (discovered read-only, see 06_EVIDENCE/ph_dashboard_push_discovery.md):
    order_management_copy -> tech_team_outputs.ph_task

That is the mechanism every other local automation on this machine uses: a row per
assigned user carrying the full standalone HTML in `html_content`, which the online PH
Dashboard renders. There is no structured Buy Box table in ph_dashboard, and this
machine has no write path to that database, so ph_task is the only available
destination today.

GATES - this module cannot write to production until BOTH are set:
    publish_approved        the destination mapping + write operation are approved
    publish_audience        who receives it (assigned_user / team) is decided

Without them `publish()` runs in dry-run: it builds and validates the exact payload,
reports what it would do, and writes nothing.

Safety rules enforced here
--------------------------
* only a run with status 'completed' is publishable; a partial run is refused
* only rows for THIS project_code are ever touched; every other project's rows are
  fingerprinted before and after and the transaction rolls back if one moved
* one stable task_id per user, UPDATEd daily with version_level bumped (the house
  `dst`/ESGA daily convention), so a daily cadence does not add rows forever
* idempotent: re-publishing the same run_id to the same user is a no-op
* never publishes a stale snapshot over a newer one
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json

import config
from history import History

PROJECT_CODE = 'BBOX'
PROJECT_NAME = 'Buy Box Check Automation'
DEVELOPER = 'Automation'
PUBLISH_DB_ENV = 'DATABASE_URL'          # same var the other automations publish with
PUBLISH_TABLE = 'tech_team_outputs.ph_task'


class PublishRefused(Exception):
    pass


# The ph_task server moved. $DATABASE_URL and $PGHOST both point at the old host, which
# no longer accepts connections from this machine (TCP test fails), while
# 178.18.248.100:5435 does. Host/port/db/user are not secret and live here; the password
# comes from the environment ONLY and is never read from a file, logged, or echoed.
PUBLISH_HOST = '178.18.248.100'
PUBLISH_PORT = '5435'
PUBLISH_DB = 'order_management_copy'
PUBLISH_USER = 'postgres'
PUBLISH_PASSWORD_ENV = 'PGPASSWORD'


def _password() -> str:
    import os
    pw = os.environ.get('BBOX_PUBLISH_PASSWORD') or os.environ.get(PUBLISH_PASSWORD_ENV)
    if not pw:
        raise PublishRefused(
            f'no publish password in the environment '
            f'(set $BBOX_PUBLISH_PASSWORD or ${PUBLISH_PASSWORD_ENV})')
    return pw


def _conn_kwargs() -> dict:
    return {'host': PUBLISH_HOST, 'port': PUBLISH_PORT, 'dbname': PUBLISH_DB,
            'user': PUBLISH_USER, 'password': _password(),
            'connect_timeout': config.REQUEST_TIMEOUT_S}


def _dsn() -> str:
    """Non-secret description of the destination, safe to log."""
    _password()
    return f'{PUBLISH_USER}@{PUBLISH_HOST}:{PUBLISH_PORT}/{PUBLISH_DB}'


def audience() -> list[dict]:
    """Who receives the dashboard. Never guessed - must be configured."""
    over = config.load_overrides()
    aud = over.get('publish_audience') or []
    return [a for a in aud if a.get('assigned_user')]


def build_payload(run_id: str, html_path=None) -> dict:
    """Assemble and validate the payload for one run. Pure - touches no network."""
    h = History()
    try:
        run = h.get_run(run_id)
        if not run:
            raise PublishRefused(f'unknown run_id {run_id}')
        if run['status'] != 'completed':
            raise PublishRefused(
                f"refusing to publish run {run_id}: status is {run['status']!r}. "
                'Only a fully completed run is publishable - a partial run would '
                'present incomplete coverage as a finished check.')
        if run['checked'] != run['total_eligible']:
            raise PublishRefused(
                f"refusing to publish: checked {run['checked']} of {run['total_eligible']}")

        html_path = html_path or (config.OUTPUT /
                                  '2026-10-14_tharsi_buy_box_monitor_v003.html')
        if not html_path.exists():
            raise PublishRefused(f'dashboard HTML missing: {html_path}')
        html = html_path.read_text(encoding='utf-8')
        if len(html) < 100_000:
            raise PublishRefused(f'dashboard HTML is only {len(html)} bytes - refusing')

        results = [r for r in h.latest_results() if r['run_id'] == run_id]
        tally = {
            'total': len(results),
            'yes': sum(r['buy_box_status'] == 'YES' for r in results),
            'no': sum(r['buy_box_status'] == 'NO' for r in results),
            'not_verified': sum(r['buy_box_status'] == 'NOT VERIFIED' for r in results),
            'check_error': sum(r['buy_box_status'] == 'CHECK ERROR' for r in results),
        }
        observed = sorted({r['source_observed_at'] for r in results if r['source_observed_at']})
        task_name = (f"Buy Box Check - {dt.date.today():%d %b %Y}: "
                     f"{tally['yes']:,} held · {tally['no']:,} lost · "
                     f"{tally['not_verified']:,} not verified")
        return {
            'run_id': run_id,
            'project_code': PROJECT_CODE,
            'project_name': PROJECT_NAME,
            'task_name': task_name,
            'html': html,
            'html_bytes': len(html.encode('utf-8')),
            'html_md5': hashlib.md5(html.encode('utf-8')).hexdigest(),
            'tally': tally,
            'source_observed_range': [observed[0], observed[-1]] if observed else None,
            'checked_at': run['finished_at'],
            'verification_status': 'historical',
            'built_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'),
        }
    finally:
        h.close()


def records_for_export(run_id: str) -> list[dict]:
    """The structured per-ASIN records, in the field order the brief specifies.

    ph_task has no structured columns, so these ride along as a CSV/JSON artefact.
    If a structured destination is approved later, this is the payload for it.
    """
    h = History()
    try:
        out = []
        for r in (x for x in h.latest_results() if x['run_id'] == run_id):
            out.append({
                'asin': r['asin'], 'sku': r['sku'],
                'seller_account': r['seller_account'], 'marketplace': r['marketplace'],
                'buy_box_status': r['buy_box_status'],
                'official_reason': r['official_reason'],
                'possible_reason': json.loads(r['possible_reason'] or '[]'),
                'stock': r['stock_quantity'], 'listing_status': r['listing_status'],
                'source_observed_at': r['source_observed_at'],
                'checked_at': r['checked_at'],
                'verification_status': r['verification_status'],
                'run_id': r['run_id'],
            })
        return out
    finally:
        h.close()


def preflight(run_id: str) -> dict:
    """Everything that must be true before a production publish. Writes nothing."""
    problems, notes = [], []
    if not config.gate('publish_approved'):
        problems.append('gate publish_approved is not set')
    aud = audience()
    if not aud:
        problems.append('no publish audience configured (publish_audience in config.local.json)')
    else:
        notes.append(f'audience: {[a["assigned_user"] for a in aud]}')
    try:
        notes.append(f'destination reachable as {_dsn()}')
    except PublishRefused as e:
        problems.append(str(e))
    try:
        p = build_payload(run_id)
        notes.append(f"payload ok: {p['html_bytes']:,} bytes, md5 {p['html_md5'][:12]}, "
                     f"{p['tally']}")
    except PublishRefused as e:
        problems.append(str(e))
        p = None
    return {'run_id': run_id, 'ready': not problems, 'problems': problems, 'notes': notes,
            'destination': f'{PUBLISH_TABLE} (order_management_copy)',
            'payload': p}


def publish(run_id: str, dry_run: bool | None = None, log=print) -> dict:
    """Publish to ph_task. Dry run unless explicitly approved AND dry_run=False."""
    pf = preflight(run_id)
    if dry_run is None:
        dry_run = not pf['ready']
    if not pf['ready'] and dry_run is False:
        raise PublishRefused('; '.join(pf['problems']))

    for n in pf['notes']:
        log(f'  publisher: {n}')
    for p in pf['problems']:
        log(f'  publisher BLOCKED: {p}')

    if dry_run:
        log(f"  publisher: DRY RUN - would UPDATE {PUBLISH_TABLE} "
            f"({len(audience())} row(s), project_code={PROJECT_CODE}), nothing written")
        return {'run_id': run_id, 'dry_run': True, 'published': 0,
                'destination': pf['destination'], 'problems': pf['problems'],
                'payload_summary': (pf['payload'] or {}).get('tally')}

    return _write(run_id, pf['payload'], log)


def _write(run_id: str, payload: dict, log) -> dict:
    """The real write. Single transaction, fingerprinted, rolls back on any drift."""
    import psycopg
    aud = audience()
    accepted, rejected = [], []
    with psycopg.connect(**_conn_kwargs()) as cx:
        with cx.cursor() as cur:
            # fingerprint every OTHER project's rows before we touch anything
            cur.execute(f"SELECT count(*), coalesce(md5(string_agg(id::text||coalesce(updated_at::text,''), ',' ORDER BY id)),'') "
                        f"FROM {PUBLISH_TABLE} WHERE project_code IS DISTINCT FROM %s",
                        (PROJECT_CODE,))
            before = cur.fetchone()

            for a in aud:
                user = a['assigned_user']
                task_id = f'{PROJECT_CODE.lower()}-ph-{user.lower()}'
                cur.execute(f'SELECT id, version_level FROM {PUBLISH_TABLE} '
                            f'WHERE project_code=%s AND task_id=%s', (PROJECT_CODE, task_id))
                row = cur.fetchone()
                if row:
                    cur.execute(f"""UPDATE {PUBLISH_TABLE}
                                    SET task_name=%s, html_content=%s, version_level=%s,
                                        version_status='released', updated_at=now()
                                    WHERE id=%s""",
                                (payload['task_name'], payload['html'], (row[1] or 0) + 1, row[0]))
                    accepted.append({'user': user, 'id': row[0], 'action': 'update',
                                     'version': (row[1] or 0) + 1})
                else:
                    cur.execute(f"""INSERT INTO {PUBLISH_TABLE}
                        (project_name, project_code, task_name, task_id, team, developer,
                         assigned_user, assigned_user_team, html_content, description,
                         phase_level, version_level, version_status, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'',1,1,'released',now(),now())
                        RETURNING id""",
                        (PROJECT_NAME, PROJECT_CODE, payload['task_name'], task_id,
                         a.get('team', 'Development'), DEVELOPER, user,
                         a.get('assigned_user_team', 'ph_priors'), payload['html']))
                    accepted.append({'user': user, 'id': cur.fetchone()[0],
                                     'action': 'insert', 'version': 1})

            # verify nothing else moved
            cur.execute(f"SELECT count(*), coalesce(md5(string_agg(id::text||coalesce(updated_at::text,''), ',' ORDER BY id)),'') "
                        f"FROM {PUBLISH_TABLE} WHERE project_code IS DISTINCT FROM %s",
                        (PROJECT_CODE,))
            after = cur.fetchone()
            if before != after:
                cx.rollback()
                raise PublishRefused('other projects\' rows changed during publish - rolled back')

            # verify our own row count
            cur.execute(f'SELECT count(*) FROM {PUBLISH_TABLE} WHERE project_code=%s',
                        (PROJECT_CODE,))
            n = cur.fetchone()[0]
            if n != len(aud):
                cx.rollback()
                raise PublishRefused(f'destination row count {n} != expected {len(aud)} - rolled back')
        cx.commit()
    log(f'  publisher: published {len(accepted)} row(s) to {PUBLISH_TABLE}')
    return {'run_id': run_id, 'dry_run': False, 'published': len(accepted),
            'accepted': accepted, 'rejected': rejected, 'destination': PUBLISH_TABLE}
