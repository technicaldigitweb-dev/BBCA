# ASSET REGISTER - BBOX

Generated from the filesystem on 2026-10-14 by
`00_PROJECT_CONTROL/gen_asset_register.py`. It is generated, not hand-maintained,
so it cannot drift from what is on disk. Re-run after adding or removing files.

**134 files across 19 directories.**

| Directory | Files | Bytes | Purpose |
|---|---|---|---|
| `(root)` | 2 | 3,967 | Original project documents and repository configuration |
| `00_PROJECT_CONTROL` | 6 | 23,116 | Project control: start-here, scope, status, asset register |
| `01_REQUIREMENT` | 4 | 174,042 | Requirement register, business rules, open questions |
| `02_DISCOVERY` | 8 | 58,274 | Discovery: data sources, existing assets, duplicate risk, push mapping |
| `02_REFERENCE` | 1 | 144,417 | Source reference material (requirement sample screen) |
| `03_SCRIPTS` | 28 | 228,977 | Analysis, extraction, build and test scripts (dashboard pipeline) |
| `04_DATA` | 16 | 83,108,476 | Extracted datasets and build inputs/outputs |
| `05_OUTPUT` | 3 | 8,527,767 | Standalone dashboard HTML versions (v001-v003) |
| `06_EVIDENCE` | 29 | 169,008 | Evidence packs: discovery, validation, live checks, screenshots |
| `06_EVIDENCE/screenshots` | 11 | 4,202,857 | Evidence packs: discovery, validation, live checks, screenshots |
| `07_AUTOMATION` | 1 | 3,351 | Index into automation/ - the code itself is NOT duplicated here |
| `08_VALIDATION` | 3 | 8,077 | Test results, validation checklist, pass/fail report |
| `09_GITHUB` | 2 | 5,016 | Repository, commit and push evidence |
| `09_HANDOVER` | 1 | 183 | Superseded by 10_HANDOVER (kept, empty) |
| `10_HANDOVER` | 3 | 14,901 | Handover, remaining work, unknown-developer check |
| `11_DAILY_STATUS` | 1 | 4,273 | Daily status notes |
| `12_PROMPTS` | 1 | 3,956 | Prompt register |
| `automation` | 13 | 109,908 | The daily automation engine (config/sources/engine/history/alerts/publisher/api/run) |
| `automation/migrations` | 1 | 5,436 | The daily automation engine (config/sources/engine/history/alerts/publisher/api/run) |

---

## Full inventory

### `(root)`

| File | Bytes |
|---|---|
| .gitignore | 301 |
| README.md | 3,666 |

### `00_PROJECT_CONTROL`

| File | Bytes |
|---|---|
| ASSET_REGISTER.md | 5,655 |
| PROJECT_SCOPE.md | 3,084 |
| PROJECT_STATUS.md | 4,140 |
| START_HERE.md | 3,702 |
| check_links.py | 3,041 |
| gen_asset_register.py | 3,494 |

### `01_REQUIREMENT`

| File | Bytes |
|---|---|
| BUSINESS_RULES.md | 3,509 |
| Buy_Box_Automation_Tharsi (1).docx | 164,275 |
| OPEN_QUESTIONS.md | 2,403 |
| REQUIREMENT_REGISTER.md | 3,855 |

### `02_DISCOVERY`

| File | Bytes |
|---|---|
| BBSA_DUPLICATE_RISK.md | 4,911 |
| DATA_SOURCE_MAPPING.md | 4,463 |
| EXISTING_ASSET_REVIEW.md | 5,070 |
| PH_DASHBOARD_MAPPING.md | 4,406 |
| buy_box_data_discovery.md | 9,081 |
| buy_box_handover.md | 7,418 |
| buy_box_source_mapping.md | 12,766 |
| buy_box_validation_report.md | 10,159 |

### `02_REFERENCE`

| File | Bytes |
|---|---|
| sample_dashboard.png | 144,417 |

### `03_SCRIPTS`

| File | Bytes |
|---|---|
| add_v003_tests.py | 4,244 |
| build_dataset.py | 6,722 |
| build_html.py | 27,900 |
| build_html_v002.py | 33,362 |
| build_html_v003.py | 35,228 |
| build_reason_investigation.py | 6,479 |
| build_v003_dataset.py | 6,461 |
| cdp_ipcheck.py | 483 |
| check_cov.py | 1,211 |
| check_price_evidence.py | 1,827 |
| diag_listings.py | 1,009 |
| extract_history.py | 2,756 |
| extract_ledsone.py | 4,145 |
| fix_price_evidence.py | 10,502 |
| fresh_bb_compare.py | 1,672 |
| fresh_bb_probe.py | 1,331 |
| make_build_html_v003.py | 2,453 |
| manual_captcha_inspect.py | 13,365 |
| parse_mcp.py | 649 |
| probe_db.py | 787 |
| probe_v002_cols.py | 1,704 |
| read_docx.py | 536 |
| run_cdp_verify.py | 4,586 |
| spotcheck.py | 2,031 |
| test_dashboard.py | 9,875 |
| test_dashboard_v002.py | 16,304 |
| test_dashboard_v003.py | 19,097 |
| verify_live_listing.py | 12,258 |

### `04_DATA`

| File | Bytes |
|---|---|
| bb_evidence.json | 1,947,136 |
| bb_history_daily.json | 11,107 |
| bb_prev.json | 1,111,344 |
| dashboard_rows.json | 12,833,605 |
| dashboard_rows_v002.json | 22,114,460 |
| dashboard_rows_v003.json | 23,860,665 |
| extract_meta.json | 90 |
| listing_status.json | 12,744,964 |
| ph_spine.json | 8,138,239 |
| price_evidence.json | 130,221 |
| price_evidence_v2.json | 196,797 |
| summary.json | 508 |
| summary_v003.json | 433 |
| test_results.json | 3,751 |
| test_results_v002.json | 6,983 |
| test_results_v003.json | 8,173 |

### `05_OUTPUT`

| File | Bytes |
|---|---|
| 2026-10-14_tharsi_buy_box_monitor_v001.html | 2,318,906 |
| 2026-10-14_tharsi_buy_box_monitor_v002.html | 3,103,839 |
| 2026-10-14_tharsi_buy_box_monitor_v003.html | 3,105,022 |

### `06_EVIDENCE`

| File | Bytes |
|---|---|
| README.md | 1,227 |
| amazon_access_block.md | 2,912 |
| amazon_uk_listing_verification.md | 4,984 |
| bulk_automation_readiness_v2.md | 6,376 |
| bulk_readiness.md | 4,939 |
| dashboard_v002_validation.md | 4,078 |
| dashboard_v003_validation.md | 7,654 |
| dashboard_validation.md | 3,992 |
| fresh_buy_box_data_validation.md | 4,540 |
| live_listing_extraction_validation.md | 6,738 |
| manual_inspect_result.json | 299 |
| manual_single.json | 410 |
| phase2_single.json | 615 |
| phase2_single_src.json | 825 |
| phase4_5_ten_asin_verification.md | 10,391 |
| phase4_ten_uk.json | 18,424 |
| price_accuracy_validation.md | 6,878 |
| price_corrections.json | 30,482 |
| reason_investigation_validation.md | 4,664 |
| reason_rule_approval_request.md | 7,247 |
| sample_10_uk.json | 8,058 |
| sample_10_uk_ordered.json | 8,058 |
| selector_validation.md | 3,816 |
| seller_identity.md | 2,745 |
| seller_identity_verification.md | 7,016 |
| smoke_1.json | 384 |
| uk_locale_and_vpn.md | 3,618 |
| uk_vpn_baseline.json | 2,395 |
| uk_vpn_comparison.md | 5,243 |

### `06_EVIDENCE/screenshots`

| File | Bytes |
|---|---|
| B018OUTQ84_uk.png | 379,293 |
| B07VFV228J_uk.png | 349,571 |
| B07VXWJ5WY_uk.png | 373,562 |
| B083TNFR73_uk.png | 404,178 |
| B0855MZ337_uk.png | 470,650 |
| B086385W3W_manual_initial.png | 24,109 |
| B086385W3W_uk.png | 369,636 |
| B08CXS3T8T_uk.png | 469,643 |
| B08S45CM19_uk.png | 413,815 |
| B0GLPLNXXC_uk.png | 498,233 |
| B0GLYZ41VT_uk.png | 450,167 |

### `07_AUTOMATION`

| File | Bytes |
|---|---|
| README.md | 3,351 |

### `08_VALIDATION`

| File | Bytes |
|---|---|
| PASS_FAIL_REPORT.md | 2,108 |
| TEST_RESULTS.md | 3,674 |
| VALIDATION_CHECKLIST.md | 2,295 |

### `09_GITHUB`

| File | Bytes |
|---|---|
| COMMIT_EVIDENCE.md | 1,437 |
| GITHUB_PUSH_STATUS.md | 3,579 |

### `09_HANDOVER`

| File | Bytes |
|---|---|
| README.md | 183 |

### `10_HANDOVER`

| File | Bytes |
|---|---|
| HANDOVER.md | 6,093 |
| REMAINING_WORK.md | 3,973 |
| UNKNOWN_DEVELOPER_CHECK.md | 4,835 |

### `11_DAILY_STATUS`

| File | Bytes |
|---|---|
| 2026-10-14_STATUS.md | 4,273 |

### `12_PROMPTS`

| File | Bytes |
|---|---|
| PROMPT_REGISTER.md | 3,956 |

### `automation`

| File | Bytes |
|---|---|
| README.md | 9,299 |
| alerts.py | 8,517 |
| api.py | 7,181 |
| config.local.example.json | 175 |
| config.local.json | 175 |
| config.py | 4,933 |
| engine.py | 9,293 |
| history.py | 8,443 |
| publisher.py | 12,604 |
| run.py | 9,018 |
| scheduler.ps1 | 5,019 |
| sources.py | 14,978 |
| test_automation.py | 20,273 |

### `automation/migrations`

| File | Bytes |
|---|---|
| 001_buy_box_history.sql | 5,436 |
