"""Run the live listing verification through an ALREADY-OPEN Chrome over CDP.

Why CDP rather than launching a browser: the UK VPN here is browser-scoped, so a
Playwright-launched context would egress via the system route (Sri Lanka) and read a
different Amazon page. Driving the open window is the only way to see what a UK
shopper is served.

READ-ONLY: touches no database. Writes only under 06_EVIDENCE/.

    python run_cdp_verify.py <sample.json> <out.json> [--label L] [--limit N] [--cdp URL]
"""
import json
import sys
import time
import datetime
import pathlib

from playwright.sync_api import sync_playwright

import verify_live_listing as V

ROOT = pathlib.Path(__file__).resolve().parents[1]


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    src, out = sys.argv[1], sys.argv[2]
    label = arg("--label", "cdp_uk")
    limit = int(arg("--limit", "999"))
    cdp = arg("--cdp", "http://127.0.0.1:9222")

    recs = json.load(open(src, encoding="utf-8"))[:limit]
    V.SHOTS.mkdir(parents=True, exist_ok=True)

    report = {
        "label": label,
        "transport": "cdp:" + cdp,
        "postcode": V.POSTCODE,
        "started_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "results": [],
    }

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(cdp, timeout=30000)
        ctx = b.contexts[0]
        page = ctx.new_page()

        # Confirm what Amazon actually sees from this window.
        try:
            page.goto("https://ipinfo.io/json", timeout=45000)
            ip = json.loads(page.inner_text("body"))
            report["egress"] = {k: ip.get(k) for k in ("ip", "country", "city", "org")}
        except Exception as e:
            report["egress"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:100])}
        print("[egress] %s" % (report["egress"],), flush=True)

        if (report.get("egress") or {}).get("country") != "GB":
            print("WARN: browser egress is not GB - fidelity comparison will not be valid",
                  flush=True)
        report["egress_is_gb"] = (report.get("egress") or {}).get("country") == "GB"

        # A VPN hop makes the odd navigation time out; that is latency, not a block,
        # so retry the locale setup before giving up on the whole run.
        page.set_default_navigation_timeout(60000)
        ok, detail, attempts = False, "not attempted", 0
        for attempts in range(1, 4):
            try:
                ok, detail = V.setup_uk(ctx, page)
            except Exception as e:
                ok, detail = False, "setup error: %s: %s" % (type(e).__name__, str(e)[:90])
            if ok or detail.startswith("BLOCKED"):
                break
            print("[locale] attempt %d failed (%s), retrying" % (attempts, detail), flush=True)
            time.sleep(5)
        report["locale_attempts"] = attempts
        report["uk_locale_ok"] = ok
        report["uk_locale_detail"] = detail
        report["blocked_by_amazon"] = detail.startswith("BLOCKED")
        print("[locale] ok=%s %s" % (ok, detail), flush=True)

        if not ok:
            report["extraction_status"] = "blocked" if report["blocked_by_amazon"] \
                else "locale_unconfirmed"
            report["aborted"] = True
            print("STOP: %s. No retry, no bypass." % report["extraction_status"], flush=True)
        else:
            report["aborted"] = False
            report["extraction_status"] = "ok"
            for i, rec in enumerate(recs, 1):
                res = V.check_asin(page, rec)
                report["results"].append(res)
                print("[%d/%d] %s http=%s price=%s seller=%s offers=%s blocked=%s" % (
                    i, len(recs), res["asin"], res.get("http_status"),
                    res.get("featured_price_live"), res.get("featured_seller_name"),
                    (res.get("offers") or {}).get("count"), res.get("blocked_markers")),
                    flush=True)
                if res.get("blocked_markers"):
                    report["extraction_status"] = "blocked_midrun"
                    print("STOP: access control appeared mid-run. Halting.", flush=True)
                    break
                time.sleep(4)   # polite rate limit
        page.close()

    report["finished_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("saved -> " + out)


if __name__ == "__main__":
    main()
