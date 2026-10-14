# Phase C — Fresh Buy Box Report Data Validation

**Run:** 2026-10-14 · read-only (`SET TRANSACTION READ ONLY`)
**Verdict: NO FRESH DATA. The source has not advanced since dashboard v002 was built.**

---

## Source

| | |
|---|---|
| Schema / table | `ledsone.business_reports.amz_sales_and_traffic_by_asin` |
| Column | `buy_box_percentage` |
| Grain | `date + child_asin + sub_source + market_place` |
| Accounts | `sub_source` 6 (DCVoltage), 8 (LEDSone) |
| Marketplaces | 23 UK, 10 DE, 9 FR, 14 IT |
| Rows in scope | 1,354,512 |
| **Duplicate grain keys since 2026-10-01** | **0** |

## Latest available dates

| Date | Rows | ASINs | |
|---|---|---|---|
| 2026-10-08 | 4,980 | 4,335 | complete |
| 2026-10-09 | 4,860 | 4,180 | complete |
| 2026-10-10 | 4,898 | 4,151 | complete |
| 2026-10-11 | 5,295 | 4,473 | **latest complete** |
| **2026-10-12** | **325** | **322** | **PARTIAL — ~6% of a normal day** |

`max(date)` is 2026-10-12, but that date is a **partial load**. The latest date that can be
treated as complete is **2026-10-11**. Any rule anchored on `max(date)` alone would silently
treat a 6%-loaded day as a full one; the v002 build avoids this because it takes the newest row
**per ASIN within a 7-day window** rather than requiring the max date.

## Comparison against the data used for dashboard v002

Every one of the **915** historical NO rows was re-queried for the newest reading now available:

| Outcome | Count |
|---|---|
| Already using the newest available reading (**same date**) | **915** |
| A newer reading now exists | **0** |
| No report row at all | 0 |
| Rows that would flip away from NO on fresher data | **0** |

**All 915 NO rows already carry the freshest reading the source holds.** Rebuilding the dataset
from the database today would reproduce v002 byte-for-byte on this dimension.

## How many of the 915 remain candidates for live checking

**All 915.** None were resolved by fresher reporting, because there is no fresher reporting.

Per the brief, the 4-of-10 sample result is **not** extrapolated to the full set. What the sample
established is that a stale reading *can* disagree with live ownership — not a rate. The 915
figure is the candidate population; how many are genuine current losses is unknown and can only
be settled per ASIN.

## Historical vs live — the distinction that matters

`buy_box_percentage` is **historical reporting evidence, not current Featured Offer ownership.**
It describes the share of page views on a given day, and the newest reading for a NO row can be
up to 7 days old.

No record has been reclassified from its historical status on the basis of reporting percentage.
The four ASINs where the live check found our own account holding the featured offer are held as
**conflicts** between two differently-dated sources, not silently overwritten:

| ASIN | Account | Historical | Live check (2026-10-14) | Treatment |
|---|---|---|---|---|
| B07VFV228J | LEDSone | NO (0% on 2026-10-11) | our account holds featured offer | **CONFLICT** |
| B07VXWJ5WY | LEDSone | NO (0% on 2026-10-11) | our account holds featured offer | **CONFLICT** |
| B0GLPLNXXC | DCVoltage | NO (0% on 2026-10-08) | our account holds featured offer | **CONFLICT** |
| B0GLYZ41VT | DCVoltage | NO (0% on 2026-10-09) | our account holds featured offer | **CONFLICT** |

Both readings are retained. Neither is deleted, and the historical status is not rewritten —
the live check used a **provisional** seller ID (see `seller_identity_verification.md`), so it is
not authoritative enough to overwrite a recorded measurement.

## Freshness / conflict flags introduced for v003

| Flag | Meaning |
|---|---|
| `live_status` | `YES` / `NO` / `NOT VERIFIED` / `CHECK ERROR`, from a live page check only |
| `live_checked_at` | real timestamp of that check; absent where never checked |
| `conflict` | historical and live disagree |
| `stale_days` | age of the historical reading at build time |

## Consequence for v003

A rebuild driven by **fresh database data is not justified** — there is none.

A v003 **is** justified by the live-check evidence collected after v002 was built (13:55 vs the
14:00–14:03 run), which v002 cannot contain. Concretely, v002 currently states for `B086385W3W`:

> Possible reason: *"Price higher than the featured offer"*

The live check disproves this — our LEDSONE offer is **£18.89**, exactly equal to the featured
offer at **£18.89**. v002 carries a possible reason that direct observation contradicts, and
that is worth correcting.
