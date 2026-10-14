# Phase F — Bulk Automation Readiness v2

**Assessed:** 2026-10-14 (supersedes `bulk_readiness.md`)
**Verdict: BLOCKED BY INTEGRATION.**

Current Featured Offer ownership at 915-ASIN scale cannot be obtained through any route
authorised and available today.

---

## 1. Authorised integration options — investigated first

### Option A — SP-API Product Pricing (`getItemOffers` / `getCompetitivePricing`) — **NOT AVAILABLE HERE**

This is the correct source. It returns the featured offer, its seller ID, its price and Prime
eligibility directly, with no scraping, and Amazon's own automation interstitial explicitly
directs automated access to it.

**An SP-API integration demonstrably exists in the estate:**

| Evidence | What it shows |
|---|---|
| `listings.amazon_marketplaces` carries `is_participating`, `has_suspended_listings` | the shape of a **Sellers API `getMarketplaceParticipations`** response |
| `Weekly_Top_Moving_ASIN_Keyword_Report/data/extract.json` holds `300403` errors with `attribute_names` and `contribution/compliance_media` paths | stored **Listings Items API** responses |

**But it is not reachable from this environment:**

- `listings.amazon_marketplaces.amz_token_id = 1` is a foreign key to a credential table that
  **does not exist in the `ledsone` warehouse**. The store lives in the application tier.
- No SP-API/LWA key exists in `product-page/.env` or anywhere else in scope
  (searched `AMZ|AMAZON|SPAPI|SP_API|LWA|SELLER|MERCHANT|REFRESH|CLIENT`).
- Per the brief, **no credential was created and no new authorisation was requested.**

**Required to unblock:** access to the existing SP-API application's credentials, with the
Product Pricing role enabled, for `sub_source` 6 and 8.

### Option B — existing internal reports — **INSUFFICIENT**

| Source | Why it cannot answer the question |
|---|---|
| `business_reports.amz_sales_and_traffic_by_asin.buy_box_percentage` | historical day-level share, **not current ownership**; names no seller; only covers ASINs with traffic that day (7-day coverage 37.8%) |
| `amazon_fba.excess_inventory_data.featuredoffer_price` | a price with **no seller identity**; FBA-excess scope only, 792 of 20,821 rows (3.8%) |
| `listings.amazon_listings.status` | our own listing state; **wrong on 3 of 10** when checked live |

No internal report carries current featured-offer ownership. This is a genuine capability gap,
not a query that has not been written yet.

### Option C — browser automation — **NOT AUTHORISED AT THIS SCALE**

Technically it now works. It is still the wrong answer for 915 ASINs.

| Measurement | Value |
|---|---|
| Ten-ASIN run (CDP, UK egress) | **10/10, 0 blocks** |
| Rate | ~15.8 s/ASIN, 2 page loads each |
| Session total | 22 loads, clean |
| **Projected full run** | **~4 hours, ~1,830 page loads** |
| Earlier Playwright-*launched* runs | interstitial after **~10–15** loads |

Amazon served an automation interstitial earlier the same day and its own notice directs
automated access to the Marketplace APIs. Scaling from 22 loads to 1,830 is a ~83× increase
against a control that has already triggered once.

Per the brief, none of the available evasions are acceptable, and none were used: no CAPTCHA
click-through, no proxy rotation to dodge restrictions, no fingerprint spoofing, no use of a
verified browser session to evade controls. **With those off the table there is no compliant way
to scale browser checks to 915 ASINs.**

---

## 2. Readiness criteria

| Criterion | Status | Detail |
|---|---|---|
| Expected ASIN volume | known | 915 historical NO (all still candidates — no fresher data exists) |
| Account / marketplace coverage | **PARTIAL** | live method proven on **UK only**; DE/FR/IT unexercised |
| API permissions | **BLOCKED** | SP-API exists in the estate, not reachable here |
| Rate limits | **UNKNOWN** | no published limit for page access; interstitial is the only observed control |
| Data freshness | **PASS** | live check is real-time; `live_checked_at` recorded per row |
| **Seller identity** | **PASS** | `A1BXMEJKH8MYIL` → LEDSone, `A3UNAW6KG6QUOJ` → DCVoltage, **VERIFIED** (SRM still unconfirmed) |
| Request duration | known | ~4 h for 915 |
| Failed checks | **PASS** | `CHECK ERROR` state exists and is preserved separately |
| Retry policy | **PARTIAL** | locale setup retries ×3; **per-ASIN retry not implemented** |
| Daily execution feasibility | **FAIL** | a 4 h browser run cannot be a daily job, and needs the VPN browser open |
| History storage | **NOT BUILT** | no run-history table; needs write approval |
| Manual Run Check integration | **FAIL** | standalone offline HTML cannot invoke any checker |

---

## 3. What changed since `bulk_readiness.md`

| Then | Now |
|---|---|
| Seller identity PARTIAL — blocker | **VERIFIED** — resolved |
| "Refresh internal data first, it may remove much of the work" | **Done. No fresher data exists.** All 915 remain candidates |
| NOT READY, pending characterisation | **BLOCKED BY INTEGRATION** — the limit is authorisation, not capability |

The two recommended pre-steps are now complete, and neither unblocked bulk running.

---

## 4. Required approval / integration

To make daily 915-ASIN checking possible, **one** of:

1. **SP-API Product Pricing access** (recommended) — enable the Product Pricing role on the
   existing SP-API application and expose credentials for `sub_source` 6 and 8.
   `getItemOffers` returns featured-offer seller ID, price and Prime eligibility in one call,
   within published rate limits, with no scraping. This also removes the Amazon-retail and
   SRM identity gap, since the API returns seller IDs the page does not expose.
2. **Written authorisation for scaled browser collection**, with an agreed rate, an agreed
   stop-on-challenge rule, and acceptance that Amazon may serve interstitials.

Without one of these, the honest position is that bulk automation is **blocked**, and the live
check remains a **targeted tool** — valuable for a shortlist of high-priority ASINs, not for the
full set.

---

## 5. Interim recommendation

Do not run 915. Run a **prioritised subset** — e.g. the highest-revenue losses — at the proven
~16 s/ASIN rate, which keeps a run inside a few hundred loads. That delivers most of the
commercial value of the exercise while the SP-API route is arranged.
