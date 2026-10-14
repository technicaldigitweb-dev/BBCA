# PROMPT REGISTER — BBOX

Mini-AIOS operating model: **GPT is the brain, Claude Code is the worker.** Each entry
below is a GPT-authored prompt that drove a build step.

**Only prompts whose source text was available in this session are registered.**
Earlier prompts were not retained and have **not** been reconstructed — inventing them
would be fabricated evidence.

---

| ID | Purpose | Date | Source | Implementation | Evidence | Status |
|---|---|---|---|---|---|---|
| P-01 | Requirement analysis → data discovery → mapping → standalone HTML dashboard | 2026-10-14 | GPT prompt, pasted | `03_SCRIPTS/build_dataset.py`, `build_html.py` | `../02_DISCOVERY/buy_box_data_discovery.md`, `../02_DISCOVERY/buy_box_source_mapping.md`, v001 | **complete** |
| P-02 | Follow the Section 6 sample design | 2026-10-14 | user instruction (Tamil/English) | `03_SCRIPTS/build_html.py` | `02_REFERENCE/sample_dashboard.png`, v001 screenshot | **complete** |
| P-03 | Find the reason data | 2026-10-14 | user question | `check_price_evidence.py` | corrected "NOT FOUND" → PARTIAL; FBA price evidence added | **complete** |
| P-04 | Reason must come from viewing the live listing | 2026-10-14 | user instruction | `03_SCRIPTS/verify_live_listing.py` | `06_EVIDENCE/amazon_uk_listing_verification.md` | **complete** |
| P-05 | Final live listing verification (Phases 1–7) | 2026-10-14 | GPT prompt, pasted | `run_cdp_verify.py`, selector fixes | `uk_vpn_comparison.md`, `phase4_5_ten_asin_verification.md`, `bulk_readiness.md` | **complete** |
| P-06 | Seller identity, fresh data, loss investigation, dashboard v003 (Phases A–G) | 2026-10-14 | GPT prompt, pasted | `build_v003_dataset.py`, `build_html_v003.py` | `seller_identity_verification.md`, `fresh_buy_box_data_validation.md`, `dashboard_v003_validation.md` | **complete** |
| P-07 | Remove the Live Check column | 2026-10-14 | user instruction | `build_html_v003.py` patch | 94/94 at the time | **complete** |
| P-08 | Remove all live-check data from the dashboard | 2026-10-14 | user instruction (Tamil) | `build_v003_dataset.py`, `make_build_html_v003.py` | 86/86 | **complete** |
| P-09 | Daily automation, manual run, history, alerts (Phases A–I) | 2026-10-14 | GPT prompt, pasted | `automation/` (9 modules) | `automation/README.md`, 69/69 | **complete** |
| P-10 | Local daily execution → automatic PH Dashboard push | 2026-10-14 | GPT prompt, pasted | `automation/publisher.py`, freshness gate in `run.py` | `02_DISCOVERY/PH_DASHBOARD_MAPPING.md`, `BBSA_DUPLICATE_RISK.md` | **partial** — publication blocked |
| P-11 | Publish the dashboard | 2026-10-14 | user instruction | `publisher.publish()` | **0 `BBOX` rows — not executed** | **blocked** |
| P-12 | Mini-AIOS folder structure and handover | 2026-10-14 | GPT prompt, pasted | this structure | `08_VALIDATION/`, `10_HANDOVER/` | **complete** |

## Reusable prompt patterns worth keeping

These worked and are worth reusing on the next project:

**1. "Do not invent missing rules."** P-01 and P-06 both instructed explicitly not to
fabricate the 8 reason checks. That single constraint is why `Official Reason` is
honestly `Unknown` rather than plausibly wrong.

**2. "Treat previously reported results as previous, not as new evidence."** P-12 forced
genuine test reruns instead of quoting earlier numbers.

**3. "Perform read-only discovery before proposing any write."** P-10 — this is what
surfaced the `bbsa` duplicate before anything was published.

**4. "Verified facts versus assumptions."** Requiring every finding to be labelled is why
`DATA_SOURCE_MAPPING.md` §6 exists and why the priority rule is marked as an assumption.

## Gap

Prompts P-01 to P-04 are reconstructed from their **effects** (the files and evidence
they produced), not from retained prompt text. The register records what each step did;
it does not claim to reproduce the original wording.
