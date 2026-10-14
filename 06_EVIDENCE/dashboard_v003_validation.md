# Phase G — Dashboard v003 Validation

**Output:** `05_OUTPUT/2026-10-14_tharsi_buy_box_monitor_v003.html` (3.46 MB, 20,821 rows)
**Generator:** `03_SCRIPTS/build_html_v003.py` (derived from v002 by `make_build_html_v003.py`)
**Data:** `04_DATA/dashboard_rows_v003.json` + `summary_v003.json`
**Tests: 94 / 94 passed** (`04_DATA/test_results_v003.json`)

**Prior versions preserved and unmodified:**

| File | Size | Status |
|---|---|---|
| `2026-10-14_tharsi_buy_box_monitor_v001.html` | 2,318,906 B | untouched |
| `2026-10-14_tharsi_buy_box_monitor_v002.html` | 3,103,839 B | untouched |

---

## 1. Why v003 was justified

Phase C established there is **no fresher database data** — all 915 NO rows already carry the
newest reading the source holds. A data-driven rebuild would have reproduced v002 exactly, and
per the brief that would not justify a new version.

v003 was built for a different reason: **v002 was generated at 13:55, the live verification ran
at 14:00–14:03**, so v002 cannot contain any live evidence. Concretely, v002 states for
`B086385W3W`:

> Possible reason: *"Price higher than the featured offer"*

The live check disproves it — our LEDSONE offer is **£18.89**, exactly equal to the featured
offer. v002 carries a possible reason that direct observation contradicts.

---

## 2. Defect found in v002 and fixed in v003

**v002 rendered an 11-column header but only a 10-cell body.** The `Possible Reason` `<td>` was
never emitted, so every column after it displayed under the wrong heading:

| Header shown | Value actually displayed under it (v002) |
|---|---|
| Possible Reason | Seller / Account |
| Seller / Account | Marketplace |
| Marketplace | Category |
| Category | Stock |
| Stock | Listing Status |
| Listing Status | Last Checked |
| Last Checked | *(empty)* |

Verified by DOM probe: with the UK filter applied, `children[5]` returned `"UK"` while the header
at index 5 read `Seller / Account`.

**Why v002's 75/75 did not catch it:** the test suite addressed cells by the *body's* indices, so
its assertions matched the misaligned layout. The tests encoded the defect rather than detecting
it. A passing suite was not evidence of a correct table.

**Fixed in v003** by emitting the missing cell. Header and body are now both 11 cells, confirmed
by DOM inspection, and a regression test asserts the counts match.

---

## 3. Changes from v002

| Area | Change |
|---|---|
| **Column alignment** | missing `Possible Reason` body cell emitted — fixes all downstream columns |
| Live-check layer | `live_status`, `live_checked_at`, `conflict`, `stale_days` carried per row |
| Summary cards | added **Live-checked** (10) and **Live Conflicts** (3) |
| Filter | added **Live Check** (`YES` / `NO` / `NOT VERIFIED` / `CHECK ERROR` / `Not checked` / `Conflicts only`) |
| Seller identity banner | states tokens are **VERIFIED**, and that a seller *name* alone is never proof |
| Stale-data banner | states the Buy Box columns are historical, names the max staleness (8 days) and that `2026-10-12` is a partial load |
| Drawer | new **Live check** section: featured seller, featured price, availability, offer count, our verified token, conflict explanation |
| Seller tokens | `A1BXMEJKH8MYIL` / `A3UNAW6KG6QUOJ` shown as VERIFIED |

**Removed at user request:** the `Live Check` table column. Live status remains reachable through
the Live Check filter, the two summary cards and the row drawer. **Consequence:** the inline ⚠
conflict marker is no longer in the table — conflicts surface via the card, the
*Conflicts only* filter and the drawer.

---

## 4. Required columns — all present

| Required | Present |
|---|---|
| ASIN · SKU · Seller / Account · Marketplace | yes |
| Buy Box Status | yes |
| Official Reason (`Reason`) | yes |
| Possible Reason | yes — **now correctly aligned** |
| Stock · Listing Status · Last Checked | yes |

Also present: summary cards, filters, price evidence, seller identity status, historical-vs-live
distinction, stale-data warning, source and timestamp, daily history, reason distribution,
Excel-compatible CSV export, truthful Run Check.

---

## 5. Acceptance criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Correct ASIN/account/marketplace grain | **PASS** | 20,821 rows, uniqueness asserted at build |
| 2 | Correct Seller ID mapping | **PASS** | VERIFIED against SP-API responses, 4/4 each |
| 3 | No duplicate records | **PASS** | build asserts; 0 duplicate grain keys in source |
| 4 | Accurate timestamps | **PASS** | `last_checked` = report date; `live_checked_at` = real check time; both distinct from build time |
| 5 | Stale snapshot detection | **PASS** | `stale_days` per row, max 8; banner states it |
| 6 | Historical and live separated | **PASS** | separate fields, separate filter, separate drawer section |
| 7 | No false ownership classification | **PASS** | live YES asserted only with a verified token present; name-only match yields NOT VERIFIED (`B0GLYZ41VT`) |
| 8 | No unsupported Reason classification | **PASS** | all 915 losses still `Official Reason = Unknown`; build asserts |
| 9 | Price evidence consistency | **PASS** | 428 comparable, 364 suppressed with reason, 0 contradictions |
| 10 | Filters and search | **PASS** | 6 filters incl. Live Check; every visible row verified against the active filter |
| 11 | Summary cards and counts | **PASS** | YES+NO+NV = total; cards match `summary_v003.json` |
| 12 | Chart reconciliation | **PASS** | chart total = Buy Box Lost card = 915 |
| 13 | Excel export | **PASS** | UTF-8 BOM, 916 rows for the NO filter (915 + header) |
| 14 | Offline HTML loading | **PASS** | opened from `file:///`, no server |
| 15 | No JavaScript console errors | **PASS** | 0 uncaught errors |
| 16 | No external asset dependency | **PASS** | 0 `<script src>` / `<link href>` / cdn references |
| 17 | Original versions preserved | **PASS** | v001 and v002 byte sizes unchanged |

### Regression tests added in v003 (19 new assertions)

Header/body column-count match · header labels sit above the right values · Live Check column
absent but live state still reachable · live-checked and conflict cards match summary · live YES
rows still display historical NO · conflicts filter count · not-checked complement · official
reason stays Unknown on every loss · both banners present and truthful · drawer live section,
verified token, conflict wording, and the "not refreshed by opening this file" warning.

---

## 6. Honest limitations carried into v003

1. **20,811 of 20,821 rows have no live check.** The Buy Box columns are historical, up to 8 days
   old. The banner says so; the dashboard does not claim current ownership.
2. **13,117 rows are NOT VERIFIED** — the Sales & Traffic report emits no row for an ASIN with no
   traffic that day. They are never counted as YES or NO.
3. **3 of the 10 live-checked rows conflict** with their historical status. Both readings are
   kept; the historical status is **not** overwritten, because the two describe different dates.
4. **The featured-offer holder is often unidentifiable by token.** Amazon retail and SRM Supplies
   expose no seller link in the pinned-offer slot, so in 5 of 10 cases the holder is known by
   display name only. Our *own* offers are token-identified, so "is one of our offers present?"
   is answerable with confidence; "who holds the Buy Box?" frequently is not.
5. **No approved reason rules exist.** `Official Reason` is `Unknown` on all 915 losses.
6. **Run Check cannot check anything.** It states that a live service is required and changes no
   status, count or timestamp.
