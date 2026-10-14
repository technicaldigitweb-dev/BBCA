"""Functional test: loads the generated dashboard in headless Chrome with an injected
test script, exercises filters / sorting / pagination / export / drawer, and reports PASS/FAIL.
Writes results into a <pre id="RESULTS"> that we read back via --dump-dom.
"""
import os, re, json, subprocess, tempfile, html as htmlmod

SRC = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\05_OUTPUT\2026-10-14_tharsi_buy_box_monitor_v001.html'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

TEST = r'''
<pre id="RESULTS"></pre>
<script>
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
t('drawer states Reason = Unknown', el('drw').textContent.indexOf('Reason = Unknown') >= 0);
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

function finish(){
  t('no uncaught JS errors', errs.length === 0, errs.join(' | '));
  document.getElementById('RESULTS').textContent = JSON.stringify(out);
}
</script>
'''


def main():
    src = open(SRC, encoding='utf-8').read()
    test_html = src.replace('</body>', TEST + '</body>')
    tmp = os.path.join(tempfile.gettempdir(), 'bb_test.html')
    open(tmp, 'w', encoding='utf-8').write(test_html)

    dom = subprocess.run(
        [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
         '--virtual-time-budget=20000', '--dump-dom',
         'file:///' + tmp.replace('\\', '/').replace(' ', '%20')],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180).stdout

    m = re.search(r'<pre id="RESULTS">(.*?)</pre>', dom, re.S)
    if not m or not m.group(1).strip():
        print('FAILED to capture results'); return 1
    res = json.loads(htmlmod.unescape(m.group(1)))

    npass = sum(r['pass'] for r in res)
    for r in res:
        print(('  PASS  ' if r['pass'] else '  FAIL  ') + r['test'] + (('   [' + r['info'] + ']') if r['info'] else ''))
    print('\n%d/%d passed' % (npass, len(res)))
    json.dump(res, open(r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA\test_results.json', 'w'), indent=1)
    return 0 if npass == len(res) else 1


if __name__ == '__main__':
    raise SystemExit(main())
