"""Join PH spine + Buy Box evidence + listing status; classify ownership honestly.

CLASSIFICATION RULES (only what the source can evidence):
  buy_box_percentage == 100            -> YES           (we held the featured offer for all page views)
  buy_box_percentage == 0              -> NO            (we held it for none)
  0 < buy_box_percentage < 100         -> NOT VERIFIED  (split ownership; no approved threshold exists)
  no report row in the window          -> NOT VERIFIED  (no evidence)

REASON: the brief's "checks 1 to 8" are never defined, so NO approved reason rule exists.
Every verified NO therefore gets Reason = "Unknown". Observed signals are recorded
separately as non-binding evidence, never as a classified reason.
"""
import json, os, datetime
from collections import Counter, defaultdict

D = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
L = lambda n: json.load(open(os.path.join(D, n + '.json'), encoding='utf-8'))

spine, bb, ls, prev, meta = L('ph_spine'), L('bb_evidence'), L('listing_status'), L('bb_prev'), L('extract_meta')
px = L('price_evidence')

bb_i   = {(r['asin'], r['sub_source'], r['marketplace']): r for r in bb}
ls_i   = {(r['asin'], r['sub_source'], r['marketplace']): r for r in ls}
prev_i = {(r['asin'], r['sub_source'], r['marketplace']): r for r in prev}
px_i   = {(r['asin'], r['sub_source'], r['marketplace']): r for r in px}

def listing_status(g):
    """Aggregate several offers on one ASIN into one status. Any buyable offer wins."""
    if not g: return 'Not Found', None
    s = set(g['statuses'])
    if s & {'Active', 'BUYABLE'}:  return 'Active', s
    if 'DISCOVERABLE' in s:        return 'Discoverable (not buyable)', s
    if 'Incomplete' in s:          return 'Incomplete', s
    if 'Inactive' in s:            return 'Inactive', s
    return 'Unknown', s

rows, dup = [], Counter()
for p in spine:
    k = (p['asin'], p['sub_source'], p['marketplace'])
    dup[k] += 1
    b, g, pv, pxr = bb_i.get(k), ls_i.get(k), prev_i.get(k), px_i.get(k)
    st, raw = listing_status(g)

    if b is None:
        status, pct, rdate = 'NOT VERIFIED', None, None
        basis = 'No Buy Box report row within %d days of %s' % (meta['window_days'], meta['max_report_date'])
    else:
        pct, rdate = b['buy_box_pct'], b['report_date']
        if pct == 100:  status, basis = 'YES', 'Buy Box held for 100%% of page views on %s' % rdate
        elif pct == 0:  status, basis = 'NO',  'Buy Box held for 0%% of page views on %s' % rdate
        else:           status, basis = 'NOT VERIFIED', 'Split ownership %.2f%% on %s - no approved threshold' % (pct, rdate)

    # Non-binding observed signals. NOT a classified reason.
    sig = []
    if status == 'NO':
        q = g['total_qty'] if g else None
        if q is not None and q <= 0: sig.append('Listing quantity is 0')
        if st in ('Inactive', 'Discoverable (not buyable)', 'Incomplete', 'Not Found'):
            sig.append('Listing status: %s' % st)
        if (p.get('uk_stock') or 0) <= 0 and (p.get('fbm_stock') or 0) <= 0:
            sig.append('No warehouse stock')
        if pxr:
            yp, fp = float(pxr['your_price']), float(pxr['featured_price'])
            sig.append('Our price is above the featured offer' if yp > fp
                       else 'Our price is at or below the featured offer')

    chg = None
    if pv and pv.get('prev_pct') is not None and pct is not None:
        pp = float(pv['prev_pct'])
        if   pct == 100 and pp < 100: chg = 'Regained'
        elif pct == 0 and pp > 0:     chg = 'Lost'
        elif pct == pp:               chg = 'No change'
        else:                         chg = 'Changed'

    rows.append({
        'asin': p['asin'], 'sku': p['sku'], 'mapped_sku': p['mapped_sku'],
        'account': p['account'], 'marketplace': p['marketplace'],
        'category': p['category'], 'ph_name': p['ph_name'],
        'status': status,
        'bb_pct': float(pct) if pct is not None else None,
        'basis': basis,
        'reason': 'Unknown' if status == 'NO' else '',
        'signals': sig,
        'listing_status': st,
        'stock': g['total_qty'] if g else None,
        'uk_stock': p.get('uk_stock'), 'fbm_stock': p.get('fbm_stock'),
        'price': p.get('price'), 'currency': p.get('currency'),
        'last_checked': rdate,
        'prev_pct': float(pv['prev_pct']) if pv and pv.get('prev_pct') is not None else None,
        'prev_date': pv['prev_date'] if pv else None,
        'change': chg,
        'url': p.get('listing_url'),
        'featured_price': float(pxr['featured_price']) if pxr else None,
        'px_your_price': float(pxr['your_price']) if pxr else None,
        'px_date': pxr['price_date'] if pxr else None,
    })

assert max(dup.values()) == 1, 'duplicate grain keys: %s' % [k for k, v in dup.items() if v > 1][:5]

summary = {
    'total': len(rows),
    'yes': sum(r['status'] == 'YES' for r in rows),
    'no': sum(r['status'] == 'NO' for r in rows),
    'not_verified': sum(r['status'] == 'NOT VERIFIED' for r in rows),
    'nv_partial': sum(r['status'] == 'NOT VERIFIED' and r['bb_pct'] is not None for r in rows),
    'nv_nodata': sum(r['status'] == 'NOT VERIFIED' and r['bb_pct'] is None for r in rows),
    'reason_unknown': sum(r['reason'] == 'Unknown' for r in rows),
    'with_stock': sum(r['stock'] is not None for r in rows),
    'with_listing_status': sum(r['listing_status'] != 'Not Found' for r in rows),
    'with_category': sum(bool(r['category']) for r in rows),
    'with_featured_price': sum(r['featured_price'] is not None for r in rows),
    'no_with_featured_price': sum(r['status'] == 'NO' and r['featured_price'] is not None for r in rows),
    'no_priced_above': sum(r['status'] == 'NO' and 'Our price is above the featured offer' in r['signals']
                           for r in rows),
    'latest_checked': max((r['last_checked'] for r in rows if r['last_checked']), default=None),
    'max_report_date': meta['max_report_date'],
    'window_days': meta['window_days'],
    'snapshot_at': spine[0]['snapshot_at'],
    'built_at': datetime.datetime.now().isoformat(timespec='seconds'),
}
json.dump(rows, open(os.path.join(D, 'dashboard_rows.json'), 'w', encoding='utf-8'))
json.dump(summary, open(os.path.join(D, 'summary.json'), 'w', encoding='utf-8'), indent=2)

for k, v in summary.items(): print(f'{k:22} {v}')
print('\nby marketplace/status:')
m = defaultdict(Counter)
for r in rows: m[r['marketplace']][r['status']] += 1
for k in sorted(m): print(' ', k, dict(m[k]))
print('\nsignals on verified NO:', Counter(s for r in rows if r['status']=='NO' for s in r['signals']))
print('no-signal NO rows:', sum(r['status']=='NO' and not r['signals'] for r in rows))
