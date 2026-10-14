# Buy Box Check Automation — BBOX

Daily Buy Box monitoring for the PH Dashboard Amazon estate.

| | |
|---|---|
| **Project code** | `BBOX` |
| **Developer** | Apirame |
| **Assigned user** | Tharsika(jaffna) — `ph_priors` |
| **Repository** | https://github.com/technicaldigitweb-dev/BBCA.git |
| **Status** | **AMBER** — built and tested; not activated, not published |
| **Tests** | **155/155** (69 automation + 86 dashboard), rerun 2026-10-14 |

> **New here? Read [`00_PROJECT_CONTROL/START_HERE.md`](00_PROJECT_CONTROL/START_HERE.md) first.**

---

## What it does

For each of **20,821** Amazon ASIN × account × marketplace records (LEDSone + DCVoltage
across UK/DE/FR/IT), it determines whether we hold the Buy Box and, for verified losses,
gathers the available evidence.

| Result | Count |
|---|---|
| Buy Box **YES** | 6,789 |
| Buy Box **NO** | 915 |
| **NOT VERIFIED** | 13,117 |

## Three things to know before changing anything

1. **The data is historical, not live.** The only Buy Box source is `buy_box_percentage`
   from Amazon's Sales & Traffic report, ~2 days behind. Never present it as current
   ownership.
2. **63% of records cannot be answered.** That report emits no row for an ASIN without
   traffic that day. `NOT VERIFIED` is correct, not a bug.
3. **The "8 reason checks" do not exist** in the requirement, the skill packs or the
   databases. Every loss carries `Official Reason = Unknown`. **Do not invent them.**

## Quick start

```bash
cd automation
python run.py --preflight      # environment + all approval gates - changes nothing
python run.py                  # full daily check (~5s)
python test_automation.py      # 69 tests
```

Dashboard: `05_OUTPUT/2026-10-14_tharsi_buy_box_monitor_v003.html` — opens offline, no
server, no external assets.

## Layout

| Folder | Contents |
|---|---|
| [`00_PROJECT_CONTROL`](00_PROJECT_CONTROL/) | start-here, scope, status, generated asset register |
| [`01_REQUIREMENT`](01_REQUIREMENT/) | requirement register, business rules, open questions |
| [`02_DISCOVERY`](02_DISCOVERY/) | data sources, existing assets, **duplicate risk**, push mapping |
| `02_REFERENCE` | requirement sample screen |
| `03_SCRIPTS` | analysis, extraction, dashboard build and test scripts |
| `04_DATA` | extracted datasets |
| `05_OUTPUT` | dashboard v001 – v003 |
| `06_EVIDENCE` | discovery, validation, live checks, screenshots |
| [`07_AUTOMATION`](07_AUTOMATION/) | **index** into `automation/` — the code is not duplicated |
| [`08_VALIDATION`](08_VALIDATION/) | test results, checklist, pass/fail |
| [`09_GITHUB`](09_GITHUB/) | commit and push evidence |
| [`10_HANDOVER`](10_HANDOVER/) | handover, remaining work, unknown-developer check |
| [`11_DAILY_STATUS`](11_DAILY_STATUS/) | daily status notes |
| [`12_PROMPTS`](12_PROMPTS/) | prompt register |
| [`automation`](automation/) | **the engine** — config, sources, engine, history, alerts, publisher, api, run |

## Read this before building more

[`02_DISCOVERY/BBSA_DUPLICATE_RISK.md`](02_DISCOVERY/BBSA_DUPLICATE_RISK.md)

An existing live daily Buy Box automation (`bbsa`, by Abiraj, version 37) already covers
the same source and accounts for the UK. This project's defensible addition is DE/FR/IT.
**That question should be settled before more is built here.**

## Safety

Nothing here is active. Seven gates default closed; `run.py --preflight` prints them all.

* no production table written — anywhere
* **never published** — 0 `BBOX` rows in `ph_task`
* no scheduled task registered
* no alert transmitted
* `bbsa` never modified
* no credentials committed — `automation/config.local.json` is git-ignored
