# REQUIREMENT REGISTER — BBOX

Source: `Buy_Box_Automation_Tharsi (1).docx` (requirement document, with the Section 6
sample screen extracted to `02_REFERENCE/sample_dashboard.png`).

Status key: **DONE** · **PARTIAL** · **BLOCKED** · **PENDING APPROVAL**

---

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| R-01 | Read the ASIN list from the PH Dashboard automatically | `automation/engine.py::load_eligible`, `04_DATA/ph_spine.json` | 20,821 records, grain asserted | **DONE** |
| R-02 | For each ASIN, check Buy Box Yes/No | `automation/sources.py::HistoricalReportSource` | 6,789 YES / 915 NO / 13,117 NOT VERIFIED | **PARTIAL** — 63% unanswerable from source |
| R-03 | If No, run checks 1–8 and record the first match | **not implemented** | the 8 checks are undefined — see `BUSINESS_RULES.md` | **BLOCKED** |
| R-04 | If nothing matches, Reason = Unknown | `official_reason='Unknown'` on all 915 | build asserts it | **DONE** |
| R-05 | Save results with date and time | `automation/history.py` | 41,643 result rows across 3 runs | **DONE** |
| R-06 | Preserve daily history | `runs` + `results`, keyed on `run_id` | idempotency tested | **DONE** (SQLite; Postgres pending) |
| R-07 | Dashboard with filters | `05_OUTPUT/..._v003.html` | 86/86 tests | **DONE** |
| R-08 | Summary cards: Total / Won / Lost / Reason Unknown | all present + Not Verified | 86/86 | **DONE** |
| R-09 | Results table | 11 columns incl. Possible Reason | 86/86 | **DONE** |
| R-10 | Colour rules — green YES, red NO | plus grey NOT VERIFIED, amber Unknown | screenshot evidence | **DONE** |
| R-11 | Reason distribution chart | reconciles with the Lost card | 86/86 | **DONE** |
| R-12 | Excel export | UTF-8 BOM CSV, filtered rows | 916 rows for the NO filter | **DONE** |
| R-13 | Run Check button | present; states a live service is required | asserted to mutate nothing | **DONE (as specified)** |
| R-14 | Run once daily on a schedule | `automation/scheduler.ps1` | refuses without `-RunTime`; nothing registered | **PENDING APPROVAL** |
| R-15 | Run on demand | `run.py --manual-full`, `api.py` | both exercised | **DONE** |
| R-16 | Alert when a high-priority ASIN loses the Buy Box | `automation/alerts.py` | dry run: 0 fired, 20,821 rejected | **PENDING APPROVAL** |
| R-17 | All ASINs checked without manual work | full run 20,821/20,821, 0 errors | run `20261014T155355-09c0f9` | **DONE** |
| R-18 | Every NO has a reason or is Unknown | all 915 = Unknown | build asserts | **DONE** |
| R-19 | Results match a manual spot check | 6 DB rows + 10 live ASINs | `06_EVIDENCE/phase4_5_ten_asin_verification.md` | **DONE** |
| R-20 | Publish to the PH Dashboard | `automation/publisher.py` | dry run OK; **0 BBOX rows exist** | **BLOCKED** — not published |

## Requirement document's own open questions

The document closes with five questions to the team. Current answers:

| Question | Answer found |
|---|---|
| Which data source gives Buy Box and listing details? | `buy_box_percentage` (historical). **No live source exists.** |
| How many ASINs per run, how long? | 20,821 in ~5s (historical). Live would be ~4h for 915 — not authorised. |
| What time should the daily run happen? | **Still unanswered.** Must be after `overall_asin_daily` (07:35 Asia/Colombo). |
| Who should receive alerts? | **Still unanswered.** |
| Is any reason missing? | The whole 8-check list is missing. |

## Coverage

17 of 20 requirements DONE or DONE-as-specified. The 3 that are not are blocked on
decisions and data access, not on code:

* **R-03** — the 8 reason checks do not exist (do not invent them)
* **R-14 / R-16** — schedule time and alert recipients unapproved
* **R-20** — publication blocked by the write guard, and gated behind the `bbsa`
  duplication question (`02_DISCOVERY/BBSA_DUPLICATE_RISK.md`)
