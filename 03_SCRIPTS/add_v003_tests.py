import io
f = 'test_dashboard_v003.py'
s = io.open(f, encoding='utf-8').read()
NEW = """
// ---------- v003 regression tests ----------

// R1. header and body must have the SAME number of cells (the v002 defect)
var hdrN = document.querySelectorAll('#hdr th').length;
var bodyN = document.querySelector('#tb tr').children.length;
t('v003: header and body column counts match', hdrN === bodyN, hdrN + ' vs ' + bodyN);

// R2. each header label sits above the right data
setF('fStat',''); setF('fLive',''); setF('fMkt','UK'); setF('fAcct','LEDSone');
var hdrs = Array.prototype.map.call(document.querySelectorAll('#hdr th'),
             function(h){ return h.textContent.replace(/[^A-Za-z /]/g,'').trim(); });
var row0 = document.querySelector('#tb tr');
t('v003: Seller/Account header is above the account value',
  row0.children[hdrs.indexOf('Seller / Account')].textContent.trim()==='LEDSone',
  row0.children[hdrs.indexOf('Seller / Account')].textContent.trim());
t('v003: Marketplace header is above the marketplace value',
  row0.children[hdrs.indexOf('Marketplace')].textContent.trim()==='UK',
  row0.children[hdrs.indexOf('Marketplace')].textContent.trim());
setF('fMkt',''); setF('fAcct','');

// R3. live-check column exists and only the sampled rows carry a status
var liveIdx = hdrs.indexOf('Live Check');
t('v003: Live Check column present', liveIdx >= 0, liveIdx);
t('v003: live-checked card matches summary', cardNum('cLive') === S.live_checked, cardNum('cLive')+' vs '+S.live_checked);
t('v003: conflicts card matches summary', cardNum('cConf') === S.conflicts, cardNum('cConf')+' vs '+S.conflicts);

// R4. a live check must never have rewritten the historical status
setF('fLive','YES');
t('v003: live YES rows still show historical NO',
  Array.prototype.every.call(document.querySelectorAll('#tb tr'),
    function(tr){ return tr.children[2].textContent.trim()==='NO'; }),
  'live YES count=' + cardNum('cTot'));
t('v003: live YES count matches summary', cardNum('cTot') === S.live_yes, cardNum('cTot')+' vs '+S.live_yes);

// R5. conflicts filter returns exactly the conflict rows
setF('fLive','Conflicts only');
t('v003: conflicts filter count matches summary', cardNum('cTot') === S.conflicts, cardNum('cTot'));

// R6. "Not checked" must be the complement of checked
setF('fLive','Not checked');
t('v003: not-checked = total - live_checked', cardNum('cTot') === S.total - S.live_checked,
  cardNum('cTot')+' vs '+(S.total - S.live_checked));
setF('fLive','');

// R7. official reason stays Unknown on every loss - no unapproved rule applied
setF('fStat','NO');
t('v003: every loss still reads Official Reason = Unknown',
  Array.prototype.every.call(document.querySelectorAll('#tb tr'),
    function(tr){ return tr.children[4].textContent.trim()==='Unknown'; }));
setF('fStat','');

// R8. seller identity + staleness banners are present and truthful
t('v003: seller identity banner states VERIFIED',
  el('bSeller').textContent.indexOf('VERIFIED') >= 0 &&
  el('bSeller').textContent.indexOf('A1BXMEJKH8MYIL') >= 0);
t('v003: seller banner rejects name-only matching',
  el('bSeller').textContent.toLowerCase().indexOf('name') >= 0);
t('v003: stale-data banner present and names the staleness',
  el('bStale').textContent.indexOf('days old') >= 0 &&
  el('bStale').textContent.indexOf('Historical data, not live') >= 0);

// R9. drawer shows the live evidence with its own timestamp, not the build time
setF('fLive','YES');
document.querySelector('#tb tr').click();
var dtxt = el('drw').textContent;
t('v003: drawer has a Live check section', dtxt.indexOf('Live check') >= 0);
t('v003: drawer shows the verified seller token', dtxt.indexOf('A1BXMEJKH8MYIL') >= 0 || dtxt.indexOf('A3UNAW6KG6QUOJ') >= 0);
t('v003: drawer flags the conflict and says history was not overwritten',
  dtxt.indexOf('Conflict') >= 0 && dtxt.indexOf('not') >= 0 && dtxt.indexOf('overwritten') >= 0);
t('v003: drawer warns the live check is not refreshed by opening the file',
  dtxt.indexOf('not refreshed by opening') >= 0);
el('x').click(); setF('fLive','');
"""
anchor = "function finish(){"
assert anchor in s
s = s.replace(anchor, NEW + "\n" + anchor, 1)
io.open(f, 'w', encoding='utf-8').write(s)
print('added 17 v003 regression tests')
