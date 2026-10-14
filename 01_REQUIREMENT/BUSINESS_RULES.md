# BUSINESS RULES — BBOX

Two kinds of rule live here: **approved** rules the code implements, and **undefined**
rules the code deliberately refuses to invent.

---

## 1. APPROVED — implemented

### BR-01 Buy Box classification
| `buy_box_percentage` | Status |
|---|---|
| `= 100` | **YES** |
| `= 0` | **NO** |
| `0 < pct < 100` | **NOT VERIFIED** (156 rows) |
| no report row in the window | **NOT VERIFIED** (12,961 rows) |

Derived from the source's own semantics: the share of page views where our offer was
the featured offer. 100% and 0% are unambiguous; anything between is not.

### BR-02 Never convert absence into a verdict
Missing or unavailable Buy Box data is **never** YES or NO. A technical failure is
`CHECK ERROR`, not `NO`.

### BR-03 Listing status aggregation
An ASIN may carry several of our offers (2,079 groups have mixed statuses):
`any Active or BUYABLE -> Active`, else `DISCOVERABLE -> Discoverable (not buyable)`,
else `Incomplete`, else `Inactive`, else `Not Found`. One buyable offer makes the ASIN
sellable, so the most-available status wins.

### BR-04 Ownership requires a verified token
Live ownership is asserted as ours only when a **verified** seller token is present on
the page. A matching seller *name* alone yields `NOT VERIFIED`.

### BR-05 Price comparison must be like-for-like
A comparison is emitted only when both prices come from the same source row, on the Buy
Box reading date, same currency, both `> 0`, and unambiguous. Otherwise suppressed with
a stated reason. (Fixed 57 contradictions to 0.)

### BR-06 Alert trigger
All five must hold: approved high-priority ASIN · ownership **verified live** as NO ·
a previous reliable check showed we held it · not a duplicate · approved channel and
recipients. **A stale historical 0% is explicitly not a loss event.**

---

## 2. UNDEFINED — deliberately not implemented

### BR-07 The eight reason checks — PENDING
The requirement says *"Run checks 1 to 8 from Section 5 in order."*
**Section 5 contains that instruction, not the checks.** Exhaustive search found no such
list in the requirement document, either skill pack, or either database.

Consequence: `Official Reason = Unknown` on all 915 losses.
Proposal awaiting sign-off: `06_EVIDENCE/reason_rule_approval_request.md`.

**Do not invent these.** Live evidence shows the five sample labels would be wrong:
on `B083TNFR73` our offer was **£4.06 cheaper** and we still lost; internal stock and
listing status were wrong on 3 of 10 sampled ASINs.

### BR-08 Partial Buy Box threshold — PENDING
156 rows sit at `0 < pct < 100`. Collapsing them needs an approved cut-off
(8 are ≥ 90%, 148 below). Held at NOT VERIFIED.

### BR-09 "Suppressed" — PENDING
The requirement expects Active / Inactive / **Suppressed**. **No `Suppressed` value
exists in the source.** `DISCOVERABLE` is the nearest concept and is shown under its own
derived label rather than renamed.

### BR-10 High-priority ASIN — PENDING
Candidate: `ph_dashboard.analytics_asinsegmentasin.priority`
(values: Scale, Fix Now, Quick Win, Growth Play, Maintain Selectively, Kill / Review).
Proposed subset `['Scale','Fix Now']` is a **proposal, not a decision**.
Until approved, **no ASIN is high-priority** and zero alerts fire.

### BR-11 Report window — ASSUMPTION
Newest report row within **7 days**. A reporting-lag allowance, not a business rule.
Measured: 7d covers 37.8%, 30d 57.5%, 90d 73.1%. Widening would make `Last Checked`
badly stale without fixing coverage.
