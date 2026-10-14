import os, psycopg
with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=30) as c, c.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    cur.execute("""SELECT max(date), count(*) FROM business_reports.amz_sales_and_traffic_by_asin
                   WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)""")
    print('overall max date / rows:', cur.fetchone())
    cur.execute("""SELECT date, count(*) rows, count(DISTINCT child_asin) asins
                   FROM business_reports.amz_sales_and_traffic_by_asin
                   WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)
                     AND date >= DATE '2026-10-08'
                   GROUP BY 1 ORDER BY 1""")
    print('\ndate        rows   asins')
    for d,r,a in cur.fetchall(): print(f'{d}  {r:6} {a:6}')
    # duplicate check at the stated grain
    cur.execute("""SELECT count(*) FROM (
                     SELECT date, child_asin, sub_source, market_place, count(*) n
                     FROM business_reports.amz_sales_and_traffic_by_asin
                     WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)
                       AND date >= DATE '2026-10-01'
                     GROUP BY 1,2,3,4 HAVING count(*)>1) q""")
    print('\nduplicate grain keys since 2026-10-01:', cur.fetchone()[0])
