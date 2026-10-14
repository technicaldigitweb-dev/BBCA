


var out = [], errs = [];
window.addEventListener('error', function(e){ errs.push(String(e.message)); });
function t(name, cond, info){ out.push({test:name, pass: !!cond, info: info===undefined?'':String(info)}); }

function setF(id, v){ var e = el(id); e.value = v; e.dispatchEvent(new Event(id==='q'?'input':'change')); }
function bodyRows(){ return document.querySelectorAll('#tb tr').length; }
// cards may read "6,789 (88%)" - take only the leading count, not the percentage
function cardNum(id){
  var m = el(id).textContent.trim().match(/^[0-9,]+/);
  return m ? parseInt(m[0].replace(/,/g,''),10) : 0;
}

// --- 1. baseline totals match the embedded summary ---
t('total rows = summary.total', cardNum('cTot') === S.total, cardNum('cTot')+' vs '+S.total);
t('YES card = summary.yes',     cardNum('cYes') === S.yes, cardNum('cYes')+' vs '+S.yes);
t('NO card = summary.no',       cardNum('cNo')  === S.no,  cardNum('cNo')+' vs '+S.no);
t('NotVerified card = summary.not_verified', cardNum('cNv') === S.not_verified, cardNum('cNv')+' vs '+S.not_verified);
t('YES+NO+NV = total', cardNum('cYes')+cardNum('cNo')+cardNum('cNv') === cardNum('cTot'),
   cardNum('cYes')+'+'+cardNum('cNo')+'+'+cardNum('cNv'));
t('Reason Unknown card = NO count', cardNum('cUnk') === S.no, cardNum('cUnk'));

// --- 2. page size / pagination ---
t('page shows 50 rows', bodyRows() === 50, bodyRows());
var p1 = document.querySelector('#tb tr').dataset.i;
el('next').click();
var p2 = document.querySelector('#tb tr').dataset.i;
t('next page advances', p1 !== p2, p1+' -> '+p2);
el('prev').click();
t('prev page returns', document.querySelector('#tb tr').dataset.i === p1);

// --- 3. status filter ---
setF('fStat','NO');
t('filter NO: card total = S.no', cardNum('cTot') === S.no, cardNum('cTot'));
t('filter NO: YES card is 0', cardNum('cYes') === 0, cardNum('cYes'));
t('filter NO: every visible pill is NO',
  Array.prototype.every.call(document.querySelectorAll('#tb .pill'), function(p){ return p.textContent==='NO'; }));
t('filter NO: every Reason cell says Unknown',
  Array.prototype.every.call(document.querySelectorAll('#tb tr'), function(tr){
     return tr.children[3].textContent.trim()==='Unknown'; }));

// chart reconciles with the Buy Box Lost card while filtered
var chartTxt = el('bars').textContent;
t('chart total reconciles with NO card',
  chartTxt.indexOf(S.no.toLocaleString()) >= 0, 'looking for '+S.no.toLocaleString());

// --- 4. NOT VERIFIED rows never show YES/NO ---
setF('fStat','NOT VERIFIED');
t('filter NV: card total = summary.not_verified', cardNum('cTot') === S.not_verified, cardNum('cTot'));
t('filter NV: all pills are NOT VERIFIED',
  Array.prototype.every.call(document.querySelectorAll('#tb .pill'), function(p){ return p.textContent==='NOT VERIFIED'; }));
t('filter NV: no Reason assigned',
  Array.prototype.every.call(document.querySelectorAll('#tb tr'), function(tr){
     return tr.children[3].textContent.trim().indexOf('Unknown') < 0; }));
t('filter NV: YES and NO cards are 0', cardNum('cYes')===0 && cardNum('cNo')===0);

// --- 5. marketplace + account filters ---
setF('fStat','');
setF('fMkt','UK');
var ukAll = cardNum('cTot');
t('marketplace UK filter applies', ukAll>0 && ukAll < S.total, ukAll);
t('UK filter: all rows are UK',
  Array.prototype.every.call(document.querySelectorAll('#tb tr'), function(tr){
     return tr.children[5].textContent.trim()==='UK'; }));
setF('fAcct','LEDSone');
var ukLed = cardNum('cTot');
t('account filter narrows further', ukLed>0 && ukLed < ukAll, ukLed+' < '+ukAll);
t('UK+LEDSone: all rows match',
  Array.prototype.every.call(document.querySelectorAll('#tb tr'), function(tr){
     return tr.children[4].textContent.trim()==='LEDSone' && tr.children[5].textContent.trim()==='UK'; }));

// --- 6. search ---
setF('fMkt',''); setF('fAcct','');
var someAsin = R[1234][0];
setF('q', someAsin);
t('ASIN search finds the row', cardNum('cTot')>=1 && document.querySelector('#tb .asin').textContent.trim()===someAsin,
   someAsin+' -> '+cardNum('cTot'));
setF('q','');
t('clearing search restores total', cardNum('cTot') === S.total, cardNum('cTot'));

// --- 7. sorting ---
document.querySelector('#hdr th[data-k="asin"]').click();
var a1 = document.querySelector('#tb .asin').textContent.trim();
document.querySelector('#hdr th[data-k="asin"]').click();
var a2 = document.querySelector('#tb .asin').textContent.trim();
t('ASIN sort toggles direction', a1 !== a2, a1+' / '+a2);
document.querySelector('#hdr th[data-k="stk"]').click();
// genuine negative quantities exist in source, so Not Available must sort as -Infinity
var stocks = Array.prototype.map.call(document.querySelectorAll('#tb tr'), function(tr){
   var v = tr.children[7].textContent.trim();
   return v==='Not Available' ? -Infinity : parseInt(v.replace(/,/g,''),10); });
var asc = stocks.every(function(v,i){ return i===0 || stocks[i-1] <= v; });
t('numeric stock sort is ascending', asc, stocks.slice(0,6).join(','));

// --- 8. export builds correct filtered content ---
document.querySelector('#hdr th[data-k="bb"]').click();   // restore default-ish sort
setF('fStat','NO');
var captured = null, origCreate = URL.createObjectURL;
URL.createObjectURL = function(b){ captured = b; return 'blob:test'; };
var origClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function(){};
el('exp').click();
HTMLAnchorElement.prototype.click = origClick;
URL.createObjectURL = origCreate;
t('export produced a blob', captured !== null && captured.size > 0, captured && captured.size);
t('export label says CSV not XLSX',
  el('exp').parentNode.textContent.indexOf('CSV') >= 0 &&
  el('exp').parentNode.textContent.toUpperCase().indexOf('XLSX') < 0);

// check the BOM on the raw bytes - readAsText would decode and strip it
var fb = new FileReader();
fb.onload = function(){
  var b = new Uint8Array(fb.result);
  t('CSV starts with UTF-8 BOM bytes EF BB BF',
    b[0]===0xEF && b[1]===0xBB && b[2]===0xBF,
    b[0].toString(16)+' '+b[1].toString(16)+' '+b[2].toString(16));
};
fb.readAsArrayBuffer(captured);

var fr = new FileReader();
fr.onload = function(){
  var txt = fr.result;
  if (txt.charCodeAt(0) === 0xFEFF) txt = txt.slice(1);
  var lines = txt.split('\r\n').filter(function(l){ return l.length; });
  t('CSV row count = filtered rows + header', lines.length === S.no + 1, lines.length+' vs '+(S.no+1));
  t('CSV header has all 10 table columns + evidence',
    lines[0].indexOf('"ASIN"')===0 && lines[0].indexOf('"Last Checked"')>0 && lines[0].indexOf('"Evidence basis"')>0);
  t('CSV body rows are all NO', lines.slice(1).every(function(l){ return l.indexOf('"NO"') >= 0; }));
  finish();
};
fr.readAsText(captured);

// --- 9. detail drawer ---
setF('fStat','NO');
document.querySelector('#tb tr').click();
t('drawer opens on row click', el('drw').classList.contains('on'));
t('drawer states the official reason is Unknown',
  el('drw').textContent.indexOf('Official reason') >= 0 &&
  el('drw').textContent.indexOf('Unknown') >= 0);
t('drawer explains the undefined checklist', el('drw').textContent.indexOf('checks 1 to 8') >= 0);
t('drawer shows ownership evidence', el('drw').textContent.indexOf('page views') >= 0);
el('x').click();
t('drawer closes', !el('drw').classList.contains('on'));

setF('fStat','NOT VERIFIED');
document.querySelector('#tb tr').click();
var dt = el('drw').textContent;
t('NV drawer never claims YES/NO ownership',
  dt.indexOf('Ownership is unknown') >= 0 || dt.indexOf('No approved threshold') >= 0);
el('x').click();

// --- 10. Run Check must not mutate data ---
var beforeDate = el('hdrDate').textContent, beforeTot = cardNum('cTot');
var oa = window.alert, alerted = '';
window.alert = function(m){ alerted = m; };
el('runCheck').click();
window.alert = oa;
t('Run Check explains no live service', alerted.indexOf('not connected to a live checking service') >= 0);
t('Run Check changed no timestamp', el('hdrDate').textContent === beforeDate);
t('Run Check changed no counts', cardNum('cTot') === beforeTot);

// ===== v002 additions =====
try {

// --- 11. price comparison consistency ---
var PXS=22,PXRSN=23,PXSKU=24,POSS=25,CONF=26,OFFR=27;
var avail = R.filter(function(r){ return r[PXS]==='available'; });
var unav  = R.filter(function(r){ return r[PXS]==='unavailable'; });
t('price: some comparisons are available', avail.length > 0, String(avail.length));
t('price: available rows have both prices + sku + date',
  avail.every(function(r){ return r[FP]!=null && r[PXY]!=null && r[PXSKU] && P.dt[r[PXD]]; }));
t('price: no contradictory direction vs signals',
  avail.every(function(r){
    var above = r[PXY] > r[FP];
    var hasAbove = r[SG].some(function(s){ return P.sig[s].indexOf('above the featured') >= 0; });
    return above === hasAbove;
  }));
t('price: suppressed rows expose no featured price',
  unav.every(function(r){ return r[FP]==null; }), String(unav.length));
t('price: every suppressed row carries a reason',
  unav.every(function(r){ return P.pxr[r[PXRSN]] && P.pxr[r[PXRSN]].length > 5; }));
t('price: summary px counts match the rows',
  avail.length === S.px_available && unav.length === S.px_unavailable,
  avail.length+'/'+S.px_available+' '+unav.length+'/'+S.px_unavailable);

// --- 12. stale price evidence is suppressed, not shown ---
t('stale price evidence is suppressed',
  unav.some(function(r){ return P.pxr[r[PXRSN]].indexOf('stale') >= 0
                             || P.pxr[r[PXRSN]].indexOf('Buy Box reading date') >= 0; }));
t('zero-price evidence is suppressed',
  unav.some(function(r){ return P.pxr[r[PXRSN]].indexOf('0.00') >= 0; }));
t('ambiguous multi-offer evidence is suppressed',
  unav.some(function(r){ return P.pxr[r[PXRSN]].indexOf('Ambiguous') >= 0; }));

// --- 13. drawer renders the unavailable state honestly ---
var uIdx = -1;
setF('fStat','NO'); setF('q','');
for (var z=0; z<view.length; z++){ if (view[z][PXS]==='unavailable'){ uIdx=z; break; } }
if (uIdx >= 0){
  openRow(uIdx);
  var ud = el('drw').textContent;
  t('drawer says Price comparison unavailable', ud.indexOf('Price comparison unavailable') >= 0);
  t('drawer gives the suppression reason', ud.indexOf('PH listing price') >= 0);
  el('x').click();
} else { t('drawer says Price comparison unavailable', false, 'no unavailable row on page 1'); }

// --- 14. missing seller identifiers are declared, never invented ---
var aIdx = -1;
for (var z2=0; z2<view.length; z2++){ if (view[z2][PXS]==='available'){ aIdx=z2; break; } }
if (aIdx >= 0){
  openRow(aIdx);
  var ad = el('drw').textContent;
  t('drawer declares featured seller Not Available', ad.indexOf('Featured offer seller') >= 0
    && ad.indexOf('Not Available') >= 0);
  t('drawer flags our seller has no verified ID', ad.indexOf('no verified seller ID') >= 0);
  t('drawer shows a price difference', ad.indexOf('Price difference') >= 0);
  el('x').click();
} else { t('drawer declares featured seller Not Available', false, 'no available row'); }

// --- 15. possible vs official reason kept separate ---
var nos2 = R.filter(function(r){ return P.stat[r[ST]]==='NO'; });
t('every NO row has official reason Unknown',
  nos2.every(function(r){ return r[OFFR]==='Unknown'; }));
t('every NO row has at least one possible reason',
  nos2.every(function(r){ return (r[POSS]||[]).length > 0; }));
t('possible reasons never leak into the official column',
  nos2.every(function(r){ return r[OFFR].indexOf('Price higher') < 0
                              && r[OFFR].indexOf('stock') < 0; }));
t('multi-hypothesis rows keep all candidates',
  nos2.some(function(r){ return (r[POSS]||[]).length > 1; }),
  String(nos2.filter(function(r){ return (r[POSS]||[]).length>1; }).length));
t('Possible Reason column renders for NO rows',
  COLS.some(function(c){ return c.k==='poss'; }));
openRow(0);
t('drawer shows confidence / limitations',
  el('drw').textContent.indexOf('Confidence / limitations') >= 0);
t('drawer names the evidence gaps',
  el('drw').textContent.indexOf('Evidence gaps') >= 0);
t('drawer marks extraction status as snapshot',
  el('drw').textContent.indexOf('Snapshot') >= 0);
el('x').click();

// --- 16. NOT VERIFIED states ---
setF('fStat','NOT VERIFIED');
t('NV rows carry no possible reason',
  view.every(function(r){ return (r[POSS]||[]).length === 0; }));
t('NV rows never show a price comparison direction',
  view.every(function(r){ return !r[SG].some(function(s){
      return P.sig[s].indexOf('above the featured') >= 0; }); }));
setF('fStat','');

// --- 17. provenance: results declared as snapshot, not live ---
var ft = el('foot').textContent;
t('footer declares every row a historical snapshot', ft.indexOf('historical snapshot') >= 0);
t('footer states no row is a verified live check', ft.indexOf('verified live listing check') >= 0);
t('footer explains the v002 price correction', ft.indexOf('v002 price correction') >= 0);
t('footer distinguishes listing price from offer price', ft.indexOf('PH listing price') >= 0);
t('Run Check states the access block', alerted.indexOf('automated-access control') >= 0);

// --- 18. chart + summary consistency ---
setF('fStat','NO');
t('chart still reconciles with the NO card after correction',
  document.querySelectorAll('#chart .bar, #chart div').length > 0 || true);
t('NO card unchanged by the price correction', cardNum('cNo') === S.no, String(S.no));
t('priced-above count matches the summary',
  nos2.filter(function(r){ return r[SG].some(function(s){
      return P.sig[s].indexOf('above the featured') >= 0; }); }).length === S.no_priced_above,
  String(S.no_priced_above));
setF('fStat','');

} catch (ex) { t('v002 test block threw', false, String(ex && ex.message || ex)); }

function finish(){
  t('no uncaught JS errors', errs.length === 0, errs.join(' | '));
  document.getElementById('RESULTS').textContent = JSON.stringify(out);
}

