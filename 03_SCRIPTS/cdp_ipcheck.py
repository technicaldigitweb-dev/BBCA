from playwright.sync_api import sync_playwright
import json
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    pg = ctx.new_page()
    pg.goto("https://ipinfo.io/json", timeout=45000)
    txt = pg.inner_text("body")
    try:
        d = json.loads(txt)
        print("BROWSER EGRESS:", d.get("country"), d.get("ip"), d.get("city"), d.get("org"))
    except Exception:
        print("raw:", txt[:300])
    pg.close()
