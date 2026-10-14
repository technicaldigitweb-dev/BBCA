import os, json, psycopg
D = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
rows = json.load(open(os.path.join(D,'dashboard_rows.json'), encoding='utf-8'))
MP = {'UK':23,'DE':10,'FR':9,'IT':14}; SS={'LEDSone':8,'DCVoltage':6}
SITE = {'UK':'UK','DE':'Germany','FR':'France','IT':'Italy'}
pick=[]
for st in ('YES','NO'):
    pick += [r for r in rows if r['status']==st][:2]
pick += [r for r in rows if r['status']=='NOT VERIFIED' and r['bb_pct'] is not None][:1]
pick += [r for r in rows if r['status']=='NOT VERIFIED' and r['bb_pct'] is None][:1]

with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=30) as cn, cn.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    for r in pick:
        ss, mp = SS[r['account']], MP[r['marketplace']]
        cur.execute("""SELECT date, buy_box_percentage FROM business_reports.amz_sales_and_traffic_by_asin
                       WHERE child_asin=%s AND sub_source=%s AND market_place=%s
                         AND date > DATE '2026-10-12'-7 AND date <= DATE '2026-10-12'
                       ORDER BY date DESC LIMIT 1""", (r['asin'], ss, mp))
        src = cur.fetchone()
        cur.execute("""SELECT array_agg(DISTINCT coalesce(status,'(null)')), sum(quantity)
                       FROM listings.amazon_listings WHERE asin=%s AND sub_source=%s AND site=%s""",
                    (r['asin'], ss, SITE[r['marketplace']]))
        lst = cur.fetchone()
        db_pct = float(src[1]) if src else None
        ok_bb  = (db_pct == r['bb_pct']) and (str(src[0]) if src else None) == (r['last_checked'] or None)
        ok_st  = (lst[1] == r['stock'])
        print(f"{r['asin']} {r['account']:10} {r['marketplace']:3} dash={r['status']:12} pct={r['bb_pct']} date={r['last_checked']}")
        print(f"    DB  -> {('date=%s pct=%s' % (src[0], float(src[1]))) if src else 'NO ROW IN WINDOW'}  | bb_match={ok_bb}")
        print(f"    dash stock={r['stock']} listing={r['listing_status']} | DB qty={lst[1]} statuses={lst[0]} | stock_match={ok_st}")
