# Phase 6 — Dashboard Validation

**Target:** `05_OUTPUT/2026-10-14_tharsi_buy_box_monitor_v001.html` (2,318,906 bytes)
**Method:** re-ran the existing harness `03_SCRIPTS/test_dashboard.py` (loads a temp
copy in headless Chrome; the shipped file is never written), plus a direct read of
`04_DATA/dashboard_rows.json`.
**The dashboard file was NOT modified.**

**Verdict: PARTIAL** — every functional test passes, but the price-comparison
evidence is computed from a different price than the one displayed.

## Functional tests: 42/42 PASS

Confirmed present and correct: Total ASINs (20,821), Buy Box Won (6,789),
Buy Box Lost (915), Reason Unknown (915), NOT VERIFIED (13,117), YES+NO+NV = total,
ASIN + SKU, seller account, marketplace, stock/listing status, Last Checked, reason
evidence drawer, filters (status/marketplace/account/search), chart reconciliation,
CSV export (UTF-8 BOM, 916 rows = 915 + header), daily history table
(Check date / Won / Lost / Partial / Measured), pagination, sorting, and
"no uncaught JS errors". The NOT VERIFIED drawer correctly never claims YES/NO
ownership, and "Run Check" correctly explains there is no live service and mutates
no timestamp or count.

## Defect 1 — price-comparison signal contradicts the displayed price

`03_SCRIPTS/build_dataset.py:63` computes the signal from
`amazon_fba.excess_inventory_data.your_price` (`px_your_price`), while the table
displays `price` from the PH spine (`analytics_overallasinlisting.price`). They
disagree:

| Measure (of the 127 NO rows that have price evidence) | Count |
|---|---|
| `px_your_price == 0.0` — unusable, but still compared | **53** |
| displayed `price` differs from `px_your_price` | **65** |
| signal says "at or below" while displayed price is **above** featured | **57** |
| median absolute gap between the two prices | £1.55 |

Worked examples:

| ASIN | Displayed price | `px_your_price` | Featured | Signal emitted |
|---|---|---|---|---|
| B07VFV228J | 26.89 | **0.0** | 24.69 | "at or below the featured offer" |
| B07VXWJ5WY | 36.89 | 33.89 | 33.89 | "at or below the featured offer" |
| B083TNFR73 | 18.89 | 11.83 | 15.89 | "at or below the featured offer" |

A user reading the B07VFV228J row sees our price £26.89 against a featured £24.69 —
visibly above — while the evidence drawer asserts the opposite, because the
comparison used a `your_price` of 0.00 as if it were a real price. 45% of priced NO
rows (57/127) carry this contradiction. `summary.no_priced_above = 19`, whereas the
displayed prices imply 73.

**This does not change any Reason** — all 915 losses remain `Unknown` — so no
published conclusion is wrong. The defect is in the supporting evidence text.

## Defect 2 — negative stock values pass through

8 rows carry negative stock (e.g. `B093T4L68X` = -30, `B0933HCG17` = -16). None are
status NO, so no loss evidence is affected, but they sort to the top of an ascending
stock sort and will read as corrupt to the user.

## Proposed change summary — NOT APPLIED, approval requested

1. **Treat `px_your_price <= 0` as missing.** Emit no price signal for those 53 rows
   rather than a false "at or below". *(fix in `build_dataset.py` ~line 63)*
2. **Compare like with like.** Either compare the displayed spine `price` against
   `featured_price`, or display `px_your_price` alongside it and label both sources.
   Recommend the former, with the FBA report date shown, since `price` is the figure
   the rest of the dashboard and the CSV already use.
3. **Clamp or flag negative stock** at build time (show `0` with a data-quality flag
   rather than a negative number).
4. Regenerate via `build_dataset.py` → `build_html.py` as **v002**; leave v001 in
   place. Per project convention, artefacts are rebuilt by the generator, never
   hand-edited.

Items 1–3 are data-layer changes only; no schema, no database writes, no change to
any Reason value. Awaiting approval before touching anything in `03_SCRIPTS/` or
`05_OUTPUT/`.
