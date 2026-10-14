# Phase B — Seller Identity Verification

**Run:** 2026-10-14 · read-only database + filesystem inspection, no credentials created or changed
**Verdict: VERIFIED for both trading accounts.** An authoritative source was found inside the
estate: an SP-API Listings Items response stored in `Weekly_Top_Moving_ASIN_Keyword_Report/data/extract.json`,
which binds each seller ID to **our own `sub_source`** in the same record.

---

## Result

| Account | Candidate Seller ID | Verified Seller ID | Source | Status |
|---|---|---|---|---|
| LEDSone (`sub_source` 8) | `A1BXMEJKH8MYIL` | **`A1BXMEJKH8MYIL`** | **SP-API Listings Items response** in `Weekly_Top_Moving_ASIN_Keyword_Report/data/extract.json` (4/4 consistent, bound to `"sub_source": 8`) + live offer-listing page + `Downloads/pagesource.txt` | **VERIFIED** |
| DCVoltage (`sub_source` 6) | `A3UNAW6KG6QUOJ` | **`A3UNAW6KG6QUOJ`** | **SP-API Listings Items response** in the same extract (4/4 consistent, bound to `"sub_source": 6`) + live offer-listing page + `Downloads/pagesource.txt` | **VERIFIED** |
| SRM Suppliers (`sub_source` 9) | *(none captured)* | — | held the pinned/featured slot on 2 ASINs, which exposes no seller link | **UNCONFIRMED** |
| Amazon retail | *(not applicable)* | — | Amazon retail renders no seller profile link at all | **NOT OBTAINABLE** |

**No value above is guessed.** Each candidate is a string read directly from an Amazon page.

---

## What was searched

### 1. Authoritative seller-identity source — NOT FOUND

Read-only `information_schema` sweep of `ledsone` for
`token`, `seller_id`, `merchant_id`, `selling_partner_id`, `amz_seller`,
and for any table named `amz_token|amazon_token|sp_api|spapi|selling_partner|amz_credential|amz_account`:

| Found | Relevance |
|---|---|
| `google_ads.campaigns/merchants/merchant_products/product_performance.merchant_id` | Google Ads, not Amazon |
| `public.personal_access_tokens.token` | Laravel/Sanctum app auth, unrelated |

**No Amazon seller/merchant token (the `A`-prefixed 13–14 character form) is stored anywhere in
the warehouse.** This confirms Side 2 of the original `seller_identity.md` finding.

### 2. An SP-API integration exists — but not here

`listings.amazon_marketplaces` carries `is_participating` and `has_suspended_listings` per
marketplace, which is the shape of the Sellers API **`getMarketplaceParticipations`** response.
Something in the estate therefore *does* call SP-API.

However:

- Every row carries `amz_token_id = 1`, a foreign key to a token table that **does not exist in
  this database**. The credential store lives in the application tier (the `personal_access_tokens`
  table indicates a Laravel app), which is not reachable from here.
- The table has **no seller-id column**, so even the account it represents cannot be named.
- A single `amz_token_id` covers all marketplaces, while we operate **three** Amazon accounts —
  so this table cannot distinguish LEDSone from DCVoltage from SRM in any case.

**`getMarketplaceParticipations` could settle both IDs in one call**, and the integration to do so
already exists somewhere. It is simply not accessible from this environment, and per the brief no
credential was created and no new authorisation was requested.

### 3. Filesystem — no SP-API credentials

`product-page/.env` (the only `.env` in scope) contains **no** key matching
`AMZ|AMAZON|SPAPI|SP_API|LWA|SELLER|MERCHANT|REFRESH|CLIENT`. No SP-API application config was
found in `Automation/`, `product-page/` or the project folder.

### 4. Independent corroboration — found

`Downloads/pagesource.txt` is a **separately captured** Amazon UK page source (marketplace
`A1F83G8C2ARO7P`), not produced by this project. It contains both tokens in Amazon's own
`merchantCustomerID` field, bound to seller names:

```
"merchantCustomerID" : "A1BXMEJKH8MYIL"   ->  LEDSONE / LEDSone
"merchantCustomerID" : "A3UNAW6KG6QUOJ"   ->  DC Voltage
```

This is a **second, independent capture at a different time by a different means**, and it agrees
with the live extraction on both mappings.

---

## Why these are now VERIFIED

A third source was found that is **not** page content, and it is authoritative.

`Weekly_Top_Moving_ASIN_Keyword_Report/data/extract.json` (28 MB) holds stored **SP-API Listings
Items** responses — error code `300403`, with `attribute_names` and
`contribution/compliance_media` paths. Amazon's own media URLs in those responses carry the
submitting seller's ID, and each record also carries **our internal `sub_source`**:

```
"sku": "PSDS4BMRGD+WCDTYE", "sub_source": 8, ... 
   .../A13V1IB3VIYZZH/SELLER/A1BXMEJKH8MYIL/185011/...

"sku": "WCBNBS+RPR44WH",    "sub_source": 6, ...
   .../A1PA6795UKMFR9/SELLER/A3UNAW6KG6QUOJ/185022/...
```

| Token | Bound `sub_source` | Occurrences | Contradictions | Marketplaces |
|---|---|---|---|---|
| `A1BXMEJKH8MYIL` | **8 = LEDSone** | 4 / 4 | **0** | FR, DE |
| `A3UNAW6KG6QUOJ` | **6 = DCVoltage** | 4 / 4 | **0** | DE |

This is Amazon's own API response correlated against our internal account identifier in the same
record — not a display name, and not scraped page content. Combined with the live offer-listing
extraction and the independent `pagesource.txt` capture, **three independent sources agree with
zero contradictions**.

### Residual limit

These responses originate from LEDSone's and DCVoltage's own listing submissions, so they prove
**which `sub_source` submits under which seller ID**. That is exactly the mapping needed to
recognise our own offers on a page. A direct `getMarketplaceParticipations` call would still be
the cleanest confirmation and is recommended as a one-off, but it is no longer a blocker.

**SRM Suppliers (`sub_source` 9) remains UNCONFIRMED** — no token was captured for it from any
source.

---

## Effect on Buy Box classification

Per the brief, **no Buy Box status has been changed on the basis of a seller name**, and none on
the basis of a provisional ID either. Specifically:

- The four ASINs where our own account appeared to hold the featured offer
  (`B07VFV228J`, `B07VXWJ5WY`, `B0GLPLNXXC`, `B0GLYZ41VT`) are **not** reclassified to YES in the
  dataset. They are flagged as **conflicting** between the historical snapshot and the live check.
- Where **Amazon** or **SRM Supplies** holds the featured offer (5 of the 10 sampled), the holder
  is identified by **display name only** — no token is exposed in the pinned-offer slot. Those
  rows carry that limitation explicitly in their evidence text.

The asymmetry is worth stating plainly: our *own* offers can be identified by token, because our
offers appear in the non-featured offer list where the seller link renders. The *holder* of the
featured offer frequently cannot. So "is one of our offers on this listing?" is answerable with
good confidence; "who holds the Buy Box?" often is not.
