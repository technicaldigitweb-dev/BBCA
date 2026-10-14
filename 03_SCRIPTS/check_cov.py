import os, json, psycopg
from collections import Counter
D = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
spine = json.load(open(os.path.join(D,'ph_spine.json'), encoding='utf-8'))
c = Counter(r['category'] for r in spine)
print('distinct categories:', len(c), '| none:', c.get(None,0))
print('top:', c.most_common(8))
print('cat_variants>1 rows:', sum(1 for r in spine if (r.get('cat_variants') or 0) > 1))

keys = {(r['asin'], r['sub_source'], r['marketplace']) for r in spine}
MP = {23:'UK',10:'DE',9:'FR',14:'IT'}
with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=30) as cn, cn.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    for w in (1,3,7,14,30,90):
        cur.execute("""
          SELECT DISTINCT child_asin, sub_source, market_place
          FROM business_reports.amz_sales_and_traffic_by_asin
          WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)
            AND date > DATE '2026-10-12' - %s AND date <= DATE '2026-10-12'
        """, (w,))
        got = {(a, s, MP[m]) for a, s, m in cur.fetchall()}
        hit = len(keys & got)
        print(f'window {w:3}d -> PH rows with a report row: {hit:6} ({hit/len(keys)*100:5.1f}%)')
