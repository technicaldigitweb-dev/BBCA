# DATA SOURCE MAPPING — BBOX

Every source below was confirmed by read-only query on 2026-10-14. Each row states
whether it is a **verified fact** or an **assumption**.

Full field-level mapping: `buy_box_source_mapping.md`
Discovery narrative: `buy_box_data_discovery.md`

---

## 1. Databases

| DB | Reached how | Access | Role |
|---|---|---|---|
| `ledsone` | `$WLP_SOURCE_DB_URL` (direct psycopg, `tech_user`) | read-only | Buy Box report, listings, FBA prices |
| `ph_dashboard` | `Ledsone_Database_MCP` only — **no direct DSN on this machine** | read-only | PH ASIN spine, categories, app scheduler |
| `order_management_copy` | `178.18.248.100:5435` + MCP | read/write | `tech_team_outputs.ph_task` publication target |

**Verified:** `$DATABASE_URL` and `$PGHOST` both point at the **old** ph_task server and
time out (TCP test fails). `178.18.248.100:5435` succeeds. Any publisher must use the
new endpoint.

## 2. Field sources

| Field | Source | Status |
|---|---|---|
| ASIN | `ph_dashboard.public.analytics_overallasinlisting.listing_ref` | VERIFIED |
| SKU / mapped SKU | same table, `.sku` / `.mapped_sku` | VERIFIED |
| Seller account | `.account_name` + `.sub_source` → `ledsone.order_management.sub_source` | VERIFIED — 8 = LEDSone, 6 = DCVoltage |
| Marketplace | `.marketplace` → `order_management.market_place` | VERIFIED — UK 23, DE 10, FR 9, IT 14 |
| **Buy Box** | `ledsone.business_reports.amz_sales_and_traffic_by_asin.buy_box_percentage` | VERIFIED — **the only Buy Box source in the estate** |
| Listing status | `ledsone.listings.amazon_listings.status`, joined on `asin + sub_source + site` | VERIFIED — `site`, **not** `region_id` |
| Stock | `listings.amazon_listings.quantity` (+ PH `uk_stock` / `fbm_stock`) | VERIFIED |
| Category | `ph_dashboard.ph_allocation_idrecord.refId` → `ph_allocation_phcategory` | VERIFIED — 100%, 66 categories |
| Featured-offer price | `ledsone.amazon_fba.excess_inventory_data` | **PARTIAL** — FBA-excess scope only, 792 of 20,821 (3.8%) |
| Seller IDs | stored SP-API Listings Items responses | **VERIFIED** — see `06_EVIDENCE/seller_identity_verification.md` |
| **Buy Box winner identity** | — | **NOT FOUND** — no source names the holder |
| **Prime eligibility / seller score** | — | **NOT FOUND** |

## 3. Grain

`ASIN × seller account × marketplace` — **20,821** rows, uniqueness asserted at build
time (the build aborts if any key repeats).

| Account | UK | DE | FR | IT | Total |
|---|---|---|---|---|---|
| LEDSone (8) | 6,151 | 2,364 | 2,192 | 1,594 | 12,301 |
| DCVoltage (6) | 5,115 | 1,766 | — | 1,639 | 8,520 |

## 4. Freshness — the central constraint

**Verified:** the Sales & Traffic report only emits a row for an ASIN on a day it had
traffic. Measured coverage of the 20,821 records:

| Lookback | Coverage |
|---|---|
| 1 day | 1.2% |
| 3 days | 24.7% |
| **7 days (used)** | **37.8%** |
| 30 days | 57.5% |
| 90 days | 73.1% |

So **13,117 records (63%) are `NOT VERIFIED`** — a property of the source, not a defect,
and not fixable by widening the window.

Latest complete source date: **2026-10-11**. `2026-10-12` exists but is a **partial
load** (325 rows vs ~5,000 typical) — any rule anchored on `max(date)` alone would treat
a 6%-loaded day as complete.

## 5. Upstream dependency

`ph_dashboard.scheduler_scheduledtask` → **`overall_asin_daily`**, cron `35 7 * * *`
`Asia/Colombo`, refreshes the ASIN spine.

**Assumption flagged:** its cron time is *not* its completion time (observed completions
vary). `run.py` therefore gates on the staged spine's own `snapshot_at`, not the clock.

## 6. Verified facts vs assumptions

| Claim | Type |
|---|---|
| `buy_box_percentage` is the only Buy Box source | **verified** — exhaustive column sweep |
| `=100` → YES, `=0` → NO | **verified** semantics |
| 0 < pct < 100 is genuinely ambiguous | **verified** — 156 rows; no approved threshold |
| Seller tokens map to sub_source 8 / 6 | **verified** — 4/4 consistent, SP-API responses |
| SRM Suppliers token | **unconfirmed** |
| `Scale` / `Fix Now` = high priority | **ASSUMPTION — not approved**, candidate only |
| A 7-day window is acceptable | **ASSUMPTION** — documented, pending approval |
| ph_task is the right destination for structured records | **rejected** — it stores HTML per user, no structured columns |
