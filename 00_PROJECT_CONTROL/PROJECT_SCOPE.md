# PROJECT SCOPE — BBOX

**Source:** `01_REQUIREMENT/Buy_Box_Automation_Tharsi (1).docx`
**Parent system:** PH Dashboard (Amazon estate), via `ph_task` publication

---

## In scope

| Dimension | Scope |
|---|---|
| Platform | **Amazon only** (the requirement's input table states Marketplace = Amazon) |
| Marketplaces | **UK, DE, FR, IT** |
| Accounts | **LEDSone** (`sub_source` 8), **DCVoltage** (`sub_source` 6) |
| Grain | ASIN × seller account × marketplace |
| Volume | **20,821** records |
| Question | Do we hold the Buy Box? If not, what evidence exists about why? |
| Delivery | standalone HTML dashboard, published to the PH Dashboard via `ph_task` |
| Cadence | once daily, plus on demand |

## Out of scope

| Excluded | Why |
|---|---|
| eBay, B&Q, Shopify | the requirement specifies Amazon |
| Amazon US / ES / NL / PL / SE and others | not in the PH Amazon spine |
| SRM Suppliers (`sub_source` 9) as a *monitored* account | not in the PH spine; appears only as a competing seller |
| Repricing or any corrective action | this project reports; it does not act |
| Changing listings, prices or stock | read-only by design |
| Cloud hosting | execution is local Windows, by requirement |

## Scope decisions worth knowing

**"Tharsi" is not a scope filter.** The project is named for the requester. The
requirement says *"All ASINs in the PH Dashboard are checked"*, so the build covers the
full Amazon list, not one person's portfolio. Every row carries `ph_name`, so filtering
to one owner is a one-line change if that was ever intended.

**Delivery recipient is Tharsika(jaffna)** — an owner decision taken 2026-10-14, because
no PH user is spelled exactly "Tharsi". See `02_DISCOVERY/PH_DASHBOARD_MAPPING.md` §4.

**63% of the scope cannot be answered.** 13,117 of 20,821 records are `NOT VERIFIED`
because the only Buy Box source emits no row for an ASIN without traffic that day. This
is a scope limit imposed by the data, not a delivery gap.

## Relationship to the parent AIOS / PH Dashboard

| | |
|---|---|
| Reads from | `ph_dashboard` (ASIN spine, categories) — read-only via MCP |
| Reads from | `ledsone` (Buy Box report, listings, FBA prices) — read-only |
| Writes to | `order_management_copy.tech_team_outputs.ph_task` — **nothing written yet** |
| Depends on | `overall_asin_daily` (PH app scheduler, 07:35 Asia/Colombo) |
| **Overlaps with** | **`bbsa`** — an existing live daily Buy Box automation. See `02_DISCOVERY/BBSA_DUPLICATE_RISK.md` |

Per the Mini-AIOS subfolder rule, work stays inside this project folder. Nothing outside
it has been modified.

## Definition of done (from the requirement)

| Criterion | State |
|---|---|
| All PH ASINs checked without manual work | **met** — 20,821/20,821, 0 errors |
| Every NO has a reason or is Unknown | **met** — all 915 `Unknown` |
| Results match a manual spot check | **met** — 6 DB rows + 10 live ASINs |
| Dashboard with filters, cards, table, chart, export | **met** — 86/86 tests |
| Daily history stored | **partially met** — SQLite; Postgres pending approval |
