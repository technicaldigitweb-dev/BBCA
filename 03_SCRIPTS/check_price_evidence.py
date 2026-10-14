"""Does amazon_fba.excess_inventory_data give usable 'Price higher' evidence
for our 915 verified Buy Box losses?"""
import os, json, psycopg
D = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
rows = json.load(open(os.path.join(D,'dashboard_rows.json'), encoding='utf-8'))
MP = {'UK':'23','DE':'10','FR':'9','IT':'14'}; SS = {'LEDSone':8,'DCVoltage':6}
nos = [r for r in rows if r['status']=='NO']
no_keys = {(r['asin'], SS[r['account']], MP[r['marketplace']]) for r in nos}
all_keys = {(r['asin'], SS[r['account']], MP[r['marketplace']]) for r in rows}

with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=30) as c, c.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    cur.execute("""
      SELECT DISTINCT ON (asin, sub_source, market_place)
             asin, sub_source, market_place, snapshot_date, your_price, featuredoffer_price
      FROM amazon_fba.excess_inventory_data
      WHERE sub_source IN (6,8)
      ORDER BY asin, sub_source, market_place, snapshot_date DESC
    """)
    ex = {(a, s, str(m)): (d, yp, fp) for a, s, m, d, yp, fp in cur.fetchall()}

print('excess-inventory keys (our 2 accounts):', len(ex))
print('overlap with FULL PH universe   :', len(all_keys & set(ex)), 'of', len(all_keys))
ov = no_keys & set(ex)
print('overlap with the 915 verified NO:', len(ov))

if ov:
    higher = same = lower = nofp = 0
    for k in ov:
        d, yp, fp = ex[k]
        if fp is None or yp is None: nofp += 1
        elif yp > fp: higher += 1
        elif yp == fp: same += 1
        else: lower += 1
    print(f'  our price HIGHER than featured offer: {higher}')
    print(f'  equal: {same} | lower: {lower} | missing price: {nofp}')
    print(f'  -> "Price higher" would be evidenced for {higher} of {len(nos)} losses '
          f'({higher/len(nos)*100:.1f}%)')
