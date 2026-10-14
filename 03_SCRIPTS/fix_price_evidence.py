"""Phase 1 - price-comparison accuracy correction.

Rebuilds the featured-offer price comparison from amazon_fba.excess_inventory_data
under strict compatibility rules, and suppresses it where it cannot be defended.

READ-ONLY against PostgreSQL (SELECT only). Writes new, versioned files only:
    04_DATA/price_evidence_v2.json       corrected evidence, one entry per key
    04_DATA/dashboard_rows_v002.json     corrected rows (originals untouched)
    06_EVIDENCE/price_corrections.json   per-row correction log

Why the original was wrong
--------------------------
extract_ledsone.py used
    SELECT DISTINCT ON (asin, sub_source, market_place) ... ORDER BY snapshot_date DESC
against a table whose true grain is asin x sub_source x market_place x sku x
snapshot_date. That collapses a SKU-grain table to one arbitrary SKU, admits
your_price = 0.00 (only NULL was excluded), and takes the newest snapshot
regardless of how far it sits from the Buy Box reading date. The dashboard then
displayed the PH spine `price` next to a comparison computed from a different
offer's `your_price`.

Eligibility rules applied here (all must hold)
----------------------------------------------
1. A source row exists for the same asin + sub_source + market_place on exactly
   the Buy Box reading date (`last_checked`). Otherwise: stale.
2. Currency matches the marketplace (GBP for UK, EUR otherwise).
3. your_price > 0 and featuredoffer_price > 0.
4. Unambiguous: all usable rows that day agree on one `your_price` and one
   `featuredoffer_price`. Two of our own offers at different prices means "our
   price" is not defined, so no comparison is made.

Both compared numbers come from the SAME source row, so the comparison is
internally consistent by construction. The compared price is carried as
`px_compared_price` and surfaced instead of the spine price wherever the
comparison is shown.
"""
import datetime
import json
import os
import pathlib
from collections import defaultdict

try:
    import psycopg
except ImportError:  # psycopg2 fallback
    import psycopg2 as psycopg

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "04_DATA"
EVID = ROOT / "06_EVIDENCE"

SUB_SOURCE = {"LEDSone": 8, "DCVoltage": 6}
MARKET = {"UK": "23", "DE": "10", "FR": "9", "IT": "14"}
CURRENCY = {"UK": "GBP", "DE": "EUR", "FR": "EUR", "IT": "EUR"}

SIG_ABOVE = "Our price is above the featured offer"
SIG_BELOW = "Our price is at or below the featured offer"


def load_source(asins):
    dsn = os.environ.get("WLP_SOURCE_DB_URL")
    if not dsn:
        raise SystemExit("WLP_SOURCE_DB_URL is not set")
    vals = ",".join("('%s')" % a for a in sorted(asins))
    q = ("WITH k(asin) AS (VALUES " + vals + ") "
         "SELECT e.asin, e.sub_source, e.market_place, e.snapshot_date, e.sku, "
         "       e.currency, e.your_price, e.featuredoffer_price "
         "FROM amazon_fba.excess_inventory_data e JOIN k ON k.asin = e.asin "
         "WHERE e.sub_source IN (6,8) AND e.market_place IN ('23','10','9','14') "
         "  AND e.your_price IS NOT NULL AND e.featuredoffer_price IS NOT NULL")
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(q)
        rows = cur.fetchall()
    idx = defaultdict(lambda: defaultdict(list))
    for asin, ss, mp, sd, sku, curr, yp, fp in rows:
        idx[(asin, ss, mp)][str(sd)].append(
            {"sku": sku, "currency": curr, "your_price": float(yp),
             "featured_price": float(fp)})
    return idx, len(rows)


def evaluate(row, idx):
    """Return (evidence_or_None, reason). evidence is a dict when comparable."""
    mkt = row["marketplace"]
    key = (row["asin"], SUB_SOURCE.get(row["account"]), MARKET.get(mkt))
    bb_date = str(row.get("last_checked") or "")
    by_day = idx.get(key, {})
    if not by_day:
        return None, "No featured-offer price exists for this ASIN/account/marketplace"
    same_day = by_day.get(bb_date, [])
    if not same_day:
        newest = max(by_day) if by_day else "none"
        return None, ("No price snapshot on the Buy Box reading date %s "
                      "(nearest available %s) - stale, not compared" % (bb_date, newest))
    want = CURRENCY.get(mkt)
    same_day = [c for c in same_day if c["currency"] == want]
    if not same_day:
        return None, "Price snapshot currency does not match the %s marketplace" % mkt
    usable = [c for c in same_day if c["your_price"] > 0 and c["featured_price"] > 0]
    if not usable:
        return None, ("Source price is 0.00 (your_price=%.2f) - unusable, not compared"
                      % same_day[0]["your_price"])
    if len({c["your_price"] for c in usable}) > 1:
        prices = sorted({c["your_price"] for c in usable})
        return None, ("Ambiguous: %d of our own offers at different prices (%s) - "
                      "'our price' is not defined for this ASIN"
                      % (len(prices), ", ".join("%.2f" % p for p in prices)))
    if len({c["featured_price"] for c in usable}) > 1:
        return None, "Ambiguous: conflicting featured-offer prices on the same snapshot"
    c0 = usable[0]
    return {"compared_price": c0["your_price"],
            "featured_price": c0["featured_price"],
            "sku": c0["sku"],
            "currency": c0["currency"],
            "snapshot_date": bb_date,
            "source": "ledsone.amazon_fba.excess_inventory_data"}, None


def main():
    rows = json.load(open(DATA / "dashboard_rows.json", encoding="utf-8"))
    targets = [r for r in rows if r.get("featured_price") is not None]
    print("rows carrying price evidence: %d (of %d)" % (len(targets), len(rows)))
    idx, nsrc = load_source({r["asin"] for r in targets})
    print("source rows loaded: %d" % nsrc)

    corrections = []
    stats = defaultdict(int)
    out = []
    for r in rows:
        r2 = dict(r)
        if r.get("featured_price") is None:
            r2["px_status"] = "not_available"
            r2["px_reason"] = "This ASIN is not covered by the FBA Excess Inventory report"
            r2["px_compared_price"] = None
            out.append(r2)
            continue
        ev, reason = evaluate(r, idx)
        sigs = [s for s in (r.get("signals") or []) if s not in (SIG_ABOVE, SIG_BELOW)]
        had = [s for s in (r.get("signals") or []) if s in (SIG_ABOVE, SIG_BELOW)]
        if ev is None:
            r2["px_status"] = "unavailable"
            r2["px_reason"] = reason
            r2["px_compared_price"] = None
            r2["featured_price"] = None          # do not display an uncomparable figure
            r2["px_featured_price_raw"] = r.get("featured_price")
            r2["px_sku"] = None
            r2["signals"] = sigs
            stats["suppressed"] += 1
            stats["reason:" + reason.split(" - ")[0][:46]] += 1
            if had:
                corrections.append({
                    "asin": r["asin"], "account": r["account"],
                    "marketplace": r["marketplace"], "action": "signal removed",
                    "was": had[0], "spine_price": r.get("price"),
                    "old_compared_price": r.get("px_your_price"),
                    "old_featured_price": r.get("featured_price"),
                    "old_px_date": str(r.get("px_date")),
                    "bb_date": str(r.get("last_checked")), "reason": reason})
        else:
            above = ev["compared_price"] > ev["featured_price"]
            # The comparison SIGNAL stays a Buy-Box-loss signal only, as in v001.
            # A YES or NOT VERIFIED row still shows the comparison in its drawer,
            # but must not carry a loss signal that could read as a reason.
            sig = (SIG_ABOVE if above else SIG_BELOW) if r.get("status") == "NO" else None
            r2["px_status"] = "available"
            r2["px_reason"] = None
            r2["px_compared_price"] = ev["compared_price"]
            r2["featured_price"] = ev["featured_price"]
            r2["px_sku"] = ev["sku"]
            r2["px_date"] = ev["snapshot_date"]
            r2["px_your_price"] = ev["compared_price"]
            r2["px_source"] = ev["source"]
            r2["signals"] = sigs + ([sig] if sig else [])
            stats["comparable"] += 1
            if had and had[0] != sig:
                stats["signal flipped"] += 1
                corrections.append({
                    "asin": r["asin"], "account": r["account"],
                    "marketplace": r["marketplace"], "action": "signal corrected",
                    "was": had[0], "now": sig, "spine_price": r.get("price"),
                    "old_compared_price": r.get("px_your_price"),
                    "new_compared_price": ev["compared_price"],
                    "featured_price": ev["featured_price"],
                    "old_px_date": str(r.get("px_date")),
                    "new_px_date": ev["snapshot_date"],
                    "bb_date": str(r.get("last_checked")),
                    "reason": "Recomputed from the snapshot on the Buy Box reading "
                              "date, single unambiguous offer, non-zero prices"})
        out.append(r2)

    json.dump(out, open(DATA / "dashboard_rows_v002.json", "w", encoding="utf-8"),
              ensure_ascii=False)
    json.dump(corrections, open(EVID / "price_corrections.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    ev_out = {r["asin"] + "|" + r["account"] + "|" + r["marketplace"]: {
        "px_status": r["px_status"], "px_reason": r.get("px_reason"),
        "compared_price": r.get("px_compared_price"),
        "featured_price": r.get("featured_price"), "sku": r.get("px_sku"),
        "snapshot_date": str(r.get("px_date"))}
        for r in out if r.get("px_status") in ("available", "unavailable")}
    json.dump(ev_out, open(DATA / "price_evidence_v2.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    print("\n--- result ---")
    print("comparable      : %d" % stats["comparable"])
    print("suppressed      : %d" % stats["suppressed"])
    print("signals flipped : %d" % stats["signal flipped"])
    print("corrections logged: %d" % len(corrections))
    for k in sorted(stats):
        if k.startswith("reason:"):
            print("   %-54s %d" % (k[7:], stats[k]))
    print("\nwritten: dashboard_rows_v002.json, price_evidence_v2.json, "
          "price_corrections.json")
    print("generated_at %s" % datetime.datetime.now().astimezone().isoformat(timespec="seconds"))


if __name__ == "__main__":
    main()
