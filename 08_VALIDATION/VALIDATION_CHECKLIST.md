# VALIDATION CHECKLIST — BBOX

Run after any structural change. Evidence: `TEST_RESULTS.md`.

| # | Check | How | 2026-10-14 |
|---|---|---|---|
| 1 | File integrity — nothing lost | `git status` clean; asset register regenerated | **PASS** (109 files) |
| 2 | Python imports resolve | import every automation module | **PASS** (7/7) |
| 3 | Automation tests | `python automation/test_automation.py` | **PASS** 69/69 |
| 4 | Dashboard tests | `python 03_SCRIPTS/test_dashboard_v003.py` | **PASS** 86/86 |
| 5 | Automation executes on real data | `python automation/run.py` | **PASS** 20,821/20,821 |
| 6 | History persists and is idempotent | suite tests 4a–4c, 12a–12h | **PASS** |
| 7 | Publisher dry run builds a valid payload | `publisher.publish(dry_run=True)` | **PASS** |
| 8 | Publisher writes nothing without approval | 0 `BBOX` rows in `ph_task` | **PASS** |
| 9 | Scheduler registers nothing | `Get-ScheduledTask` for BBOX | **PASS** — none |
| 10 | Alerts stay in dry run | `run.py --alerts <run_id>` | **PASS** — 0 fired |
| 11 | No duplicate source of truth | engine not copied into `07_AUTOMATION` | **PASS** — index only |
| 12 | No broken paths after reorganisation | no Python file moved | **PASS** |
| 13 | Ignore rules exclude secrets and local state | inspect + `git ls-files` | **PASS** |
| 14 | No credentials staged | grep tracked files | **PASS** — 0 matches |
| 15 | README links resolve | check every referenced path exists | **PASS** |
| 16 | Dashboard versions preserved | v001/v002/v003 byte sizes unchanged | **PASS** |
| 17 | Unknown-developer readiness | `10_HANDOVER/UNKNOWN_DEVELOPER_CHECK.md` | **PASS** |
| 18 | No production database modified | only SELECT against ledsone / ph_dashboard | **PASS** |
| 19 | `bbsa` untouched | no write issued; publisher fingerprints other projects | **PASS** |

## How to rerun everything

```bash
cd "C:/Users/LED 222/Buy_Box_Check_Automation_Tharsi"
python 00_PROJECT_CONTROL/gen_asset_register.py   # refresh the inventory
python automation/run.py --preflight              # gates + freshness, changes nothing
python automation/test_automation.py              # 69 tests
python 03_SCRIPTS/test_dashboard_v003.py          # 86 tests
git status --porcelain                            # should be clean
```
