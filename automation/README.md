# Buy Box Check Automation — Operations & Handover

**Status: built and tested, NOT activated.** Nothing is scheduled, no production table is
written, no alert can be transmitted. Six approval gates hold it that way, and each one
fails loudly rather than guessing.

```
python run.py --preflight      # environment + every gate, in one screen
```

---

## 1. What this is

A daily Buy Box monitoring workflow for the PH Dashboard Amazon estate — 20,821
ASIN × account × marketplace records across LEDSone and DCVoltage in UK/DE/FR/IT.

It reuses the house automation pattern already on this machine (`pythonw.exe` +
`automation/run.py`, Interactive/Limited principal, `IgnoreNew` overlap prevention) so it
looks and behaves like the other 50 scheduled jobs here.

---

## 2. Commands

| Command | Does |
|---|---|
| `python run.py --preflight` | environment, sources, gates, schedule — changes nothing |
| `python run.py` | full daily check (historical source) |
| `python run.py --live` | full check requiring a live source — **refuses**, no SP-API |
| `python run.py --asin B07VFV228J --account LEDSone --marketplace UK` | manual single check |
| `python run.py --manual-full` | on-demand full check |
| `python run.py --resume <run_id>` | resume an interrupted run |
| `python run.py --alerts <run_id>` | alert dry run |
| `python run.py --status` | recent runs + last successful run |
| `python run.py --dry-run` | resolve source and count work, write nothing |
| `python api.py --port 8787` | local backend for the Run Check button |
| `python test_automation.py` | 69-test suite (isolated, synthetic fixtures) |
| `.\scheduler.ps1 -RunTime "HH:mm"` | scheduler **dry run** |
| `.\scheduler.ps1 -RunTime "HH:mm" -Confirm` | register (only after approval) |

The scheduled task calls `run.py` with no arguments, so a manual run and the scheduled
run execute identical code. There is no separate scheduled pipeline.

---

## 3. Sources — and why one is deliberately broken

| Adapter | Gives live ownership? | State |
|---|---|---|
| `historical_report` | **No** — day-level report evidence | available |
| `spapi_product_pricing` | Yes | **unavailable** — credentials live in the app tier |
| `live_browser_cdp` | Yes | available, **capped at 25 records** |

The adapter interface exists so that an unavailable source **says so** instead of being
silently replaced by a weaker one. `sources.resolve(prefer_live=True)` raises rather than
quietly handing back historical data — a live request never degrades into a historical
answer without the operator seeing it.

`live_browser_cdp` refuses batches over 25 records. Amazon serves an automation
interstitial under volume, and bypassing it is out of scope, so the cap is a **refusal,
not a retry**. Bulk live checking needs SP-API.

### Three timestamps, never interchanged

| Field | Meaning |
|---|---|
| `source_observed_at` | when the **source** observed the fact (e.g. report date) |
| `checked_at` | when **this run** executed the check |
| `live_verified_at` | only set when ownership was genuinely verified live |

A historical result never sets `live_verified_at`. This is what stops a stale report
being presented as a live check.

---

## 4. Reliability

| Control | Implementation |
|---|---|
| Batching | `BBOX_BATCH_SIZE`, default 500 |
| Checkpoint / resume | per-run checkpoint after every batch; `--resume <run_id>` |
| Duplicate-run protection | PID-aware lock file; a stale lock from a dead PID is reclaimed |
| Idempotency | results keyed `(run_id, asin, account, marketplace)` — same run_id upserts, new run_id preserves history |
| Bounded retry | 2 retries, 5s backoff — **never** applied to an access-control response |
| Partial recovery | a failed batch is recorded and the run continues |
| Honest status | any skip, failure or CHECK ERROR downgrades the run to `completed_with_errors` |

**A full run is never reported successful while records were skipped or unverified.**

---

## 5. History

Local **SQLite** at `state/buy_box_history.db` — used for all development and testing.

Postgres is a **proposal only**: `migrations/001_buy_box_history.sql`, marked
`STATUS: NOT APPLIED`, with a rollback section. It has not been executed anywhere.
Recommended placement is a `buy_box` schema in `ph_dashboard` (where the ASIN spine and
the existing scheduler/run-log tables already live), but that needs owner approval plus
a write path — this machine currently reaches `ph_dashboard` only through a read-only
MCP tool.

---

## 6. Scheduler

`scheduler.ps1` **will not pick a run hour**. `-RunTime` is mandatory and has no default,
because the hour and timezone are an unapproved business decision. Without `-Confirm` it
only prints what it would register.

**Upstream dependency:** the PH spine is refreshed by `ph_dashboard`'s
`overall_asin_daily` at `35 7 * * *` Asia/Colombo. An approved run time must fall
**after** that, or the run reads yesterday's ASIN list.

House timezone convention is `Asia/Colombo` (from `scheduler_scheduledtask`).

---

## 7. Run Check button

The dashboard stays a standalone offline file. `api.py` is an optional local backend it
can call.

| Endpoint | Purpose |
|---|---|
| `GET /api/buy-box/health` | sources, gates, schedule, last successful run |
| `POST /api/buy-box/check` | one ASIN |
| `POST /api/buy-box/check-all` | background full run |
| `GET /api/buy-box/runs/<run_id>` | run status + progress |
| `GET /api/buy-box/results/latest` | newest result per grain |
| `GET /api/buy-box/history` | per-ASIN history |
| `GET /api/buy-box/daily` | daily rollup |

Binds to `127.0.0.1` by default — an operator tool, not a public service. **No database
credential or API secret is ever sent to the browser.** If the backend is absent the
button must say live execution is unavailable rather than pretend.

---

## 8. Alerts

All five conditions must hold before anything is generated:

1. ASIN is high-priority under an **approved** rule
2. current ownership is **verified live** as NO
3. a previous reliable check established we **held** it (a real transition)
4. not a duplicate
5. approved channel and recipients configured

Condition 2 is the one that matters. **A stale historical 0% reading is explicitly not a
loss event** — the ten-ASIN sample found 3 of 10 such readings where we actually still
held the Buy Box, so alerting on them would have produced false alarms.

There is **no delivery transport implemented**. With `dry_run=False` and no approved
channel the engine downgrades to dry run and says why; if a channel were set it would
raise rather than invent a transport.

**High-priority source is not approved.** Candidate:
`ph_dashboard.analytics_asinsegmentasin.priority` (values: Scale, Fix Now, Quick Win,
Growth Play, Maintain Selectively, Kill / Review). Proposed subset `['Scale','Fix Now']`
— a proposal, not a decision. Until approved, **no ASIN is high-priority** and zero
alerts fire.

---

## 9. Approval gates

Set in `config.local.json` (not version controlled, no secrets):

```json
{ "gates": { "daily_schedule_approved": true },
  "alert_channel": "email",
  "alert_recipients": ["someone@example.com"],
  "priority_asins": ["B0...", "B0..."] }
```

| Gate | Blocks | Needs |
|---|---|---|
| `live_ownership_source_approved` | live checking at scale | SP-API Product Pricing access for sub_source 6 and 8 |
| `reason_rules_approved` | any Official Reason | the 8 ordered checks (`06_EVIDENCE/reason_rule_approval_request.md`) |
| `daily_schedule_approved` | scheduling | run time + timezone + machine |
| `history_write_approved` | Postgres history | DBA action + placement decision |
| `priority_rule_approved` | all alerts | definition of "high-priority ASIN" |
| `alert_delivery_approved` | alert transmission | channel + recipients |

---

## 10. Verified behaviour

| | |
|---|---|
| Test suite | **69/69 passing** (`python test_automation.py`) |
| Real full run | 20,821 records in ~5s, `completed`, 0 failed, 0 skipped |
| Cross-check | engine totals **6,789 YES / 915 NO / 13,117 NOT VERIFIED** — identical to the dashboard, via an independent code path |
| Backend | all endpoints exercised; validation and 404s correct |
| Scheduler | refuses without `-RunTime`; dry run registers nothing (confirmed) |
| Alerts | 0 fired, 20,821 rejected, reason stated explicitly |

Synthetic test records use a `TEST-` prefix and a temporary SQLite file. A test asserts
no `TEST-` record ever appears in the dashboard.

---

## 11. Known limitations

1. **No live ownership at scale.** Historical readings are up to 7 days old. The sample
   found 3 of 10 "NO" readings where we actually held the Buy Box.
2. **Official Reason is always `Unknown`** — the 8 checks are undefined.
3. **13,117 of 20,821 records are NOT VERIFIED** — the Sales & Traffic report emits no
   row for an ASIN with no traffic that day.
4. **SRM Suppliers' seller token is unconfirmed**, so a loss to that group company is
   identified by display name only.
5. **History is local SQLite.** It does not survive a machine rebuild and is not shared.
6. **The PH spine is a staged file.** `ph_dashboard` has no direct DSN here, so
   `04_DATA/ph_spine.json` must be refreshed via the read-only MCP route before a run
   reflects a new ASIN list.
