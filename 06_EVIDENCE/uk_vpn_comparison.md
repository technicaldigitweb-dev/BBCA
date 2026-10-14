# Phase 2 (completed) — UK VPN Fidelity Comparison

**Run:** 2026-10-14, `03_SCRIPTS/run_cdp_verify.py --label uk_vpn --limit 1`
**ASIN:** `B086385W3W` · **Postcode:** `SW1A1AA` · **Currency:** GBP
**Evidence:** `06_EVIDENCE/uk_vpn_baseline.json`

## Network

| | Sri Lanka connection | UK VPN |
|---|---|---|
| Egress IP | `123.231.101.76` | `57.129.148.71` |
| Country / city | LK, Colombo (AS18001 Dialog Axiata) | **GB, Erith (AS16276 OVH SAS)** |
| Scope | system-wide | **browser-scoped** |

**Important operational finding:** the VPN is **browser-scoped, not system-wide**. During this
run `curl` from the shell still egressed via Sri Lanka (`123.231.101.76`) while the Chrome window
egressed via GB. A Playwright-*launched* browser would therefore have taken the system route and
read a Sri Lankan page. All collection must be driven over **CDP against the already-open
window** (`run_cdp_verify.py`), never `verify_live_listing.py`'s own launcher, whenever a
browser-scoped VPN is in use.

## Field comparison

| Field | Sri Lanka connection | UK VPN | Verdict |
|---|---|---|---|
| Product ASIN | B086385W3W | B086385W3W | **MATCH** |
| Featured seller | Amazon | Amazon | **MATCH** |
| Featured price | £18.89 | £18.89 | **MATCH** |
| Availability | In stock | In stock | **MATCH** |
| Other offers | 2 | 2 | **MATCH** |
| Delivery location | London SW1A1AA | London SW1A1AA | **MATCH** |
| Currency | GBP | GBP | **MATCH** |
| Merchant row form | "Shipper / Seller" (combined) | "Shipper / Seller" (combined) | **MATCH** |

**7 of 7 comparable fields MATCH. Verdict: PASS.**

## The export-vs-domestic caveat is resolved — differently than expected

`uk_locale_and_vpn.md` recorded the combined **"Shipper / Seller"** row and the *"on your first
order to UK or Ireland"* delivery promise as evidence that the Sri Lankan view might be an
AmazonGlobal/export rendering rather than the UK-domestic one, and marked it NOT VERIFIED.

From a genuine **GB** IP the row still renders as **"Shipper / Seller"**, and the delivery promise
still reads *"FREE delivery Sunday, 18 October on your first order to UK or Ireland"*.

So the combined row was **never an export artefact**. It is how Amazon renders the merchant block
when **Amazon itself is the featured seller**, and the "first order" wording is a new-customer
promotion tied to the fresh browser profile, not to the egress country.

**Consequence:** the Sri Lanka + UK-postcode + GBP-cookie configuration produces a page that is
field-for-field identical to the UK-VPN view on this ASIN. The evidence collected earlier from
Sri Lanka is therefore **valid**, and a VPN is **not required for data fidelity**. It remains
useful for access reputation (a fresh IP), not for correctness.

One honest limit: this is **one ASIN with Amazon as the featured seller**. An ASIN whose featured
offer belongs to a third-party merchant may render the UK-domestic split
("Dispatches from" / "Sold by"), which this test could not exercise. The Phase 4 sample covers
further ASINs.

## Breakthrough: the seller identifier IS obtainable

`seller_identity.md` recorded **FAIL** — "no merchant token could be extracted for any offer".
That verdict was caused by a **selector defect, not by Amazon**.

The `[id^=aod-offer-soldBy]` container emits a *label* column and a *value* column under the same
id prefix. The previous extractor took the first match and therefore returned the literal string
`"Sold by"`, and because it never reached the value column it never reached the
`a[href*='seller=']` anchor either.

With the corrected extractor (`sold_by()` in `verify_live_listing.py`, which reads
`.a-col-right` first and rejects known label strings), the offer-listing page yields:

| Offer | Price | Seller name | **Seller ID** |
|---|---|---|---|
| Featured (pinned) | £18.89 | Amazon | *(none — Amazon retail exposes no seller link)* |
| Offer 1 | £18.89 | LEDSONE | **`A1BXMEJKH8MYIL`** |
| Offer 2 | £20.89 | LEDSONE | **`A1BXMEJKH8MYIL`** |

`A1BXMEJKH8MYIL` is a genuine Amazon merchant token (the `A`-prefixed 13–14 character form).

**This overturns the Phase 4 seller-identity FAIL.** Identity matching by identifier is possible
after all — the token is on the **offer-listing page**, not the buy-box row. Side 2 of that
finding still stands: no merchant token is stored anywhere in the warehouse, so the mapping
`A1BXMEJKH8MYIL → LEDSone (sub_source 8)` must still be established and recorded once, and
confirmed for DCVoltage, before identity matching can be relied on in bulk.

## What this ASIN actually shows about the Buy Box loss

`B086385W3W` is recorded internally as Buy Box **NO** (`buy_box_percentage = 0`). The live page
explains why, and it is **not** a price problem:

- The featured offer is held by **Amazon retail** at £18.89.
- **Our own LEDSONE offer matches that price exactly at £18.89** — we are not priced above.
- Our second offer sits at £20.89.
- The listing is **In stock** with Add-to-basket present.

Price, stock and listing status are therefore all ruled out by direct observation. The loss is
attributable to Amazon retail holding the featured offer — a condition none of the five sample
reason labels in the requirement describes.
