"""Headed Amazon UK inspection session for MANUAL verification-page review.

Opens a VISIBLE Chromium window on B086385W3W and holds it open.
Does NOT solve, click through, or bypass any CAPTCHA / verification page.
Does NOT spoof fingerprints and makes no automatic retries.

Flow (driven by sentinel files, because this runs detached from the terminal):
  1. Opens the page, classifies what Amazon returned, writes it to the log.
  2. Waits for   06_EVIDENCE/logs/PROCEED   -> then extracts listing data.
  3. Waits for   06_EVIDENCE/logs/CLOSE     -> then closes the browser.

The browser is never closed before CLOSE appears (or the safety timeout expires).
"""
import datetime
import json
import pathlib
import re
import sys
import time

from playwright.sync_api import sync_playwright

ASIN = "B086385W3W"
URL = "https://www.amazon.co.uk/dp/" + ASIN
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
POSTCODE = "SW1A1AA"

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOGS = ROOT / "06_EVIDENCE" / "logs"
SHOTS = ROOT / "06_EVIDENCE" / "screenshots"
PROCEED = LOGS / "PROCEED"
CLOSE = LOGS / "CLOSE"
LOGF = LOGS / "manual_inspect.log"
OUTF = ROOT / "06_EVIDENCE" / "manual_inspect_result.json"

MAX_HOLD_SEC = 3600          # safety cap: never hang a browser longer than 1h
POLL_SEC = 3


def log(msg):
    line = "[{0}] {1}".format(
        datetime.datetime.now().astimezone().isoformat(timespec="seconds"), msg)
    with open(LOGF, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)


def clean(s):
    return re.sub(r"[​-‏⁠]", "", re.sub(r"\s+", " ", s or "")).strip()


def t1(page, sel, limit=200):
    try:
        el = page.query_selector(sel)
        return clean(el.inner_text())[:limit] if el else None
    except Exception:
        return None


def classify(page):
    """What did Amazon actually serve? No interaction, just observation."""
    html = page.content()
    low = html.lower()
    markers = [m for m in ("validatecaptcha",
                           "click the button below to continue shopping",
                           "enter the characters you see below",
                           "api-services-support",
                           "robot check") if m in low]
    # A geo-suppressed UK page still renders the full document but can omit
    # #productTitle, so fall back to other product-page evidence before
    # concluding we were blocked.
    is_product = any(page.query_selector(s) is not None for s in (
        "#productTitle", "#dp", "#dp-container", "#centerCol", "#ppd"))
    if markers:
        return "VERIFICATION_PAGE", markers, len(html)
    if is_product or len(html) > 500000:
        return "PRODUCT_PAGE", markers, len(html)
    return "UNKNOWN", markers, len(html)


def wait_for(path, what):
    log("WAITING for {0} -> create file: {1}".format(what, path))
    waited = 0
    while waited < MAX_HOLD_SEC:
        if path.exists():
            log("{0} received.".format(what))
            return True
        time.sleep(POLL_SEC)
        waited += POLL_SEC
        if waited % 120 == 0:
            log("still holding, {0}s elapsed (browser open)".format(waited))
    log("SAFETY TIMEOUT after {0}s without {1}.".format(MAX_HOLD_SEC, what))
    return False


def extract(page, ctx):
    """Post-confirmation data collection from whatever is on screen now."""
    res = {"asin": ASIN,
           "checked_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "current_url": page.url}
    state, markers, nbytes = classify(page)
    res["page_state"] = state
    res["block_markers"] = markers
    res["bytes"] = nbytes

    if state != "PRODUCT_PAGE":
        res["conclusion"] = ("Amazon is still showing an access restriction - "
                             "stopping rather than retrying.")
        log("STILL RESTRICTED: state={0} markers={1}".format(state, markers))
        return res

    # 1. listing loaded + correct marketplace
    res["listing_loaded"] = True
    res["marketplace_host"] = re.sub(r"^https?://([^/]+).*", r"\1", page.url)
    res["product_title"] = t1(page, "#productTitle", 160)
    res["asin_on_page"] = ASIN in page.content()

    # 2. delivery location - set it via Amazon's own picker only if not already UK
    loc = t1(page, "#glow-ingress-line2", 60)
    res["delivery_location_initial"] = loc
    if not loc or not ("SW1A" in (loc or "").upper() or "LONDON" in (loc or "").upper()):
        log("delivery location is {0!r}; applying UK postcode via Amazon's own "
            "location picker".format(loc))
        try:
            page.click("#nav-global-location-popover-link", timeout=15000)
            page.wait_for_selector("#GLUXZipUpdateInput", timeout=15000)
            page.fill("#GLUXZipUpdateInput", POSTCODE)
            page.click("#GLUXZipUpdate", timeout=12000)
            page.wait_for_timeout(3500)
            page.goto(URL, timeout=35000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            res["postcode_applied"] = True
        except Exception as e:
            res["postcode_applied"] = False
            res["postcode_error"] = type(e).__name__
    else:
        res["postcode_applied"] = False
    res["delivery_location"] = t1(page, "#glow-ingress-line2", 60)

    # 3. currency
    price = None
    for sel in ("#corePriceDisplay_desktop_feature_div span.a-offscreen",
                "#corePrice_feature_div span.a-offscreen",
                "#desktop_buybox span.a-offscreen"):
        price = t1(page, sel, 40)
        if price and re.search(r"\d", price):
            break
    if not price:
        bb = t1(page, "#desktop_buybox", 120) or ""
        m = re.search(r"[£$€][\d,.]+", bb)
        price = m.group(0) if m else None
    res["featured_price"] = price
    res["currency"] = ("GBP" if price and "£" in price
                       else ("NON-GBP" if price else None))
    res["currency_cookie"] = [c["value"] for c in ctx.cookies()
                              if c["name"] == "i18n-prefs"]

    # 4/5. featured seller - current offer-display-feature layout
    rows = page.query_selector_all(
        "#desktop_buybox [offer-display-feature-name='desktop-merchant-info']")
    vals = [clean(x.inner_text()) for x in rows if clean(x.inner_text())]
    res["merchant_rows"] = vals
    res["featured_seller_name"] = vals[1] if len(vals) > 1 else (vals[0] if vals else None)
    sid = None
    for x in rows:
        try:
            for a in x.query_selector_all("a[href*='seller=']"):
                m = re.search(r"seller=([A-Z0-9]{10,20})", a.get_attribute("href") or "")
                if m:
                    sid = m.group(1)
                    break
        except Exception:
            pass
        if sid:
            break
    res["featured_seller_id"] = sid

    # 6. stock
    res["availability"] = t1(page, "#availability", 160)
    res["add_to_basket_present"] = page.query_selector(
        "#add-to-cart-button, #add-to-cart-button-ubb") is not None
    res["out_of_stock_block"] = page.query_selector("#outOfStock") is not None

    # screenshot of the product page
    try:
        p = SHOTS / (ASIN + "_manual_product.png")
        page.screenshot(path=str(p))
        res["screenshot_product"] = str(p.relative_to(ROOT))
    except Exception as e:
        res["screenshot_product"] = "failed: " + type(e).__name__

    # 7. other offers - separate tab so the inspected page is left intact
    offers = {"count": None, "list": [], "error": None}
    try:
        op = ctx.new_page()
        r = op.goto("https://www.amazon.co.uk/gp/offer-listing/" + ASIN,
                    timeout=35000, wait_until="domcontentloaded")
        op.wait_for_timeout(2000)
        ostate, omarkers, _ = classify(op)
        offers["page_state"] = ostate
        offers["block_markers"] = omarkers
        if r is not None and r.status == 200 and not omarkers:
            offs = op.query_selector_all("#aod-offer")
            offers["count"] = len(offs)
            pin = op.query_selector("#aod-pinned-offer")
            if pin is not None:
                pp = pin.query_selector("span.a-offscreen, .a-price")
                offers["featured_offer_price"] = clean(pp.inner_text()) if pp else None
            for o in offs[:12]:
                pr = o.query_selector("span.a-offscreen, .a-price")
                sb = o.query_selector("[id^=aod-offer-soldBy] a")
                offers["list"].append({
                    "price": clean(pr.inner_text()) if pr else None,
                    "seller_name": clean(sb.inner_text()) if sb else None,
                })
            try:
                p2 = SHOTS / (ASIN + "_manual_offers.png")
                op.screenshot(path=str(p2))
                offers["screenshot"] = str(p2.relative_to(ROOT))
            except Exception:
                pass
        else:
            offers["error"] = "HTTP {0} / markers {1}".format(
                r.status if r else "none", omarkers)
        op.close()
    except Exception as e:
        offers["error"] = "{0}: {1}".format(type(e).__name__, str(e)[:140])
    res["offers"] = offers
    res["conclusion"] = "Product page accessible; data extracted."
    return res


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    for f in (PROCEED, CLOSE):
        if f.exists():
            f.unlink()
    log("=== manual headed inspection session start ===")
    log("ASIN {0} | headless=False | no captcha solving, no fingerprint spoofing".format(ASIN))

    # Persistent profile: an ordinary browser profile directory, so cookies -
    # including a verification the USER cleared, and the UK delivery postcode -
    # survive between runs instead of forcing a fresh challenge every time.
    profile = ROOT / "06_EVIDENCE" / ".browser_profile"
    profile.mkdir(parents=True, exist_ok=True)
    log("using persistent profile: {0}".format(profile))

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(profile), headless=False, timeout=45000,
            args=["--start-maximized"], user_agent=UA, locale="en-GB",
            no_viewport=True,
            extra_http_headers={"Accept-Language": "en-GB,en;q=0.9"})
        b = ctx.browser if ctx.browser is not None else ctx
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            r = page.goto(URL, timeout=45000, wait_until="domcontentloaded")
            log("navigated to {0} -> HTTP {1}".format(URL, r.status if r else "?"))
        except Exception as e:
            log("NAVIGATION FAILED: {0}: {1}".format(type(e).__name__, str(e)[:160]))
        page.wait_for_timeout(2500)

        state, markers, nbytes = classify(page)
        log("page state = {0} | bytes = {1} | markers = {2}".format(state, nbytes, markers))
        try:
            shot = SHOTS / (ASIN + "_manual_initial.png")
            page.screenshot(path=str(shot))
            log("initial screenshot -> {0}".format(shot.name))
        except Exception:
            pass
        if state == "VERIFICATION_PAGE":
            log("A verification page is on screen. It is being LEFT UNTOUCHED "
                "for manual inspection. Nothing will be clicked.")
        elif state == "PRODUCT_PAGE":
            log("The product page loaded directly - no verification challenge.")
        log("BROWSER IS OPEN AND WILL STAY OPEN.")

        # Hold open, extracting each time PROCEED appears, until CLOSE appears.
        # PROCEED is consumed so extraction can be repeated without restarting.
        waited = 0
        log("WAITING: create PROCEED to extract, CLOSE to finish. Browser stays open.")
        while waited < MAX_HOLD_SEC:
            if CLOSE.exists():
                log("close instruction (CLOSE) received.")
                break
            if PROCEED.exists():
                try:
                    PROCEED.unlink()
                except Exception:
                    pass
                log("PROCEED received - extracting listing data from the current page ...")
                try:
                    res = extract(page, ctx)
                except Exception as e:
                    res = {"error": "{0}: {1}".format(type(e).__name__, str(e)[:200])}
                    log("EXTRACTION ERROR: " + res["error"])
                json.dump(res, open(OUTF, "w", encoding="utf-8"), indent=1,
                          ensure_ascii=False)
                log("result written -> " + str(OUTF.name))
                log("SUMMARY: state={0} price={1} seller={2} avail={3} offers={4}".format(
                    res.get("page_state"), res.get("featured_price"),
                    res.get("featured_seller_name"), res.get("availability"),
                    (res.get("offers") or {}).get("count")))
                log("still holding. PROCEED again to re-extract, CLOSE to finish.")
            time.sleep(POLL_SEC)
            waited += POLL_SEC
            if waited % 300 == 0:
                log("still holding, {0}s elapsed (browser open)".format(waited))
        log("closing browser now.")
        try:
            ctx.close()
        except Exception:
            pass
    log("=== session end ===")


if __name__ == "__main__":
    main()
