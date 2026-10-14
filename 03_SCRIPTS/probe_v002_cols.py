import io, os, re, json, subprocess, tempfile, html as H
BS = chr(92)
SRC = os.path.join(r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\05_OUTPUT',
                   '2026-10-14_tharsi_buy_box_monitor_v002.html')
TEST = """
<pre id="RESULTS"></pre><script>
var o=[];
function setF(id,v){var e=el(id);e.value=v;e.dispatchEvent(new Event(id==='q'?'input':'change'));}
setF('fMkt','UK');
var rows=document.querySelectorAll('#tb tr');
o.push({visible_rows:rows.length, selValue:el('fMkt').value,
        c4:rows[0]?rows[0].children[4].textContent.trim():null,
        c5:rows[0]?rows[0].children[5].textContent.trim():null,
        c6:rows[0]?rows[0].children[6].textContent.trim():null,
        every_on_c5:Array.prototype.every.call(rows,function(t){return t.children[5].textContent.trim()==='UK';}),
        every_on_c6:Array.prototype.every.call(rows,function(t){return t.children[6].textContent.trim()==='UK';})});
document.getElementById('RESULTS').textContent=JSON.stringify(o);
</script>"""
s = io.open(SRC, encoding='utf-8').read().replace('</body>', TEST + '</body>')
tmp = os.path.join(tempfile.gettempdir(), 'v002_probe.html')
io.open(tmp, 'w', encoding='utf-8').write(s)
url = 'file:///' + tmp.replace(BS, '/').replace(' ', '%20')
dom = subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe', '--headless=new',
                      '--disable-gpu', '--no-sandbox', '--virtual-time-budget=20000', '--dump-dom', url],
                     capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180).stdout
m = re.search(r'<pre id="RESULTS">(.*?)</pre>', dom, re.S)
print(json.loads(H.unescape(m.group(1))) if m and m.group(1).strip() else 'no result')
