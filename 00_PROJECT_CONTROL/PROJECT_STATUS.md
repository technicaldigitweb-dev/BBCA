# PROJECT STATUS — BBOX

**As at:** 2026-10-14 · **Developer:** Apirame · **Assigned user:** Tharsika(jaffna)
**Overall: AMBER** — the build is complete and tested; activation is blocked on decisions, not code.

---

## 1. Completed and verified

| Feature | Evidence | Verified |
|---|---|---|
| PH ASIN discovery (20,821 records) | `02_DISCOVERY/DATA_SOURCE_MAPPING.md` | 2026-10-14 |
| Buy Box classification (YES / NO / NOT VERIFIED / CHECK ERROR) | `../02_DISCOVERY/buy_box_source_mapping.md` | 2026-10-14 |
| Price evidence correction (57 contradictions → 0) | `06_EVIDENCE/price_accuracy_validation.md` | 2026-10-14 |
| **Seller identity VERIFIED** | `06_EVIDENCE/seller_identity_verification.md` | 2026-10-14 |
| UK VPN fidelity comparison (7/7 MATCH) | `06_EVIDENCE/uk_vpn_comparison.md` | 2026-10-14 |
| Ten-ASIN live verification (10/10, 0 blocks) | `06_EVIDENCE/phase4_5_ten_asin_verification.md` | 2026-10-14 |
| Dashboard v003 | `08_VALIDATION/TEST_RESULTS.md` — **86/86** | 2026-10-14 |
| Automation engine (3 modes, reliability controls) | `08_VALIDATION/TEST_RESULTS.md` — **69/69** | 2026-10-14 |
| Full daily run, real data | run `20261014T155355-09c0f9`, 20,821/20,821, 0 errors | 2026-10-14 |
| Publisher adapter (dry run) | `06_EVIDENCE/publication/` | 2026-10-14 |
| Scheduler template (inactive) | `automation/scheduler.ps1` | 2026-10-14 |
| Alert engine (dry run) | 0 fired / 20,821 rejected, reason stated | 2026-10-14 |
| Git repository + first commit | `09_GITHUB/GITHUB_PUSH_STATUS.md` | 2026-10-14 |

## 2. Current data position

| Metric | Value |
|---|---|
| Total records | 20,821 |
| Buy Box **YES** | 6,789 (88% of the verified base) |
| Buy Box **NO** | 915 (12%) |
| **NOT VERIFIED** | 13,117 |
| Reason Unknown | 915 — every loss |
| Source latest complete date | 2026-10-11 (2026-10-12 is a partial load) |
| Max staleness at build | 8 days |

## 3. Not done — and why

| Item | State | Blocked by |
|---|---|---|
| **PH Dashboard publication** | **NOT PUBLISHED** — 0 `BBOX` rows in `ph_task`, verified 2026-10-14 | the write was blocked by the environment's production-write guard; needs the operator to run it |
| Live ownership at scale | not possible | no SP-API Product Pricing access |
| Official Reason | always `Unknown` | the 8 checks are undefined |
| Daily schedule | template only, nothing registered | run time + timezone unapproved |
| Postgres history | SQLite only; migration written, never applied | `history_write_approved` + DBA |
| Alerts | dry run only | no approved priority rule, channel or recipients |
| DE / FR / IT live checking | unexercised | live method proven on UK only |

## 4. Open risks

| # | Risk | Severity |
|---|---|---|
| 1 | **Duplicate of `bbsa`** — an existing live daily Buy Box automation by Abiraj (v37, same source, same accounts) | **HIGH** — may make this project redundant |
| 2 | 13,117 records (63%) can never be answered from the available source | HIGH |
| 3 | Historical readings disagree with live reality — 3 of 10 sampled "NO" rows were actually ours | MEDIUM |
| 4 | SRM Suppliers' seller token unconfirmed; losses to that group company identified by display name only | MEDIUM |
| 5 | History is local SQLite — does not survive a machine rebuild, not shared | MEDIUM |
| 6 | `04_DATA/ph_spine.json` is staged manually via the read-only MCP route; a stale spine silently ages the whole run | MEDIUM — mitigated by the freshness gate in `run.py` |

## 5. Ownership

| Role | Who |
|---|---|
| Developer | Apirame |
| Assigned user / reviewer | Tharsika(jaffna) (`ph_priors`) |
| Owner of the overlapping `bbsa` project | Abiraj |
| Decisions needed from | business owner (reason rules, priority, alerts, schedule) |

## 6. Next action

**Settle the `bbsa` duplication question before building or publishing anything further.**
See `02_DISCOVERY/BBSA_DUPLICATE_RISK.md`. The options are extend `bbsa` to DE/FR/IT,
keep this project separate for a different audience, or stop it.

Everything else here is ready and waiting on that answer.
