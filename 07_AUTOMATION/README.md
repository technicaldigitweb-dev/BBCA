# 07_AUTOMATION — index into `automation/`

**The automation engine lives in `../automation/`. It is NOT copied here.**

A second copy would create exactly the duplicate source of truth the Mini-AIOS guide
forbids, and would break the scheduled task, which runs
`automation/run.py` with `automation/` as its working directory. This folder is a map,
not a mirror.

Full operations documentation: **`../automation/README.md`**

---

## Modules

| File | Purpose | Inputs | Outputs | Status |
|---|---|---|---|---|
| `config.py` | paths, accounts, marketplaces, seller IDs, **six approval gates** | `config.local.json` (git-ignored) | constants, `gate()` | stable |
| `sources.py` | the source adapter interface + 3 adapters | `$WLP_SOURCE_DB_URL`, CDP browser | `CheckResult` | stable |
| `engine.py` | 3 execution modes, batching, checkpoint/resume, run lock | eligible records | run tally, history rows | stable |
| `history.py` | SQLite run + result + alert store | `CheckResult` list | `../automation/state/buy_box_history.db` | stable |
| `alerts.py` | 5-condition trigger, dedupe, dry run | a completed run | alert payloads (dry run only) | stable |
| `publisher.py` | PH Dashboard publication to `ph_task` | completed run + dashboard HTML | `ph_task` row (**never executed**) | built, unused |
| `api.py` | local backend for the Run Check button | HTTP on `127.0.0.1:8787` | JSON | stable |
| `run.py` | CLI entry point and daily orchestration | flags | logs, history, dry-run publish | stable |
| `scheduler.ps1` | Windows Task Scheduler template | `-RunTime`, `-Confirm` | a registered task (**never registered**) | template |
| `test_automation.py` | 69 isolated tests, synthetic fixtures | — | pass/fail | **69/69** |
| `../automation/migrations/001_buy_box_history.sql` | proposed Postgres schema | — | — | **NOT APPLIED** |

## Dependencies

| | |
|---|---|
| Python | 3.13 (`C:\Program Files\Python313`) |
| Packages | `psycopg` (v3), `playwright` (live checks only) |
| Environment | `$WLP_SOURCE_DB_URL` required; `$BBOX_PUBLISH_PASSWORD` or `$PGPASSWORD` for publishing |
| Upstream data | `04_DATA/ph_spine.json`, staged from `ph_dashboard` via the read-only MCP route |

## The three source adapters

| Adapter | Live ownership? | State |
|---|---|---|
| `HistoricalReportSource` | **no** — day-level report | available, used by every run |
| `SpApiPricingSource` | yes | **unavailable** — credentials sit in the app tier |
| `LiveBrowserSource` | yes | available, **hard cap of 25 records** |

`sources.resolve(prefer_live=True)` **raises** rather than quietly returning historical
data. A live request never silently degrades.

## Evidence

| Claim | Evidence |
|---|---|
| 69/69 tests | `08_VALIDATION/TEST_RESULTS.md` |
| Real run, 20,821/20,821, 0 errors | run `20261014T155355-09c0f9` |
| Engine totals match the dashboard | both report 6,789 / 915 / 13,117 |
| Scheduler registers nothing | `Get-ScheduledTask` returns no BBOX task |
| Publisher has never written | 0 `BBOX` rows in `ph_task` |

## Do not

* copy these modules into this folder
* move `automation/` — the scheduler template and test fixtures reference that path
* set a gate in `config.py` — gates belong in `config.local.json`, which is git-ignored
* commit `config.local.json`
