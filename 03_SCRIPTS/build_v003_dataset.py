"""Build the v003 dataset: v002 rows + live-check evidence, held as separate states.

Rules enforced here:
  * The historical status is NEVER overwritten by a live check. Both are kept.
  * A live check uses a PROVISIONAL seller ID, so it cannot promote a row to YES.
  * Live ownership is only asserted when OUR OWN offer carries a token we recognise;
    a featured seller known only by display name yields NOT VERIFIED for ownership.
  * Official reason stays 'Unknown' everywhere - no approved rule exists.

Reads : 04_DATA/dashboard_rows_v002.json, 06_EVIDENCE/phase4_ten_uk.json
Writes: 04_DATA/dashboard_rows_v003.json, 04_DATA/summary_v003.json
"""
import json
import os
import datetime

ROOT = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi'
D = os.path.join(ROOT, '04_DATA')
E = os.path.join(ROOT, '06_EVIDENCE')

# VERIFIED against stored SP-API Listings Items responses in
# Weekly_Top_Moving_ASIN_Keyword_Report/data/extract.json, where Amazon's own
# .../SELLER/<token>/ media paths sit in the same record as our "sub_source".
# 4/4 consistent per token, zero contradictions. See seller_identity_verification.md.
OUR_TOKENS = {'A1BXMEJKH8MYIL': 'LEDSone', 'A3UNAW6KG6QUOJ': 'DCVoltage'}
TOKEN_STATUS = 'VERIFIED'
# Group companies: same estate, not external competitors (order_management.sub_source).
GROUP = {'SRM SUPPLIES': 'SRM Suppliers (sub_source 9)'}

rows = json.load(open(os.path.join(D, 'dashboard_rows_v002.json'), encoding='utf-8'))
live = json.load(open(os.path.join(E, 'phase4_ten_uk.json'), encoding='utf-8'))

BUILD_DATE = datetime.date(2026, 10, 14)


def norm(s):
    return (s or '').strip().upper()


def classify(res):
    """Derive live ownership state + possible reason from one live page result."""
    err = res.get('error')
    if err:
        return 'CHECK ERROR', ['Page could not be loaded: ' + str(err)[:80]], 'low'
    if res.get('blocked_markers'):
        return 'CHECK ERROR', ['Amazon access control present during check'], 'low'

    feat = norm(res.get('featured_seller_name'))
    offers = (res.get('offers') or {}).get('list') or []
    our_tokens_on_page = {o.get('seller_id') for o in offers if o.get('seller_id') in OUR_TOKENS}
    avail = res.get('availability') or ''

    # Listing is dead - no featured offer at all.
    if not feat and res.get('out_of_stock_block'):
        return 'NO', ['Listing unavailable: "%s"' % avail[:70].strip()], 'high'
    if not feat:
        return 'NOT VERIFIED', ['No featured offer seller could be read from the page'], 'low'

    # Does the featured seller match one of our accounts by NAME?
    # A name match alone is not proof - but combined with our own token present on the
    # page it is strong enough to flag a conflict (never to assert YES outright).
    feat_is_ours = any(norm(v) == feat or feat == norm(k) for k, v in
                       [('LEDSONE', 'LEDSone'), ('DC VOLTAGE', 'DCVoltage')])
    if feat_is_ours and our_tokens_on_page:
        return 'YES', ['Our account holds the featured offer (verified seller token %s '
                       'present on page)' % sorted(our_tokens_on_page)[0]], 'high'
    if feat_is_ours:
        return 'NOT VERIFIED', ['Featured seller name matches our account but no token '
                                'was present to confirm it'], 'low'

    if feat in GROUP:
        return 'NO', ['Featured offer held by %s - our own group company, not an external '
                      'competitor' % GROUP[feat]], 'medium'
    if feat == 'AMAZON':
        return 'NO', ['Featured offer held by Amazon retail (no seller token is exposed '
                      'for Amazon, so identified by display name only)'], 'medium'
    return 'NO', ['Featured offer held by a third party: %s (display name only, no token)'
                  % res.get('featured_seller_name')], 'low'


live_ix = {}   # live-check merge intentionally disabled - see note below
# NOTE: the live verification evidence is retained in 06_EVIDENCE/ (phase4_ten_uk.json,
# phase4_5_ten_asin_verification.md). It is deliberately NOT merged into the dashboard:
# only 10 of 20,821 rows could ever carry it, which made the table inconsistent between
# rows. The dashboard therefore presents one uniform source - the historical report.

out = []
n_live = n_conflict = 0
for r in rows:
    r = dict(r)
    r['live_status'] = None
    r['live_checked_at'] = None
    r['conflict'] = False
    lcd = r.get('last_checked')
    r['stale_days'] = (BUILD_DATE - datetime.date(*map(int, lcd.split('-')))).days if lcd else None
    out.append(r)

summary = {
    'total': len(out),
    'yes': sum(r['status'] == 'YES' for r in out),
    'no': sum(r['status'] == 'NO' for r in out),
    'not_verified': sum(r['status'] == 'NOT VERIFIED' for r in out),
    'official_reason_unknown': sum(r.get('official_reason') == 'Unknown' for r in out),
    'px_available': sum(r.get('px_status') == 'available' for r in out),
    'max_stale_days': max((r['stale_days'] for r in out if r['stale_days'] is not None), default=None),
    'latest_checked': max((r['last_checked'] for r in out if r['last_checked']), default=None),
    'source_max_date': '2026-10-12',
    'source_latest_complete_date': '2026-10-11',
    'token_status': TOKEN_STATUS,
    'our_tokens': OUR_TOKENS,
    'built_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
}

json.dump(out, open(os.path.join(D, 'dashboard_rows_v003.json'), 'w', encoding='utf-8'))
json.dump(summary, open(os.path.join(D, 'summary_v003.json'), 'w', encoding='utf-8'), indent=1)

assert summary['yes'] + summary['no'] + summary['not_verified'] == summary['total']
# Every loss must still carry Unknown - no unapproved rule may have assigned a reason.
_bad = [r['asin'] for r in out if r['status'] == 'NO' and r.get('official_reason') != 'Unknown']
assert not _bad, 'official reason must stay Unknown on every NO: %s' % _bad[:5]
# A live check must never have rewritten a recorded historical status.
_v2 = {(r['asin'], r['account'], r['marketplace']): r['status'] for r in rows}
_moved = [k for k, r in ((( r['asin'], r['account'], r['marketplace']), r) for r in out)
          if _v2[k] != r['status']]
assert not _moved, 'historical status was overwritten: %s' % _moved[:5]
for k, v in summary.items():
    if k not in ('our_tokens',):
        print('%-28s %s' % (k, v))
