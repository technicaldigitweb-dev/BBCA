# Phase 7 — Bulk Automation Readiness

**Assessed:** 2026-10-14, after the ten-ASIN UK run
**Verdict: NOT READY.** Access is now viable; the blockers are correctness, not plumbing.

---

## Measured operating characteristics

| Metric | Observed |
|---|---|
| ASINs attempted / succeeded | **10 / 10** |
| Access blocks | **0** |
| HTTP failures | 0 (all `200`) |
| Wall clock | 14:00:48 → 14:03:26 = **158 s** |
| Per ASIN | **~15.8 s** (2 page loads + 4 s politeness sleep) |
| Amazon page loads this session | ~22 (2 setup + 20 sample) |
| **Projected full run (915 ASINs)** | **~4 hours** at the current rate |

## Access: the transport change is what fixed it

| Approach | Loads before block |
|---|---|
| Playwright-**launched** Chromium (headless *and* headed) | blocked at ~10–15 |
| **CDP against an operator-opened Chrome** | **22+, no block** |

Driving a browser the operator opened and navigated is a materially weaker automation signal
than a Playwright-launched context. Combined with the fresh UK egress IP, this session completed
twice the previous block threshold cleanly.

**This is not proof it scales to 915.** 22 loads is not 1,830. The earlier block appeared
*part-way through* a session that had also been working. Volume behaviour beyond ~20 loads is
**uncharacterised**, and the honest read is that a 4-hour, 1,830-load run is a very different
proposition from a 3-minute one.

## Readiness by criterion

| Criterion | Status | Note |
|---|---|---|
| Browser stability | **PASS** | 10/10, no crash, no hang after the retry fix |
| Transport / access | **PARTIAL** | works at 22 loads; unproven at 1,830 |
| Selector reliability | **PASS** | structural selectors + the fixed `sold_by()` returned values on every page that had them |
| Marketplace correctness | **PASS** | UK locale asserted before extraction; run aborts if not GB/GBP |
| Seller identity matching | **PARTIAL** | our tokens now captured; **holder** identified by display name in 5/10; mapping unconfirmed |
| Request rate / limits | **PARTIAL** | 4 s spacing held; no published limit to verify against |
| Failure handling | **PASS** | per-ASIN exceptions captured; mid-run block halts the run and records it |
| Retry behaviour | **PARTIAL** | locale setup retries ×3; **per-ASIN failures are not retried** |
| Check timestamps | **PASS** | real per-ASIN `checked_at` |
| Data quality | **FAIL** | see below |
| Amazon access restrictions | **RESPECTED** | no challenge clicked, no bypass, no fingerprint spoofing |

## Why NOT READY — the three real blockers

**1. The output has no approved reason to write into.**
The 8-check list is still undefined. A 4-hour run would produce 915 rows of evidence that all
still land in `Reason = Unknown`. The run is only worth its cost *after* the rules exist — and
the sample shows those rules must cover **"we actually hold it"**, **"Amazon retail holds it"**
and **"our own group company holds it"**, none of which appear in the requirement's five sample
labels.

**2. 40% of the target set may not be losses at all.**
Four of ten sampled "Buy Box NO" rows showed our own account holding the featured offer live.
Scraping 915 ASINs to re-discover that a large share are stale readings is the wrong order of
work. Re-running the internal extraction against the newest report date is cheaper and should
come first.

**3. Seller identity is not yet authoritative.**
`A1BXMEJKH8MYIL → LEDSone` and `A3UNAW6KG6QUOJ → DCVoltage` are inferred from co-occurrence, not
confirmed. At 915-row scale an inferred mapping will mis-attribute ownership somewhere. One
SP-API `getMarketplaceParticipations` call settles it.

## Recommended sequence before any bulk run

1. **Confirm the two merchant tokens** against SP-API or Seller Central. Cheap, removes the
   identity caveat entirely.
2. **Refresh the internal Buy Box reading** to the newest available report date and re-measure
   how many of the 915 are still 0% — likely removing a large fraction of the work.
3. **Get the 8 checks defined**, now informed by what the sample actually found.
4. **Characterise block behaviour** with a staged run — 50, then 150 ASINs, with cooldown
   between — before committing to the full set.
5. Add per-ASIN retry and resume-from-checkpoint, so a 4-hour run that trips a block at ASIN 600
   does not lose everything.

## Operational notes for whoever runs this next

- **The VPN here is browser-scoped.** Shell `curl` still egresses via Sri Lanka while Chrome
  egresses via GB. Bulk collection **must** use `run_cdp_verify.py` against the opened window,
  never `verify_live_listing.py`'s own launcher, or it will silently collect the wrong page.
- Chrome must be started with `--remote-debugging-port=9222` and a dedicated
  `--user-data-dir`, with the VPN active in that window.
- UK locale (`SW1A1AA` + `i18n-prefs=GBP`) is asserted each run and aborts on failure — do not
  remove that guard.
