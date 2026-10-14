# Buy Box Reason Rules — Approval Request

**To:** Business owner (Buy Box Check Automation – Tharsi)
**From:** Automation team · 2026-10-14
**Status of every rule below: NOT APPROVED — PROPOSAL ONLY**

> **Nothing in this document has been implemented.** The `Official Reason` column in the
> dashboard remains `Unknown` on all 915 losses. These rules take effect only if and when you
> approve them, and only after a further build.

---

## 1. Confirmation: the checklist is undefined

`Buy_Box_Automation_Tharsi (1).docx` ¶29 states:

> "Run checks 1 to 8 from Section 5 in order. Stop at the first match and save it as the Reason."

**Section 5 of that document is "Automation Logic (Simple Flow)" — it contains that instruction,
not a list of checks.** An exhaustive search has confirmed no such list exists:

| Searched | Result |
|---|---|
| The requirement DOCX (all paragraphs, tables, embedded image) | no list of 8 checks |
| `skills_minimal_pack 2 (2) 2.zip` | 2 incidental Buy Box mentions, both narrative margin context |
| `skills 3 (1) (3) 1.zip` | same |
| `ledsone` + `ph_dashboard` databases | no reason/rule/check table |

The document's own closing section confirms it was never settled: *"Is any reason missing from?"*

The five labels on the sample dashboard image (Price higher, Out of stock, Listing suppressed,
Low seller score, Not Prime eligible) are captioned by the document itself as
*"Numbers and names are only examples."*

---

## 2. What the live evidence says before you write the rules

Ten UK losses were verified against the live Amazon page on 2026-10-14. The findings should shape
the checklist, because **the five sample labels do not cover what actually occurs**:

| What we actually found | Count (of 10) | Covered by the 5 sample labels? |
|---|---|---|
| Our own account was holding the featured offer — the record was stale | **3** (+1 unconfirmed) | **No** |
| Amazon retail held the featured offer | 3 | **No** |
| Our own group company (SRM Suppliers) held it | 2 | **No** |
| Listing genuinely unavailable | 1 | partly ("Out of stock") |
| Our price higher than the featured offer | **1** — and that was against our own group company | yes |

Three findings worth your attention before deciding:

1. **Price is not the main driver.** On `B083TNFR73` our offer was **£4.06 cheaper** than the
   featured offer and we still did not hold the Buy Box. On `B086385W3W` our price matched
   exactly. A "Price higher" check placed early would mislabel both.
2. **Internal stock and listing status were wrong on 3 of 10.** Rows marked stock 0 / Inactive /
   not-buyable were live, in stock and buyable. Any rule built on those fields would have produced
   confident wrong answers.
3. **We compete against ourselves.** On `B08S45CM19`, LEDSone, DCVoltage *and* SRM Suppliers all
   had offers on one listing, and SRM held the Buy Box.

---

## 3. Proposed checklist — NOT APPROVED

Ordered most-certain first, so an earlier check never masks a better-evidenced one. Each stops on
match.

| # | Proposed rule | Condition | Evidence source | Why this precedence | Status |
|---|---|---|---|---|---|
| 1 | **Ownership not verified** | no live check, or featured seller unreadable | live page | Never guess a reason for a loss we have not confirmed is current | **NOT APPROVED** |
| 2 | **Not actually lost — stale record** | our verified seller token holds the featured offer live | live page + verified seller ID | A stale record is not a loss; must precede every causal check | **NOT APPROVED** |
| 3 | **Listing unavailable** | no featured offer, no Add-to-basket, `#outOfStock` present | live page | Observed directly; the only internal signal corroborated live | **NOT APPROVED** |
| 4 | **Out of stock (our offer)** | our offer absent from the offer list **and** internal stock 0 | live page **+** DB | Needs *both* — internal stock alone was wrong 3 times in 10 | **NOT APPROVED** |
| 5 | **Won by our own group company** | featured seller is SRM Suppliers / LEDSone / DCVoltage (not the measured account) | live page + `order_management.sub_source` | Commercially distinct from losing to a competitor; needs different action | **NOT APPROVED** |
| 6 | **Won by Amazon retail** | featured seller is Amazon | live page | Amazon retail usually cannot be out-competed on price; separating it prevents futile repricing | **NOT APPROVED** |
| 7 | **Our price higher** | our live offer price > featured offer price, same currency, same check | live page (both prices from one page load) | Only after 2–6, since we lost at equal and lower prices too | **NOT APPROVED** |
| 8 | **Won by a third-party seller** | featured seller is none of the above | live page | Residual competitive loss | **NOT APPROVED** |
| — | **Unknown** | nothing above matches | — | Existing fallback | current behaviour |

### Rules deliberately NOT proposed

| Sample label | Why not proposed |
|---|---|
| **Listing suppressed** | No `Suppressed` status exists in `listings.amazon_listings`. `DISCOVERABLE` is the nearest value, and it was **wrong** on the one row we checked live (`B08S45CM19` was live and buyable). |
| **Low seller score** | No Amazon account-health data exists anywhere in the estate. Only `customer_service.ebay_account_ratings` (eBay) exists. |
| **Not Prime eligible** | No Prime eligibility flag exists in the database, and it was not reliably readable from the page. |

Approving any of these three would require a data source that does not currently exist.

---

## 4. Decisions needed from you

| # | Question | Default if you do not decide |
|---|---|---|
| 1 | Approve the eight rules above, in this order? | Official Reason stays `Unknown` |
| 2 | Should "won by our own group company" (#5) be a *reason* at all, or escalated as a separate commercial issue? | treated as a reason |
| 3 | Should rules requiring a live check be allowed, given there is no approved bulk live-check route yet? | rules 1–3, 5–8 cannot run at scale |
| 4 | Partial Buy Box (0 % < x < 100 %) — 156 rows. Approve a threshold, e.g. "≥ 90 % = YES"? | held at NOT VERIFIED |
| 5 | Is a reading up to 7 days old acceptable as "current"? | shown with a staleness warning |

---

## 5. Dependencies before any of this can run in bulk

1. **Seller IDs confirmed** — `A1BXMEJKH8MYIL` (LEDSone) and `A3UNAW6KG6QUOJ` (DCVoltage) are
   PROVISIONAL. Rules 2 and 5 depend on them. One SP-API
   `getMarketplaceParticipations` call, or a Seller Central Merchant Token read, settles it.
2. **An authorised route to current ownership** — six of the eight proposed rules need a live
   featured-offer reading, which today exists only via browser checks that Amazon rate-limits.
   See `bulk_automation_readiness_v2.md`.

---

## 6. Sign-off

| | |
|---|---|
| Approved by | ............................................ |
| Date | ............................................ |
| Rules approved | all / numbers: ..................... |
| Amendments | ............................................ |

Until this is signed, `Official Reason` remains `Unknown` on every record, and the dashboard
continues to show evidence-backed `Possible Reason` values separately and clearly labelled as
not approved.
