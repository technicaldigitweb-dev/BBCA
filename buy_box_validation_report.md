# Buy Box Check Automation — Validation Report

**Deliverable:** `05_OUTPUT\2026-10-14_tharsi_buy_box_monitor_v001.html`
**Built:** 2026-10-14 · **Rows:** 20,821 · **File size:** 1.97 MB
**Automated test suite:** `03_SCRIPTS\test_dashboard.py` — **42 / 42 PASS** (headless Chrome, real DOM)

---

## 1. Requirement checklist (Phase 7)

| # | Requirement | Result | Evidence |
|---|---|---|---|
| 1 | HTML opens without a local server | **PASS** | Rendered from `file:///` in headless Chrome; screenshot captured; no server involved |
| 2 | No JavaScript errors | **PASS** | `window.onerror` collector returned empty; `node --check` on the inline script passed |
| 3 | Embedded data matches the validated extraction | **PASS** | Card values read from the DOM equal `summary.json` exactly: 20,821 / 6,789 / 915 / 13,117 |
| 4 | All eligible ASINs included | **PASS** | 20,821 of 20,821 PH Amazon rows embedded; zero dropped by any join |
| 5 | No duplicate records | **PASS** | Grain uniqueness asserted in `build_dataset.py` (build aborts if any key repeats); max key count = 1 |
| 6 | YES/NO values have ownership evidence | **PASS** | Every YES = `buy_box_percentage` 100; every NO = 0; both carry the source report date. 6 rows re-queried against source — exact match |
| 7 | Unverified records not misclassified | **PASS** | 13,117 NOT VERIFIED rows render a grey pill, carry no Reason, and are excluded from Won/Lost percentages. Verified in-browser across the filtered set |
| 8 | Reason categories follow approved rules | **PASS** *(with gap)* | No approved rule exists, so the only reason emitted is `Unknown` — the brief's prescribed fallback. No invented rule was applied. See §4 |
| 9 | Summary counts reconcile with the table | **PASS** | YES + NO + NOT VERIFIED = Total, verified in the DOM; cards recompute from the filtered set on every filter change |
| 10 | Filters work correctly | **PASS** | Marketplace, Category, Buy Box, Account and ASIN/SKU search each tested; every visible row verified to match the active filter |
| 11 | Sorting and pagination work | **PASS** | All 10 columns sortable with direction toggle; numeric sort verified ascending (including genuine negative stock); 50/page, next/prev verified |
| 12 | Chart totals reconcile with NO results | **PASS** | Reason chart total = 915 = Buy Box Lost card, under both unfiltered and filtered states |
| 13 | Export contains the correct filtered rows | **PASS** | Filtered to NO → CSV contained 915 data rows + 1 header; all rows `"NO"`; 13 columns incl. evidence basis |
| 14 | Stock and listing values match their sources | **PASS** | Spot-checked against `listings.amazon_listings` — quantity and status matched on all 6 samples |
| 15 | Timestamps represent actual checks | **PASS** | `Last Checked` is the Amazon report `date`, i.e. the day Amazon measured ownership — not the build time. Build/snapshot times shown separately in the footer |
| 16 | No credentials or connection details embedded | **PASS** | Scan for `password / postgres:// / PGPASSWORD / tech_user / temp_user / DATABASE_URL / token / secret / host IPs` over the HTML returned **zero** matches |
| 17 | No external assets needed | **PASS** | Scan for `src="http` / `href="http` / `cdn` / `<link` returned **zero** matches. One inline `<script>`, one inline `<style>` |

---

## 2. Requirement-by-requirement delivery status

| Requirement (DOCX) | Status | Note |
|---|---|---|
| Read ASIN list from PH Dashboard automatically | **PASS** | 20,821 rows from `analytics_overallasinlisting`, no manual input |
| Buy Box Yes/No per ASIN | **PARTIAL** | Resolved for 7,704 (37%). 13,117 cannot be resolved — the source emits no row for ASINs without traffic (see §3) |
| Reason when NO | **FAIL — blocked** | The 8 reason checks are undefined in the specification. All 915 losses carry `Unknown` |
| Save result with date and time / history | **PARTIAL** | A real 14-day daily trend from source is shown. No automation-run history table exists — nothing has been created (no write approval) |
| Dashboard with filters | **PASS** | 5 working filters, all verified |
| Summary cards | **PASS** | 4 required cards + a 5th "Not Verified" card so unverified rows are never hidden inside YES/NO |
| Results table | **PASS** | All 10 required columns; ASIN, SKU, Buy Box, Reason kept as the first four, per the sample screen |
| Colour rules (Green YES / Red NO) | **PASS** | Plus neutral grey for NOT VERIFIED and amber for Unknown reason, as the task spec requires |
| Reason distribution chart | **PASS** | Verified losses by reason, plus a separately-captioned "observed signals" breakdown |
| Excel export | **PASS** | UTF-8 BOM CSV (opens directly in Excel), labelled CSV — **not** mislabelled as XLSX |
| Run Check button | **PASS (as specified)** | Present; states that a live checking service is required; verified to change no status, count or timestamp |
| Daily scheduling | **NOT DONE** | Out of scope — requires approval; nothing scheduled |
| High-priority alerts | **NOT DONE** | No high-priority ASIN definition and no recipient list exist |
| UI follows the sample screen | **PASS** | Dark navy header, filter row with orange Run Check, four accent-bar cards, pill table, right-hand reasons panel with `[ Export to Excel ]` — matches `02_REFERENCE/sample_dashboard.png` |

---

## 3. Data results

| Metric | Value |
|---|---|
| Total eligible ASIN × account × marketplace rows | **20,821** |
| Verified Buy Box **YES** | **6,789** (88% of the verified base) |
| Verified Buy Box **NO** | **915** (12% of the verified base) |
| **NOT VERIFIED** | **13,117** |
| &nbsp;&nbsp;— no report row within 7 days | 12,961 |
| &nbsp;&nbsp;— partial/split ownership (0 < % < 100) | 156 |
| Reason = Unknown | **915** (every verified loss) |
| Records with stock data | 20,820 / 20,821 |
| Records with listing status | 20,821 / 20,821 |
| Records with category | 20,821 / 20,821 |
| Records with a featured-offer price comparison | 792 / 20,821 (127 of the 915 losses) |
| Latest verified check date | **2026-10-12** |

**Won/Lost percentages are computed against the verified base of 7,704, never against 20,821.**
The dashboard states this explicitly above the table so the 88% can never be misread as 88% of the catalogue.

### Why 13,117 are NOT VERIFIED
The Sales & Traffic report only emits a row for an ASIN on a day it received traffic.
Measured coverage: 7 days → 37.8%, 14 days → 46.8%, 30 days → 57.5%, 90 days → 73.1%.
This is a property of the source, not of the window chosen. Widening the window would not
resolve it and would make `Last Checked` badly stale.

---

## 4. Honest limitations (read before using this dashboard)

1. **Reason is always `Unknown` for losses.** The specification's "checks 1 to 8" are never
   defined — not in the DOCX, not in either skill pack, not in the database. Inventing them was
   explicitly forbidden, so no reason rule was applied. The chart's 915 "Unknown" is a true
   statement about the specification, not a data-quality failure.

2. **77% of losses carry no signal at all.** Of 915 confirmed losses, 705 have an Active listing
   *with stock* and no price comparison available. Competitor price exists only in the FBA Excess
   Inventory report, which covers just 127 of the 915 losses (19 priced above the featured offer,
   74 priced below). Seller metrics and Prime eligibility are **not in this database at all**.

3. **The Buy Box winner's identity is unknown.** The source measures only *our* share of the
   featured offer. Even the FBA price comparison names no seller. The dashboard never claims who
   won instead.

4. **Temporal mismatch between columns.** Buy Box % and `Last Checked` are as of the report date
   (up to 7 days old). Stock and Listing Status are current as of the 2026-10-14 refresh. A row
   can therefore legitimately show `YES` alongside stock 0 — the Buy Box was held on the report
   date and stock has since fallen. The detail drawer shows both dates so this is never hidden.

5. **"Suppressed" is not available.** The source has no such status. `DISCOVERABLE` (visible but
   not buyable) is the nearest concept and is shown under its own derived label rather than
   renamed.

6. **156 partial-ownership rows are held at NOT VERIFIED** pending an approved threshold.
   8 are ≥ 90%; 148 are below.

7. **Negative stock values are shown as-is.** 21 listing groups carry a negative summed quantity
   in source (oversold `DISCOVERABLE` listings, minimum −154). These are displayed faithfully
   rather than clamped to zero.

8. **This is a snapshot, not a live monitor.** The HTML is standalone and offline; Run Check
   cannot query anything.

---

## 5. Safety confirmation

| Control | Result |
|---|---|
| Read-only database access | **PASS** — only `SELECT` / `information_schema`; direct session pinned with `SET TRANSACTION READ ONLY` |
| No INSERT / UPDATE / DELETE / DDL | **PASS** — none issued |
| No production schema modification | **PASS** |
| No credentials in output | **PASS** — DSNs read from environment variables inside scripts, never printed or embedded |
| No commit / push / deploy / schedule / alert enabled | **PASS** — none performed |
| Existing versions not overwritten | **PASS** — `v001` is a new file in a new project folder |
| Archives not executed | **PASS** — ZIP contents read in place; no script from them was run |

---

## 6. Overall status

### AMBER

The dashboard is built, fully tested (42/42), populated entirely with verified data, and
contains no invented values. It is usable today for Buy Box *ownership* monitoring.

It is **not GREEN** because the headline business question — *"when we lose the Buy Box, why?"* —
cannot be answered. That is blocked by two gaps outside this build: the undefined 8-check
reason list, and the absence of any competitor-pricing or seller-metric data source. Both are
listed in the handover with what is needed to close them.
