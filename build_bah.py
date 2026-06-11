#!/usr/bin/env python3
# Generates one BAH-rates landing page per Military Housing Area (~299 pages) from the 2025 dataset.
import json, os, re, urllib.parse

SITE = "https://militarypaytool.com"
DATE = "2026-06-08"
YEAR = "2025"
CF = '<script defer src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "c43478f52cc24acbba0aa708dac34c10"}\'></script>'

s = open('data/bah_2025.js').read()
BAH = json.loads(s[s.index('=')+1: s.rstrip().rstrip(';').rfind('}')+1])
GI = BAH['meta']['grades']
NAMES = BAH['names']

def glabel(g):
    m = re.match(r'^([EWO])(\d{2})(E)?$', g)
    return f"{m.group(1)}-{int(m.group(2))}{('E' if m.group(3) else '')}"

DISPLAY_GRADES = [g for g in GI]  # all grades in dataset order

def money(v): return "$"+format(int(round(v)), ",d") if v is not None else "&mdash;"

def slugify(n):
    s = n.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def deep_loc(code, name):
    snap = {"mhaCode": code, "mhaInput": f"{name}  ({code})"}
    return "/#" + urllib.parse.quote(json.dumps(snap, separators=(',',':')))

STATE_FULL = {"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado",
"CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii",
"ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine",
"MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri",
"MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York",
"NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania",
"RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah",
"VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"}

ABBR = {"AFB","NAS","NS","NSB","NSY","NSA","NWS","MCB","MCAS","MCRD","MCLB","MCAGCC","JB","JBLM","JBSA",
        "JBMDL","ARB","AAF","AAP","AGS","AFS","ANGB","ANG","AFRC","NTC","USAG","NSGA","CG","PMRF","JRB",
        "II","III","IV","DC","US","NSF","NWC","AFCONUS"}
def titlecase_city(name):
    # "SAN DIEGO, CA" -> "San Diego, CA"; keep base abbreviations uppercase
    city, st = name.rsplit(",", 1)
    st = st.strip()
    def tc(words):
        o = []
        for w in words:
            if w == "/": o.append("/")
            elif len(w) == 2 and w.isupper(): o.append(w)      # state code (CA, DC)
            elif w.upper() in ABBR: o.append(w.upper())
            else: o.append(w.capitalize())
        return " ".join(o)
    return tc(city.replace("/", " / ").split()), tc(st.split())

def head(title, desc, path, jsonld):
    url = f"{SITE}{path}"
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/article.css">
<meta property="og:type" content="article"><meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png"><meta property="og:site_name" content="U.S. Military Pay Calculator">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{SITE}/og-image.png">
<script type="application/ld+json">{json.dumps(jsonld)}</script>
{CF}
</head><body>
<header class="bar"><div class="wrap"><span class="seal">&#9733;</span>
<a class="brand" href="/">militarypaytool.com</a>
<a class="cta" href="/">Open calculator &rarr;</a></div></header>
<main>
'''

def foot(related):
    items = "".join(f'<li><a href="{href}">{txt}</a></li>' for txt,href in related)
    return (f'<div class="related"><h2>Related guides</h2><ul>{items}</ul></div></main>\n'
            f'<footer class="foot">BAH rates are official {YEAR} DoD figures (the latest complete public dataset). '
            f'2026 rates average ~4.2% higher &mdash; use the <a href="/">calculator</a> or the DoD BAH lookup for an exact '
            f'current amount. Estimates for planning only; not affiliated with the U.S. Government or DoD. &middot; '
            f'<a href="/bah/">All BAH locations</a> &middot; <a href="/blog/">Pay guides</a></footer>\n</body></html>')

os.makedirs("bah", exist_ok=True)
pages = []   # (slug, city, st, name, code)
seen = set()

valid = [(c,n) for c,n in NAMES.items() if ',' in n and c in BAH['with']]
valid.sort(key=lambda x: x[1])

# ---- first pass: assign slugs + build state -> [(city, slug)] for cross-linking ----
entries = []   # (code, name, city, st, slug)
state_cities = {}
for code, name in valid:
    city, st = titlecase_city(name)
    slug = slugify(name)
    if slug in seen: slug = slug + "-" + code.lower()
    seen.add(slug)
    entries.append((code, name, city, st, slug))
    state_cities.setdefault(st, []).append((city, slug))
for st in state_cities: state_cities[st].sort()

# ---- second pass: generate each page ----
for code, name, city, st, slug in entries:
    stfull = STATE_FULL.get(st, st)
    # internal links to sibling cities in the same state (dense mesh across all BAH pages)
    sibs = [(c, sl) for c, sl in state_cities[st] if sl != slug]
    if sibs:
        shown = sibs[:24]
        nlinks = " &middot; ".join(f'<a href="/bah/{sl}.html">{c}</a>' for c, sl in shown)
        more = (f' &middot; <a href="/bah/#{st.lower()}">+{len(sibs)-24} more in {stfull}</a>'
                if len(sibs) > 24 else '')
        neighbor_html = (f'<h2>Other BAH rates in {stfull}</h2>'
                         f'<p style="line-height:2">{nlinks}{more}</p>')
    else:
        neighbor_html = f'<p><a href="/bah/">Browse BAH rates in other states &rarr;</a></p>'
    w = BAH['with'][code]; wo = BAH['without'][code]
    # rate range
    allr = [x for x in w+wo if x]
    lo, hi = money(min(allr)), money(max(allr))
    def gi(g): return GI.index(g)
    e5w, e5wo = w[gi('E05')], wo[gi('E05')]
    e7w, e7wo = w[gi('E07')], wo[gi('E07')]
    o3w, o3wo = w[gi('O03')], wo[gi('O03')]
    # table
    rows = ""
    for g in DISPLAY_GRADES:
        rows += f"<tr><td>{glabel(g)}</td><td>{money(w[gi(g)])}</td><td>{money(wo[gi(g)])}</td></tr>"
    table = (f'<div class="tablewrap"><table class="pay"><thead><tr><th>Pay grade</th>'
             f'<th>With dependents</th><th>Without dependents</th></tr></thead><tbody>{rows}</tbody></table></div>')
    place = f"{city}, {st}"
    title = f"{place} BAH Rates {YEAR} | Basic Allowance for Housing"
    desc = (f"{YEAR} BAH rates for {place} by pay grade, with and without dependents. "
            f"An E-5 gets {money(e5w)}/mo with dependents. BAH is tax-free.")
    faq_pairs = [
        (f"How much is BAH in {place} for an E-5?",
         f"In {YEAR}, BAH for an E-5 in {place} is <b>{money(e5w)}/month with dependents</b> and {money(e5wo)}/month without dependents."),
        (f"How much is BAH for an E-7 in {place}?",
         f"An E-7 in {place} receives <b>{money(e7w)}/month with dependents</b> ({money(e7wo)} without) in {YEAR}."),
        (f"Is BAH in {place} taxable?",
         "No. BAH is not subject to federal income tax, so you keep the full amount."),
    ]
    faq_html = "<h2>Frequently asked questions</h2>" + "".join(
        f'<p class="faq-q">{q}</p><p>{a}</p>' for q,a in faq_pairs)
    faq_ld = {"@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a.replace("<b>","").replace("</b>","")}}
        for q,a in faq_pairs]}
    art_ld = {"@type":"Article","headline":f"{place} BAH Rates {YEAR}","description":desc,
              "datePublished":DATE,"dateModified":DATE,"mainEntityOfPage":f"{SITE}/bah/{slug}.html",
              "image":f"{SITE}/og-image.png","author":{"@type":"Organization","name":"militarypaytool.com"},
              "publisher":{"@type":"Organization","name":"militarypaytool.com","logo":{"@type":"ImageObject","url":f"{SITE}/favicon.svg"}}}
    bc_ld = {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"BAH Rates","item":SITE+"/bah/"},
        {"@type":"ListItem","position":3,"name":place,"item":f"{SITE}/bah/{slug}.html"}]}
    jsonld = {"@context":"https://schema.org","@graph":[art_ld, faq_ld, bc_ld]}
    body = f'''<div class="crumb"><a href="/">Home</a> &rsaquo; <a href="/bah/">BAH Rates</a> &rsaquo; {place}</div>
<article>
<h1>{place} BAH Rates ({YEAR})</h1>
<p class="meta">Updated {DATE} &middot; Official {YEAR} DoD rates</p>
<p class="lead"><strong>Basic Allowance for Housing (BAH)</strong> for {place} in {YEAR} ranges from
<strong>{lo} to {hi} per month</strong>, depending on your pay grade and whether you have dependents. BAH is
<strong>tax-free</strong>.</p>
<p>The table below shows the full {YEAR} monthly BAH rates for {place} (Military Housing Area {code}) for every pay grade,
both with and without dependents.</p>
{table}
<p class="callout">For example, an <strong>E-5</strong> in {place} receives <strong>{money(e5w)}/month with dependents</strong>
or {money(e5wo)}/month without. An <strong>O-3</strong> receives {money(o3w)} / {money(o3wo)}.</p>
{('<div class="cta-box"><p>See your full take-home pay for ' + place + ' &mdash; pre-loaded with this location, plus basic pay, BAS, and taxes.</p><a href="' + deep_loc(code, name) + '">Calculate my ' + place.split(",")[0] + ' pay &rarr;</a></div>')}
<h2>How BAH works in {place}</h2>
<p>BAH is set by the cost of rental housing in the {place} Military Housing Area, your pay grade, and your dependent
status. It is paid monthly and is not taxed. Higher ranks and members with dependents receive more. Because it reflects
local rents, {place}'s rates differ from other locations &mdash; compare yours in the <a href="/">calculator</a>.</p>
<p>These are the official <strong>{YEAR}</strong> rates (the latest complete public dataset). 2026 BAH rose about 4.2% on
average nationwide; for an exact current figure, enter your ZIP in the <a href="/">military pay calculator</a> or check the
DoD BAH lookup. Learn more in our <a href="/blog/2026-bah-rates-explained.html">2026 BAH guide</a>.</p>
{neighbor_html}
{faq_html}
</article>
'''
    related = [("All BAH rates by location","/bah/"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html"),
               ("BAH with vs without dependents","/blog/bah-with-vs-without-dependents.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html")]
    html = head(title, desc, f"/bah/{slug}.html", jsonld) + body + foot(related)
    open(f"bah/{slug}.html","w").write(html)
    pages.append((slug, city, st, name, code))

# -------- HUB grouped by state --------
bystate = {}
for slug,city,st,name,code in pages:
    bystate.setdefault(st, []).append((city, slug))
hub_ld = {"@context":"https://schema.org","@graph":[
    {"@type":"CollectionPage","name":f"{YEAR} BAH Rates by Location","url":f"{SITE}/bah/"},
    {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"BAH Rates","item":SITE+"/bah/"}]}]}
sections = ""
for st in sorted(bystate, key=lambda s: STATE_FULL.get(s, s)):
    cities = sorted(bystate[st])
    links = " &middot; ".join(f'<a href="/bah/{slug}.html">{city}</a>' for city,slug in cities)
    sections += f'<h2 id="{st.lower()}">{STATE_FULL.get(st, st)}</h2><p>{links}</p>'
hub = head(f"{YEAR} BAH Rates by Location (All Military Housing Areas) | militarypaytool.com",
           f"Browse {YEAR} Basic Allowance for Housing (BAH) rates for {len(pages)}+ U.S. military housing areas by city and state. Tax-free housing allowance by pay grade.",
           "/bah/", hub_ld)
hub += f'''<div class="crumb"><a href="/">Home</a> &rsaquo; BAH Rates</div>
<article>
<h1>{YEAR} BAH Rates by Location</h1>
<p class="lead">Official {YEAR} <strong>Basic Allowance for Housing (BAH)</strong> rates for {len(pages)} U.S. military
housing areas. Pick your city to see the full rate table by pay grade (with and without dependents), or use the
<a href="/">calculator</a> to get your exact take-home pay by ZIP code.</p>
<div class="cta-box"><p>Don't see your city, or want your exact rate? Enter your ZIP in the calculator.</p><a href="/">Open the pay calculator &rarr;</a></div>
{sections}
</article>
'''
hub += foot([("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
             ("BAH with vs without dependents","/blog/bah-with-vs-without-dependents.html"),
             ("2026 military pay chart","/blog/2026-military-pay-chart.html")])
open("bah/index.html","w").write(hub)

# -------- merge into sitemap.xml (keep existing main+blog urls, add bah) --------
existing = []
if os.path.exists("sitemap.xml"):
    existing = re.findall(r'<loc>([^<]+)</loc>', open("sitemap.xml").read())
existing = [u for u in existing if "/bah/" not in u]
locs = list(existing) + [f"{SITE}/bah/"] + [f"{SITE}/bah/{slug}.html" for slug,_,_,_,_ in pages]
# dedup preserve order
seen2=set(); ordered=[]
for u in locs:
    if u not in seen2: seen2.add(u); ordered.append(u)
def pri(u):
    if u==f"{SITE}/" : return "1.0"
    if u.endswith("/blog/") or u.endswith("/bah/"): return "0.9"
    if "/blog/" in u: return "0.8"
    return "0.6"
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in ordered:
    sm += f'  <url><loc>{u}</loc><lastmod>{DATE}</lastmod><priority>{pri(u)}</priority></url>\n'
sm += '</urlset>\n'
open("sitemap.xml","w").write(sm)

print(f"wrote {len(pages)} BAH pages + bah/index.html")
print(f"sitemap.xml now has {len(ordered)} URLs")
print("sample:", pages[0][0], "|", pages[100][0])
