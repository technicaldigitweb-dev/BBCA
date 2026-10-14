# Phase 4 — Seller Identity Verification

**Verdict: FAIL.** Our seller account cannot be matched to a page offer by identifier.

The brief requires: *"Identify our seller account using verified identifiers"* and
*"Do not rely only on visible seller names for account identity matching."*
Neither side of that match is currently available.

## Side 1 — the page does not expose a seller identifier

On `B086385W3W` the featured offer is Amazon itself. No seller-profile link is
rendered, so no merchant token can be read:

| Attempt | Result |
|---|---|
| `a[href*='seller=']` within `#desktop_buybox` | no match |
| `a[href*='seller=']` within `#aod-pinned-offer` | no match |
| `a[href*='seller=']` within each `#aod-offer` (2 offers) | no match |
| `#sellerProfileTriggerId` (legacy) | absent |

Only a **display string** was obtainable: `"Amazon"`, read from the second
`desktop-merchant-info` node.

## Side 2 — we hold no Amazon merchant token internally

Read-only `information_schema` sweep of the `ledsone` warehouse
(`WLP_SOURCE_DB_URL`, SELECT only):

```sql
-- columns matching %merchant%id%, %seller_id%, %merchant_token%, %seller_token%
customer_service.amazon_returns   merchant_rma_id     -- returns RMA, not a seller
google_ads.campaigns              merchant_id         -- Google Ads
google_ads.merchant_products      merchant_id         -- Google Ads
google_ads.merchants              merchant_id         -- Google Ads
google_ads.product_performance    merchant_id         -- Google Ads
```

Widened to `%seller%`, `%merchant%`, `%mws%`, `%token%` across
`listings`, `business_reports`, `amazon_fba`, `orders`, `public`:

```
listings.amazon_marketplaces   amz_token_id    -- integer FK (=1), internal
public.personal_access_tokens  token           -- app auth, unrelated
```

`listings.amazon_marketplaces.amz_mar_id` holds the Amazon **marketplace** id, not a
seller id. **No Amazon seller/merchant token (the `A`-prefixed 13–14 char form)
exists anywhere in the estate.**

## Consequence

Our accounts are known only as the display names `LEDSone` and `DCVoltage`
(`sub_source` 8 and 6). Matching those strings against a page's seller text is
exactly the name-only matching the brief rules out — and it is unsafe here, because
an unrelated third-party seller may trade under a similar display name, and Amazon
renders our own offers as `"Amazon"` when fulfilled/sold by Amazon, which is
indistinguishable from a genuine Amazon retail offer.

Until a merchant token is available for each account — SP-API
`getMarketplaceParticipations` returns it directly — Buy Box **ownership** read from
a public page cannot be attributed to our account with confidence, only the
featured offer's existence can be observed.
