# Phase 3 — Playwright Selector Validation

**Collected:** 2026-10-14, Amazon UK (`www.amazon.co.uk`), ASIN `B086385W3W`
**Conditions:** Chromium 147.0.7727.15, Playwright 1.59.0, UK postcode `SW1A1AA`,
`i18n-prefs=GBP`, locale `en-GB`. Results below were captured **before** Amazon began
serving the automation interstitial (see `amazon_access_block.md`).
**Status:** PARTIAL — the structural selectors pass; the two identity-bearing
extractions (seller token, per-offer seller name) do not.

## Requested selectors

| Selector | Verdict | Observed |
|---|---|---|
| `[offer-display-feature-name='desktop-merchant-info']` | **PASS (with caveat)** | Returns **two** nodes, not one: node[0] = label `"Shipper / Seller"`, node[1] = value `"Amazon"`. Must index the value row; reading node[0] yields the label, not data. |
| `#aod-ingress-link` | **PASS** | Present. `[data-action='show-all-offers-display']` also present and equivalent. |
| `#aod-pinned-offer` | **PASS** | Present on `/gp/offer-listing/<ASIN>`; carries the featured offer block. |
| `#aod-offer` | **PASS** | Returned **2** competing offers for B086385W3W. |
| `#availability` | **PASS** | `"In stock"` once UK postcode applied; `"This item cannot be dispatched to your selected delivery location."` without it. |
| `#desktop_buybox` | **PASS** | Present; contains price, availability, merchant rows, Add-to-basket. |

## Additional selectors tested

| Purpose | Selector | Verdict |
|---|---|---|
| Featured price | `#corePriceDisplay_desktop_feature_div span.a-offscreen` | **FAIL** — returned empty string. Price is reachable via `#desktop_buybox` text (`£18.89`) or a `.a-price .a-offscreen` fallback chain. A fallback list is required. |
| Delivery location assert | `#glow-ingress-line2` | **PASS** — `"London SW1A1AA"`; the correct guard for marketplace/region correctness. |
| Seller **identifier** | `a[href*='seller=']` inside buybox | **NOT VERIFIED** — no seller-profile href present when the featured seller is Amazon itself. No merchant token could be extracted for any offer. |
| Per-offer seller name | `[id^=aod-offer-soldBy] a` | **PARTIAL** — returned the label `"Sold by"` rather than the seller value on both offers. Needs the sibling/value node, not the labelled container. |
| Legacy `#tabular-buybox .tabular-buybox-text` | — | **FAIL** — row count **0**. |
| Legacy `#merchant-info` | — | **FAIL** — absent. |
| Legacy `#sellerProfileTriggerId` | — | **FAIL** — absent. |

## Field values actually extracted (B086385W3W)

| Field | Value |
|---|---|
| Product title | LEDSone Metal E27 Pendant Light Fitting with Twisted Braided Cable |
| Availability | In stock |
| Featured offer price | £18.89 (GBP confirmed) |
| Featured seller (name) | Amazon |
| Featured seller (token) | **not available** |
| Other offer count | 2 |
| Other seller names | **not extracted** (label returned instead of value) |
| Delivery location | London SW1A1AA |

## Conclusions

1. The legacy selector set in the original spec is dead — all three legacy selectors
   return nothing. Confirmed replacement is the `offer-display-feature` layout.
2. `desktop-merchant-info` emits a label row and a value row under the **same**
   attribute; any extractor that takes the first match will silently record
   `"Shipper / Seller"` as the seller name.
3. The buy-box seller row renders as the combined **"Shipper / Seller"**, which is the
   AmazonGlobal/export presentation rather than the UK-domestic split
   ("Dispatches from" / "Sold by"). UK-domestic rendering remains unconfirmed.
4. **No seller identifier is obtainable from the page** for an Amazon-owned featured
   offer, and no merchant token exists internally either (see
   `seller_identity.md`). Identity matching by identifier is therefore not possible today.
