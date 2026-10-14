"""Daily Buy Box history from the Amazon Sales & Traffic report (read-only).
Two outputs:
  bb_history_daily.json - per-day YES/NO/partial counts over 14 days (trend)
  bb_prev.json          - each ASIN's PREVIOUS report row before its latest one (change detection)
"""
import os, json, decimal, datetime, psycopg
OUT = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
MP = {23: 'UK', 10: 'DE', 9: 'FR', 14: 'IT'}

def jd(o):
    if isinstance(o, decimal.Decimal): return float(o)
    if isinstance(o, (datetime.date, datetime.datetime)): return o.isoformat()
    raise TypeError(type(o))

with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=30) as conn, conn.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    cur.execute("""SELECT max(date) FROM business_reports.amz_sales_and_traffic_by_asin
                   WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)""")
    mx = cur.fetchone()[0]

    cur.execute("""
      SELECT date, sub_source, market_place,
             count(*) FILTER (WHERE buy_box_percentage = 100) AS won,
             count(*) FILTER (WHERE buy_box_percentage = 0)   AS lost,
             count(*) FILTER (WHERE buy_box_percentage > 0 AND buy_box_percentage < 100) AS partial,
             count(*) AS total
      FROM business_reports.amz_sales_and_traffic_by_asin
      WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)
        AND date > %s::date - 14 AND date <= %s::date
      GROUP BY 1,2,3 ORDER BY 1,2,3
    """, (mx, mx))
    hist = [{'date': r[0], 'sub_source': r[1], 'marketplace': MP[r[2]],
             'won': r[3], 'lost': r[4], 'partial': r[5], 'total': r[6]} for r in cur.fetchall()]
    print('history rows:', len(hist))

    # previous report row per ASIN (the one before the latest, within 14 days)
    cur.execute("""
      WITH ranked AS (
        SELECT child_asin, sub_source, market_place, date, buy_box_percentage,
               row_number() OVER (PARTITION BY child_asin, sub_source, market_place
                                  ORDER BY date DESC) AS rn
        FROM business_reports.amz_sales_and_traffic_by_asin
        WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)
          AND date > %s::date - 14 AND date <= %s::date
      )
      SELECT child_asin, sub_source, market_place, date, buy_box_percentage
      FROM ranked WHERE rn = 2
    """, (mx, mx))
    prev = [{'asin': r[0], 'sub_source': r[1], 'marketplace': MP[r[2]],
             'prev_date': r[3], 'prev_pct': r[4]} for r in cur.fetchall()]
    print('previous-row records:', len(prev))

for n, o in (('bb_history_daily', hist), ('bb_prev', prev)):
    json.dump(o, open(os.path.join(OUT, n + '.json'), 'w', encoding='utf-8'), default=jd)
    print('wrote', n)
