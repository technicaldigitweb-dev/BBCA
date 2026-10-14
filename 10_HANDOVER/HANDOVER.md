# HANDOVER — Buy Box Check Automation (BBOX)

**Date:** 2026-10-14 · **Developer:** Apirame · **Assigned user:** Tharsika(jaffna) (`ph_priors`)
**Repository:** https://github.com/technicaldigitweb-dev/BBCA.git · branch `main`
**Conclusion: PASS for delivery. Project status AMBER — built, tested, not activated.**

---

## 1. Objective

For every Amazon ASIN on the PH Dashboard, determine whether we hold the Buy Box, and
when we do not, gather evidence about why — on a daily schedule, shown on a dashboard,
with history and high-priority alerts.

## 2. Current status

| Area | State |
|---|---|
| Data pipeline | **working** — 20,821 records, grain asserted, two runs agreeing |
| Dashboard v003 | **working** — 86/86 tests, offline, no external assets |
| Automation engine | **working** — 69/69 tests, full run clean in ~5 s |
| Seller identity | **VERIFIED** — `A1BXMEJKH8MYIL` (LEDSone), `A3UNAW6KG6QUOJ` (DCVoltage) |
| Reason determination | **blocked** — the 8 checks are undefined; all 915 losses `Unknown` |
| Live ownership | **blocked** — no SP-API; 63% of records unanswerable |
| PH Dashboard publication | **NOT PUBLISHED** — 0 `BBOX` rows, verified today |
| Daily schedule | **not registered** — run time unapproved |
| Alerts | **dry run only** — no priority rule, channel or recipients |

## 3. Files created or modified today

**Created (reorganisation):** `00_PROJECT_CONTROL/` (START_HERE, PROJECT_SCOPE,
PROJECT_STATUS, ASSET_REGISTER, gen_asset_register.py) · `01_REQUIREMENT/`
(REQUIREMENT_REGISTER, BUSINESS_RULES, OPEN_QUESTIONS) · `02_DISCOVERY/`
(DATA_SOURCE_MAPPING, EXISTING_ASSET_REVIEW, BBSA_DUPLICATE_RISK, PH_DASHBOARD_MAPPING) ·
`07_AUTOMATION/README.md` · `08_VALIDATION/` (TEST_RESULTS, VALIDATION_CHECKLIST,
PASS_FAIL_REPORT) · `09_GITHUB/` (GITHUB_PUSH_STATUS, COMMIT_EVIDENCE) · `10_HANDOVER/`
(this, REMAINING_WORK, UNKNOWN_DEVELOPER_CHECK) · `11_DAILY_STATUS/2026-10-14_STATUS.md` ·
`12_PROMPTS/PROMPT_REGISTER.md` · `automation/config.local.example.json`

**Modified:** `.gitignore` (added `automation/config.local.json`)

**Untracked from Git:** `automation/config.local.json` — it carried an open publish gate.

**No Python file, dashboard or evidence file was moved, renamed or deleted.**

## 4. Evidence locations

| Claim | Evidence |
|---|---|
| Data sources and grain | `02_DISCOVERY/DATA_SOURCE_MAPPING.md`, `../02_DISCOVERY/buy_box_source_mapping.md` |
| Seller identity VERIFIED | `06_EVIDENCE/seller_identity_verification.md` |
| Price correction 57 → 0 | `06_EVIDENCE/price_accuracy_validation.md` |
| UK VPN fidelity 7/7 MATCH | `06_EVIDENCE/uk_vpn_comparison.md` |
| Ten-ASIN live check 10/10 | `06_EVIDENCE/phase4_5_ten_asin_verification.md` |
| No fresher data exists | `06_EVIDENCE/fresh_buy_box_data_validation.md` |
| Reason rules proposal | `06_EVIDENCE/reason_rule_approval_request.md` |
| Bulk automation blocked | `06_EVIDENCE/bulk_automation_readiness_v2.md` |
| Test results (rerun today) | `08_VALIDATION/TEST_RESULTS.md` |
| **Duplicate risk** | `02_DISCOVERY/BBSA_DUPLICATE_RISK.md` |

## 5. GitHub

Commit `531cb38930427e92ca3f92eb7d8dd82fa1b977fd` — *"Initial BBCA project setup -
Apirame"*, 2026-10-14 17:09, pushed (`origin/main` resolves to the same hash).

**The reorganisation above is on disk but not committed.** No hash is claimed for it.
Commit plan: `09_GITHUB/GITHUB_PUSH_STATUS.md`.

## 6. Systems touched

| System | How |
|---|---|
| `ledsone` | **read-only** SELECT (`SET TRANSACTION READ ONLY` on direct sessions) |
| `ph_dashboard` | **read-only** via MCP |
| `order_management_copy` | **read-only** — `ph_task` inspected, never written |
| Amazon UK | ~30 page loads via an operator-opened browser; no CAPTCHA interaction, no bypass |
| Local filesystem | project folder only |
| Git | one commit, already pushed before this session |

## 7. Systems NOT touched

* **No production table written** — anywhere
* **`ph_task` not written** — 0 `BBOX` rows
* **`bbsa` not modified** — not a single row
* **No scheduled task registered**
* **No alert transmitted**
* **No Postgres schema created** — migration written, never applied
* **No credential created, changed or committed**

## 8. Known risks

| # | Risk | Severity |
|---|---|---|
| 1 | **Duplicate of `bbsa`** (Abiraj, v37, same source, same accounts, live daily) | **HIGH** |
| 2 | 63% of records unanswerable from the only available source | HIGH |
| 3 | Historical readings disagree with live reality — 3 of 10 sampled "NO" rows were ours | MEDIUM |
| 4 | SRM Suppliers token unconfirmed | MEDIUM |
| 5 | History is local SQLite — lost on machine rebuild | MEDIUM |
| 6 | `04_DATA` (83 MB) is tracked in Git and grows each run | LOW–MEDIUM |

## 9. Duplicate-risk status

**UNRESOLVED.** `02_DISCOVERY/BBSA_DUPLICATE_RISK.md` sets out three options
(extend `bbsa` / keep separate / stop). The defensible differentiator is marketplace
coverage: `bbsa` is UK-only, BBOX covers UK + DE + FR + IT.

## 10. Validation

155/155 tests passing (69 automation + 86 dashboard), rerun today. All 19 checklist
items PASS. Details: `08_VALIDATION/`.

## 11. Remaining blockers

See `REMAINING_WORK.md`. In priority order: the duplication decision, the 8 reason
rules, SP-API access, then the activation approvals.

## 12. Next action

**Settle the `bbsa` duplication question with Abiraj and the PH automation owner.**
Everything else here is complete and parked behind that answer. No option wastes the
work — the verified seller tokens, the price correction and the live-check method all
transfer to `bbsa` if that is the chosen route.

## 13. Conclusion

**PASS.** The deliverables are built, tested, evidence-backed and safe: nothing is
activated, nothing is published, no production data was modified, and every claim above
is traceable to a file or a command. An unknown developer can continue from
`00_PROJECT_CONTROL/START_HERE.md` without a conversation.
