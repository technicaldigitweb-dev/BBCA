# Phase 2 — Amazon UK Live Listing Verification

**ASIN:** `B086385W3W` · **Marketplace:** amazon.co.uk
**Network:** egress `123.231.101.76` (Colombo, LK, AS18001 Dialog Axiata), no proxy
**Result: BLOCKED** by an Amazon access control at 2026-10-14 ~13:45 (+05:30).

## Memory and browser safety checks (performed before launching Chromium)

| Check | Result |
|---|---|
| Free system memory | 3.63 GB free of 15.89 GB (22.8%) — adequate for one instance |
| Playwright-owned browser processes already running | **0** — no orphan from the earlier session |
| Other `chrome.exe` processes | 50 — the user's own browser, ownership verified as **not ours**, left untouched |
| Duplicate instances | avoided — one instance, one ASIN |
| Process timeout | strict 150 s wall-clock cap on the run |
| Indefinite background processes | none used; the run executed in the foreground |

An earlier holding process from the previous session was terminated by Claude Code
under system memory pressure, not by instruction. That is why the orphan check matters
and it was explicitly confirmed clean before relaunching.

## Access verification: one attempt, no retries

A single strictly-timed attempt was made. Amazon returned its access-control page:

```
[locale] ok=False BLOCKED by Amazon access control; markers=['validatecaptcha',
         'click the button below to continue shopping', 'api-services-support',
         'to discuss automated access']
STOP: Amazon access control present. Marking run BLOCKED. No retry, no bypass.
```

Per instruction, automated requests stopped at that point. The challenge was **not**
interacted with, no retry was issued, no stealth plugin, fingerprint spoofing,
CAPTCHA-solving service or proxy rotation was used. Evidence: `phase2_single.json`
(`extraction_status: "blocked"`).

The verifier now classifies this condition explicitly rather than reporting it as a
selector timeout, so a blocked run can never be mistaken for a data problem.

## Evidence captured earlier the same day, before the block

These values were collected by the same code path while access was still open, and
are recorded with that provenance rather than presented as current:

| Field | Value | |
|---|---|---|
| Delivery location | London SW1A1AA | set via Amazon's own location picker |
| Currency | GBP (`i18n-prefs=GBP`) | |
| Availability | In stock | |
| Featured offer price | **£18.89** | |
| Featured offer seller (name) | Amazon | display string only |
| Featured offer seller (ID) | **not available** | no `seller=` href rendered |
| Other offers | **2** | via `/gp/offer-listing/` |

Without the UK postcode the same page is **suppressed**: "Deliver to Sri Lanka",
"This item cannot be dispatched to your selected delivery location", price shown as
`LKR8,303.29`. The user independently confirmed this state in a manual browser
session — their screenshot showed Deliver to Sri Lanka, LKR pricing, no buy box, no
Add to Basket, only "Add to List".

## Export vs UK domestic — NOT RESOLVED

The buy-box seller row renders as the combined **"Shipper / Seller: Amazon"** and the
delivery promise reads *"FREE delivery … on your first order to UK or Ireland"*. That
is the AmazonGlobal/export presentation, not the UK-domestic split
("Dispatches from" / "Sold by").

Setting a UK postcode changes the **delivery destination**; it does not make the
session a UK-domestic shopper. Whether the featured offer observed is the same offer a
UK shopper is served therefore remains **NOT VERIFIED**. Nothing in this phase may be
treated as a confirmed UK domestic offer.

## VPN investigation

- **A VPN is not required for page accessibility.** Plain `curl` from this IP returns
  the full 2.3 MB product page.
- **A VPN will not solve the automation challenge.** The block is not IP-based: `curl`
  from the same IP succeeds while Playwright Chromium is challenged in **both**
  headless and headed modes. This is detection of the automation control layer, not of
  the network.
- **A VPN remains worth doing for one purpose only** — settling the export-vs-domestic
  question above, under an authorized browser session.
- **No VPN connection or configuration change was made.** Confirmation was not
  requested or given, and none will be made without asking first.

## Acceptance

| Criterion | Status |
|---|---|
| UK marketplace and delivery context confirmed | **PARTIAL** — confirmed pre-block (London SW1A1AA), unverifiable now |
| Correct GBP price | **PARTIAL** — £18.89 GBP confirmed pre-block |
| Seller information accurately extracted | **FAIL** — display name only; no seller ID obtainable |
| No Sri Lanka export offer misclassified as UK domestic | **MET** — explicitly recorded as unresolved, not claimed as domestic |
| Any access restriction recorded clearly | **MET** — `extraction_status: blocked` with markers |

**Phase 2 verdict: PARTIAL / BLOCKED.** Live re-verification is not currently possible
by browser automation.
