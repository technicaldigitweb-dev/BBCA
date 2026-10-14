# PH DASHBOARD PUBLICATION MAPPING — BBOX

**Destination: `tech_team_outputs.ph_task` in `order_management_copy`.**
Discovered read-only 2026-10-14. **Nothing has been published** — 0 `BBOX` rows exist.

---

## 1. How local automations reach the PH Dashboard

Confirmed by reading a working example (`eBay_SKU_Gap_Analysis_Sharmilan/automation/`,
project `ESGA`, published today):

```
local run  ->  generate HTML  ->  atomic swap to output/  ->  UPSERT ph_task row per user
```

`ph_task` carries the **entire standalone HTML** in `html_content`, one row per assigned
user. The online PH Dashboard renders it. There is no API and no structured ingestion
endpoint for this kind of operational output.

## 2. The four options considered

| Option | Verdict |
|---|---|
| **A. Existing PH Dashboard API** | **Not found.** No REST/ingestion endpoint for automation output. |
| **B. Approved PostgreSQL ingestion** | **Not available.** `ph_dashboard`'s `analytics_*` tables are populated by the app's own server-side scheduler (`scheduler_scheduledtask`, 15 jobs). This machine has **no write path** to that database — MCP access is read-only. |
| **C. HTML publication via `ph_task`** | **AVAILABLE and established.** Used by ~50 local automations. **Chosen.** |
| **D. Extend an existing dashboard module** | Possible but requires Django model + migration + app deploy — out of scope here, and see the duplicate-risk note below. |

### On the brief's warning about `ph_task`

The brief cautioned against assuming `ph_task` suits *operational monitoring records*.
That caution is correct, and the discovery confirms it:

* `ph_task` columns are `project_code, task_name, assigned_user, html_content, …` —
  **there is no ASIN, status, reason or timestamp column.**
* It is a **delivery registry for a rendered report**, not a record store.

So it is the right destination for **the dashboard**, and the wrong destination for
**structured per-ASIN records**. Structured records stay in the automation's own history
(SQLite now, Postgres proposed in `automation/migrations/001_buy_box_history.sql`), and
`publisher.records_for_export()` can emit them if a structured destination is ever
approved.

## 3. Mapping

| Required field | Carried as |
|---|---|
| ASIN, SKU, Seller Account, Marketplace | inside the HTML table **and** `records_for_export()` |
| Buy Box Status, Official Reason, Possible Reason | same |
| Stock, Listing Status | same |
| Source Observed At, Actual Checked At, Verification Status, Run ID | same |
| — | `ph_task.task_name` carries the headline tally |
| — | `ph_task.version_level` increments per release |

## 4. Row strategy

One stable row per assigned user, UPDATEd daily with `version_level` bumped — the house
daily convention (`dst` is at version 113, `ESGA` at 9). Inserting a fresh row set per
day would add megabytes of HTML daily.

| | |
|---|---|
| `project_code` | `BBOX` |
| `task_id` | `bbox-ph-<user>` |
| `assigned_user` | **Tharsika(jaffna)** (`ph_priors`) — selected by the project owner on 2026-10-14 |
| `developer` | Apirame |

**Recipient note:** no PH user is spelled exactly "Tharsi". Candidates were
`Tharsika(jaffna)`, `Tharsiga(nelli)`, `Tharshana`, `Utharsika`. The owner chose
**Tharsika(jaffna)**. This was a decision, not an inference.

## 5. Connection

| | |
|---|---|
| Host | `178.18.248.100:5435` — **verified reachable** |
| Database | `order_management_copy` |
| `$DATABASE_URL`, `$PGHOST` | point at the **old** server, **time out** |
| Password | from `$BBOX_PUBLISH_PASSWORD` or `$PGPASSWORD` — environment only, never from a file, never logged |

## 6. Safety built into the publisher

1. only a run with `status = 'completed'` and full coverage is publishable
2. all non-`BBOX` rows fingerprinted before and after; **rollback on any drift**
3. destination row count verified before commit
4. idempotent — same `run_id` to the same user is a no-op
5. refuses rather than falling back to a default audience

## 7. Current state

| | |
|---|---|
| Publication | **NOT PUBLISHED** — 0 `BBOX` rows, verified 2026-10-14 |
| Last dry run | run `20261014T155355-09c0f9`, payload 3,104,415 bytes, md5 `12f76233b995` |
| Blocker | the production write was refused by the environment's write guard; it needs the operator to execute it |
| Prerequisite | the `bbsa` duplication question — see `BBSA_DUPLICATE_RISK.md` |
