# Phase 3 — Listing Data Extraction

**Verdict: INTEGRATION BLOCKER.** No authorized source can supply the required live
offer data, and browser automation is blocked. Extraction is **not** complete and is
not claimed to be.

## Step 1 — Is there an authorized source? (investigated first, as instructed)

### Warehouse sweep (read-only)

Tables matching `%offer%`, `%competitive%`, `%pricing%`, `%buybox%`, `%buy_box%`,
`%sp_api%`, `%spapi%` across all schemas of `ledsone`:

```
candidate authorized-source tables: 0
```

The complete set of authorized Amazon feeds present:

| Source | What it gives | Limit |
|---|---|---|
| `business_reports.amz_sales_and_traffic_by_asin` | `buy_box_percentage`, `buy_box_percentage_b2b` (of 53 columns, the only Buy Box fields) | Ownership **percentage** only. No featured-offer seller, no offer price, no Prime flag. Max date 2026-10-12, 1,509,878 rows |
| `amazon_fba.excess_inventory_data` | `your_price`, `featuredoffer_price`, `sku`, `currency`, `snapshot_date` | FBA **excess** scope only — 792 of 20,821 PH rows (3.8%). Names **no seller** |
| `business_reports.amz_catalog_performance_data`, `amz_search_query_performance`, `amz_best_seller_rank`, `amazon_campaigns.*` | traffic, search, ads | no offer or seller data |

### SP-API integration

Searched the project and estate for `sp-api`, `sp_api`, `sellingpartnerapi`,
`selling-partner`, `getCompetitivePricing`, `getItemOffers`, `SellingPartner`, `LWA_`,
`refresh_token`. The only hits are **`buy_box_handover.md`** and
**`buy_box_source_mapping.md`** — this project's own documents, recommending SP-API.
There is **no SP-API client, no LWA credential, no refresh token and no integration**
anywhere in the estate.

**Conclusion:** no authorized source supplies featured-offer seller identity, and none
supplies offer prices beyond 3.8% FBA-excess coverage. Preferring authorized
integrations for recurring automation is the right policy, and there is nothing yet to
prefer.

## Step 2 — Browser-based inspection

`03_SCRIPTS/verify_live_listing.py` implements the full required field set and was
validated end to end while access was open. It is reusable and re-runnable.

| Required field | Implementation | Status |
|---|---|---|
| ASIN | input + `asin_on_page` verification against page HTML | working |
| Marketplace | host assertion `www.amazon.co.uk` | working |
| Delivery region | `#glow-ingress-line2`, asserted as UK or the run aborts | working |
| Currency | `£` in price + `i18n-prefs` cookie check | working |
| Product title | `#productTitle` | working |
| Featured Offer seller | `[offer-display-feature-name='desktop-merchant-info']` node[1] | working (name only) |
| Featured Offer seller ID | `a[href*='seller=']` → merchant token | **never resolved** — no such href when Amazon owns the offer |
| Featured Offer price | `#desktop_buybox` with fallback chain | working |
| Our seller account | from the internal record (`account`) | working |
| Our seller ID | — | **unavailable**, see `seller_identity.md` |
| Our offer price | from the internal record, kept **separate** from the featured price | working |
| Stock availability | `#availability`, `#outOfStock`, add-to-cart presence | working |
| Listing availability | buy-box presence + add-to-cart presence | working |
| Competing offers | `/gp/offer-listing/<ASIN>` → `#aod-pinned-offer`, `#aod-offer` | working (count); per-offer seller name returns the label, needs the value node |
| Fulfilment information | merchant-info rows | partial — combined "Shipper / Seller" only |
| Checking timestamp | real local timestamp per ASIN | working |
| Source URL | recorded | working |
| Extraction status | `blocked` / `locale_unconfirmed` / per-ASIN error | working |
| Error / missing-data reason | recorded per field and per run | working |

### Data validation safeguards built in

- The run **aborts** unless `#glow-ingress-line2` is a UK location and `i18n-prefs=GBP`,
  so a Sri-Lanka-suppressed page can never be silently collected.
- `asin_on_page` confirms the returned document is the intended ASIN.
- The featured-offer price and our own price are carried in separate fields; the
  featured price is never read as ours.
- Sellers are **not** matched by display name. No approved mapping exists, so no match
  is asserted.

## Step 3 — Sample verification

The balanced 10-ASIN UK sample (`06_EVIDENCE/sample_10_uk.json`) is prepared and
covers the required strata and both accounts:

| ASIN | Account | Stratum |
|---|---|---|
| B07VFV228J | LEDSone | price above featured |
| B07VXWJ5WY | LEDSone | price above featured |
| B086385W3W | LEDSone | price at/below featured |
| B083TNFR73 | LEDSone | zero stock |
| B0855MZ337 | LEDSone | zero stock |
| B08CXS3T8T | LEDSone | listing inactive |
| B08S45CM19 | LEDSone | discoverable (not buyable) |
| B0GLPLNXXC | DCVoltage | no reason signal |
| B0GLYZ41VT | DCVoltage | no reason signal |
| B018OUTQ84 | LEDSone | no reason signal |

**Executed: 0 of 10.** The access control described in
`amazon_uk_listing_verification.md` blocked the run before any ASIN was read. Marked
blocked; not retried; not bypassed.

Only `B086385W3W` has verified live values at all, captured earlier the same day
before the block (£18.89, seller "Amazon", 2 other offers, In stock, London SW1A1AA).

## Acceptance

| Criterion | Status |
|---|---|
| Correct seller and price extraction for successfully checked ASINs | **PARTIAL** — price yes; seller name only, never seller ID |
| Separate handling of missing, stale and blocked results | **MET** — distinct statuses, and Phase 1 adds stale/ambiguous/unusable price states |
| No false ownership classification | **MET** — no ASIN classified from a page; all 915 remain `Unknown` |
| Reusable extraction implementation with evidence | **MET** — script works; evidence saved |

## The blocker, stated plainly

Recurring Buy Box loss investigation needs, per ASIN, the featured offer's **seller
identity** and **price**. Today:

- the authorized warehouse feeds contain **neither**;
- the public page exposes the price but **not** a seller identifier;
- and the page is no longer reachable by automation at all.

SP-API is the only path that resolves all three — `getItemOffers` /
`getCompetitivePricing` return the featured offer with its seller id, and
`getMarketplaceParticipations` returns our own merchant token, which would also close
the seller-identity gap in `seller_identity.md`. That integration does not exist and
is a decision for the business, not something to improvise.
