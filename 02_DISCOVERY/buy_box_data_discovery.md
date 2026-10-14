# Buy Box Check Automation — Data Discovery

**Project:** Buy Box Check Automation – Tharsi
**Date:** 2026-10-14
**Access used:** read-only (`SET TRANSACTION READ ONLY`) + read-only MCP
**Databases inspected:** `ledsone`, `ph_dashboard`

---

## 1. Input files located

| File | Path | Status |
|---|---|---|
| `Buy_Box_Automation_Tharsi (1).docx` | `C:\Users\LED 222\Downloads\` | FOUND — primary spec |
| `skills_minimal_pack 2 (2) 2.zip` | `C:\Users\LED 222\Downloads\` | FOUND (already extracted alongside) |
| `skills 3 (1) (3) 1.zip` | `C:\Users\LED 222\Downloads\` | FOUND (already extracted as `skills 3 (1) (3) (1)`) |
| `ledsone_postgresql_data_structure (1).xlsx` | `C:\Users\LED 222\Downloads\` | FOUND |
| `Mini-AIOS_Master_Instruction_and_Skill_Guide (1).docx` | `C:\Users\LED 222\Downloads\` | FOUND |

ZIP archives were **not re-extracted or executed** — previously extracted copies were read in place, and no script inside them was run.

### Skill pack review
Both packs are text-to-SQL guidance for the `order_management` domain (orders, traffic, PPC,
stock, expenses, shipment). `grep -ri "buy.box"` across both packs returns **only two incidental
mentions** inside `SKILL_threshold_validator.md`, both as narrative context for margin rules
("can selling price increase without losing Buy Box"). **Neither pack defines any Buy Box
ownership rule, reason checklist, or reason priority order.**

---

## 2. Requirement extraction (from the DOCX)

Fully recovered: objective, manual process, automation scope, input table, output table,
flow, colour rules, schedule/alerts, done criteria, open questions, and the sample UI image
(`word/media/image1.png`, extracted to `02_REFERENCE/sample_dashboard.png`).

### The critical gap in the specification
Paragraph 29 states:

> "Run checks 1 to 8 from Section 5 in order. Stop at the first match and save it as the Reason."

**Section 5 of the document is "Automation Logic (Simple Flow)" — it contains the instruction
itself, not a list of checks.** There is no numbered list of 8 reason checks anywhere in the
document, and no priority order. The document's own closing section confirms this is unresolved:

> "10. Questions for the Team to Confirm … Is any reason missing from?"

The sample dashboard image shows five example reason labels (Price higher, Out of stock,
Listing suppressed, Low seller score, Not Prime eligible) under a heading that the document
explicitly captions *"Numbers and names are only examples."*

**Consequence: no approved reason rule exists.** Per the brief ("Do not invent those eight
checks or their priority" / "If no approved reason can be established, assign Unknown"),
every verified NO is assigned `Reason = Unknown`. Observed signals are recorded separately as
non-binding evidence and are never promoted to a classified reason.

---

## 3. Database discovery

### 3.1 Buy Box ownership — what exists

Exhaustive column search across `ledsone` for
`buybox|buy_box|competitive_price|landed_price|is_winner|offer_count|number_of_offers|seller_id|merchant`
returned **exactly one family of Buy Box columns**:

| Schema | Table | Column | Type |
|---|---|---|---|
| `business_reports` | `amz_sales_and_traffic_by_asin` | `buy_box_percentage` | numeric |
| `business_reports` | `amz_sales_and_traffic_by_asin` | `buy_box_percentage_b2b` | numeric |
| `business_reports` | `amz_sales_and_traffic_by_date` | `buy_box_percentage` | numeric |
| `business_reports` | `amz_sales_and_traffic_by_sku` | `buy_box_percentage` | numeric |

`amz_sales_and_traffic_by_asin` is the only one at ASIN grain and is therefore the sole
usable Buy Box source.

**Grain:** `date + child_asin + sub_source + market_place`
**Freshness:** latest loaded date `2026-10-12` (two-day reporting lag; normal for this report)
**Semantics:** Amazon Sales & Traffic "Buy Box Percentage" — the share of **page views** on
that ASIN, that day, where **our** offer was the featured offer. It is our own seller-account
measurement, so it is direct ownership evidence for our account.

### 3.2 Buy Box ownership — what does NOT exist

| Needed for | Searched for | Result |
|---|---|---|
| Competitor / winning seller identity | `featured`, `seller_id`, `merchant`, `is_winner` | **NOT FOUND** — only `amazon_fba.excess_inventory_data.featuredoffer_price` (a price, FBA-excess scope, no seller identity) |
| Competitor price for "Price higher" | `competitive_price`, `landed_price`, `lowest_price`, `featured` | **PARTIAL** — `amazon_fba.excess_inventory_data` holds `your_price` + `featuredoffer_price` (fresh to 2026-10-13), but only for ASINs flagged as **excess FBA stock**: 792 of 20,821 PH rows (3.8%), and 127 of the 915 verified losses |
| Offer count on the ASIN | `offer_count`, `number_of_offers` | only `average_offer_count`, and only in `..._by_date` (no ASIN grain) |
| Amazon seller score / account health | account rating tables | only `customer_service.ebay_account_ratings` (**eBay only**) |
| Prime eligibility flag | `prime` | **NOT FOUND** |

There is **no live Amazon SP-API / Product Pricing integration** in this database. Buy Box
ownership can only be read from the daily business report, never on demand.

### 3.3 The PH Dashboard ASIN list

`ph_dashboard.public.analytics_overallasinlisting` — the PH Dashboard's own listing table,
rebuilt daily (`snapshot_at = 2026-10-14 02:05`).

Amazon scope, one row per ASIN × account × marketplace (no duplicates — verified):

| Account | `sub_source` | UK | DE | FR | IT | Total |
|---|---|---|---|---|---|---|
| LEDSone | 8 | 6,151 | 2,364 | 2,192 | 1,594 | 12,301 |
| DCVoltage | 6 | 5,115 | 1,766 | — | 1,639 | 8,520 |
| **Total** | | **11,266** | **4,130** | **2,192** | **3,233** | **20,821** |

Non-Amazon platforms in the same table (eBay, B&Q, Shopify) are **out of scope** — the
requirement's input table states `Marketplace = Amazon`.

### 3.4 Account and marketplace mapping (verified against lookup tables)

`order_management.sub_source`: `6 = "amazon Dcvoltage"`, `8 = "amazon Ledsone"` — both PH
Amazon accounts are covered by the Buy Box report.

`order_management.market_place`: `23 = UK`, `10 = Germany`, `9 = France`, `14 = Italy`.

### 3.5 Listing status and stock

`ledsone.listings.amazon_listings` — refreshed `2026-10-14 03:01`.

- Per-marketplace resolution is via **`site`** (`UK`, `Germany`, `France`, `Italy`), **not**
  `region_id` (which is only `1 = Europe`, `2 = North America`).
- Grain is **one row per SKU offer**, so an ASIN can carry several offers.
  **2,079** ASIN × account × marketplace groups hold offers with *differing* statuses —
  these must be aggregated, not arbitrarily picked.
- Observed `status` values: `Active`, `BUYABLE`, `DISCOVERABLE`, `Inactive`, `Incomplete`, `NULL`.
  **There is no `Suppressed` value in the source** (see mapping file — flagged for approval).
- `quantity` is the marketplace-facing listing quantity; PH `uk_stock` / `fbm_stock` are
  warehouse figures.

### 3.6 Category

`ph_dashboard.public.ph_allocation_idrecord.refId` holds the **ASIN**, joined to
`ph_allocation_phcategory`. Coverage over the PH Amazon spine: **20,821 / 20,821 (100%)**,
66 distinct categories (Cable 2,071; Lampshade 1,933; shade 1,826; Wire Cage 1,246; Bulbs 1,114 …).
Only 1 ASIN maps to more than one category name.

---

## 4. Buy Box coverage — the single biggest constraint

The Sales & Traffic report only emits a row for an ASIN on a day when that ASIN **had traffic**.
Measured coverage of the 20,821 PH Amazon rows:

| Lookback from 2026-10-12 | PH rows with a report row | Coverage |
|---|---|---|
| 1 day | 255 | 1.2% |
| 3 days | 5,151 | 24.7% |
| **7 days (chosen)** | **7,860** | **37.8%** |
| 14 days | 9,749 | 46.8% |
| 30 days | 11,974 | 57.5% |
| 90 days | 15,221 | 73.1% |

Even at 90 days only 73% of PH ASINs ever receive a reading. **The large NOT VERIFIED share is a
real property of the data source, not an artefact of the chosen window.** Widening the window
would not fix it and would make "Last Checked" badly stale, so 7 days was chosen as the shortest
window that absorbs the reporting lag and weekend gaps while keeping the reading current.

---

## 5. Existing assets reviewed

- **PH Dashboard app** — Django (`ph_dashboard` DB: `accounts_*`, `analytics_*`, `ph_allocation_*`,
  `scheduler_scheduledtask`, `ingestion_ingestionrun`). No Buy Box model, table, or column exists
  anywhere in it.
- **No existing Buy Box monitoring logic** was found in the database or the skill packs.
- `scheduler_scheduledtask` (15 rows) is the app's own scheduler — a possible future host for the
  daily run, but **not touched** (no write approval).

---

## 6. Safety confirmation

Only `SELECT`, `information_schema` reads and read-only aggregates were issued. The direct
psycopg session was pinned with `SET TRANSACTION READ ONLY`. No INSERT/UPDATE/DELETE/DDL was
executed. No credentials appear in any script output, document, or the HTML — connection
strings are read from environment variables inside the scripts and never printed.
