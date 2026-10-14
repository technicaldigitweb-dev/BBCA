# Phase 5 — Standalone HTML v002

**Built:** 2026-10-14 · `03_SCRIPTS/build_html_v002.py`
**Output:** `05_OUTPUT/2026-10-14_tharsi_buy_box_monitor_v002.html` (2.96 MB, 20,821 rows)
**Previous version preserved:** `2026-10-14_tharsi_buy_box_monitor_v001.html` (2,318,906 bytes, untouched)
**Tests: 75/75 passed** (`04_DATA/test_results_v002.json`; v001's results also preserved)

## What changed from v001

| Area | Change |
|---|---|
| Data source | reads `dashboard_rows_v002.json` (Phase 1 corrected + Phase 4 reasons) |
| Price comparison | shown only when defensible; otherwise **"Price comparison unavailable"** with the specific reason |
| Price panel | now shows Our offer price (with its SKU), Featured offer price, **Price difference**, Featured offer seller, Our seller account |
| Reason | `Official reason` and `Possible reason` held and displayed **separately**; new **Possible Reason** table column |
| Drawer | adds Confidence / limitations, Evidence source, Extraction status, Checked at, and a named list of evidence gaps |
| Provenance | footer states every row is a **historical snapshot**, no row is a verified live check |
| Run Check | already explained it cannot check live; now also states no SP-API exists and browser access is blocked |
| Summary | price counters recomputed from corrected rows (`px_available` 428, `px_unavailable` 364, `no_priced_above` 18) |

## Required content — verified present

Summary cards: Total ASINs, Buy Box Won, Buy Box Lost, Reason Unknown, Not Verified (`cTot`, `cYes`, `cNo`, `cNv` all present).
Filters: ASIN/SKU search, Seller Account, Marketplace, Category, Buy Box Status (`q`, `fAcct`, `fMkt`, `fCat`, `fStat` all present).
Table: ASIN, SKU, Buy Box, Reason, **Possible Reason**, Seller/Account, Marketplace, Category, Stock, Listing Status, Last Checked.
Drawer: Featured Offer Seller, Our Seller, Our Price, Featured Offer Price, Price difference, Stock, Listing Status, Possible Reason, Official Reason, Evidence Source, Extraction Status, Checked At.
Functionality: search, filters, sorting, pagination, reason distribution chart, Excel-compatible CSV export (UTF-8 BOM), daily history, latest check timestamp.

## Offline operation

```
external <script>/<link>/<img> loads pointing at http(s):  0
```

No backend, no CDN, no external asset. Amazon links are built at runtime and are
user-clicked only.

## Test coverage added in v002 (33 new assertions)

Price comparison consistency (6), stale/zero/ambiguous evidence suppression (3),
honest unavailable state in the drawer (2), missing seller identifiers declared not
invented (3), possible vs official reason separation (7), NOT VERIFIED states (2),
provenance and access-block disclosure (5), chart/summary consistency (3), plus the
rewritten reason-wording assertion.

## Two defects found by the new tests, and fixed

1. **Price loss-signal leaked onto non-NO rows.** The Phase 1 correction initially
   emitted the comparison signal for every row carrying price evidence, where v001
   emitted it only for Buy Box NO rows. A YES or NOT VERIFIED row would then have
   carried a loss signal that could read as a reason. Fixed in
   `fix_price_evidence.py`; the comparison still appears in those rows' drawers, but
   the signal does not. Verified: **0** price signals on non-NO rows.
2. **A test asserted the wrong invariant.** After fix 1 the "no contradictory
   direction" check failed because it expected a signal on every row with a
   comparison. It was scoped to NO rows and a companion assertion added that non-NO
   rows carry no loss signal. The data was right; the test was wrong.

## Acceptance

| Criterion | Status |
|---|---|
| All automated tests pass | **MET** — 75/75 |
| HTML works offline | **MET** — 0 external resources |
| No invented data | **MET** — seller IDs declared Not Available; official reason Unknown for all 915 |
| No misleading price evidence | **MET** — 0 contradictions; 364 comparisons suppressed with reasons |
| Previous version preserved | **MET** — v001 HTML and its test results untouched |
