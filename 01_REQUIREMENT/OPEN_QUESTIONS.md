# OPEN QUESTIONS — BBOX

Every item blocks something. None can be answered from the data.

| # | Question | Blocks | Asked of | Status |
|---|---|---|---|---|
| Q-01 | **Is this project a duplicate of `bbsa`?** Extend it, keep BBOX separate, or stop? | everything downstream | PH automation owner + **Abiraj** | **OPEN — highest priority** |
| Q-02 | What are the 8 reason checks, in order, with fields and thresholds? | `Official Reason` (R-03) | business owner | OPEN — proposal ready |
| Q-03 | Approve a partial-Buy-Box threshold (e.g. >= 90% = YES)? | 156 rows | business owner | OPEN |
| Q-04 | What time and timezone for the daily run? | scheduler (R-14) | operations | OPEN — must be after 07:35 Asia/Colombo |
| Q-05 | Which machine hosts the schedule? | deployment | operations | OPEN — assumed this Windows PC |
| Q-06 | Approve SP-API Product Pricing access for sub_source 6 and 8? | live ownership, 6 of 8 proposed rules | Amazon account owner | OPEN |
| Q-07 | What counts as a high-priority ASIN? | all alerts (R-16) | business owner | OPEN |
| Q-08 | Alert channel and recipients? | alert delivery | business owner | OPEN — **no delivery infrastructure exists in the estate** |
| Q-09 | Where should Postgres history live, and who grants write? | durable history | DBA + owner | OPEN — migration written, not applied |
| Q-10 | Confirm SRM Suppliers' seller token | attribution of group-company losses | Amazon account owner | OPEN |
| Q-11 | Should "lost to our own group company" be a reason, or a separate commercial escalation? | reason taxonomy | business owner | OPEN |
| Q-12 | Is a reading up to 7 days old acceptable as "current"? | BR-11 | business owner | OPEN |

## Answered during the project

| Question | Answer | Evidence |
|---|---|---|
| Who is "Tharsi"? | **Tharsika(jaffna)** — owner decision 2026-10-14 | `02_DISCOVERY/PH_DASHBOARD_MAPPING.md` |
| What are our seller IDs? | LEDSone `A1BXMEJKH8MYIL`, DCVoltage `A3UNAW6KG6QUOJ` — **VERIFIED** | `06_EVIDENCE/seller_identity_verification.md` |
| Is a UK VPN required for fidelity? | **No** — 7/7 fields matched | `06_EVIDENCE/uk_vpn_comparison.md` |
| Is there fresher Buy Box data? | **No** — all 915 already use the newest reading | `06_EVIDENCE/fresh_buy_box_data_validation.md` |
| Where do local automations publish? | `tech_team_outputs.ph_task` | `02_DISCOVERY/PH_DASHBOARD_MAPPING.md` |
