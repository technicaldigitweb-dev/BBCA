# Phase 2 — UK Marketplace Accuracy + VPN Comparison

**ASIN:** `B086385W3W` · **Marketplace:** amazon.co.uk · **Postcode:** `SW1A1AA`
**Network:** Sri Lanka, egress `123.231.101.76` (Colombo, AS18001 Dialog Axiata), no proxy

## UK locale verification: PASS (with one unresolved caveat)

Amazon's default behaviour from this IP is to geolocate to Sri Lanka and **suppress the
entire Buy Box**:

| | Default (no locale set) | After UK postcode + GBP |
|---|---|---|
| Delivery location | `Sri Lanka` | `London SW1A1AA` |
| Availability | "This item cannot be dispatched to your selected delivery location." | `In stock` |
| Price | *(absent)* → then `LKR8,303.29` | **£18.89** |
| Currency cookie | `i18n-prefs=LKR` | `i18n-prefs=GBP` |
| Add to basket | absent | present |
| Featured seller | *(absent)* | `Amazon` |
| Other offers | *(absent)* | **2** |

The fix uses Amazon's own delivery-location picker
(`#nav-global-location-popover-link` → `#GLUXZipUpdateInput` → `#GLUXZipUpdate`) plus the
`i18n-prefs=GBP` cookie. No restriction was bypassed. `verify_live_listing.py`
**asserts** the result and aborts the run if `#glow-ingress-line2` is not a UK location
and the cookie is not GBP, so suppressed pages can never be silently collected.

**Unresolved caveat:** the seller row renders as the combined **"Shipper / Seller: Amazon"**
and the delivery promise reads *"FREE delivery … on your first order to UK or Ireland"* —
this is the AmazonGlobal/export presentation, not the UK-domestic split
("Dispatches from" / "Sold by"). Whether the featured offer shown to a Sri Lankan IP with
a UK postcode is the **same offer** a UK shopper sees is therefore **NOT VERIFIED**.
That is precisely what the VPN comparison below exists to settle.

## VPN comparison: PENDING

No UK VPN connection was made. Per instruction, network and VPN settings were not
changed, and confirmation was not given. Recorded as PENDING, **not** assumed to match.

| Field | Sri Lanka connection | UK VPN |
|---|---|---|
| Product ASIN | B086385W3W | NOT VERIFIED |
| Featured seller | Amazon *(display name only)* | NOT VERIFIED |
| Featured price | £18.89 | NOT VERIFIED |
| Availability | In stock | NOT VERIFIED |
| Other offers | 2 | NOT VERIFIED |
| Delivery location | London SW1A1AA *(set manually)* | NOT VERIFIED |
| Currency | GBP *(set via cookie)* | NOT VERIFIED |

Every field: **NOT VERIFIED** for the UK VPN column.

### Important: a VPN will not resolve the current blocker

The session is now receiving Amazon's automation interstitial
(see `amazon_access_block.md`). That block is **not** IP-related — plain `curl` from the
same IP is served the full 2.3 MB page, while both headless *and* headed
Playwright Chromium are challenged. A UK VPN would change the egress country but not
the automation detection.

A UK VPN remains worth doing for **one specific purpose**: settling the
export-vs-domestic caveat above, i.e. confirming that the featured offer and seller we
read match what a UK shopper is served. It is a data-fidelity check, not a fix for access.

### Safe verification test once a UK VPN is connected (awaiting your go-ahead)

1. `curl https://ipinfo.io/json` — confirm `"country": "GB"`.
2. Re-run `verify_live_listing.py` on `B086385W3W` only (`--limit 1 --label uk_vpn`).
3. Assert: `#glow-ingress-line2` is UK, currency GBP, no interstitial markers.
4. Compare against this baseline — **£18.89 / seller Amazon / 2 other offers** — and
   check whether the merchant row splits into "Dispatches from" + "Sold by".
5. Classify each field MATCH / DIFFERENT, then stop. One ASIN only.
