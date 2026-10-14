"""Generate the standalone Buy Box Monitor dashboard.

Layout follows the sample screen in Section 6 of Buy_Box_Automation_Tharsi (1).docx
(extracted to 02_REFERENCE/sample_dashboard.png): dark navy header, filter row with an
orange Run Check button, four accent-bar summary cards, results table with green/red
status pills, and a right-hand "Top Reasons - No Buy Box" bar panel with Export to Excel.

Regenerate with this script - never hand-edit the HTML.
"""
import json, os, datetime

D = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
OUT = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\05_OUTPUT\2026-10-14_tharsi_buy_box_monitor_v002.html'

load = lambda n: json.load(open(os.path.join(D, n + '.json'), encoding='utf-8'))
rows, summary, hist = load('dashboard_rows_v002'), load('summary'), load('bb_history_daily')

# ---- v002: recompute the price-evidence counters from the CORRECTED rows ----
summary = dict(summary)
summary['version'] = 'v002'
summary['px_available'] = sum(1 for r in rows if r.get('px_status') == 'available')
summary['px_unavailable'] = sum(1 for r in rows if r.get('px_status') == 'unavailable')
summary['with_featured_price'] = summary['px_available']
summary['no_with_featured_price'] = sum(
    1 for r in rows if r['status'] == 'NO' and r.get('px_status') == 'available')
summary['no_priced_above'] = sum(
    1 for r in rows if r['status'] == 'NO'
    and 'Our price is above the featured offer' in (r.get('signals') or []))
summary['not_determined'] = sum(
    1 for r in rows if r['status'] == 'NO'
    and r.get('possible_reason') == ['Not Determined'])
summary['built_at'] = __import__('datetime').datetime.now().isoformat(timespec='seconds')

# ---- intern repeated strings so the embedded payload stays small ----
class Pool:
    def __init__(self): self.v, self.i = [], {}
    def __call__(self, s):
        if s is None: s = ''
        if s not in self.i:
            self.i[s] = len(self.v); self.v.append(s)
        return self.i[s]

acct, mkt, cat, stat, lst, dt, sig, chg, phn = (Pool() for _ in range(9))
pxr, pos, conf = Pool(), Pool(), Pool()   # v002: price reason, possible reason, confidence

data = []
for r in rows:
    data.append([
        r['asin'], r['sku'] or '', acct(r['account']), mkt(r['marketplace']),
        cat(r['category']), stat(r['status']), r['stock'],
        lst(r['listing_status']), dt(r['last_checked']),
        r['bb_pct'], [sig(s) for s in r['signals']],
        r['uk_stock'], r['fbm_stock'], r['price'], r['mapped_sku'] or '',
        phn(r['ph_name'] or ''), r['prev_pct'], chg(r['change']), r['currency'] or '',
        r['featured_price'], r['px_compared_price'], dt(r['px_date']),
        # --- v002 additions ---
        r.get('px_status') or '', pxr(r.get('px_reason') or ''),
        r.get('px_sku') or '',
        [pos(p) for p in (r.get('possible_reason') or [])],
        conf(r.get('reason_confidence') or ''),
        r.get('official_reason') or 'Unknown',
    ])

# daily trend aggregated across accounts + marketplaces
trend = {}
for h in hist:
    t = trend.setdefault(h['date'], {'won': 0, 'lost': 0, 'partial': 0, 'total': 0})
    for k in ('won', 'lost', 'partial', 'total'):
        t[k] += h[k]
trend = [dict(date=d, **v) for d, v in sorted(trend.items())]

payload = {
    'rows': data,
    'pools': {'acct': acct.v, 'mkt': mkt.v, 'cat': cat.v, 'stat': stat.v,
              'lst': lst.v, 'dt': dt.v, 'sig': sig.v, 'chg': chg.v, 'phn': phn.v,
              'pxr': pxr.v, 'pos': pos.v, 'conf': conf.v},
    'summary': summary,
    'trend': trend,
}

TPL = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Buy Box Monitor</title>
<style>
  :root{
    --navy:#1c2b45; --bg:#f3f5f9; --card:#ffffff; --line:#dfe4ec;
    --ink:#1f2937; --muted:#6b7280;
    --green:#27a35a; --red:#d9453d; --amber:#e0a800; --grey:#8a94a6; --orange:#f0952a;
    --purple:#7b52ab; --blue:#3a7cc4;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}

  /* header */
  header{background:var(--navy);color:#fff;padding:18px 24px;
         display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
  header h1{margin:0;font-size:21px;font-weight:700;letter-spacing:.2px}
  header h1 span{font-weight:400;opacity:.55;margin:0 8px}
  .refreshed{font-size:13px;opacity:.85}

  .wrap{padding:20px 24px 40px;max-width:1800px;margin:0 auto}

  /* filter row */
  .filters{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:20px}
  .filters input,.filters select{
    flex:1 1 190px;min-width:150px;background:#fff;border:1px solid var(--line);
    border-radius:6px;padding:12px 14px;font-size:14px;color:var(--ink)}
  .filters input::placeholder{color:#9aa3b2}
  .filters input:focus,.filters select:focus{outline:2px solid #c3d4ec;outline-offset:-1px}
  #runCheck{flex:0 0 auto;background:var(--orange);color:#fff;border:0;border-radius:6px;
            padding:12px 30px;font-size:15px;font-weight:700;cursor:pointer}
  #runCheck:hover{filter:brightness(.95)}

  /* summary cards */
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;margin-bottom:20px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:6px;
        padding:18px 20px 20px 22px;position:relative;overflow:hidden}
  .card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:7px;background:var(--navy)}
  .card.g::before{background:var(--green)} .card.r::before{background:var(--red)}
  .card.a::before{background:var(--amber)} .card.n::before{background:var(--grey)}
  .card .lbl{color:var(--muted);font-size:14px;margin-bottom:12px}
  .card .val{font-size:30px;font-weight:700;letter-spacing:-.5px}
  .card.g .val{color:var(--green)} .card.r .val{color:var(--red)}
  .card.a .val{color:var(--amber)} .card.n .val{color:var(--grey)}
  .card .val small{font-size:19px;font-weight:700;margin-left:4px}

  /* notice */
  .notice{background:#fff;border:1px solid var(--line);border-left:5px solid var(--grey);
          border-radius:6px;padding:14px 18px;margin-bottom:20px;font-size:13.5px;color:#374151}
  .notice b{color:var(--ink)}

  /* main split: table left, chart right (as per sample screen) */
  .main{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:20px;align-items:start}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:6px;overflow:hidden}
  .panel h2{margin:0;padding:18px 20px 14px;font-size:16px;font-weight:700}

  /* table */
  .tscroll{overflow-x:auto}
  table{border-collapse:collapse;width:100%;font-size:13.5px}
  thead th{background:#e8edf5;text-align:left;padding:14px 14px;font-weight:700;
           white-space:nowrap;cursor:pointer;user-select:none;border-bottom:1px solid var(--line)}
  thead th:hover{background:#dde5f0}
  thead th .ar{opacity:.45;font-size:11px;margin-left:4px}
  tbody td{padding:13px 14px;border-bottom:1px solid #eef1f6;vertical-align:middle}
  tbody tr{cursor:pointer}
  tbody tr:hover{background:#f7f9fc}
  .asin{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:600}
  .na{color:#aeb6c2}
  .num{text-align:right;font-variant-numeric:tabular-nums}

  .pill{display:inline-block;min-width:54px;text-align:center;padding:7px 16px;border-radius:999px;
        color:#fff;font-weight:700;font-size:12.5px;white-space:nowrap}
  .pill.yes{background:var(--green)} .pill.no{background:var(--red)} .pill.nv{background:var(--grey)}
  .rsn-unknown{color:var(--amber);font-weight:600}

  .tfoot{display:flex;justify-content:space-between;align-items:center;gap:14px;
         padding:14px 20px;flex-wrap:wrap;border-top:1px solid var(--line)}
  .hint{color:var(--muted);font-style:italic;font-size:13px}
  .pager{display:flex;gap:8px;align-items:center}
  .pager button{background:#fff;border:1px solid var(--line);border-radius:5px;
                padding:7px 13px;cursor:pointer;font-size:13px}
  .pager button:disabled{opacity:.4;cursor:default}

  /* reasons chart */
  .bars{padding:4px 20px 18px}
  .bar{margin-bottom:14px}
  .bar .t{display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px}
  .bar .track{background:#eef1f6;border-radius:3px;overflow:hidden}
  .bar .fill{height:19px;border-radius:3px}
  .exp{border-top:1px solid var(--line);padding:16px 20px}
  .exp button{background:none;border:0;padding:0;font-size:14px;font-weight:700;
              color:var(--ink);cursor:pointer}
  .exp button:hover{color:var(--orange)}
  .exp .sub{color:var(--muted);font-size:12px;margin-top:6px}

  .sect{padding:4px 20px 20px;font-size:13px}
  .sect table{font-size:12.5px}
  .sect thead th{background:#f4f6fa;padding:9px 10px;cursor:default}
  .sect tbody td{padding:9px 10px}

  /* detail drawer */
  .ovl{position:fixed;inset:0;background:rgba(17,24,39,.5);display:none;z-index:50}
  .ovl.on{display:block}
  .drw{position:fixed;top:0;right:0;bottom:0;width:min(460px,100%);background:#fff;
       box-shadow:-4px 0 20px rgba(0,0,0,.2);padding:24px;overflow:auto;z-index:51;display:none}
  .drw.on{display:block}
  .drw h3{margin:0 0 4px;font-size:18px}
  .drw .cls{position:absolute;top:16px;right:20px;border:0;background:none;font-size:26px;
            cursor:pointer;color:var(--muted);line-height:1}
  .kv{display:grid;grid-template-columns:140px 1fr;gap:9px 12px;margin-top:18px}
  .kv dt{color:var(--muted)} .kv dd{margin:0;font-weight:600;word-break:break-word}
  .evid{margin-top:20px;background:#f7f9fc;border:1px solid var(--line);border-radius:6px;padding:14px}
  .evid h4{margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted)}
  .evid ul{margin:8px 0 0;padding-left:18px} .evid li{margin-bottom:4px}
  .warnbox{margin-top:14px;background:#fff8e6;border:1px solid #f0dca0;border-radius:6px;
           padding:12px;font-size:12.5px;color:#6b5300}
  .lnk{display:inline-block;margin-top:16px;color:var(--blue);font-weight:600}

  .empty{padding:50px 20px;text-align:center;color:var(--muted)}
  footer{margin-top:22px;color:var(--muted);font-size:12.5px;line-height:1.7}

  @media (max-width:1100px){ .main{grid-template-columns:1fr} }
  @media (max-width:640px){
    .wrap{padding:16px 14px 30px} header{padding:16px 14px}
    .filters input,.filters select,#runCheck{flex:1 1 100%}
  }
</style>
</head>
<body>

<header>
  <h1>PH Dashboard <span>|</span> Buy Box Monitor</h1>
  <div class="refreshed">Last verified check: <b id="hdrDate"></b></div>
</header>

<div class="wrap">

  <div class="filters">
    <input id="q" type="search" placeholder="Search ASIN / SKU...">
    <select id="fMkt"></select>
    <select id="fCat"></select>
    <select id="fStat"></select>
    <select id="fAcct"></select>
    <button id="runCheck">Run Check</button>
  </div>

  <div class="cards">
    <div class="card"><div class="lbl">Total ASINs</div><div class="val" id="cTot">0</div></div>
    <div class="card g"><div class="lbl">Buy Box Won</div><div class="val" id="cYes">0</div></div>
    <div class="card r"><div class="lbl">Buy Box Lost</div><div class="val" id="cNo">0</div></div>
    <div class="card a"><div class="lbl">Reason Unknown</div><div class="val" id="cUnk">0</div></div>
    <div class="card n"><div class="lbl">Not Verified</div><div class="val" id="cNv">0</div></div>
  </div>

  <div class="notice" id="notice"></div>

  <div class="main">

    <div class="panel">
      <div class="tscroll">
        <table>
          <thead><tr id="hdr"></tr></thead>
          <tbody id="tb"></tbody>
        </table>
      </div>
      <div class="empty" id="empty" style="display:none">No records match the current filters.</div>
      <div class="tfoot">
        <span class="hint">Click any row &rarr; opens ASIN detail with full check evidence</span>
        <div class="pager">
          <span id="pinfo"></span>
          <button id="prev">Prev</button>
          <button id="next">Next</button>
        </div>
      </div>
    </div>

    <div>
      <div class="panel">
        <h2>Top Reasons &ndash; No Buy Box</h2>
        <div class="bars" id="bars"></div>
        <div class="exp">
          <button id="exp">[ Export to Excel ]</button>
          <div class="sub">Exports the <b id="expN">0</b> currently filtered rows as CSV (UTF-8, opens in Excel).</div>
        </div>
      </div>

      <div class="panel" style="margin-top:20px">
        <h2>Daily History</h2>
        <div class="sect" id="hist"></div>
      </div>
    </div>

  </div>

  <footer id="foot"></footer>
</div>

<div class="ovl" id="ovl"></div>
<aside class="drw" id="drw" aria-label="ASIN detail"></aside>

<script>
const PAY = __DATA__;
const P = PAY.pools, S = PAY.summary;
const R = PAY.rows;

// row field indexes
const A=0,SK=1,AC=2,MK=3,CT=4,ST=5,STK=6,LS=7,DT=8,PCT=9,SG=10,UKS=11,FBM=12,PR=13,MSK=14,PH=15,PPCT=16,CHG=17,CUR=18,FP=19,PXY=20,PXD=21;
/* v002 additions */
const PXS=22,PXRSN=23,PXSKU=24,POSS=25,CONF=26,OFFR=27;

const DOM = {UK:'amazon.co.uk', DE:'amazon.de', FR:'amazon.fr', IT:'amazon.it'};
const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const NA = '<span class="na">Not Available</span>';
const el = id => document.getElementById(id);

/* ---------- filters ---------- */
function fill(sel, label, vals){
  sel.innerHTML = '<option value="">' + label + ': All</option>' +
    vals.filter(v=>v!=='').sort().map(v=>'<option>'+esc(v)+'</option>').join('');
}
fill(el('fMkt'), 'Marketplace', P.mkt);
fill(el('fCat'), 'Category',    P.cat);
fill(el('fAcct'),'Account',     P.acct);
el('fStat').innerHTML = '<option value="">Buy Box: All</option>' +
  ['YES','NO','NOT VERIFIED'].map(v=>'<option>'+v+'</option>').join('');

/* ---------- table definition ---------- */
const COLS = [
  {k:'asin', t:'ASIN',           g:r=>r[A]},
  {k:'sku',  t:'SKU',            g:r=>r[SK]},
  {k:'bb',   t:'Buy Box',        g:r=>P.stat[r[ST]]},
  {k:'rsn',  t:'Reason',         g:r=>P.stat[r[ST]]==='NO'?(r[OFFR]||'Unknown'):''},
  {k:'poss', t:'Possible Reason',g:r=>P.stat[r[ST]]==='NO'
                                      ? (r[POSS]||[]).map(j=>P.pos[j]).join('; ') : ''},
  {k:'acct', t:'Seller / Account',g:r=>P.acct[r[AC]]},
  {k:'mkt',  t:'Marketplace',    g:r=>P.mkt[r[MK]]},
  {k:'cat',  t:'Category',       g:r=>P.cat[r[CT]]},
  {k:'stk',  t:'Stock',          g:r=>r[STK], n:true},
  {k:'ls',   t:'Listing Status', g:r=>P.lst[r[LS]]},
  {k:'dt',   t:'Last Checked',   g:r=>P.dt[r[DT]]}
];

let sortK = 'bb', sortD = 1, page = 0, view = [];
const PER = 50;

el('hdr').innerHTML = COLS.map(c=>'<th data-k="'+c.k+'">'+c.t+'<span class="ar"></span></th>').join('');

function filtered(){
  const q = el('q').value.trim().toUpperCase(),
        m = el('fMkt').value, c = el('fCat').value,
        s = el('fStat').value, a = el('fAcct').value;
  return R.filter(r =>
    (!m || P.mkt[r[MK]]   === m) &&
    (!c || P.cat[r[CT]]   === c) &&
    (!s || P.stat[r[ST]]  === s) &&
    (!a || P.acct[r[AC]]  === a) &&
    (!q || r[A].toUpperCase().indexOf(q) >= 0
        || (r[SK] && r[SK].toUpperCase().indexOf(q) >= 0)
        || (r[MSK] && r[MSK].toUpperCase().indexOf(q) >= 0))
  );
}

const RANK = {'YES':0,'NO':1,'NOT VERIFIED':2};
function sortRows(rows){
  const col = COLS.find(c=>c.k===sortK);
  return rows.slice().sort((x,y)=>{
    let a, b;
    if (sortK==='bb'){ a = RANK[P.stat[x[ST]]]; b = RANK[P.stat[y[ST]]]; }
    else { a = col.g(x); b = col.g(y); }
    if (a==null) a = col.n ? -Infinity : '';
    if (b==null) b = col.n ? -Infinity : '';
    if (typeof a === 'number' && typeof b === 'number') return (a-b)*sortD;
    return String(a).localeCompare(String(b))*sortD;
  });
}

function pillOf(st){
  const cls = st==='YES' ? 'yes' : st==='NO' ? 'no' : 'nv';
  return '<span class="pill '+cls+'">'+st+'</span>';
}

function render(){
  view = sortRows(filtered());
  const maxP = Math.max(0, Math.ceil(view.length/PER)-1);
  if (page > maxP) page = maxP;
  const slice = view.slice(page*PER, page*PER+PER);

  el('tb').innerHTML = slice.map((r,i)=>{
    const st = P.stat[r[ST]];
    const idx = page*PER+i;
    return '<tr data-i="'+idx+'">'
      + '<td class="asin">'+esc(r[A])+'</td>'
      + '<td>'+(r[SK]?esc(r[SK]):NA)+'</td>'
      + '<td>'+pillOf(st)+'</td>'
      + '<td>'+(st==='NO' ? '<span class="rsn-unknown">Unknown</span>'
                          : '<span class="na">&ndash;</span>')+'</td>'
      + '<td>'+esc(P.acct[r[AC]])+'</td>'
      + '<td>'+esc(P.mkt[r[MK]])+'</td>'
      + '<td>'+(P.cat[r[CT]]?esc(P.cat[r[CT]]):NA)+'</td>'
      + '<td class="num">'+(r[STK]==null?NA:r[STK])+'</td>'
      + '<td>'+esc(P.lst[r[LS]])+'</td>'
      + '<td>'+(P.dt[r[DT]]?esc(P.dt[r[DT]]):NA)+'</td>'
      + '</tr>';
  }).join('');

  el('empty').style.display = view.length ? 'none' : 'block';
  el('pinfo').textContent = view.length
    ? ((page*PER+1) + '-' + Math.min(view.length,(page+1)*PER) + ' of ' + view.length.toLocaleString())
    : '0 of 0';
  el('prev').disabled = page<=0;
  el('next').disabled = page>=maxP;

  document.querySelectorAll('#hdr th').forEach(th=>{
    th.querySelector('.ar').textContent = th.dataset.k===sortK ? (sortD>0?'\u25b2':'\u25bc') : '';
  });

  cards(view);
  bars(view);
  el('expN').textContent = view.length.toLocaleString();
}

/* ---------- summary cards (recompute from the filtered set) ---------- */
function cards(rows){
  let y=0,n=0,nv=0;
  rows.forEach(r=>{ const s=P.stat[r[ST]]; if(s==='YES')y++; else if(s==='NO')n++; else nv++; });
  const ver = y+n;
  const pc = v => ver ? ' <small>(' + Math.round(v/ver*100) + '%)</small>' : '';
  el('cTot').textContent = rows.length.toLocaleString();
  el('cYes').innerHTML = y.toLocaleString() + pc(y);
  el('cNo').innerHTML  = n.toLocaleString() + pc(n);
  el('cUnk').textContent = n.toLocaleString();   // every verified NO carries Reason = Unknown
  el('cNv').textContent  = nv.toLocaleString();
  el('notice').innerHTML =
    '<b>' + ver.toLocaleString() + '</b> of <b>' + rows.length.toLocaleString() +
    '</b> records have verified Buy Box ownership. The remaining <b>' + nv.toLocaleString() +
    '</b> are <b>NOT VERIFIED</b> and are excluded from the Won / Lost percentages above &mdash; ' +
    'they are never counted as YES or NO. Won / Lost percentages are shown against the ' +
    'verified base of ' + ver.toLocaleString() + '.';
}

/* ---------- reasons chart ---------- */
const PALETTE = ['#d9453d','#f0952a','#e0b400','#7b52ab','#3a7cc4'];
function bars(rows){
  const nos = rows.filter(r=>P.stat[r[ST]]==='NO');
  if (!nos.length){ el('bars').innerHTML = '<p class="hint" style="padding:8px 0">No verified Buy Box losses in the current filter.</p>'; return; }
  // Only one approved reason category exists: Unknown.
  const counts = [['Unknown', nos.length]];
  const max = counts[0][1];
  let h = counts.map((c,i)=>
      '<div class="bar"><div class="t"><span>'+esc(c[0])+'</span><b>'+c[1].toLocaleString()+'</b></div>'
    + '<div class="track"><div class="fill" style="width:'+(c[1]/max*100)+'%;background:'+PALETTE[i%5]+'"></div></div></div>'
  ).join('');
  h += '<p class="hint" style="margin:14px 0 0">Total verified losses: <b>'+nos.length.toLocaleString()+'</b>'
     + ' &mdash; reconciles with the Buy Box Lost card.</p>';

  // observed signals shown separately - these are NOT approved reasons
  const sc = {};
  nos.forEach(r=>r[SG].forEach(s=>{ const k=P.sig[s]; sc[k]=(sc[k]||0)+1; }));
  const sl = Object.entries(sc).sort((a,b)=>b[1]-a[1]);
  const none = nos.filter(r=>!r[SG].length).length;
  h += '<div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--line)">'
     + '<div style="font-weight:700;margin-bottom:4px">Observed signals on lost rows</div>'
     + '<p class="hint" style="margin:0 0 12px">Supporting evidence only &mdash; not approved reason rules.</p>';
  if (sl.length){
    const mx = sl[0][1];
    h += sl.map((c,i)=>
        '<div class="bar"><div class="t"><span>'+esc(c[0])+'</span><b>'+c[1].toLocaleString()+'</b></div>'
      + '<div class="track"><div class="fill" style="width:'+(c[1]/mx*100)+'%;background:'+PALETTE[(i+1)%5]+';opacity:.75"></div></div></div>'
    ).join('');
  }
  h += '<p class="hint" style="margin:10px 0 0">No signal found on <b>'+none.toLocaleString()+'</b> lost rows '
     + '(listing active and in stock) &mdash; cause is outside the available data.</p></div>';
  el('bars').innerHTML = h;
}

/* ---------- daily history ---------- */
(function(){
  const t = PAY.trend;
  if (!t || !t.length){ el('hist').innerHTML = '<p class="hint">History data has not yet been established.</p>'; return; }
  el('hist').innerHTML =
      '<p class="hint" style="margin:0 0 12px">No automation run history exists yet &mdash; this is the first build. '
    + 'The trend below is the real daily Buy Box reading from the Amazon Sales &amp; Traffic report '
    + '(all PH Amazon accounts and marketplaces).</p>'
    + '<table><thead><tr><th>Check date</th><th class="num">Won</th><th class="num">Lost</th>'
    + '<th class="num">Partial</th><th class="num">Measured</th></tr></thead><tbody>'
    + t.slice().reverse().map(d=>'<tr><td>'+esc(d.date)+'</td>'
        + '<td class="num" style="color:var(--green);font-weight:600">'+d.won.toLocaleString()+'</td>'
        + '<td class="num" style="color:var(--red);font-weight:600">'+d.lost.toLocaleString()+'</td>'
        + '<td class="num">'+d.partial.toLocaleString()+'</td>'
        + '<td class="num">'+d.total.toLocaleString()+'</td></tr>').join('')
    + '</tbody></table>';
})();

/* ---------- detail drawer ---------- */
function openRow(i){
  const r = view[i]; if (!r) return;
  const st = P.stat[r[ST]], pct = r[PCT], dte = P.dt[r[DT]];
  let basis;
  if (st==='YES')      basis = 'Buy Box held for 100% of page views on ' + dte + '.';
  else if (st==='NO')  basis = 'Buy Box held for 0% of page views on ' + dte + '.';
  else if (pct!=null)  basis = 'Split ownership &mdash; ' + pct + '% of page views on ' + dte
                             + '. No approved threshold exists to call this YES or NO.';
  else                 basis = 'No Buy Box report row within ' + S.window_days + ' days of '
                             + S.max_report_date + '. Ownership is unknown.';

  const row = (k,v) => '<dt>'+k+'</dt><dd>'+(v==null||v===''?NA:v)+'</dd>';
  let h = '<button class="cls" id="x">&times;</button>'
    + '<h3>'+esc(r[A])+'</h3><div style="color:var(--muted)">'+esc(P.acct[r[AC]])+' &middot; '+esc(P.mkt[r[MK]])+'</div>'
    + '<div style="margin-top:14px">'+pillOf(st)+'</div>'
    + '<dl class="kv">'
    + row('SKU', esc(r[SK])) + row('Mapped SKU', esc(r[MSK])) + row('Category', esc(P.cat[r[CT]]))
    + row('PH owner', esc(P.phn[r[PH]]))
    + row('Buy Box %', pct==null ? null : pct + '%')
    + row('Reason', st==='NO' ? '<span class="rsn-unknown">Unknown</span>' : '&ndash;')
    + row('Stock (listing qty)', r[STK])
    + row('Warehouse UK / FBM', (r[UKS]==null?'-':r[UKS]) + ' / ' + (r[FBM]==null?'-':r[FBM]))
    + row('Listing status', esc(P.lst[r[LS]]))
    + row('Price', r[PR]==null ? null : esc(r[CUR])+' '+r[PR])
    + row('Last checked', esc(dte))
    + '</dl>'
    + '<div class="evid"><h4>Ownership evidence</h4>' + basis;

  if (r[PPCT]!=null)
    h += '<p style="margin:10px 0 0">Previous reading: <b>'+r[PPCT]+'%</b>'
       + (P.chg[r[CHG]] ? ' &mdash; ' + esc(P.chg[r[CHG]]) : '') + '</p>';

  h += '</div>';

  /* ---- v002: price comparison, only when defensible ---- */
  if (r[PXS]==='available' && r[FP]!=null && r[PXY]!=null){
    var above = r[PXY] > r[FP];
    var diff  = Math.round((r[PXY] - r[FP]) * 100) / 100;
    h += '<div class="evid"><h4>Featured-offer price comparison</h4>'
       + '<dl class="kv">'
       + row('Our offer price', esc(r[CUR]) + ' ' + r[PXY].toFixed(2)
             + ' <span class="hint">(SKU ' + esc(r[PXSKU]) + ')</span>')
       + row('Featured offer price', esc(r[CUR]) + ' ' + r[FP].toFixed(2))
       + row('Price difference', (diff>0?'+':'') + diff.toFixed(2) + ' ' + esc(r[CUR]))
       + row('Featured offer seller', NA + ' <span class="hint">&mdash; no authorized '
             + 'source supplies the featured seller</span>')
       + row('Our seller account', esc(P.acct[r[AC]])
             + ' <span class="hint">(display name; no verified seller ID)</span>')
       + '</dl>'
       + '<div style="margin-top:8px"><b style="color:'
       + (above ? 'var(--red)' : 'var(--green)') + '">'
       + (above ? 'We are priced ABOVE the featured offer'
                : 'We are priced at or BELOW the featured offer') + '</b>.</div>'
       + '<p class="hint" style="margin:8px 0 0">Source: '
       + '<code>ledsone.amazon_fba.excess_inventory_data</code>, snapshot '
       + esc(P.dt[r[PXD]]) + ' &mdash; the same date as the Buy Box reading. Both figures '
       + 'come from the same source row. Evidence only, not a classified reason.</p></div>';
  } else if (r[PXS]==='unavailable'){
    h += '<div class="evid"><h4>Featured-offer price comparison</h4>'
       + '<div><b>Price comparison unavailable.</b></div>'
       + '<p class="hint" style="margin:8px 0 0">' + esc(P.pxr[r[PXRSN]]) + '</p>'
       + '<p class="hint" style="margin:6px 0 0">The Price column above is the PH listing '
       + 'price, which is a different figure from the offer price used in a comparison. '
       + 'No comparison is shown rather than an unsupported one.</p></div>';
  } else {
    h += '<div class="evid"><h4>Featured-offer price comparison</h4>'
       + '<div><b>Price comparison unavailable.</b></div>'
       + '<p class="hint" style="margin:8px 0 0">This ASIN is not covered by the FBA Excess '
       + 'Inventory report, which is the only featured-offer price source available '
       + '(3.8% of the estate).</p></div>';
  }

  if (st==='NO'){
    var poss = (r[POSS]||[]).map(j=>P.pos[j]);
    h += '<div class="evid"><h4>Reason investigation</h4><dl class="kv">'
       + row('Official reason', '<span class="rsn-unknown">' + esc(r[OFFR]||'Unknown') + '</span>')
       + row('Possible reason', poss.length
             ? '<ul style="margin:0;padding-left:18px">'
               + poss.map(p=>'<li>'+esc(p)+'</li>').join('') + '</ul>' : null)
       + row('Confidence / limitations', esc(P.conf[r[CONF]]))
       + row('Evidence source',
             '<code>amz_sales_and_traffic_by_asin.buy_box_percentage</code>'
             + (r[PXS]==='available' ? ', <code>amazon_fba.excess_inventory_data</code>' : '')
             + ', <code>listings.amazon_listings</code>')
       + row('Extraction status', 'Snapshot &mdash; no live listing check')
       + row('Checked at', esc(dte) + ' <span class="hint">(Buy Box report date)</span>')
       + '</dl></div>';
    h += '<div class="warnbox"><b>Official reason is Unknown.</b> The requirement refers to '
       + '"checks 1 to 8" but that checklist is not defined anywhere in the specification, so no '
       + 'approved reason rule exists to apply. Possible reasons above are evidence-backed '
       + 'hypotheses, not Amazon\'s decision &mdash; a public product page does not reveal why '
       + 'Amazon awarded the Featured Offer.';
    if (r[SG].length)
      h += '<div style="margin-top:8px">Observed signals (evidence only):'
         + '<ul>' + r[SG].map(s=>'<li>'+esc(P.sig[s])+'</li>').join('') + '</ul></div>';
    h += '<div style="margin-top:8px"><b>Evidence gaps</b> &mdash; no source exists for: '
       + 'seller account matching (no merchant token anywhere), Prime / fulfilment eligibility, '
       + 'competing seller offers (needs a live read; Amazon automated access is blocked), '
       + 'and account or listing eligibility.</div>';
    h += '</div>';
  }

  h += '<a class="lnk" target="_blank" rel="noopener" href="https://www.'
     + DOM[P.mkt[r[MK]]] + '/gp/product/' + encodeURIComponent(r[A]) + '">Open on Amazon &rarr;</a>';

  el('drw').innerHTML = h;
  el('drw').classList.add('on'); el('ovl').classList.add('on');
  el('x').onclick = close;
}
function close(){ el('drw').classList.remove('on'); el('ovl').classList.remove('on'); }
el('ovl').onclick = close;
document.addEventListener('keydown', e=>{ if(e.key==='Escape') close(); });

/* ---------- CSV export (UTF-8 BOM so Excel reads it correctly) ---------- */
el('exp').onclick = function(){
  const head = COLS.map(c=>c.t).concat(['Buy Box %','Observed signals','Evidence basis']);
  const q = v => { v = (v==null?'':String(v)); return '"' + v.split('"').join('""') + '"'; };
  const lines = [head.map(q).join(',')];
  view.forEach(r=>{
    const st = P.stat[r[ST]], dte = P.dt[r[DT]];
    let basis;
    if (st==='YES')     basis = 'Buy Box held for 100% of page views on ' + dte;
    else if (st==='NO') basis = 'Buy Box held for 0% of page views on ' + dte;
    else if (r[PCT]!=null) basis = 'Split ownership ' + r[PCT] + '% on ' + dte + ' - no approved threshold';
    else                basis = 'No Buy Box report row within ' + S.window_days + ' days of ' + S.max_report_date;
    lines.push(COLS.map(c=>q(c.g(r))).concat([
      q(r[PCT]), q(r[SG].map(s=>P.sig[s]).join(' | ')), q(basis)
    ]).join(','));
  });
  const blob = new Blob(['\ufeff' + lines.join('\r\n')], {type:'text/csv;charset=utf-8;'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'buy_box_monitor_' + S.max_report_date + '_filtered.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
};

/* ---------- Run Check ---------- */
el('runCheck').onclick = function(){
  alert(
    'Run Check is not connected to a live checking service.\n\n' +
    'This is a standalone offline HTML file. Running a real check needs either:\n' +
    '  - the Amazon SP-API (live featured-offer ownership), or\n' +
    '  - a backend that re-queries the PostgreSQL sources.\n\n' +
    'Neither is available to this file, so no status, reason or timestamp has been changed.\n\n' +
    'Status as at this build: no SP-API integration exists in the estate, and browser-based\n' +
    'checking is currently blocked by an Amazon automated-access control.\n\n' +
    'The data shown is the verified snapshot described in the footer.'
  );
};

/* ---------- events ---------- */
['q','fMkt','fCat','fStat','fAcct'].forEach(id=>{
  el(id).addEventListener(id==='q'?'input':'change', ()=>{ page=0; render(); });
});
el('prev').onclick = ()=>{ if(page>0){ page--; render(); window.scrollTo({top:0,behavior:'smooth'}); } };
el('next').onclick = ()=>{ page++; render(); window.scrollTo({top:0,behavior:'smooth'}); };
el('hdr').addEventListener('click', e=>{
  const th = e.target.closest('th'); if(!th) return;
  if (sortK === th.dataset.k) sortD = -sortD; else { sortK = th.dataset.k; sortD = 1; }
  page = 0; render();
});
el('tb').addEventListener('click', e=>{
  const tr = e.target.closest('tr'); if(tr) openRow(+tr.dataset.i);
});

/* ---------- boot ---------- */
el('hdrDate').textContent = S.latest_checked || 'not available';
el('foot').innerHTML =
    '<b>Data sources</b> &mdash; Buy Box: <code>ledsone.business_reports.amz_sales_and_traffic_by_asin</code> '
  + '(Amazon Sales &amp; Traffic, buy_box_percentage). ASIN list, SKU, stock, category: '
  + '<code>ph_dashboard.public.analytics_overallasinlisting</code> + <code>ph_allocation_*</code>. '
  + 'Listing status: <code>ledsone.listings.amazon_listings</code>.<br>'
  + '<b>Snapshot</b> &mdash; PH listing snapshot ' + esc(S.snapshot_at ? S.snapshot_at.slice(0,16).replace('T',' ') : '')
  + '; latest Buy Box report date ' + esc(S.max_report_date)
  + '; readings taken from the most recent report row within ' + S.window_days + ' days; built ' + esc(S.built_at.replace('T',' ')) + '.<br>'
  + '<b>Grain</b> &mdash; one row per ASIN &times; seller account &times; marketplace ('
  + S.total.toLocaleString() + ' rows, uniqueness asserted at build time).<br>'
  + '<b>Scope</b> &mdash; Amazon only (UK, DE, FR, IT) for accounts LEDSone and DCVoltage, per the requirement input table.<br>'
  + '<b>Result type</b> &mdash; every row is a <b>historical snapshot</b> from the Amazon Sales &amp; Traffic report. '
  + 'No row is a verified live listing check: there is no SP-API integration, and browser-based checking is currently '
  + 'blocked by an Amazon automated-access control.<br>'
  + '<b>v002 price correction</b> &mdash; the featured-offer comparison is drawn from a single source row '
  + '(same SKU, same snapshot date as the Buy Box reading, non-zero, unambiguous, currency-matched). '
  + 'Where those conditions fail the comparison is suppressed and shown as <i>Price comparison unavailable</i> with its reason. '
  + S.px_available.toLocaleString() + ' comparisons are shown; ' + S.px_unavailable.toLocaleString() + ' are suppressed. '
  + 'The Price column is the PH listing price and is a different figure from the offer price used in a comparison.';

render();
</script>
</body>
</html>
'''

html = TPL.replace('__DATA__', json.dumps(payload, separators=(',', ':')))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print('wrote', OUT)
print('size: %.2f MB' % (len(html.encode('utf-8')) / 1048576))
print('rows embedded:', len(data))
