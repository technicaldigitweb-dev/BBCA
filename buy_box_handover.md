# Buy Box Check Automation — Handover

**Project:** Buy Box Check Automation – Tharsi · **System:** PH Dashboard
**Built:** 2026-10-14 · **Version:** v001 · **Status:** AMBER

---

## 1. Deliverable

**Open this file:**

```
C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\05_OUTPUT\2026-10-14_tharsi_buy_box_monitor_v001.html
```

Double-click it. It opens in Chrome or Edge with no server, no internet and no database
connection. 20,821 records are embedded.

---

## 2. Folder layout

```
Buy_Box_Check_Automation_Tharsi\
├─ buy_box_data_discovery.md      what exists in the databases, and what does not
├─ buy_box_source_mapping.md      field-by-field source-to-dashboard mapping
├─ buy_box_validation_report.md   42/42 test results, limitations, safety
├─ buy_box_handover.md            this file
├─ 02_REFERENCE\sample_dashboard.png   the design from Section 6 of the DOCX
├─ 03_SCRIPTS\                    all generators (see §5)
├─ 04_DATA\                       extracted + built JSON datasets
└─ 05_OUTPUT\                     the dashboard HTML
```

---

## 3. How to read the dashboard

The numbers only make sense if you read the three Buy Box states correctly:

| Pill | Meaning | Count |
|---|---|---|
| **YES** (green) | Amazon recorded our offer as the featured offer for **100%** of page views that day | 6,789 |
| **NO** (red) | Amazon recorded **0%** — we definitely did not hold it | 915 |
| **NOT VERIFIED** (grey) | Ownership is **not known**: either no report row exists, or ownership was split during the day | 13,117 |

**The 88% Buy Box Won figure is 88% of the 7,704 verified records — not of all 20,821.**
The notice bar above the table states this on screen.

NOT VERIFIED is never counted as a win or a loss. 13,117 rows sit there because the Amazon
Sales & Traffic report only produces a row for an ASIN on a day it actually received traffic —
a low-traffic ASIN simply has no Buy Box reading. This is a source limitation, not a bug.

**Click any row** to open the detail panel: it shows the exact ownership evidence, the previous
reading and whether the status changed, warehouse vs listing stock, and a link to the live
Amazon page for manual confirmation.

---

## 4. What is blocked, and what unblocks it

### 4.1 Reason is always "Unknown" — needs a business decision

The requirement says (¶29): *"Run checks 1 to 8 from Section 5 in order."*
**That list of 8 checks does not exist.** Section 5 contains the instruction, not the checks.
They are not in the DOCX, not in either skill pack, and not in the database. The document's own
closing section confirms it is unresolved: *"Is any reason missing from?"*

Because inventing them was explicitly forbidden, all 915 losses carry `Reason = Unknown`.

**What we need from the team:** the 8 checks written out, in priority order, each with the
field it tests and its threshold.

**Important caveat before that work starts:** of the 915 confirmed losses, **705 (77%) have an
Active listing with stock and no price comparison available**. Stock- and status-based checks
would leave most of them unexplained. Where we *can* compare price (127 losses), only 19 are
priced above the featured offer and 74 are priced *below* — so price is demonstrably not the
cause in most of those either. See 4.2.

### 4.2 No competitor or seller-metric data exists — needs an integration

| Sample reason | Data needed | In the database? |
|---|---|---|
| Price higher | competitor / featured-offer price per ASIN | **Partly** — FBA Excess Inventory report covers 127 of the 915 losses (19 priced above) |
| Listing suppressed | a `Suppressed` status | **No** — the value does not exist |
| Low seller score | Amazon account health | **No** — only eBay ratings exist |
| Not Prime eligible | Prime eligibility flag | **No** |
| Out of stock | our quantity | Yes — but quantity alone does not prove *why* the Buy Box was lost |

**What unblocks it:** an Amazon SP-API **Product Pricing** integration
(`getItemOffers` / `getCompetitivePricing`). That single integration would deliver the Buy Box
winner's identity, the competing price, and Prime eligibility — turning the ownership check into
a live check and making genuine reason analysis possible for the first time.

### 4.3 Items awaiting approval

| Item | Current handling | Decision needed |
|---|---|---|
| Partial Buy Box (0 < % < 100) — 156 rows | held at NOT VERIFIED | Approve a threshold (e.g. "≥ 90% = YES")? 8 rows are ≥ 90%, 148 below |
| 7-day lookback window | readings taken from the newest report row within 7 days | Confirm 7 days, or set another figure |
| `DISCOVERABLE` vs "Suppressed" | shown as `Discoverable (not buyable)` | Approve renaming it to "Suppressed", or keep the source wording |
| Daily schedule | not scheduled | Approve, and confirm the run time |
| Alerts | not built | Define "high-priority ASIN" and name the recipients |
| Run history storage | not created | Approve a history table — this needs database **write** access, which was not granted |

### 4.4 Scope note

The project is named for Tharsi. The PH Dashboard contains several similar names
(`Tharsika(jaffna)`, `Tharsiga(nelli)`, `Tharshana`) and none spelled exactly "Tharsi".
The requirement says *"All ASINs in the PH Dashboard are checked"*, so the build covers the
**full Amazon PH list (20,821 rows)**, not one person's. If it should be filtered to one PH
owner, say which name and it is a one-line change — the `ph_name` is already carried on every row.

---

## 5. How to rebuild

Run in order from `03_SCRIPTS\`. All database access is read-only.

| Step | Script | What it does |
|---|---|---|
| 1 | `extract_ledsone.py` | Buy Box evidence + listing status from `ledsone` (direct psycopg, read-only txn) |
| 2 | `extract_history.py` | 14-day daily trend + each ASIN's previous reading |
| 3 | *(MCP query)* | PH spine from `ph_dashboard` — see note below |
| 4 | `build_dataset.py` | joins, classifies, asserts grain uniqueness, writes `dashboard_rows.json` + `summary.json` |
| 5 | `build_html.py` | generates the dashboard HTML |
| 6 | `test_dashboard.py` | 42 functional browser tests — run this before sharing any rebuild |

**Never hand-edit the HTML.** It is generated; edits are lost on the next build.

**Step 3 note:** `ph_dashboard` is not reachable by direct connection from this machine — only
through the `Ledsone_Database_MCP` read-only tool. The spine is pulled with a single
`json_agg(...)::text` query whose result auto-saves to a file, then parsed by `parse_mcp.py`
into `04_DATA\ph_spine.json`. The exact query is recorded in `buy_box_source_mapping.md` §1.

**Credentials:** read from the `WLP_SOURCE_DB_URL` environment variable inside the scripts.
They are never printed, logged, or embedded in the HTML.

---

## 6. Version

`v001` is the first build. Do not overwrite it — the filename carries the date and version,
so the next build should be `v002` (and `build_html.py`'s `OUT` path updated accordingly).

Nothing was committed, pushed, deployed, scheduled, or published, and no production database
was modified. The `ph_task` / Hub registration for this project has **not** been created —
that needs approval and a project code.
