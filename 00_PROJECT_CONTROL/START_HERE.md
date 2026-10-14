# START HERE — Buy Box Check Automation (BBOX)

**If you have never seen this project before, read this page first. It should take five minutes.**

| | |
|---|---|
| **Project** | Buy Box Check Automation – Tharsi |
| **Project code** | `BBOX` |
| **Developer** | Apirame |
| **Assigned user** | Tharsika(jaffna) — `ph_priors` |
| **Parent system** | PH Dashboard (Amazon estate) |
| **Repository** | https://github.com/technicaldigitweb-dev/BBCA.git (branch `main`) |
| **Status** | AMBER — built and tested, **not activated, not published** |
| **Last verified** | 2026-10-14 |

---

## 1. What this project does

For every Amazon ASIN on the PH Dashboard, it answers: **do we hold the Buy Box?**
And when we do not, it gathers whatever evidence exists about why.

Scope: **20,821** records at the grain `ASIN × seller account × marketplace`
(LEDSone + DCVoltage, across UK / DE / FR / IT).

## 2. The three things you must understand before changing anything

**a) Most answers are historical, not live.**
The only Buy Box source in the estate is `buy_box_percentage` from Amazon's Sales &
Traffic report — a daily figure that runs ~2 days behind. A live check needs SP-API,
which this project does not have. Never present a historical reading as current
ownership.

**b) 13,117 of 20,821 records cannot be answered at all.**
That report only emits a row for an ASIN that had traffic that day. Those records are
`NOT VERIFIED` — never counted as YES or NO. That is correct behaviour, not a bug.

**c) The "8 reason checks" do not exist.**
The requirement document refers to "checks 1 to 8" but never defines them, and they are
not in any skill pack or database. Every verified loss therefore carries
`Official Reason = Unknown`. **Do not invent them.** A proposal awaiting sign-off is at
`06_EVIDENCE/reason_rule_approval_request.md`.

## 3. Run it

```bash
cd automation
python run.py --preflight      # environment + all six approval gates - changes nothing
python run.py                  # full daily check (~5s, 20,821 records)
python test_automation.py      # 69 tests
```

`--preflight` is the fastest way to see the true state of the project.

## 4. Where things are

| Need | Go to |
|---|---|
| Current status, blockers, next action | `00_PROJECT_CONTROL/PROJECT_STATUS.md` |
| Every significant file and what it is | `00_PROJECT_CONTROL/ASSET_REGISTER.md` |
| What was asked for, and whether it is done | `01_REQUIREMENT/REQUIREMENT_REGISTER.md` |
| Where the data comes from | `02_DISCOVERY/DATA_SOURCE_MAPPING.md` |
| **Why this project may be a duplicate** | `02_DISCOVERY/BBSA_DUPLICATE_RISK.md` |
| The automation engine | `automation/README.md` |
| Test results | `08_VALIDATION/TEST_RESULTS.md` |
| Full handover | `10_HANDOVER/HANDOVER.md` |

## 5. Read this before you do any more work

`02_DISCOVERY/BBSA_DUPLICATE_RISK.md`.

There is an **existing, live, daily Buy Box automation** in the estate — project `bbsa`,
"Amazon Buy Box / Suppression Alerts (UK)", developed by **Abiraj**, at version 37,
using the same data source and the same accounts. This project substantially overlaps it.

That question should be settled before more is built here.

## 6. What is deliberately switched off

Six approval gates, all closed. Nothing publishes, schedules or alerts without a named
decision:

`live_ownership_source_approved` · `reason_rules_approved` · `daily_schedule_approved` ·
`history_write_approved` · `priority_rule_approved` · `alert_delivery_approved`

Plus `publish_approved`, which is set locally in `automation/config.local.json`
(not in Git). **The dashboard has never been published to `ph_task`** — verified
2026-10-14, zero `BBOX` rows exist.
