# Phases 4 & 5 — Ten-ASIN Live Verification + Reason Investigation

**Run:** 2026-10-14 14:00–14:03 (+05:30) · `03_SCRIPTS/run_cdp_verify.py --label phase4_uk_vpn`
**Transport:** CDP against the operator-opened Chrome (`127.0.0.1:9222`)
**Egress:** **GB** `57.129.148.71` (Erith, AS16276 OVH SAS) — UK VPN, browser-scoped
**Locale:** `London SW1A1AA`, `i18n-prefs=GBP`, asserted before any extraction
**Result:** **10 of 10 succeeded. Zero access blocks. Zero CAPTCHA interactions.**
**Evidence:** `06_EVIDENCE/phase4_ten_uk.json`, screenshots in `06_EVIDENCE/screenshots/*_uk.png`

All ten records are UK-marketplace Buy Box **NO** rows drawn from the verified PH dataset,
stratified across price-above, zero-stock, inactive, not-buyable, and no-signal cases.

---

## 1. Headline finding — 4 of 10 "Buy Box NO" records are stale, not lost

On four ASINs **our own account currently holds the featured offer**, confirmed by seller
identifier, despite the dataset recording Buy Box NO:

| ASIN | Account | Internal reading | Live featured seller | Seller ID | Verdict |
|---|---|---|---|---|---|
| B07VFV228J | LEDSone | 0% on 2026-10-11 | **LEDSONE** £24.69 | `A1BXMEJKH8MYIL` | **we hold it** |
| B07VXWJ5WY | LEDSone | 0% on 2026-10-11 | **LEDSONE** £33.89 | `A1BXMEJKH8MYIL` | **we hold it** |
| B0GLPLNXXC | DCVoltage | 0% on 2026-10-08 | **DC Voltage** £35.89 | `A3UNAW6KG6QUOJ` | **we hold it** |
| B0GLYZ41VT | DCVoltage | 0% on 2026-10-09 | **DC Voltage** £59.09 | `A3UNAW6KG6QUOJ` | **we hold it** |

The internal readings are 3–6 days old. The Buy Box moved in between. **`buy_box_percentage = 0`
on a report date is not evidence that we lack the Buy Box today** — it is evidence about that day
only.

If this 40% rate generalises, a material share of the dashboard's **915 Buy Box Lost** is
historical rather than current. That is a question about how the figure is *labelled*, not a data
error: the dashboard already shows the per-row `Last Checked` date and reports against a verified
base. But "Buy Box Lost" reads as a present-tense claim, and on this sample it frequently is not.

**Recommended (not applied):** relabel the card to carry its as-of date, e.g.
*"Buy Box Lost (as measured 2026-10-05 → 10-12)"*.

---

## 2. Internal stock and listing status are contradicted live on 3 of 10

| ASIN | Internal | Live | Assessment |
|---|---|---|---|
| B083TNFR73 | stock 0, Active | **In stock**, Add-to-basket present, our offer £11.83 live | internal stock wrong |
| B0855MZ337 | stock 0, **Inactive** | **In stock**, Add-to-basket present | internal status wrong |
| B08S45CM19 | stock 0, **Discoverable (not buyable)** | **In stock**, our LEDSONE offer £25.39 live | internal status wrong |

The "Listing quantity is 0", "No warehouse stock", "Listing status: Inactive" and
"Discoverable (not buyable)" signals were **false on every one of these**. Had the undefined
8-check list been implemented with stock- and status-based rules, all three would have been
assigned a confidently wrong reason.

**One internal signal was corroborated:**

| ASIN | Internal | Live | Assessment |
|---|---|---|---|
| B08CXS3T8T | stock 0, Inactive | **"Currently unavailable. We don't know when or if this item will be back in stock."** — no Add-to-basket, `#outOfStock` present, 0 offers | **CONFIRMED** |

---

## 3. Price is demonstrably not the determinant

| ASIN | Our live offer | Featured offer | Gap | Outcome |
|---|---|---|---|---|
| **B083TNFR73** | LEDSONE **£11.83** | Amazon £15.89 | we are **£4.06 cheaper** | **we still lost** |
| B086385W3W | LEDSONE £18.89 | Amazon £18.89 | **exact match** | we still lost |
| B018OUTQ84 | LEDSONE £7.69 | SRM Supplies £5.79 | we are £1.90 dearer | lost |
| B07VXWJ5WY | LEDSONE £33.89 *(featured)* | Amazon £34.99 also listed | we are £1.10 cheaper | **we hold it** |

`B083TNFR73` is decisive: our offer is **£4.06 below** the featured offer and Amazon retail still
holds the Buy Box. A "Price higher" rule would have returned the wrong answer here.

---

## 4. Two of the "losses" are to our own group company

| ASIN | Featured seller | Our offer on the same page |
|---|---|---|
| B08S45CM19 | **SRM Supplies** £25.39 | LEDSONE £25.39 *(`A1BXMEJKH8MYIL`)* + DC Voltage £25.49 *(`A3UNAW6KG6QUOJ`)* |
| B018OUTQ84 | **SRM Supplies** £5.79 | LEDSONE £7.69 *(`A1BXMEJKH8MYIL`)* |

**SRM Supplies is `sub_source` 9 — "amazon SRM Amazon" / company "SRM Suppliers"** in
`order_management.sub_source`, the same estate as LEDSone (8) and DCVoltage (6).

These are not competitive losses. We are bidding against ourselves across three of our own
seller accounts on the same ASIN. On `B08S45CM19` **all three** of our accounts are on the
listing simultaneously.

This is a commercial finding the requirement's five sample reason labels cannot express, and it
would be invisible to any database-only check.

---

## 5. Seller identity — the Phase 4 FAIL is overturned

`seller_identity.md` recorded **FAIL**: "no merchant token could be extracted for any offer".
That was a **selector defect**, not an Amazon limitation.

`[id^=aod-offer-soldBy]` emits a label column and a value column under the same id prefix. The
previous extractor took the first match, returned the literal string `"Sold by"`, and so never
reached the `a[href*='seller=']` anchor in the value column. Fixed in `verify_live_listing.py`
via `sold_by()`, which reads `.a-col-right` first and rejects known label strings.

**Tokens now captured across the sample:**

| Seller display name | Merchant token | Appears on |
|---|---|---|
| LEDSONE | **`A1BXMEJKH8MYIL`** | 6 ASINs |
| DC Voltage | **`A3UNAW6KG6QUOJ`** | 2 ASINs |
| Amazon | *(none — Amazon retail renders no seller link)* | 3 ASINs |
| SRM Supplies | *(not captured — held the pinned/featured slot, which exposes no link)* | 2 ASINs |

Identity matching by identifier is therefore **possible**, with two residual limits:

1. **Amazon retail exposes no token**, so an Amazon-held featured offer can only ever be
   identified by the display string `"Amazon"`.
2. The token appears on the **offer-listing page**, not the buy-box row, so confirming *who holds
   the featured offer* by identifier requires the pinned-offer block to expose a link — which it
   does not when the holder is Amazon or (in this sample) SRM.

The mapping `A1BXMEJKH8MYIL → LEDSone (8)` and `A3UNAW6KG6QUOJ → DCVoltage (6)` is inferred from
co-occurrence across 8 ASINs and is **consistent**, but has **not** been confirmed against an
authoritative source. SP-API `getMarketplaceParticipations` returns each account's token
directly and would settle it in one call.

---

## 6. Required Phase 5 table

`Official Reason` stays **Unknown** throughout — the 8-check list remains undefined, so no
approved rule exists to apply. `Possible Reason` is an evidence-backed hypothesis only.

| ASIN | Our Seller | Featured Seller | Our Price | Featured Price | Stock (internal) | Listing Status | Buy Box Status | Possible Reason | Official Reason | Confidence / Limitations | Checked At |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B07VFV228J | LEDSone | **LEDSONE** | £26.89 | **£24.69** | 39 | Active | **NOT A LOSS — we hold it** | Internal reading 3 days stale | Unknown | High — confirmed by token `A1BXMEJKH8MYIL` | 14:00:48 |
| B07VXWJ5WY | LEDSone | **LEDSONE** | £36.89 | **£33.89** | 19 | Active | **NOT A LOSS — we hold it** | Internal reading 3 days stale | Unknown | High — token confirmed | 14:01:04 |
| B083TNFR73 | LEDSone | Amazon | £11.83 live | £15.89 | 0 *(wrong)* | Active | NO | **Amazon retail holds it** despite us being £4.06 cheaper | Unknown | High on observation; Amazon's award logic is not public | 14:01:24 |
| B0855MZ337 | LEDSone | Amazon | — *(no offer visible)* | £7.70 | 0 *(wrong)* | Inactive *(wrong)* | NO | Amazon retail holds it; our offer absent from the listing | Unknown | Medium — 0 offers returned; our offer may exist but not render | 14:01:44 |
| B08CXS3T8T | LEDSone | *(none)* | — | — | 0 | Inactive | NO | **Listing is dead** — "Currently unavailable", no Add-to-basket, 0 offers | Unknown | **High — only case where internal signals are corroborated live** | 14:02:02 |
| B08S45CM19 | LEDSone | **SRM Supplies** | £25.39 | £25.39 | 0 *(wrong)* | Discoverable *(wrong)* | NO | **Lost to our own group company** at an identical price | Unknown | High — all 3 of our accounts on one listing | 14:02:18 |
| B0GLPLNXXC | DCVoltage | **DC Voltage** | £35.89 | £35.89 | 30 | Active | **NOT A LOSS — we hold it** | Internal reading 6 days stale | Unknown | High — token `A3UNAW6KG6QUOJ` | 14:02:38 |
| B0GLYZ41VT | DCVoltage | **DC Voltage** | £59.09 | £59.09 | 4 | Active | **NOT A LOSS — we hold it** | Internal reading 5 days stale | Unknown | High — token confirmed | 14:02:54 |
| B018OUTQ84 | LEDSone | **SRM Supplies** | £7.69 | £5.79 | 39 | Active | NO | **Lost to our own group company**, which is £1.90 cheaper | Unknown | High | 14:03:09 |
| B086385W3W | LEDSone | Amazon | £18.89 | £18.89 | 39 | Active | NO | Amazon retail holds it at an **identical** price | Unknown | High | 14:03:26 |

### Summary of possible reasons across the sample

| Category | Count |
|---|---|
| **Not actually a loss** — we hold the featured offer (stale internal reading) | **4** |
| Amazon retail holds the featured offer | 3 |
| Lost to our own group company (SRM Supplies) | 2 |
| Listing genuinely dead / unavailable | 1 |
| *Attributable to our price being higher* | **1** (B018OUTQ84, and that is against our own group company) |
| *Attributable to our stock or listing status* | **1** (B08CXS3T8T) |

**Not one of the five sample reason labels in the requirement describes the two largest
categories** — stale readings (4) and Amazon retail ownership (3).

---

## 7. Caveat carried forward

Every "we hold it" and "lost to" conclusion above rests on the **featured seller display name**
plus, where available, our own offers' tokens. Because Amazon retail and SRM Supplies expose no
token in the pinned-offer slot, the *holder* is identified by display string in 5 of 10 cases.
The brief warns against name-only identity matching, and that warning still applies to the
holder side. It does **not** affect the 4 "we hold it" findings, where our account's token is
present on the page.
