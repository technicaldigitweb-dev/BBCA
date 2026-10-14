# 06_EVIDENCE

Evidence files are kept **flat in this folder** - they are referenced by name from
`02_DISCOVERY/`, `08_VALIDATION/` and `10_HANDOVER/`, and moving them would break those
references for no gain.

The subfolders exist for future evidence only.

| Area | Files |
|---|---|
| Discovery | `amazon_access_block.md`, `amazon_uk_listing_verification.md`, `selector_validation.md`, `fresh_buy_box_data_validation.md` |
| Identity | `seller_identity.md` (superseded), `seller_identity_verification.md` (**current, VERIFIED**) |
| Validation | `price_accuracy_validation.md`, `live_listing_extraction_validation.md`, `reason_investigation_validation.md`, `dashboard_validation.md`, `dashboard_v002_validation.md`, `dashboard_v003_validation.md` |
| Live checks | `uk_locale_and_vpn.md`, `uk_vpn_comparison.md`, `phase4_5_ten_asin_verification.md`, `phase4_ten_uk.json`, `uk_vpn_baseline.json`, `sample_10_uk.json` |
| Readiness | `bulk_readiness.md`, `bulk_automation_readiness_v2.md` (**current**) |
| Approval | `reason_rule_approval_request.md` |
| Raw | `screenshots/` (11), `logs/` (4), `price_corrections.json` |

**Superseded files are kept, not deleted.** Where two versions exist the current one is
marked above.
