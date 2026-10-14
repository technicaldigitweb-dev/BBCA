# Phase 4 — Buy Box Loss Reason Investigation

**Built:** 2026-10-14 · `03_SCRIPTS/build_reason_investigation.py`
**Scope:** all 915 Buy Box NO records. **Official reason: Unknown for all 915.**

## The undefined checklist — not invented

The source requirement (`Buy_Box_Automation_Tharsi (1).docx` ¶29) cites "checks 1 to 8
from Section 5". **That list does not exist** — not in the DOCX, not in either skill
pack, not in the database. It was re-confirmed during this phase, not assumed.

Consequences, applied strictly:

- `official_reason` is `"Unknown"` for every one of the 915 records.
- No first-match priority is applied. Where several hypotheses hold at once, **all**
  are kept visible, because the ordering that would choose between them is precisely
  what is missing.
- The five labels in the DOCX are captioned "only examples" there and are **not**
  implemented as rules.

## Structure held per record

| Field | Content |
|---|---|
| `official_reason` | `Unknown` — always, pending an approved checklist |
| `possible_reason` | list of evidence-backed hypotheses, or `Not Determined` |
| `reason_evidence` | the specific observations, with values and dates |
| `reason_confidence` | qualitative statement of evidential support — **no invented probabilities** |
| `reason_source` | the actual tables the evidence came from |
| `reason_evidence_gaps` | dimensions with no available source, named explicitly |
| `reason_checked_at` | real timestamp |

## Results across the 915 NO records

| Possible reason (hypothesis) | Records |
|---|---|
| **Not Determined** | **801** |
| No sellable stock on the listing | 66 |
| Listing inactive | 55 |
| Listing discoverable but not buyable | 35 |
| Price higher than the featured offer | 18 |

60 records carry **more than one** hypothesis and retain all of them.

The hypotheses total more than 915−801 because of that overlap. 801 of 915 (87.5%)
have **no** evidence pointing anywhere: the listing is Active, has stock, and either
has no price comparison or one showing we were not priced above. The loss is real —
Buy Box 0% of page views — but nothing in the available data explains it. That figure
is the honest headline of this phase, not a gap to be papered over.

Only **18** of 915 losses (2.0%) have defensible evidence that we were priced above
the featured offer — down from a previously implied 19 computed on contradictory
inputs, and now each verified against its own source row (Phase 1).

## Evidence gaps recorded on every record

| Dimension | Why no evidence exists |
|---|---|
| Seller account matching | No Amazon merchant token exists internally or on the page; our account cannot be matched to the featured offer by identifier |
| Fulfilment / Prime eligibility | No Prime or fulfilment flag in any authorized source |
| Competing seller offers | Requires a live listing read; Amazon automated access is currently blocked |
| Other eligibility issues | No account-health or listing-eligibility source available |

These are carried as explicit gaps rather than silently treated as "no problem found".

## Worked examples

**A — price evidence present** (`B07VXWJ5WY`, LEDSone, UK)
Evidence: our offer 33.89 vs featured 33.89 on 2026-10-11 (SKU `CRSF100BM2PK+…_AML`);
Buy Box 0% on 2026-10-11.
Possible reason: *price does not explain this loss* — we were not priced above.
Official reason: **Unknown**.

**B — several hypotheses at once** (zero stock on an inactive listing)
Evidence: listing quantity 0; listing status Inactive; Buy Box 0%.
Possible reasons: *No sellable stock on the listing*, *Listing inactive* — both kept.
Confidence: "2 hypotheses are simultaneously supported; the approved priority order
that would choose between them is undefined, so none is selected."
Official reason: **Unknown**.

**C — no usable evidence** (the 801-record majority)
Evidence: Active listing, stock present, price comparison unavailable, Buy Box 0%.
Possible reason: *Not Determined*.
Official reason: **Unknown**.

## Acceptance

| Criterion | Status |
|---|---|
| Every investigated NO result has evidence or an explicit evidence gap | **MET** — verified programmatically across all 915 |
| No unsupported reason assignments | **MET** — `official_reason` is `Unknown` for all 915 |
| Multiple candidate reasons remain visible where relevant | **MET** — 60 records keep 2+ hypotheses |
| Official Reason remains Unknown when the approved checklist cannot be applied | **MET** |

No hypothesis is stated as a cause. A public product page does not reveal Amazon's
internal decision for awarding the Featured Offer, and nothing here claims otherwise.
