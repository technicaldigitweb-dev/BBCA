# DUPLICATE RISK — `bbsa` vs `BBOX`

**Severity: HIGH.** An existing, live, daily Buy Box automation already covers most of
what this project does.

**Discovered:** 2026-10-14, read-only query of `tech_team_outputs.ph_task`
**Status: UNRESOLVED — needs an owner decision before more is built here.**

---

## 1. The existing project

| Field | Value | Source |
|---|---|---|
| Project code | **`bbsa`** | `ph_task.project_code` |
| Name | **BBSA – Amazon Buy Box / Suppression Alerts (UK)** | `ph_task.project_name` |
| **Developer** | **Abiraj** | `ph_task.developer` |
| Assigned user | **Arudchelvi** (`ph_priors`) | `ph_task.assigned_user` |
| `ph_task.id` | 1639 · `task_id` `bbsa-ph-arudchelvi` | |
| Created | 2026-09-15 | `ph_task.created_at` |
| Last run | **2026-10-14 09:21** | `ph_task.updated_at` |
| Version | **37** (≈37 daily releases) | `ph_task.version_level` |
| Status | `released` | `ph_task.version_status` |
| Size | 388,568 bytes | |

Today's headline: *"Buy Box & Suppression Alerts – 11 Oct 2026: 11 alerts · 9 sales
stopped · 162 not ours"*

Abiraj also owns four sibling Amazon PH automations — `asew`, `asr`, `pca`, `psro` —
34 `ph_task` rows in total, all `ph_priors`, all updated the same morning. This is an
established, maintained family, not an abandoned experiment.

## 2. Overlap — what is genuinely the same

Read directly from the published BBSA dashboard text:

| Dimension | BBSA | BBOX (this project) | Same? |
|---|---|---|---|
| Buy Box source | *"Amazon's report, ~2 days behind"* | `buy_box_percentage`, same report, same lag | **identical** |
| Accounts | filters on sub_source **8, 6, 9** | 8, 6 (not 9) | BBSA **broader** |
| Scale | **19,371** products checked | 20,821 records | comparable |
| Loss detection | *"had the Buy Box last week and have lost it now"* | transition model in `alerts.py` | **same model** |
| Thin evidence | "Watch" tab — dips seen by 1–9 visitors | NOT VERIFIED / partial band | **same idea** |
| Amazon-retail attribution | *"Amazon Retail selling stock it bought from us (Vendor) cheaper"* — 158 of 162 | our live sample found the same dominant pattern | **same conclusion** |
| Suppression | "Suppressed candidates" tab (181) | `Discoverable (not buyable)` / `Inactive` | similar |
| UK postcode requirement | *"Set a UK postcode before you check a product live"* | same finding, `06_EVIDENCE/uk_vpn_comparison.md` | **same finding** |

BBSA reached several of our conclusions independently, a month earlier.

## 3. Where this project genuinely differs

| | BBSA | BBOX |
|---|---|---|
| **Marketplaces** | **UK only** | **UK + DE + FR + IT** |
| Seller tokens | not evident in the output | **VERIFIED** `A1BXMEJKH8MYIL` / `A3UNAW6KG6QUOJ` |
| Ownership states | Alerts / Watch / Held-by-another | explicit 4-state YES / NO / NOT VERIFIED / CHECK ERROR |
| Reason handling | its own operational taxonomy | `Official Reason` held at `Unknown` with a separate evidence-backed `Possible Reason` |
| Live page check | advises the user to check manually | automated CDP check, proven 10/10 |
| Price evidence | not evident | FBA featured-offer comparison, 428 defensible |

**The defensible differentiator is marketplace coverage.** DE/FR/IT is roughly 46% of
the ASIN estate and BBSA does not cover it.

## 4. Why this matters

Publishing BBOX to `ph_priors` puts a **second** Buy Box dashboard in front of the same
team, built from the same source, by a different developer, with different vocabulary
and different numbers for the same underlying facts. That is precisely the
"duplicate truth" the Mini-AIOS guide warns against:

> *No duplicate truth. Always check existing assets first. Always avoid duplication.*

## 5. Options

| # | Option | Effort | Consequence |
|---|---|---|---|
| **A** | **Extend `bbsa` to DE/FR/IT**, folding in verified tokens and the 4-state model | medium — needs Abiraj | one dashboard, one job, no duplicate truth. **Recommended.** |
| B | Keep BBOX separate for a genuinely different audience/scope | low | two Buy Box dashboards coexist; must be an explicit, communicated decision |
| C | Stop BBOX; contribute its findings to BBSA | low | work is not wasted — tokens, price correction and live method transfer |

## 6. What has NOT been done

* **No `bbsa` row has been read beyond public `ph_task` metadata and its rendered HTML.**
* **No `bbsa` row has been modified.** Verified: BBOX's publisher fingerprints all
  non-BBOX rows and rolls back on any drift.
* **BBOX has never been published** — 0 rows with `project_code = 'BBOX'`, verified
  2026-10-14.

## 7. Required decision

Whoever owns the PH automation roadmap, with **Abiraj**, should pick A, B or C.

Until then this project is complete and parked. Nothing it has built is lost under any
option — the seller-token verification, the price correction and the live-check method
are all reusable by BBSA.
