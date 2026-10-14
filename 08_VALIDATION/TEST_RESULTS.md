# TEST RESULTS — BBOX

**All results below are from reruns executed on 2026-10-14 during this reorganisation**,
not carried over from earlier reports.

---

## 1. Suites rerun

| Suite | Command | Result | Previously reported |
|---|---|---|---|
| Automation engine | `python automation/test_automation.py` | **69 / 69 PASS** | 69/69 (matches) |
| Dashboard v003 | `python 03_SCRIPTS/test_dashboard_v003.py` | **86 / 86 PASS** | 86/86 (matches) |
| **Total** | | **155 / 155 PASS** | |

Raw results: `04_DATA/test_results_v003.json`, `04_DATA/test_results_v002.json`.

## 2. Import integrity

All automation modules import cleanly after the reorganisation:

```
config OK · sources OK · engine OK · history OK · alerts OK · publisher OK · api OK
```

This matters: the reorganisation added documentation folders only. **No Python file was
moved**, so no import or relative path changed.

## 3. Live execution

| Run ID | Mode | Status | Coverage | YES | NO | NV | Errors |
|---|---|---|---|---|---|---|---|
| `20261014T155355-09c0f9` | full_daily | completed | 20,821/20,821 | 6,789 | 915 | 13,117 | 0 |
| `20261014T154007-4b01a5` | manual_single | completed | 1/1 | 0 | 1 | 0 | 0 |
| `20261014T153635-b2b1ad` | full_daily | completed | 20,821/20,821 | 6,789 | 915 | 13,117 | 0 |

41,643 result rows persisted. Two independent full runs produced identical totals, and
those totals match the dashboard exactly — a genuine cross-check of two code paths.

## 4. Component checks

| Component | Check | Result |
|---|---|---|
| Publisher | dry run on the last successful run | payload 3,104,415 bytes, md5 `12f76233b995`, tally verified — **0 rows written** |
| Publisher | production write | **BLOCKED** by the environment write guard; 0 `BBOX` rows exist |
| Scheduler | `scheduler.ps1` without a run time | refuses, exit 2 |
| Scheduler | `scheduler.ps1 -RunTime 09:30` without confirm | dry run; **nothing registered** (verified via `Get-ScheduledTask`) |
| Alerts | dry run | 0 fired, 20,821 rejected, reason stated |
| History | idempotency | same run id upserts; a new run id preserves prior rows |
| Freshness gate | spine age | OK — snapshot 2026-10-14, 8.3 h old |
| Dashboard | offline load | opens from a file URL, 0 external assets, 0 console errors |
| Dashboard | secrets scan | 0 credential matches in all three HTML files |

## 5. Dashboard versions

| Version | Bytes | md5 (first 16) | Tests | Preserved |
|---|---|---|---|---|
| v001 | 2,318,906 | `126406694dcf417a` | 42/42 (at build) | yes |
| v002 | 3,103,839 | `4b29822284009740` | 75/75 (at build) | yes |
| **v003 (current)** | **3,105,022** | `f18e0618cbe3970a` | **86/86 (rerun today)** | yes |

## 6. Repository hygiene

| Check | Result |
|---|---|
| Tracked files | 107 to 106 (`config.local.json` untracked during this pass) |
| Credential literals in tracked files | **0** |
| `.env`, `*.db`, `state/`, `*.log` tracked | **none** |
| `automation/config.local.json` | **now ignored**; `config.local.example.json` added in its place |

**Issue found and fixed during this reorganisation:** `config.local.json` was committed
with the publish gate set to true. Anyone cloning the repo would have inherited an open
publish gate. It is now git-ignored, with a safe example file committed instead.

## 7. Not tested

| Area | Why |
|---|---|
| Live SP-API path | no access — adapter returns `INTEGRATION_NOT_AVAILABLE` by design |
| Bulk live browser checking | not authorised; the adapter refuses above 25 records |
| DE / FR / IT live checks | live method exercised on UK only |
| Postgres history | migration never applied |
| Real alert delivery | no channel exists in the estate |
