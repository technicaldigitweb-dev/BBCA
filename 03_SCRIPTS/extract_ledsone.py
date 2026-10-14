"""Read-only extraction from ledsone: Buy Box evidence + Amazon listing status.
Scope: PH Dashboard Amazon accounts (sub_source 6=DCVoltage, 8=LEDSone)
       and marketplaces UK=23, DE=10, FR=9, IT=14.
"""
import os, json, decimal, datetime, psycopg

OUT = r'C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi\04_DATA'
MP = {23: 'UK', 10: 'DE', 9: 'FR', 14: 'IT'}
SITE = {'UK': 'UK', 'Germany': 'DE', 'France': 'FR', 'Italy': 'IT'}
WINDOW_DAYS = 7          # ASSUMPTION - documented in mapping file, pending approval

def jdefault(o):
    if isinstance(o, decimal.Decimal): return float(o)
    if isinstance(o, (datetime.date, datetime.datetime)): return o.isoformat()
    raise TypeError(type(o))

with psycopg.connect(os.environ['WLP_SOURCE_DB_URL'], connect_timeout=30) as conn, conn.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")

    cur.execute("""SELECT max(date) FROM business_reports.amz_sales_and_traffic_by_asin
                   WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)""")
    max_date = cur.fetchone()[0]
    print('max report date:', max_date)

    # --- Buy Box evidence: latest report row per ASIN x account x marketplace ---
    cur.execute("""
      SELECT DISTINCT ON (child_asin, sub_source, market_place)
             child_asin, sub_source, market_place, date,
             buy_box_percentage, sessions, page_views, units_ordered
      FROM business_reports.amz_sales_and_traffic_by_asin
      WHERE sub_source IN (6,8) AND market_place IN (23,10,9,14)
        AND date > %s::date - %s AND date <= %s::date
      ORDER BY child_asin, sub_source, market_place, date DESC
    """, (max_date, WINDOW_DAYS, max_date))
    bb = [{'asin': r[0], 'sub_source': r[1], 'marketplace': MP[r[2]], 'report_date': r[3],
           'buy_box_pct': r[4], 'sessions': r[5], 'page_views': r[6], 'units_ordered': r[7]}
          for r in cur.fetchall()]
    print('buy box rows:', len(bb))

    # --- Listing status: all our offers per ASIN x account x marketplace ---
    cur.execute("""
      SELECT asin, sub_source, site,
             array_agg(DISTINCT coalesce(status,'(null)')) AS statuses,
             sum(quantity) AS total_qty,
             array_agg(DISTINCT coalesce(fulfilment,'(null)')) AS fulfilments,
             count(*) AS offer_rows,
             count(*) FILTER (WHERE wrong_sku = 1) AS wrong_sku_rows,
             max(updated_at) AS last_upd
      FROM listings.amazon_listings
      WHERE sub_source IN (6,8) AND site IN ('UK','Germany','France','Italy')
      GROUP BY 1,2,3
    """)
    ls = [{'asin': r[0], 'sub_source': r[1], 'marketplace': SITE[r[2]], 'statuses': r[3],
           'total_qty': r[4], 'fulfilments': r[5], 'offer_rows': r[6],
           'wrong_sku_rows': r[7], 'last_upd': r[8]} for r in cur.fetchall()]
    print('listing groups:', len(ls))

    # --- Featured-offer price comparison (FBA Excess Inventory report) ---
    # NOTE: this report only covers ASINs flagged as excess FBA stock, so coverage of the
    # PH universe is low (~4%). Used as EVIDENCE only, never as a classified reason.
    cur.execute("""
      SELECT DISTINCT ON (asin, sub_source, market_place)
             asin, sub_source, market_place, snapshot_date, your_price, featuredoffer_price
      FROM amazon_fba.excess_inventory_data
      WHERE sub_source IN (6,8) AND market_place IN ('23','10','9','14')
        AND your_price IS NOT NULL AND featuredoffer_price IS NOT NULL
      ORDER BY asin, sub_source, market_place, snapshot_date DESC
    """)
    px = [{'asin': r[0], 'sub_source': r[1], 'marketplace': MP[int(r[2])],
           'price_date': r[3], 'your_price': r[4], 'featured_price': r[5]}
          for r in cur.fetchall()]
    print('featured-offer price rows:', len(px))

meta = {'max_report_date': max_date, 'window_days': WINDOW_DAYS,
        'extracted_at': datetime.datetime.now().isoformat(timespec='seconds')}
for name, obj in (('bb_evidence', bb), ('listing_status', ls), ('price_evidence', px), ('extract_meta', meta)):
    with open(os.path.join(OUT, name + '.json'), 'w', encoding='utf-8') as f:
        json.dump(obj, f, default=jdefault)
    print('wrote', name)
