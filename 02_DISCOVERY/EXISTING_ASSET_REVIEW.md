# EXISTING ASSET REVIEW — BBOX

Mini-AIOS rule: **Reuse → Extend → Merge → Create New.** This records what already
existed, what was reused, and what was genuinely new.

All findings read-only, 2026-10-14.

---

## 1. The big one — an existing Buy Box automation

| | |
|---|---|
| Asset | `bbsa` — "Amazon Buy Box / Suppression Alerts (UK)", developer **Abiraj** |
| State | live, daily, version 37, last run 2026-10-14 09:21 |
| Verdict | **DUPLICATE RISK — unresolved** |

Full analysis: `BBSA_DUPLICATE_RISK.md`. This should have been found before building,
not after. It was found by inspecting `ph_task` while looking for a publication route.

## 2. Reused — adopted wholesale

| Existing asset | Reused as |
|---|---|
| **House automation layout** (`eBay_SKU_Gap_Analysis_Sharmilan/automation/`) | module split (`config`/`logger`/`run`), `--preflight` / `--dry-run` conventions |
| **Windows Task Scheduler pattern** (50+ live tasks) | `pythonw.exe` + `run.py`, Interactive/Limited principal, `IgnoreNew` overlap prevention, PT2H limit |
| **`ph_task` publication pattern** (ESGA `publish_team.py`) | one stable row per user, `version_level` bump, fingerprint-and-rollback safety |
| **`scheduler_scheduledtask` conventions** | cron + `Asia/Colombo`; found the `overall_asin_daily` upstream dependency |
| **Playwright CDP pattern** (`Competitor_Check_Powsteena`) | live listing checks through an operator-opened browser |
| **`03_SCRIPTS` dashboard pipeline** (this project, earlier phases) | v003 built by patching the v002 generator, not rewriting it |

## 3. Extended rather than rebuilt

| Asset | Extension |
|---|---|
| `verify_live_listing.py` | fixed the label-vs-value selector defect; added `sold_by()` — this is what revealed the seller tokens |
| `build_html_v002.py` | `build_html_v003.py` derived by patch (`make_build_html_v003.py`), preserving the UI |
| `test_dashboard_v002.py` | extended to 86 tests; column indices realigned after a real defect was found |
| `dashboard_rows_v002.json` | `v003` adds staleness without rewriting history |

## 4. Searched for and NOT found

| Looked for | Result |
|---|---|
| Existing Buy Box check script in this estate | only `bbsa` (not source-accessible here) |
| **SP-API integration reachable from this machine** | **none** — credentials live in the app tier; `amz_token_id` FK points at a table absent from the warehouse |
| PH Dashboard API for automation output | **none** |
| Writable structured destination for Buy Box records | **none** — `ph_task` stores HTML, not records |
| Existing Buy Box history table | **none** in `ledsone` or `ph_dashboard` |
| **Alert delivery infrastructure** (email / Discord / Slack / Teams) | **none anywhere in the estate** — `logs` is a scheduler run-log with an acknowledge flag, not a channel |
| Amazon seller/merchant token in the warehouse | **none** — found instead inside stored SP-API responses in another project's data |
| High-priority ASIN flag | `analytics_asinsegmentasin.priority` exists — **candidate only, not approved** |

## 5. Created new — and why it was justified

| New asset | Why nothing existing fit |
|---|---|
| `automation/sources.py` adapter interface | no existing abstraction kept an unavailable source from silently degrading to a weaker one |
| `automation/history.py` | no Buy Box history table exists anywhere |
| `automation/alerts.py` | no alert engine and no delivery channel exist |
| `automation/publisher.py` | the ESGA pattern was reused, but it is project-specific code |
| `../automation/migrations/001_buy_box_history.sql` | proposal only, never applied |
| Dashboard v001–v003 | no Amazon Buy Box dashboard existed **for DE/FR/IT** (`bbsa` covers UK) |

## 6. Duplication deliberately avoided

| Temptation | Decision |
|---|---|
| Copy `automation/` into `07_AUTOMATION/` | **refused** — index only; two copies would break the scheduler and create duplicate truth |
| Move the four root `buy_box_*.md` documents | **refused** — other documents reference them by name; indexed instead |
| Create `01_REQUIREMENTS` beside the existing `01_REQUIREMENT` | **refused** — two folders differing by one letter is a drift trap; populated the existing one |
| Rebuild the dashboard for v003 | **refused** — patched the v002 generator |
| Re-verify seller IDs with a fresh scrape | **refused** — already VERIFIED from an authoritative source |
| Write our own scheduler service | **refused** — Windows Task Scheduler is the house standard |

## 7. Honest note on sequencing

The Mini-AIOS rule is *"No existing asset search = no approval to create new work."*
On this project the existing-asset search for **`bbsa` happened late** — after the
dashboard and engine were built. The build is still valuable (DE/FR/IT coverage, verified
tokens, price correction), but had `ph_task` been inspected on day one, the duplication
conversation would have come first. Recorded here so the lesson is not lost.
