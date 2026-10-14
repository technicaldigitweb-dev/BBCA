"""Live Amazon UK listing verifier for Buy Box evidence collection.

READ-ONLY: touches no database. Writes only under 06_EVIDENCE/.
Usage: python verify_live_listing.py <sample.json> <out.json> [--label LBL] [--limit N]
"""
import json
import re
import sys
import time
import datetime
import pathlib

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
POSTCODE = "SW1A1AA"
ROOT = pathlib.Path(__file__).resolve().parents[1]
SHOTS = ROOT / "06_EVIDENCE" / "screenshots"


def clean(s):
    return re.sub(r"[​-‏⁠]", "", re.sub(r"\s+", " ", s or "")).strip()


def t1(page, sel, limit=200):
    try:
        el = page.query_selector(sel)
        return clean(el.inner_text())[:limit] if el else None
    except Exception:
        return None


def seller_id_from(el):
    """Merchant token from a seller-profile href: identity, not display name."""
    if el is None:
        return None
    try:
        for a in el.query_selector_all("a[href*='seller=']"):
            m = re.search(r"seller=([A-Z0-9]{10,20})", a.get_attribute("href") or "")
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def first_text(el, selectors):
    if el is None:
        return None
    for sel in selectors:
        try:
            got = el.query_selector(sel)
        except Exception:
            got = None
        if got is not None:
            val = clean(got.inner_text())
            if val:
                return val
    return None


LABELS = {"sold by", "sold by:", "dispatches from", "dispatches from:",
          "ships from", "ships from:", "shipper / seller", "shipper/seller",
          "sold by amazon", "dispatched from"}


def sold_by(el):
    """Seller NAME from an AOD offer block.

    The soldBy container holds a label column and a value column under the same id
    prefix, so taking the first match returns the literal string "Sold by".
    Read the value column first, then fall back, and reject anything that is just
    a label.
    """
    if el is None:
        return None
    cands = ["[id^=aod-offer-soldBy] .a-col-right a",
             "[id^=aod-offer-soldBy] .a-col-right span",
             "[id^=aod-offer-soldBy] a[href*='seller=']",
             "#aod-offer-soldBy .a-col-right a",
             "[id^=aod-offer-soldBy] a",
             "[id^=aod-offer-soldBy] span.a-size-small"]
    for sel in cands:
        try:
            for got in el.query_selector_all(sel):
                val = clean(got.inner_text())
                if val and val.lower().rstrip(":") not in LABELS:
                    return val
        except Exception:
            continue
    return None


BLOCK_MARKERS = ("validatecaptcha", "click the button below to continue shopping",
                 "enter the characters you see below", "api-services-support",
                 "robot check", "to discuss automated access")


def access_block(page):
    """Return the Amazon access-control markers present, if any."""
    try:
        low = page.content().lower()
    except Exception:
        return []
    return [m for m in BLOCK_MARKERS if m in low]


def setup_uk(ctx, page):
    """Apply Amazon's own delivery-location + currency preference, then ASSERT it."""
    ctx.add_cookies([{"name": "i18n-prefs", "value": "GBP",
                      "domain": ".amazon.co.uk", "path": "/"}])
    page.goto("https://www.amazon.co.uk/dp/B086385W3W", timeout=30000,
              wait_until="domcontentloaded")
    blocked = access_block(page)
    if blocked:
        # Amazon access control. Stop here - do not interact with the challenge.
        return False, "BLOCKED by Amazon access control; markers=%s" % (blocked,)
    try:
        page.click("#nav-global-location-popover-link", timeout=12000)
        page.wait_for_selector("#GLUXZipUpdateInput", timeout=12000)
        page.fill("#GLUXZipUpdateInput", POSTCODE)
        page.click("#GLUXZipUpdate", timeout=10000)
        page.wait_for_timeout(3000)
    except Exception as e:
        return False, "picker failed: " + type(e).__name__
    page.goto("https://www.amazon.co.uk/dp/B086385W3W", timeout=30000,
              wait_until="domcontentloaded")
    loc = t1(page, "#glow-ingress-line2", 60) or ""
    cur = [c["value"] for c in ctx.cookies() if c["name"] == "i18n-prefs"]
    ok = ("SW1A" in loc.upper() or "LONDON" in loc.upper()) and cur == ["GBP"]
    return ok, "location={0!r} i18n-prefs={1}".format(loc, cur)


def offers_for(page, asin):
    """Competing offers from the all-offers-display page."""
    out = {"count": None, "featured": None, "list": [], "error": None}
    try:
        r = page.goto("https://www.amazon.co.uk/gp/offer-listing/" + asin,
                      timeout=30000, wait_until="domcontentloaded")
        if r is None or r.status != 200:
            out["error"] = "offer-listing HTTP {0}".format(r.status if r else "none")
            return out
        page.wait_for_timeout(1800)
        pin = page.query_selector("#aod-pinned-offer")
        if pin is not None:
            out["featured"] = {
                "price": first_text(pin, ["span.a-offscreen", ".a-price"]),
                "seller_name": sold_by(pin),
                "seller_id": seller_id_from(pin),
            }
        offs = page.query_selector_all("#aod-offer")
        out["count"] = len(offs)
        for o in offs[:12]:
            out["list"].append({
                "price": first_text(o, ["span.a-offscreen", ".a-price"]),
                "seller_name": sold_by(o),
                "seller_id": seller_id_from(o),
            })
    except Exception as e:
        out["error"] = "{0}: {1}".format(type(e).__name__, str(e)[:120])
    return out


def check_asin(page, rec):
    asin = rec["asin"]
    res = {
        "asin": asin,
        "expected_account": rec.get("account"),
        "stratum": rec.get("stratum"),
        "internal": {
            "our_price": rec.get("price"),
            "stock": rec.get("stock"),
            "listing_status": rec.get("listing_status"),
            "featured_price_db": rec.get("featured_price"),
            "bb_pct": rec.get("bb_pct"),
            "last_checked": rec.get("last_checked"),
        },
        "checked_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    try:
        r = page.goto("https://www.amazon.co.uk/dp/" + asin, timeout=30000,
                      wait_until="domcontentloaded")
        res["http_status"] = r.status if r else None
        page.wait_for_timeout(1200)
    except Exception as e:
        res["error"] = "goto {0}: {1}".format(type(e).__name__, str(e)[:120])
        return res

    html = page.content()
    low = html.lower()
    res["blocked_markers"] = [m for m in (
        "enter the characters you see below", "api-services-support",
        "robot check", "to discuss automated access") if m in low]
    res["page_title"] = clean(page.title())[:120]
    res["delivery_location"] = t1(page, "#glow-ingress-line2", 60)
    res["asin_on_page"] = asin in html
    res["availability"] = t1(page, "#availability", 160)
    res["out_of_stock_block"] = page.query_selector("#outOfStock") is not None
    res["add_to_cart_present"] = page.query_selector(
        "#add-to-cart-button, #add-to-cart-button-ubb") is not None
    res["buybox_present"] = page.query_selector("#desktop_buybox") is not None
    res["delivery_promise"] = t1(page, "#mir-layout-DELIVERY_BLOCK, #deliveryBlockMessage", 160)

    price = None
    for sel in ("#corePriceDisplay_desktop_feature_div span.a-offscreen",
                "#corePrice_feature_div span.a-offscreen",
                "#desktop_buybox span.a-offscreen",
                "#priceblock_ourprice"):
        price = t1(page, sel, 40)
        if price and re.search(r"\d", price):
            break
    res["featured_price_live"] = price
    if price and "£" in price:
        res["currency"] = "GBP"
    elif price:
        res["currency"] = "NON-GBP"
    else:
        res["currency"] = None

    # Merchant info via the CURRENT offer-display-feature layout.
    rows = page.query_selector_all(
        "#desktop_buybox [offer-display-feature-name='desktop-merchant-info']")
    vals = []
    for x in rows:
        v = clean(x.inner_text())
        if v:
            vals.append(v)
    # The same attribute emits a label row and a value row; never take vals[0] blindly.
    value = next((v for v in vals if v.lower().rstrip(":") not in LABELS), None)
    merch = {"label": vals[0] if vals else None,
             "value": value,
             "all_rows": vals,
             "seller_id": None}
    for x in rows:
        sid = seller_id_from(x)
        if sid:
            merch["seller_id"] = sid
            break
    res["merchant_info"] = merch
    res["featured_seller_name"] = merch["value"]
    res["featured_seller_id"] = merch["seller_id"]

    res["legacy_selectors"] = {
        "tabular_buybox_rows": len(page.query_selector_all("#tabular-buybox .tabular-buybox-text")),
        "merchant_info_id": page.query_selector("#merchant-info") is not None,
        "sellerProfileTriggerId": page.query_selector("#sellerProfileTriggerId") is not None,
    }
    res["aod_ingress_present"] = page.query_selector(
        "#aod-ingress-link, [data-action='show-all-offers-display']") is not None

    try:
        page.screenshot(path=str(SHOTS / (asin + "_uk.png")))
        res["screenshot"] = "06_EVIDENCE/screenshots/" + asin + "_uk.png"
    except Exception:
        res["screenshot"] = None

    res["offers"] = offers_for(page, asin)
    return res


def main():
    src, out = sys.argv[1], sys.argv[2]
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else "baseline"
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 999
    recs = json.load(open(src, encoding="utf-8"))[:limit]
    SHOTS.mkdir(parents=True, exist_ok=True)
    report = {
        "label": label,
        "postcode": POSTCODE,
        "started_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "user_agent": UA,
        "results": [],
    }
    headed = "--headed" in sys.argv
    report["headed"] = headed
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not headed, timeout=45000)
        ctx = b.new_context(user_agent=UA, locale="en-GB",
                            viewport={"width": 1440, "height": 900},
                            extra_http_headers={"Accept-Language": "en-GB,en;q=0.9"})
        page = ctx.new_page()
        ok, detail = setup_uk(ctx, page)
        report["uk_locale_ok"] = ok
        report["uk_locale_detail"] = detail
        report["blocked_by_amazon"] = detail.startswith("BLOCKED")
        print("[locale] ok={0} {1}".format(ok, detail), flush=True)
        if not ok:
            if report["blocked_by_amazon"]:
                print("STOP: Amazon access control present. Marking run BLOCKED. "
                      "No retry, no bypass.", flush=True)
                report["extraction_status"] = "blocked"
            else:
                print("ABORT: UK locale not confirmed - refusing to collect "
                      "suppressed pages", flush=True)
                report["extraction_status"] = "locale_unconfirmed"
            report["aborted"] = True
        else:
            for i, rec in enumerate(recs, 1):
                res = check_asin(page, rec)
                report["results"].append(res)
                print("[{0}/{1}] {2} http={3} price={4} seller={5} offers={6} blocked={7}".format(
                    i, len(recs), res["asin"], res.get("http_status"),
                    res.get("featured_price_live"), res.get("featured_seller_name"),
                    (res.get("offers") or {}).get("count"), res.get("blocked_markers")),
                    flush=True)
                time.sleep(4)   # polite rate limit
        b.close()
    report["finished_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("saved -> " + out)


if __name__ == "__main__":
    main()
