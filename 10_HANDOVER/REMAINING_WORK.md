# REMAINING WORK — BBOX

Priority order. Items 1–3 are decisions; 4–8 follow from them.

---

## 1. Settle the `bbsa` duplication — **BLOCKING EVERYTHING**

| | |
|---|---|
| Owner | PH automation owner + **Abiraj** |
| Evidence | `02_DISCOVERY/BBSA_DUPLICATE_RISK.md` |
| Options | **A** extend `bbsa` to DE/FR/IT (recommended) · **B** keep BBOX separate · **C** stop BBOX |
| Effort | one conversation |

Until this is answered, publishing BBOX puts a second Buy Box dashboard in front of the
same team from the same data. No option wastes the work — the verified tokens, price
correction and live-check method transfer to `bbsa` under any outcome.

## 2. Define the 8 reason checks

| | |
|---|---|
| Owner | business owner |
| Evidence | `06_EVIDENCE/reason_rule_approval_request.md` — 8 rules proposed, all marked NOT APPROVED |
| Effort | review + sign-off |

Until signed, `Official Reason = Unknown` on all 915 losses. **Do not invent them** —
live evidence shows the five sample labels would be wrong (we lost while £4.06 cheaper;
internal stock/status was wrong on 3 of 10 sampled ASINs).

## 3. Approve SP-API Product Pricing access

| | |
|---|---|
| Owner | Amazon account owner |
| Evidence | `06_EVIDENCE/bulk_automation_readiness_v2.md` |
| Effort | enable the Product Pricing role on the existing SP-API app for sub_source 6 and 8 |

The single highest-value unblock. `getItemOffers` returns featured-offer seller ID, price
and Prime eligibility in one call — it closes the bulk blocker, the Amazon/SRM identity
gap, and makes six of the eight proposed rules executable.

## 4. Publish to the PH Dashboard

| | |
|---|---|
| State | **NOT PUBLISHED** — 0 `BBOX` rows, verified 2026-10-14 |
| Blocked by | item 1, plus the environment's production-write guard |
| Ready | publisher built, preflight green, payload verified (3,104,415 bytes, md5 `12f76233b995`) |

Command: `python -c "import publisher; from history import History; h=History(); r=h.last_successful_run(); h.close(); publisher.publish(r['run_id'], dry_run=False)"` from `automation/`.

## 5. Approve and register the daily schedule

| | |
|---|---|
| Owner | operations |
| Needs | run time + timezone + machine |
| Constraint | **must start after `overall_asin_daily` completes** (cron 07:35 Asia/Colombo; completion varies) |
| Ready | `automation/scheduler.ps1 -RunTime "HH:mm" -Confirm` |

## 6. Automate the PH spine refresh — **the largest autonomy gap**

`04_DATA/ph_spine.json` is staged manually through the read-only MCP route; a scheduled
task cannot do this. Options: obtain a direct read-only DSN for `ph_dashboard`, or have
the app export the spine on a schedule. Until then the daily run depends on a human step,
and the freshness gate will refuse a stale spine.

## 7. Durable history

Migration written (`automation/migrations/001_buy_box_history.sql`, `STATUS: NOT APPLIED`).
Needs a placement decision and write permission. Today history is local SQLite and does
not survive a machine rebuild.

## 8. Alerts

Needs a high-priority definition (candidate: `analytics_asinsegmentasin.priority`), a
channel and recipients. **No alert delivery infrastructure exists anywhere in the estate**
— that has to be built or chosen, not just configured.

---

## Smaller items

| Item | Note |
|---|---|
| Confirm SRM Suppliers' seller token | group-company losses are name-matched only |
| Decide whether `04_DATA` (83 MB) belongs in Git | tracked today, grows each run |
| Exercise the live method on DE/FR/IT | proven on UK only |
| Commit and push the reorganisation | plan in `09_GITHUB/GITHUB_PUSH_STATUS.md` |

## Explicitly NOT remaining work

* rebuilding the dashboard — v003 passes 86/86 and reproduces the engine's totals exactly
* re-verifying seller identity — VERIFIED against SP-API responses
* refreshing Buy Box data — all 915 already carry the newest reading the source holds
* a UK VPN for fidelity — 7/7 fields matched without one
