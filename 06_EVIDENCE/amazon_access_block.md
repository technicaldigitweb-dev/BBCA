# Amazon Automation Interstitial — Access Blocker

**Discovered:** 2026-10-14 ~12:30 (+05:30), during Phase 2 of the final verification.
**Effect:** Phases 4 and 5 (ten-ASIN live verification) could not be executed.
**Action taken:** collection halted. No click-through, no fingerprint spoofing, no retry storm.

## What Amazon returns

Playwright-driven Chromium now receives a 3,518-byte interstitial instead of the
2.3 MB product page:

```
HTTP 200   title: "Amazon.co.uk"
body:  "Click the button below to continue shopping"
form action: /errors_page/validateCaptcha
html comment: "To discuss automated access to Amazon data please contact
               api-services-support@amazon.com. For information about migrating
               to our APIs refer to our Marketplace APIs at
               https://developer.amazonservices..."
```

The page carries a single `Continue shopping` button posting to
`/errors_page/validateCaptcha`. **This is an Amazon access control.** It was not
clicked, submitted, or circumvented, per the project instruction not to bypass
CAPTCHA, IP restrictions, or Amazon access controls.

## Diagnostic matrix (same machine, same IP, same UA string)

| Client | Bytes | Result |
|---|---|---|
| `curl` (plain HTTPS) | 2,297,792 | **Full product page** — 0 captcha markers, 6 `productTitle` hits |
| Playwright Chromium **headless** | 3,518 | Automation interstitial |
| Playwright Chromium **headed** (`headless=False`) | 3,518 | Automation interstitial |

Earlier the same day, the identical Playwright headless configuration returned the
full 2.3 MB page repeatedly (that is how the Phase 3 selector evidence and the
£18.89 / seller Amazon / 2-offers baseline were captured). The block therefore
appeared **part-way through the session**, after roughly 10–15 automated page loads
from this IP.

## Interpretation

- **Not a network or VPN problem.** `curl` from the same IP is served the real page
  in full. Egress IP is `123.231.101.76` (Colombo, LK, AS18001 Dialog Axiata).
- **Not headless-specific.** A real visible browser window is challenged identically,
  so this is detection of the automation control layer (CDP / `navigator.webdriver`),
  not of headless rendering.
- **Rate/volume sensitive.** The same configuration worked, then stopped working,
  with no code change in between. That is the signature of a request-volume or
  reputation trigger.

## Consequence for this project

The automation needs **915** product pages per full run. The block appeared after
~10–15. Browser-driven scraping of the full set is therefore not viable on the
current approach, and no amount of VPN or selector work changes that — Amazon's own
notice on the interstitial directs automated access to the Marketplace APIs (SP-API).

A cooldown characterisation probe was run (`logs/cooldown_retry.log`) to establish
whether the block lifts on its own and on what timescale.
