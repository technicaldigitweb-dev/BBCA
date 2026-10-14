import os, psycopg
SITE = {'UK':'UK','DE':'Germany','FR':'France','IT':'Italy'}
with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=20) as c, c.cursor() as cur:
    cur.execute("""
      SELECT site, status, is_ended, wrong_sku, count(*) AS rows, count(DISTINCT asin) AS asins
      FROM listings.amazon_listings
      WHERE sub_source IN (6,8) AND site IN ('UK','Germany','France','Italy')
      GROUP BY 1,2,3,4 ORDER BY 1,2,3,4
    """)
    print(f"{'site':8} {'status':14} {'ended':5} {'wrong':5} {'rows':>7} {'asins':>7}")
    for r in cur.fetchall():
        print(f"{str(r[0]):8} {str(r[1]):14} {str(r[2]):5} {str(r[3]):5} {r[4]:7} {r[5]:7}")
    cur.execute("""
      SELECT count(*) FROM (
        SELECT asin, sub_source, site FROM listings.amazon_listings
        WHERE sub_source IN (6,8) AND site IN ('UK','Germany','France','Italy')
        GROUP BY 1,2,3 HAVING count(DISTINCT status) > 1) q
    """)
    print('\nASIN+acct+site groups with MIXED status:', cur.fetchone()[0])
