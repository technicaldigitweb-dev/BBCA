"""Phase 4 - Buy Box loss reason investigation.

Adds a structured, evidence-backed reason block to every row of the corrected
dataset. Reads 04_DATA/dashboard_rows_v002.json, writes it back in place with the
reason fields added (the ORIGINAL dashboard_rows.json is never touched).

Hard rules honoured here
------------------------
* The source requirement cites "checks 1 to 8" but never defines them. That list is
  NOT invented. `official_reason` is therefore "Unknown" for every row.
* `possible_reason` is a hypothesis carried separately, and ALL applicable
  hypotheses are kept visible - no first-match priority is applied, because the
  priority order is exactly what is undefined.
* Correlation is never promoted to cause. The wording of every hypothesis says what
  was observed, not why Amazon awarded the Featured Offer.
* Dimensions with no data source available (seller matching, Prime/fulfilment,
  competing offers) are recorded as explicit evidence GAPS, not as absence of a
  problem.
"""
import datetime
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "04_DATA"

SIG_ABOVE = "Our price is above the featured offer"

# Investigation dimensions and whether a source exists for each (see
# 06_EVIDENCE/live_listing_extraction_validation.md).
GAPS = {
    "seller_account_matching":
        "No Amazon merchant token exists internally or on the page; our account "
        "cannot be matched to the featured offer by identifier",
    "fulfilment_prime_eligibility":
        "No Prime or fulfilment flag exists in any authorized source",
    "competing_seller_offers":
        "Requires a live listing read; Amazon automated access is currently blocked",
    "other_eligibility_issues":
        "No account-health or listing-eligibility source is available",
}


def investigate(r):
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    ev = []
    poss = []
    sources = set()

    if r["status"] != "NO":
        return {
            "official_reason": "Unknown",
            "possible_reason": [],
            "reason_evidence": [],
            "reason_confidence": ("Not investigated - Buy Box ownership is %s for "
                                  "this record" % r["status"]),
            "reason_source": [],
            "reason_evidence_gaps": [],
            "reason_checked_at": now,
        }

    # --- 1. price comparison (corrected in Phase 1) ---
    if r.get("px_status") == "available":
        sources.add("ledsone.amazon_fba.excess_inventory_data")
        cp, fp = r.get("px_compared_price"), r.get("featured_price")
        ev.append("Our offer %.2f vs featured offer %.2f on %s (SKU %s)"
                  % (cp, fp, r.get("px_date"), r.get("px_sku")))
        if SIG_ABOVE in (r.get("signals") or []):
            poss.append("Price higher than the featured offer")
        else:
            ev.append("Our price was at or below the featured offer, so price does "
                      "not explain this loss")
    elif r.get("px_status") == "unavailable":
        ev.append("Price comparison unavailable: " + (r.get("px_reason") or ""))
    else:
        ev.append("Price comparison unavailable: ASIN is not covered by the FBA "
                  "Excess Inventory report (3.8% of the estate is)")

    # --- 2. stock ---
    stock = r.get("stock")
    if stock is not None:
        sources.add("ledsone.listings.amazon_listings.quantity")
        ev.append("Listing quantity %s (warehouse uk_stock %s, fbm_stock %s)"
                  % (stock, r.get("uk_stock"), r.get("fbm_stock")))
        if stock <= 0:
            poss.append("No sellable stock on the listing")

    # --- 3 & 4. listing status / buyability ---
    st = r.get("listing_status")
    if st:
        sources.add("ledsone.listings.amazon_listings.status")
        ev.append("Listing status: %s" % st)
        if st == "Inactive":
            poss.append("Listing inactive")
        elif st == "Discoverable (not buyable)":
            poss.append("Listing discoverable but not buyable")
        elif st in ("Incomplete", "Not Found"):
            poss.append("Listing %s" % st.lower())

    # --- Buy Box reading itself ---
    sources.add("ledsone.business_reports.amz_sales_and_traffic_by_asin.buy_box_percentage")
    ev.append("Buy Box held for %s%% of page views on %s"
              % (r.get("bb_pct"), r.get("last_checked")))

    gaps = [{"dimension": k, "reason": v} for k, v in GAPS.items()]

    if not poss:
        poss = ["Not Determined"]
        conf = ("No usable evidence points to a cause. The loss is real (Buy Box 0%) "
                "but nothing in the available sources explains it.")
    elif len(poss) == 1:
        conf = ("One evidence-backed hypothesis. Supported by the observation above, "
                "but not confirmed as Amazon's reason for awarding the Featured Offer.")
    else:
        conf = ("%d hypotheses are simultaneously supported; the approved priority "
                "order that would choose between them is undefined, so none is "
                "selected." % len(poss))

    return {
        "official_reason": "Unknown",
        "possible_reason": poss,
        "reason_evidence": ev,
        "reason_confidence": conf,
        "reason_source": sorted(sources),
        "reason_evidence_gaps": gaps,
        "reason_checked_at": now,
    }


def main():
    path = DATA / "dashboard_rows_v002.json"
    rows = json.load(open(path, encoding="utf-8"))
    for r in rows:
        r.update(investigate(r))
    json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False)

    no = [r for r in rows if r["status"] == "NO"]
    c = Counter()
    for r in no:
        for p in r["possible_reason"]:
            c[p] += 1
    multi = sum(1 for r in no if len(r["possible_reason"]) > 1)
    print("NO records investigated: %d" % len(no))
    print("official_reason == Unknown for all NO: %s"
          % all(r["official_reason"] == "Unknown" for r in no))
    print("every NO row has evidence or an explicit gap: %s"
          % all(r["reason_evidence"] and r["reason_evidence_gaps"] for r in no))
    print("\npossible_reason distribution (hypotheses, not approved reasons):")
    for k, v in c.most_common():
        print("   %-46s %d" % (k, v))
    print("\nrows with more than one hypothesis kept visible: %d" % multi)
    print("written -> %s" % path.name)


if __name__ == "__main__":
    main()
