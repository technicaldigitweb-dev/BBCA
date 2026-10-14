"""Buy Box check history.

Backing store is local SQLite. Postgres is a PROPOSAL ONLY
(migrations/001_buy_box_history.sql) and is never created or written here - that needs
the history_write_approved gate plus DBA action.

Design
------
`runs`    one row per execution, with the full outcome tally.
`results` one row per (run_id, asin, seller_account, marketplace).

Idempotency: results are keyed on (run_id, asin, seller_account, marketplace), so
re-running the SAME run_id upserts rather than duplicating. A NEW run_id always
creates new rows, which is what preserves daily history.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id              TEXT PRIMARY KEY,
  mode                TEXT NOT NULL,
  source              TEXT,
  started_at          TEXT NOT NULL,
  finished_at         TEXT,
  status              TEXT NOT NULL,           -- running|completed|completed_with_errors|failed
  total_eligible      INTEGER DEFAULT 0,
  checked             INTEGER DEFAULT 0,
  buy_box_yes         INTEGER DEFAULT 0,
  buy_box_no          INTEGER DEFAULT 0,
  not_verified        INTEGER DEFAULT 0,
  check_error         INTEGER DEFAULT 0,
  reason_unknown      INTEGER DEFAULT 0,
  failed_requests     INTEGER DEFAULT 0,
  skipped             INTEGER DEFAULT 0,
  detail              TEXT
);
CREATE TABLE IF NOT EXISTS results (
  run_id              TEXT NOT NULL,
  asin                TEXT NOT NULL,
  sku                 TEXT,
  seller_account      TEXT NOT NULL,
  seller_id           TEXT,
  marketplace         TEXT NOT NULL,
  buy_box_status      TEXT NOT NULL,
  official_reason     TEXT,
  possible_reason     TEXT,
  stock_quantity      INTEGER,
  listing_status      TEXT,
  evidence_source     TEXT,
  source_observed_at  TEXT,
  checked_at          TEXT,
  live_verified_at    TEXT,
  error_code          TEXT,
  verification_status TEXT,
  detail              TEXT,
  PRIMARY KEY (run_id, asin, seller_account, marketplace)
);
CREATE INDEX IF NOT EXISTS ix_results_asin ON results(asin, seller_account, marketplace);
CREATE INDEX IF NOT EXISTS ix_results_checked ON results(checked_at);
CREATE TABLE IF NOT EXISTS alerts_sent (
  alert_key   TEXT PRIMARY KEY,               -- dedupe key
  run_id      TEXT,
  asin        TEXT,
  seller_account TEXT,
  marketplace TEXT,
  channel     TEXT,
  dry_run     INTEGER,
  sent_at     TEXT,
  payload     TEXT
);
"""


class History:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or config.HISTORY_SQLITE)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.cx = sqlite3.connect(str(self.path))
        self.cx.row_factory = sqlite3.Row
        self.cx.executescript(SCHEMA)
        self.cx.commit()

    def close(self):
        self.cx.close()

    # --- runs ---------------------------------------------------------------
    def start_run(self, run_id: str, mode: str, source: str, total_eligible: int) -> None:
        self.cx.execute(
            'INSERT OR REPLACE INTO runs(run_id,mode,source,started_at,status,total_eligible) '
            'VALUES(?,?,?,?,?,?)',
            (run_id, mode, source, dt.datetime.now().astimezone().isoformat(timespec='seconds'),
             'running', total_eligible))
        self.cx.commit()

    def finish_run(self, run_id: str, status: str, tally: dict, detail: str = '') -> None:
        self.cx.execute("""
            UPDATE runs SET finished_at=?, status=?, checked=?, buy_box_yes=?, buy_box_no=?,
                   not_verified=?, check_error=?, reason_unknown=?, failed_requests=?,
                   skipped=?, detail=?
            WHERE run_id=?""",
            (dt.datetime.now().astimezone().isoformat(timespec='seconds'), status,
             tally.get('checked', 0), tally.get('YES', 0), tally.get('NO', 0),
             tally.get('NOT VERIFIED', 0), tally.get('CHECK ERROR', 0),
             tally.get('reason_unknown', 0), tally.get('failed_requests', 0),
             tally.get('skipped', 0), detail, run_id))
        self.cx.commit()

    def get_run(self, run_id: str) -> dict | None:
        r = self.cx.execute('SELECT * FROM runs WHERE run_id=?', (run_id,)).fetchone()
        return dict(r) if r else None

    def recent_runs(self, limit: int = 20) -> list[dict]:
        return [dict(r) for r in self.cx.execute(
            'SELECT * FROM runs ORDER BY started_at DESC LIMIT ?', (limit,))]

    def last_successful_run(self) -> dict | None:
        r = self.cx.execute(
            "SELECT * FROM runs WHERE status IN ('completed','completed_with_errors') "
            "ORDER BY started_at DESC LIMIT 1").fetchone()
        return dict(r) if r else None

    # --- results ------------------------------------------------------------
    def save_results(self, run_id: str, results: list) -> int:
        rows = []
        for r in results:
            d = r.as_dict() if hasattr(r, 'as_dict') else dict(r)
            rows.append((run_id, d['asin'], d.get('sku'), d['seller_account'], d.get('seller_id'),
                         d['marketplace'], d['buy_box_status'], d.get('official_reason'),
                         json.dumps(d.get('possible_reason') or []), d.get('stock_quantity'),
                         d.get('listing_status'), d.get('evidence_source'),
                         d.get('source_observed_at'), d.get('checked_at'),
                         d.get('live_verified_at'), d.get('error_code'),
                         d.get('verification_status'), d.get('detail')))
        self.cx.executemany(
            'INSERT OR REPLACE INTO results VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
        self.cx.commit()
        return len(rows)

    def latest_results(self, limit: int | None = None) -> list[dict]:
        """Most recent result per (asin, seller_account, marketplace)."""
        q = """
          SELECT r.* FROM results r
          JOIN (SELECT asin, seller_account, marketplace, MAX(checked_at) AS mx
                FROM results GROUP BY 1,2,3) m
            ON r.asin=m.asin AND r.seller_account=m.seller_account
           AND r.marketplace=m.marketplace AND r.checked_at=m.mx
        """
        if limit:
            q += f' LIMIT {int(limit)}'
        return [dict(x) for x in self.cx.execute(q)]

    def history_for(self, asin: str, seller_account: str, marketplace: str) -> list[dict]:
        return [dict(x) for x in self.cx.execute(
            'SELECT * FROM results WHERE asin=? AND seller_account=? AND marketplace=? '
            'ORDER BY checked_at DESC', (asin, seller_account, marketplace))]

    def previous_status(self, asin: str, seller_account: str, marketplace: str,
                        before_run: str) -> dict | None:
        r = self.cx.execute(
            'SELECT * FROM results WHERE asin=? AND seller_account=? AND marketplace=? '
            'AND run_id<>? ORDER BY checked_at DESC LIMIT 1',
            (asin, seller_account, marketplace, before_run)).fetchone()
        return dict(r) if r else None

    def daily_history(self, days: int = 14) -> list[dict]:
        return [dict(x) for x in self.cx.execute("""
            SELECT substr(checked_at,1,10) AS day,
                   SUM(buy_box_status='YES')          AS yes,
                   SUM(buy_box_status='NO')           AS no,
                   SUM(buy_box_status='NOT VERIFIED') AS not_verified,
                   SUM(buy_box_status='CHECK ERROR')  AS check_error,
                   COUNT(*) AS total
            FROM results GROUP BY day ORDER BY day DESC LIMIT ?""", (days,))]

    # --- alerts -------------------------------------------------------------
    def alert_already_sent(self, alert_key: str) -> bool:
        return self.cx.execute('SELECT 1 FROM alerts_sent WHERE alert_key=?',
                               (alert_key,)).fetchone() is not None

    def record_alert(self, alert_key: str, run_id: str, rec: dict, channel: str,
                     dry_run: bool, payload: dict) -> None:
        self.cx.execute(
            'INSERT OR REPLACE INTO alerts_sent VALUES(?,?,?,?,?,?,?,?,?)',
            (alert_key, run_id, rec['asin'], rec['seller_account'], rec['marketplace'],
             channel, 1 if dry_run else 0,
             dt.datetime.now().astimezone().isoformat(timespec='seconds'),
             json.dumps(payload)))
        self.cx.commit()
