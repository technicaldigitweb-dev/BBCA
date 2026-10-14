"""For every historical NO row, find the newest report row available NOW and compare."""
import os, json, psycopg
from collections import Counter
D = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
rows = json.load(open(os.path.join(D,'dashboard_rows_v002.json'), encoding='utf-8'))
SS={'LEDSone':8,'DCVoltage':6}; MP={'UK':23,'DE':10,'FR':9,'IT':14}
nos=[r for r in rows if r['status']=='NO']
keys={(r['asin'],SS[r['account']],MP[r['marketplace']]):r for r in nos}

with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=30) as c, c.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    cur.execute("""
      SELECT DISTINCT ON (child_asin, sub_source, market_place)
             child_asin, sub_source, market_place, date, buy_box_percentage
      FROM business_reports.amz_sales_and_traffic_by_asin
      WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)
      ORDER BY child_asin, sub_source, market_place, date DESC
    """)
    latest={(a,s,m):(d,p) for a,s,m,d,p in cur.fetchall()}

c_newer=Counter(); flips=[]
for k,r in keys.items():
    lt=latest.get(k)
    if not lt: c_newer['no_row_at_all']+=1; continue
    d,p = lt; used=r['last_checked']; p=float(p)
    if str(d) > str(used):
        c_newer['NEWER_available']+=1
        if p>0: flips.append((r['asin'],r['account'],used,str(d),r['bb_pct'],p))
    elif str(d)==str(used): c_newer['same_date']+=1
    else: c_newer['older?']+=1

print('historical NO rows:', len(nos))
for k,v in c_newer.most_common(): print(f'  {k:20} {v}')
print('\nrows where a NEWER reading exists AND is >0% (would flip away from NO):', len(flips))
for f in flips[:15]: print('   ', f)
