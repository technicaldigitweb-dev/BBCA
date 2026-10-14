"""Buy Box Check Automation - configuration and approval gates.

Every value that needs a business or operational decision lives here as an explicit
gate that defaults to OFF. Nothing activates by being written; it activates by being
approved and set. `python run.py --preflight` prints the current gate state.
"""
from __future__ import annotations

import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUTO = ROOT / 'automation'
DATA = ROOT / '04_DATA'
EVID = ROOT / '06_EVIDENCE'
OUTPUT = ROOT / '05_OUTPUT'
LOGS = AUTO / 'logs'
STATE = AUTO / 'state'
MIGRATIONS = AUTO / 'migrations'

# --- data sources (read-only) ------------------------------------------------
SOURCE_DB_ENV = 'WLP_SOURCE_DB_URL'      # ledsone warehouse, tech_user, read-only
SOURCE_DB_NAME = 'ledsone'
# ph_dashboard has no direct DSN on this machine - it is reachable only through the
# read-only Ledsone_Database_MCP tool, so the spine is staged to 04_DATA by that route.
PH_SPINE_FILE = DATA / 'ph_spine.json'

ACCOUNTS = {8: 'LEDSone', 6: 'DCVoltage'}
MARKETPLACES = {23: 'UK', 10: 'DE', 9: 'FR', 14: 'IT'}
SITE_OF = {'UK': 'UK', 'DE': 'Germany', 'FR': 'France', 'IT': 'Italy'}

# Verified against stored SP-API Listings Items responses - see
# 06_EVIDENCE/seller_identity_verification.md
SELLER_IDS = {'LEDSone': 'A1BXMEJKH8MYIL', 'DCVoltage': 'A3UNAW6KG6QUOJ'}
SELLER_ID_STATUS = 'VERIFIED'
# sub_source 9 (SRM Suppliers) trades on the same ASINs but its token is unconfirmed.
GROUP_ACCOUNTS = {'SRM Suppliers', 'SRM'}

# Buy Box reading window: the newest report row per ASIN within this many days.
REPORT_WINDOW_DAYS = 7

# --- history -----------------------------------------------------------------
# Local SQLite is used for all development and testing. Postgres is a proposal only
# (migrations/001_buy_box_history.sql) and is NOT applied.
HISTORY_SQLITE = STATE / 'buy_box_history.db'
HISTORY_PG_TABLE = 'buy_box.check_history'          # proposed, not created

# --- reliability -------------------------------------------------------------
BATCH_SIZE = int(os.environ.get('BBOX_BATCH_SIZE', '500'))
REQUEST_TIMEOUT_S = 30
MAX_RETRIES = 2                 # bounded; never applied to an access-control response
RETRY_BACKOFF_S = 5
CHECKPOINT_FILE = STATE / 'checkpoint.json'
RUNLOCK_FILE = STATE / 'run.lock'

# --- approval gates ----------------------------------------------------------
# Each stays False until the named owner decision is recorded. The engine reads these
# and refuses the corresponding action with a transparent reason rather than guessing.
GATES = {
    'live_ownership_source_approved': False,   # SP-API Product Pricing access
    'reason_rules_approved': False,            # the 8 ordered checks
    'daily_schedule_approved': False,          # run time + timezone + machine
    'history_write_approved': False,           # Postgres write permission
    'priority_rule_approved': False,           # what counts as a high-priority ASIN
    'alert_delivery_approved': False,          # channel + recipients
}

# --- scheduler (template values, inactive until approved) --------------------
# House convention from ph_dashboard.scheduler_scheduledtask: cron + Asia/Colombo.
SCHEDULE_TIMEZONE = 'Asia/Colombo'
SCHEDULE_CRON = None      # deliberately unset - do NOT default to an hour
# The PH spine is refreshed by `overall_asin_daily` at 35 7 * * * Asia/Colombo, so any
# Buy Box run must start after that job completes.
UPSTREAM_DEPENDENCY = {'task': 'overall_asin_daily', 'cron': '35 7 * * *',
                       'timezone': 'Asia/Colombo'}

# --- alerts ------------------------------------------------------------------
ALERT_DRY_RUN_DEFAULT = True
ALERT_CHANNEL = None        # 'email' | 'discord' | 'internal' - unset until approved
ALERT_RECIPIENTS: list[str] = []
# Candidate high-priority source, NOT approved:
#   ph_dashboard.analytics_asinsegmentasin.priority
#   observed values: Scale, Fix Now, Quick Win, Growth Play, Maintain Selectively, Kill / Review
PRIORITY_SOURCE_CANDIDATE = 'analytics_asinsegmentasin.priority'
PRIORITY_VALUES_CANDIDATE = ['Scale', 'Fix Now']   # proposal only

LOCAL_CONFIG = AUTO / 'config.local.json'


def load_overrides() -> dict:
    """Operator overrides live outside version control and never contain secrets."""
    if LOCAL_CONFIG.exists():
        try:
            return json.loads(LOCAL_CONFIG.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def gate(name: str) -> bool:
    return bool(load_overrides().get('gates', {}).get(name, GATES.get(name, False)))


def blocked_gates() -> list[str]:
    return [g for g in GATES if not gate(g)]


def source_db_available() -> bool:
    return bool(os.environ.get(SOURCE_DB_ENV))


def source_db_dsn() -> str | None:
    return os.environ.get(SOURCE_DB_ENV)


for _d in (LOGS, STATE, MIGRATIONS):
    _d.mkdir(parents=True, exist_ok=True)
