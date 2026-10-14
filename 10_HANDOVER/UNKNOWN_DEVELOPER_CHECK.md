# UNKNOWN DEVELOPER CHECK — BBOX

The Mini-AIOS guide (Prompt 8, Unknown Developer Audit) asks: *assume an unknown
developer starts tomorrow — can they safely continue, understanding objective, status,
assets, evidence, next actions and ownership, without meetings or verbal explanation?*

**Verdict: PASS**, with three caveats stated below rather than hidden.

---

## The six audit criteria

| Criterion | Where it is answered | Verdict |
|---|---|---|
| **Objective** | `00_PROJECT_CONTROL/START_HERE.md` §1, `PROJECT_SCOPE.md` | **PASS** |
| **Status** | `PROJECT_STATUS.md` — completed / not done / blocked, with evidence per row | **PASS** |
| **Assets** | `00_PROJECT_CONTROL/ASSET_REGISTER.md` — generated from disk, 109 files, cannot drift | **PASS** |
| **Evidence** | every claim links to a file; `08_VALIDATION/TEST_RESULTS.md` carries reruns, not quoted history | **PASS** |
| **Next actions** | `REMAINING_WORK.md` priority-ordered; single next action in `HANDOVER.md` §12 | **PASS** |
| **Ownership** | developer Apirame, assigned Tharsika(jaffna), `bbsa` owner Abiraj — named throughout | **PASS** |

## Can they actually run it?

| Question | Answer |
|---|---|
| How do I see the true state? | `python automation/run.py --preflight` — gates, sources, freshness, one screen |
| How do I run it? | `python automation/run.py` — ~5 s, 20,821 records |
| How do I know it worked? | `python automation/test_automation.py` (69) and `03_SCRIPTS/test_dashboard_v003.py` (86) |
| What will it break? | nothing — every write path is gated and defaults closed |
| What must I not do? | `START_HERE.md` §2 and §6; `07_AUTOMATION/README.md` "Do not" |
| Where is the dashboard? | `05_OUTPUT/2026-10-14_tharsi_buy_box_monitor_v003.html`, opens offline |
| What is dangerous here? | publishing to `ph_task` and registering the scheduler — both blocked by design |

## Traps an unknown developer would otherwise fall into

Each is documented where they would hit it:

1. **`$DATABASE_URL` and `$PGHOST` point at a dead server.** The live ph_task endpoint is
   `178.18.248.100:5435`. — `02_DISCOVERY/PH_DASHBOARD_MAPPING.md` §5
2. **`ph_dashboard` has no direct DSN.** MCP read-only only; the spine is a staged file.
   — `DATA_SOURCE_MAPPING.md` §1
3. **`buy_box_percentage` is historical, never live.** — `BUSINESS_RULES.md` BR-01/02
4. **The 8 reason checks do not exist. Do not invent them.** — `BUSINESS_RULES.md` BR-07
5. **`2026-10-12` is a partial load** — anchoring on `max(date)` silently uses a 6%-loaded day.
   — `DATA_SOURCE_MAPPING.md` §4
6. **Listing status joins on `site`, not `region_id`** (which is only Europe/North America).
   — `DATA_SOURCE_MAPPING.md` §2
7. **A matching seller *name* is not proof of ownership** — a token is required.
   — `BUSINESS_RULES.md` BR-04
8. **An existing project already does most of this.** — `BBSA_DUPLICATE_RISK.md`

## Caveats — honest gaps

**1. The spine refresh is a manual step.** `04_DATA/ph_spine.json` is staged from
`ph_dashboard` through the read-only MCP route, which a scheduled task cannot perform on
its own. A new developer will find the exact query in `../02_DISCOVERY/buy_box_source_mapping.md` §1 and
the freshness gate in `run.py` will refuse a stale spine — but the restaging itself is
not yet automated. **This is the largest single gap to full autonomy.**

**2. Prompt history is partial.** `12_PROMPTS/PROMPT_REGISTER.md` records the prompts
whose source text was available in this session. Earlier prompts were not retained and
have **not** been reconstructed.

**3. The Mini-AIOS guide does not define this folder taxonomy.** The guide supplies
principles and the audit criteria above; the `00_`–`12_` structure came from the task
brief. Noted so nobody searches the guide for a specification that is not in it.

## Closure questions (guide §0.0)

| Question | Answer |
|---|---|
| What reusable asset was created today? | The Mini-AIOS structure, a generated asset register, and the duplicate-risk report |
| What reusable asset was improved today? | Repository hygiene — an open publish gate removed from version control |
| What evidence was created today? | 155/155 rerun results, commit evidence captured by command, publication status verified as zero rows |
| What duplication risk was eliminated today? | `bbsa` overlap documented with evidence and three decision options — **identified, not yet eliminated** |
| What capability was discovered today? | That the estate already runs a daily Buy Box automation, and that `ph_task` is the only available publication route |
| Can an unknown developer continue tomorrow? | **Yes** — from `00_PROJECT_CONTROL/START_HERE.md`, subject to the three caveats above |
