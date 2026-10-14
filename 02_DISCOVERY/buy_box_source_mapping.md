# Buy Box Check Automation — Source-to-Target Data Mapping

**Project:** Buy Box Check Automation – Tharsi
**Date:** 2026-10-14
**Grain:** `ASIN + Seller Account + Marketplace + Check Timestamp`
**Row count at grain:** 20,821 (uniqueness asserted in `build_dataset.py`; max key count = 1)

Classification legend: **VERIFIED** / **PARTIAL** / **NOT FOUND** / **REQUIRES APPROVAL**

---

## 1. Field mapping

### 1.1 ASIN — VERIFIED

| | |
|---|---|
| **Database / schema / table** | `ph_dashboard` → `public.analytics_overallasinlisting` |
| **Column** | `listing_ref` |
| **Join key** | spine column — the grain root |
| **Transformation** | none |
| **Null handling** | none observed; filter `platform = 'AMAZON'` guarantees ASIN form |
| **Evidence** | 20,821 / 20,821 match `^B0[A-Z0-9]{8}$`; `count(DISTINCT listing_ref)` equals row count within each account × marketplace |

### 1.2 SKU — VERIFIED

| | |
|---|---|
| **Table / column** | `analytics_overallasinlisting.sku` (+ `mapped_sku` carried as secondary) |
| **Join key** | same row as ASIN |
| **Transformation** | none. `mapped_sku` is the bundle SKU and is **not** substituted for `sku` |
| **Null handling** | displayed as `Not Available` if absent |
| **Evidence** | the PH Dashboard has already resolved one representative SKU per ASIN × account × marketplace; multi-offer relationships are preserved separately via `offer_rows` in `listings.amazon_listings` |

### 1.3 Seller / Account — VERIFIED

| | |
|---|---|
| **Table / column** | `analytics_overallasinlisting.account_name`, `.sub_source` |
| **Join key** | `sub_source` → `ledsone.order_management.sub_source.id` |
| **Transformation** | none |
| **Evidence** | `6 = "amazon Dcvoltage"`, `8 = "amazon Ledsone"` read from the lookup table. Exactly these two accounts appear in the PH Amazon spine, and both are present in the Buy Box report |

### 1.4 Marketplace — VERIFIED

| | |
|---|---|
| **Table / column** | `analytics_overallasinlisting.marketplace` (UK / DE / FR / IT) |
| **Join key** | → `ledsone.order_management.market_place.abbreviation` → `.id` |
| **Transformation** | `UK→23, DE→10, FR→9, IT→14` for the Buy Box join; `UK→'UK', DE→'Germany', FR→'France', IT→'Italy'` for the listing join (`site` column) |
| **Evidence** | both lookups read directly from `order_management.market_place` |

### 1.5 Buy Box Owner — **NOT FOUND**

| | |
|---|---|
| **Searched** | `featured`, `seller_id`, `merchant`, `is_winner`, `competitive_price`, `landed_price`, `offer_count` across all of `ledsone` |
| **Found** | only `amazon_fba.excess_inventory_data.featuredoffer_price` — a price, FBA-excess scope, carrying **no seller identity** |
| **Consequence** | the **identity** of a competing Buy Box winner cannot be reported. Only *whether our own offer held it* is knowable |
| **Status** | **NOT FOUND** — requires an Amazon SP-API Product Pricing / `getItemOffers` integration |

### 1.6 Buy Box Status — VERIFIED (within coverage) / REQUIRES APPROVAL (partial band)

| | |
|---|---|
| **Database / schema / table** | `ledsone` → `business_reports.amz_sales_and_traffic_by_asin` |
| **Column** | `buy_box_percentage` |
| **Join key** | `child_asin = listing_ref` AND `sub_source` AND `market_place` |
| **Row selection** | `DISTINCT ON (child_asin, sub_source, market_place) … ORDER BY date DESC` within the window |
| **Window** | `date > '2026-10-12'::date - 7 AND date <= '2026-10-12'` |
| **Null handling** | no row in window → `NOT VERIFIED`, never YES/NO |

**Derivation (only what the source evidences):**

| `buy_box_percentage` | Status | Rationale |
|---|---|---|
| `= 100` | **YES** | our offer was the featured offer for *every* page view that day |
| `= 0` | **NO** | our offer was the featured offer for *no* page view that day |
| `> 0 and < 100` | **NOT VERIFIED** *(sub-state: Partial)* | ownership was split during the day. Collapsing this to YES or NO needs a cut-off that **no approved rule defines** |
| no row in window | **NOT VERIFIED** *(sub-state: No report row)* | no evidence |

> **REQUIRES APPROVAL — partial-ownership threshold.** 156 rows (0.7%) fall in the partial band.
> They are held at NOT VERIFIED rather than being forced to a side. If the team approves a
> cut-off (e.g. "≥ 90% counts as YES"), only `build_dataset.py` changes — 8 of these rows are
> ≥ 90%, 148 are below.

> **REQUIRES APPROVAL — the 7-day window.** Documented and measured in the discovery file.
> It is a reporting-lag allowance, not a business rule.

**Evidence:** bucket counts over the window — `=100`: 10,821 rows; `90–99.99`: 8;
`0.01–89.99`: 238; `=0`: 1,641 (source-side, all accounts/markets before the PH join).

### 1.7 Reason — **REQUIRES APPROVAL** (no rule exists)

| | |
|---|---|
| **Specified by** | DOCX ¶29: "Run checks 1 to 8 from Section 5 in order" |
| **Defined by** | **nothing.** Section 5 contains the instruction, not the checks. No list of 8 checks exists in the DOCX, in either skill pack, or in the database |
| **Applied value** | `Unknown` for every verified NO (915 rows), per the brief's fallback |
| **Null handling** | blank for YES and NOT VERIFIED rows — a reason is only meaningful for a verified loss |

**Why the sample labels were not implemented as rules:**

| Sample label | Data needed | Available? |
|---|---|---|
| Price higher | competitor / featured-offer price at ASIN grain | **Partially** — see §1.7a; covers only 127 of the 915 losses |
| Out of stock | our quantity | Yes — but quantity alone is **not** proof of why the Buy Box was lost |
| Listing suppressed | a `Suppressed` status | **No** such value exists in `amazon_listings` |
| Low seller score | Amazon account health | **No** (only eBay ratings exist) |
| Not Prime eligible | Prime eligibility flag | **No** |

The DOCX captions the sample screen *"Numbers and names are only examples."*

**Observed signals (recorded, never promoted to a reason).** Carried in the `signals` array and
shown in the dashboard's detail panel under an explicit "not an approved reason" caption:

| Signal | Verified-NO rows |
|---|---|
| Our price is at or below the featured offer | 108 |
| Listing quantity is 0 | 66 |
| Listing status: Inactive | 55 |
| No warehouse stock | 37 |
| Listing status: Discoverable (not buyable) | 35 |
| Our price is above the featured offer | 19 |
| **No signal at all** | **705 of 915 (77%)** |

That 77% figure is itself the finding: for the large majority of confirmed losses the listing is
Active and in stock and no price comparison is even available, so the cause lies outside the data
this database holds.

### 1.7a Featured-offer price comparison — PARTIAL (evidence only)

| | |
|---|---|
| **Table** | `ledsone.amazon_fba.excess_inventory_data` |
| **Columns** | `your_price`, `featuredoffer_price`, `snapshot_date` |
| **Join key** | `asin` + `sub_source` + `market_place`, newest `snapshot_date` per key |
| **Coverage** | **792 of 20,821** PH rows (3.8%); **127 of the 915** verified losses |
| **Freshness** | 2026-10-13 |

This is the **FBA Excess Inventory report**, so it only contains ASINs flagged as overstocked FBA
inventory — that is the whole reason coverage is so low. Of the 127 covered losses: **19** are
priced **above** the featured offer, 34 equal, 74 **below**.

**Used as a signal, never as a reason.** Two further cautions, both surfaced in the dashboard
drawer: its `snapshot_date` differs from the Buy Box reading date, and it names no seller — so it
still cannot identify who won the Buy Box.

The 74 losses where we are priced *below* the featured offer are a genuine finding in their own
right: price was not the cause there, which redirects investigation toward seller metrics or
fulfilment.

### 1.8 Stock — VERIFIED

| | |
|---|---|
| **Primary** | `ledsone.listings.amazon_listings.quantity`, summed per ASIN × `sub_source` × `site` |
| **Secondary** | `analytics_overallasinlisting.uk_stock`, `.fbm_stock` (warehouse figures, shown in the detail panel) |
| **Join key** | `asin` + `sub_source` + `site` |
| **Transformation** | `sum(quantity)` across all our offers on that ASIN |
| **Null handling** | `Not Available` where no listing row exists (1 row of 20,821) |
| **Evidence** | 20,820 / 20,821 populated; spot-checked against source — exact match on all 6 samples |

Units: marketplace-facing listing quantity. It is deliberately **not** the same number as
warehouse stock, and both are shown so they are never confused.

### 1.9 Listing Status — PARTIAL

| | |
|---|---|
| **Table / column** | `ledsone.listings.amazon_listings.status` |
| **Join key** | `asin` + `sub_source` + `site` |
| **Null handling** | `Not Found` where we hold no listing row |
| **Coverage** | 20,821 / 20,821 |

**Aggregation (an ASIN may carry several offers — 2,079 groups have mixed statuses):**

```
any offer Active or BUYABLE   -> Active
else any DISCOVERABLE         -> Discoverable (not buyable)
else any Incomplete           -> Incomplete
else any Inactive             -> Inactive
else                          -> Unknown / Not Found
```

Rationale: one buyable offer makes the ASIN sellable by us, so the most-available status wins.
All distinct raw statuses are retained per row so nothing is lost.

> **REQUIRES APPROVAL — "Suppressed".** The requirement's output table expects
> *Active / Inactive / Suppressed*. **`Suppressed` does not exist in the source.**
> `DISCOVERABLE` (listing visible but no buyable offer) is the closest concept, but renaming it
> to "Suppressed" would be an invented mapping, so the derived label is shown verbatim instead.

**Note:** `wrong_sku = 1` rows are **included** for status derivation — `wrong_sku` flags a bad
SKU-to-product mapping, not an invalid listing, and excluding it would hide genuine live offers.
The flag is counted per group (`wrong_sku_rows`) so the decision is auditable.

### 1.10 Category — VERIFIED

| | |
|---|---|
| **Table** | `ph_dashboard.public.ph_allocation_idrecord` → `ph_allocation_phcategory` |
| **Columns** | `refId` (holds the ASIN) → `category_id` → `phcategory.name` |
| **Join key** | `refId = listing_ref`, de-duplicated with `GROUP BY refId` |
| **Transformation** | `min(name)` with `count(DISTINCT name)` retained as `cat_variants` to expose ambiguity |
| **Null handling** | `Not Available` |
| **Evidence** | 20,821 / 20,821 (100%), 66 distinct categories, only 1 ASIN with `cat_variants > 1` |

De-duplication is deliberate: joining `ph_allocation_idrecord` un-grouped would inflate the
spine. Row count after the join is unchanged at 20,821 — asserted in code.

### 1.11 Last Checked — VERIFIED (with a precise meaning)

| | |
|---|---|
| **Column** | `amz_sales_and_traffic_by_asin.date` of the selected row |
| **Meaning** | the **date Amazon measured** the Buy Box for that ASIN — the real verification date |
| **Null handling** | blank where status is NOT VERIFIED with no report row |
| **Latest value present** | `2026-10-12` |

This is deliberately **not** the dashboard build time. A build timestamp would misrepresent
stale data as a fresh check. Snapshot/build times are shown separately in the header.

---

## 2. Grain and integrity validation

| Check | Result |
|---|---|
| Uniqueness at ASIN + account + marketplace | **PASS** — max key occurrence = 1 (asserted, build fails otherwise) |
| Row count preserved through all joins | **PASS** — 20,821 in, 20,821 out |
| Buy Box join reconciliation | **PASS** — independent coverage query returned 7,860 PH rows with a report row; classified YES 6,789 + NO 915 + partial 156 = **7,860** |
| Multi-SKU relationships preserved | **PASS** — aggregated by rule, never arbitrarily selected; `offer_rows` retained |
| Category join inflation | **PASS** — de-duplicated before join |
| Seller-account match | **PASS** — both `sub_source` values verified against the lookup table |
| Marketplace match | **PASS** — all four IDs verified against `order_management.market_place` |
| Manual spot check vs source | **PASS** — 6 rows (2 YES, 2 NO, 1 partial, 1 no-data) re-queried directly; Buy Box %, report date, listing quantity and status matched exactly on all 6 |

---

## 3. Summary of mapping classifications

| Field | Status |
|---|---|
| ASIN | VERIFIED |
| SKU | VERIFIED |
| Seller / Account | VERIFIED |
| Marketplace | VERIFIED |
| **Buy Box Owner (identity)** | **NOT FOUND** |
| Buy Box Status | VERIFIED within coverage; partial band REQUIRES APPROVAL |
| **Reason** | **REQUIRES APPROVAL** — no approved rule exists; `Unknown` applied |
| Stock | VERIFIED |
| Listing Status | PARTIAL — `Suppressed` REQUIRES APPROVAL |
| Category | VERIFIED |
| Last Checked | VERIFIED |
