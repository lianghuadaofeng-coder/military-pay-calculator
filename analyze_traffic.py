#!/usr/bin/env python3
"""
Daily traffic analysis for militarypaytool.com.

Pulls page-view counts from Cloudflare Web Analytics (RUM) via the GraphQL API,
maps each URL path to its content category, and ranks categories by traffic so
the highest-traffic topic cluster can be expanded next.

Usage:
    CF_ANALYTICS_TOKEN=<token-with-Account-Analytics:Read> python3 analyze_traffic.py [days]

Needs a Cloudflare API token scoped to **Account Analytics: Read** (the DNS-edit
token used for setup does NOT have this permission).
"""
import os, sys, json, datetime, urllib.request

ACCOUNT_ID = "7b9408ee5277084a04365803847d2e16"
SITE_TAG   = "c43478f52cc24acbba0aa708dac34c10"   # Cloudflare Web Analytics beacon site tag
GRAPHQL    = "https://api.cloudflare.com/client/v4/graphql"

# ---- category rules (kept in sync with build_blog.py _cat) ----
CAT_ORDER = [
    ("Policy News (2027 & Reform)", ["2027","fy2027","bah-reform"]),
    ("Home Buying & VA Loans",      ["va-loan","va-home-loan","homebuyer","buy-or-rent","funding-fee"]),
    ("Reserve & National Guard",    ["reserve","national-guard"]),
    ("Pay Charts & Rank Pay",       ["how-much-does-an","how-much-does-a-general","navy-seal","academy-rotc",
                                     "2026-military-pay-chart","warrant-officer-pay","prior-enlisted",
                                     "officer-vs-enlisted","basic-training-pay","does-military-pay-differ","promotion-value"]),
    ("Special & Incentive Pays",    ["special-pays","flight-pay","sea-pay","submarine","deployment-pay","bonuses"]),
    ("Taxes",                       ["combat-zone","states-that-dont","tax-filing"]),
    ("Retirement, Benefits & Total Comp", ["tsp","retirement","sgli","roth","gi-bill","tricare","va-disability",
                                     "separation-severance","total-compensation","civilian-equivalent-rmc",
                                     "continuation","survivor-benefit","sbp","crdp","crsc"]),
    ("Paychecks, Moves & Money Moves", ["pay-dates","how-to-read","why-is-my","military-pay-raise","2025-vs-2026",
                                     "ppm","selling-military-leave","per-diem","scra","basic-needs"]),
    ("Allowances, BAH & Family",    ["bah","bas-rates","cola","on-base","dual-military","dislocation",
                                     "family-allowances","partial-bah","clothing-allowance"]),
]

def category_for(path):
    if path in ("/", "/index.html"): return "Calculator (home)"
    if path.startswith("/bah/"):     return "BAH location pages"
    if path == "/blog/":             return "Blog index"
    if path.startswith("/blog/"):
        slug = path[len("/blog/"):]
        for name, subs in CAT_ORDER:
            if any(s in slug for s in subs): return name
        return "Blog: uncategorized"
    return "Other"

def fetch(token, days):
    to   = datetime.datetime.utcnow()
    frm  = to - datetime.timedelta(days=days)
    q = """
    query($acct:String!,$site:String!,$from:Time!,$to:Time!){
      viewer{ accounts(filter:{accountTag:$acct}){
        rumPageloadEventsAdaptiveGroups(
          filter:{AND:[{datetime_geq:$from},{datetime_leq:$to},{siteTag:$site}]},
          limit:200, orderBy:[count_DESC]
        ){ count dimensions{ requestPath } }
      }}}
    """
    body = json.dumps({"query": q, "variables": {
        "acct": ACCOUNT_ID, "site": SITE_TAG,
        "from": frm.strftime("%Y-%m-%dT%H:%M:%SZ"), "to": to.strftime("%Y-%m-%dT%H:%M:%SZ")}}).encode()
    req = urllib.request.Request(GRAPHQL, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    if d.get("errors"):
        raise SystemExit("GraphQL errors: " + json.dumps(d["errors"]))
    rows = d["data"]["viewer"]["accounts"][0]["rumPageloadEventsAdaptiveGroups"]
    return [(g["dimensions"]["requestPath"], g["count"]) for g in rows]

def main():
    token = os.environ.get("CF_ANALYTICS_TOKEN")
    if not token:
        sys.exit("Set CF_ANALYTICS_TOKEN (Cloudflare API token with Account Analytics: Read).")
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    rows = fetch(token, days)
    total = sum(c for _, c in rows)
    by_cat, top_pages = {}, []
    for path, c in rows:
        by_cat[category_for(path)] = by_cat.get(category_for(path), 0) + c
        if path.startswith("/blog/") and path != "/blog/":
            top_pages.append((c, path))
    print(f"=== militarypaytool.com traffic — last {days} day(s) — {total} pageviews ===\n")
    print("By category (highest traffic first):")
    ranked = sorted(by_cat.items(), key=lambda x: -x[1])
    for name, c in ranked:
        bar = "#" * min(40, c)
        print(f"  {c:6}  {name:34} {bar}")
    blog_cats = [(n, c) for n, c in ranked if n not in
                 ("Calculator (home)", "BAH location pages", "Blog index", "Other")]
    print("\nTop blog articles:")
    for c, p in sorted(top_pages, reverse=True)[:15]:
        print(f"  {c:5}  {p}")
    if blog_cats:
        print(f"\n>>> EXPAND NEXT: '{blog_cats[0][0]}' (highest-traffic article category).")
    else:
        print("\n>>> Not enough article traffic yet to pick a category — check back in a couple of weeks.")

if __name__ == "__main__":
    main()
