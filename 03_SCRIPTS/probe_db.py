import os, psycopg
for var in ("WLP_SOURCE_DB_URL","DATABASE_URL","HUB_DB_URL","VARMEN_DB_URL"):
    dsn = os.environ.get(var)
    if not dsn:
        print(f"{var}: NOT SET"); continue
    try:
        with psycopg.connect(dsn, connect_timeout=12) as c, c.cursor() as cur:
            cur.execute("select current_database(), current_user")
            db, usr = cur.fetchone()
            cur.execute("""select count(*) from information_schema.tables
                           where table_name in ('amz_sales_and_traffic_by_asin','analytics_overallasinlisting','amazon_listings')""")
            hits = cur.fetchone()[0]
            print(f"{var}: db={db} user={usr} key_tables_found={hits}")
    except Exception as e:
        print(f"{var}: FAIL {type(e).__name__}: {str(e)[:120]}")
