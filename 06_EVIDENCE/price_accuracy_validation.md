# Phase 1 — Price Data Accuracy Correction

**Run:** 2026-10-14 13:42 (+05:30) · `03_SCRIPTS/fix_price_evidence.py`
**Database access:** read-only (SELECT only). No production data changed.
**Outcome:** 0 internally contradictory price signals (was 57).

## Reconciliation of reported counts

Every previously reported count was re-derived from `04_DATA/dashboard_rows.json`
rather than assumed:

| Metric | Reported | Actual | |
|---|---|---|---|
| Total records | 20,821 | 20,821 | MATCH |
| Buy Box NO records | 915 | 915 | MATCH |
| Reason = Unknown | 915 | 915 | MATCH |
| NO records with price evidence | 127 | 127 | MATCH |
| Inconsistent price signals | 57 | 57 | MATCH |

## Root cause

`03_SCRIPTS/extract_ledsone.py:61` selects

```sql
SELECT DISTINCT ON (asin, sub_source, market_place)
       asin, sub_source, market_place, snapshot_date, your_price, featuredoffer_price
FROM amazon_fba.excess_inventory_data
WHERE ... your_price IS NOT NULL AND featuredoffer_price IS NOT NULL
ORDER BY asin, sub_source, market_place, snapshot_date DESC
```

The true grain of that table is **asin × sub_source × market_place × sku × snapshot_date**
(confirmed from `information_schema`: the table carries `sku`, `currency` and
`snapshot_date` columns). Three defects follow:

1. **Arbitrary SKU.** `DISTINCT ON` collapses a SKU-grain table to one row per ASIN.
   Where an ASIN has several of our offers, which one survives is arbitrary.
   `B083TNFR73` on 2026-10-12 has `LDMST64E278pck3-AMN` at `your_price` 16.89 **and**
   `amzn.gr.LDMST64E278pck3_K-…-LN` at 11.83, against the same featured 15.89 — one
   above, one below. The build picked 11.83 by sort order alone.
2. **Zero admitted as a price.** Only `NULL` was excluded, so `your_price = 0.00`
   passed and always compared as "at or below". 53 NO rows were affected.
3. **Date drift.** The newest snapshot was taken regardless of distance from the Buy
   Box reading date. `B07VFV228J` compared a price from **2026-09-02** against a Buy
   Box reading on **2026-10-11** — 39 days apart — and that price was 0.00.

The visible symptom was different: the table displayed the PH spine `price`
(`analytics_overallasinlisting.price`) while the signal was computed from a different
offer's `your_price`. **Both numbers were real**; they describe different sellable
units. The contradiction came from showing one and comparing the other.

## Compatibility rules now enforced

A comparison is made only when all of these hold. Both numbers are then taken from
the **same source row**, so the comparison is internally consistent by construction.

1. A source row exists for the same `asin + sub_source + market_place` on **exactly**
   the Buy Box reading date (`last_checked`).
2. `currency` matches the marketplace (GBP for UK, EUR otherwise). All 9,967 rows
   examined for the 127 covered ASINs were GBP, so no row failed on this.
3. `your_price > 0` **and** `featuredoffer_price > 0`.
4. Unambiguous: all usable rows that day agree on a single `your_price` and a single
   `featuredoffer_price`.

No alternative price source was substituted to make a discrepancy disappear. Where the
rules fail the comparison is suppressed and `featured_price` is cleared, so the
dashboard shows **Price comparison unavailable** with the specific reason.

## Results (all 792 rows carrying price evidence)

| | Count |
|---|---|
| Comparable, internally consistent | **428** |
| Suppressed | **364** |
| Signals corrected (direction changed) | 1 |
| Correction log entries | 70 |

Suppression reasons:

| Reason | Count |
|---|---|
| No price snapshot on the Buy Box reading date (stale) | 266 |
| Ambiguous — 2 of our own offers at different prices | 62 |
| Source price is 0.00 (unusable) | 31 |
| Ambiguous — 3 of our own offers at different prices | 4 |
| Ambiguous — 4 of our own offers at different prices | 1 |

Of the **915 Buy Box NO** rows, **58** now carry a defensible comparison, of which
**18** are priced above the featured offer. All 915 `reason` values remain `Unknown` —
the correction changes evidence only, never a reason.

## Disposition of the original 57 contradictions

| Outcome | Count |
|---|---|
| Retained as a consistent comparison (compared price now displayed) | 26 |
| Suppressed — no snapshot on the Buy Box reading date | 20 |
| Suppressed — ambiguous, 2 of our own offers at different prices | 5 |
| Suppressed — source price 0.00 | 4 |
| Suppressed — ambiguous, 3 of our own offers at different prices | 2 |
| **Still contradictory** | **0** |

The 26 retained rows were never wrong in their arithmetic — our FBA offer genuinely
was at or below the featured offer. They looked wrong because the table displayed the
spine price beside them. They now carry `px_compared_price`, which is the figure the
signal actually used.

## Validation — 11/11 checks passed

```
PASS  row count preserved                        [20821 vs 20821]
PASS  original file untouched on disk
PASS  every row classified                       [428+364+20029]
PASS  signal matches the two compared numbers    [0 contradictions]
PASS  no false 'priced above' classification     [0]
PASS  suppressed rows display no featured price  [0]
PASS  suppressed rows carry no price signal      [0]
PASS  every suppressed row records a reason      [0]
PASS  every comparison has sku + date + both prices [0]
PASS  compared price == px_your_price shown      [0]
PASS  no price signal outside available rows     [0]
```

## Acceptance

| Criterion | Status |
|---|---|
| Zero internally contradictory price signals | **MET** — 57 → 0 |
| No false Price Higher classification | **MET** — every "above" verified against its own source row |
| Every displayed comparison has supporting source evidence | **MET** — each carries sku, snapshot date, currency, both prices and the source table |
| Original data remains recoverable | **MET** — `dashboard_rows.json` untouched (12,833,605 bytes); corrections are additive in `dashboard_rows_v002.json` |

## Files

| Path | Role |
|---|---|
| `04_DATA/dashboard_rows.json` | original, unmodified |
| `04_DATA/dashboard_rows_v002.json` | corrected rows (new fields `px_status`, `px_reason`, `px_compared_price`, `px_sku`, `px_source`) |
| `04_DATA/price_evidence_v2.json` | corrected evidence per key |
| `06_EVIDENCE/price_corrections.json` | per-row correction log with before/after and reason |
| `03_SCRIPTS/fix_price_evidence.py` | the correction, re-runnable |

## Carried into Phase 5

The spine `price` and the compared price are different offers and must be **labelled
distinctly** in the dashboard — the table's Price column is the PH listing price,
while the comparison panel must show `px_compared_price` with its SKU and snapshot
date. Showing the spine price beside a comparison it did not participate in is what
produced the original 57.
