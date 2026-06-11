#!/usr/bin/env python3
# Generates SEO article pages for militarypaytool.com under blog/.
import json, os, urllib.parse

SITE = "https://militarypaytool.com"
DATE = "2026-06-08"
CF = '<script defer src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "c43478f52cc24acbba0aa708dac34c10"}\'></script>'

# ---- load 2026 basic pay ----
s = open('data/basic_pay_2026.js').read()
BP = json.loads(s[s.index('=')+1: s.rstrip().rstrip(';').rfind('}')+1])
YOS = ["<2","2","3","4","6","8","10","12","14","16","18","20","22","24","26"]
YOS_LBL = {"<2":"&lt;2","2":"2","3":"3","4":"4","6":"6","8":"8","10":"10","12":"12","14":"14","16":"16","18":"18","20":"20","22":"22","24":"24","26":"26"}

def money(v): return "$"+format(int(round(v)), ",d") if v is not None else "—"

def deep(grade=None, mode=None, extra=None):
    snap = {}
    if grade: snap["grade"] = grade
    if mode: snap["mode"] = mode
    if extra: snap.update(extra)
    return "/#" + urllib.parse.quote(json.dumps(snap, separators=(',',':')))

def pay_table(grades, cols=YOS, caption=None):
    th = "".join(f"<th>{YOS_LBL[c]}</th>" for c in cols)
    rows = ""
    for g in grades:
        tds = "".join(f"<td>{money(BP[g].get(c)) if BP[g].get(c) is not None else '—'}</td>" for c in cols)
        rows += f"<tr><td>{g}</td>{tds}</tr>"
    cap = f"<caption>{caption}</caption>" if caption else ""
    return (f'<div class="tablewrap"><table class="pay">{cap}'
            f'<thead><tr><th>Grade</th>{th}</tr></thead><tbody>{rows}</tbody></table></div>')

def rank_table(grade, cols=("<2","2","3","4","6","8","10","12","14","16","18","20")):
    rows = "".join(f"<tr><td>Over {c} years</td><td>{money(BP[grade].get(c))}</td></tr>"
                   if c!="<2" else f"<tr><td>Less than 2 years</td><td>{money(BP[grade].get(c))}</td></tr>"
                   for c in cols)
    return (f'<div class="tablewrap"><table class="pay"><thead><tr><th>Years of service</th>'
            f'<th>Monthly basic pay</th></tr></thead><tbody>{rows}</tbody></table></div>')

def head(title, desc, slug, crumb, jsonld):
    url = f"{SITE}/blog/{slug}"
    j = json.dumps(jsonld)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/article.css">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta property="og:site_name" content="U.S. Military Pay Calculator">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{SITE}/og-image.png">
<script type="application/ld+json">{j}</script>
{CF}
</head>
<body>
<header class="bar"><div class="wrap"><span class="seal">&#9733;</span>
<a class="brand" href="/">militarypaytool.com</a>
<a class="cta" href="/">Open calculator &rarr;</a></div></header>
<main>
<div class="crumb"><a href="/">Home</a> &rsaquo; <a href="/blog/">Articles</a> &rsaquo; {crumb}</div>
<article>
'''

def cta(text, href):
    return f'<div class="cta-box"><p>{text}</p><a href="{href}">Calculate my pay &rarr;</a></div>'

def faq_block(pairs):
    html = '<h2>Frequently asked questions</h2>'
    for q,a in pairs:
        html += f'<p class="faq-q">{q}</p><p>{a}</p>'
    ld = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a_plain}}
        for (q,a),a_plain in zip(pairs,[p[1].replace("<b>","").replace("</b>","").replace("&amp;","and") for p in pairs])]}
    return html, ld

def article_ld(title, desc, slug):
    return {"@context":"https://schema.org","@type":"Article",
            "headline":title,"description":desc,
            "datePublished":DATE,"dateModified":DATE,
            "mainEntityOfPage":f"{SITE}/blog/{slug}",
            "image":f"{SITE}/og-image.png",
            "author":{"@type":"Organization","name":"militarypaytool.com"},
            "publisher":{"@type":"Organization","name":"militarypaytool.com",
                         "logo":{"@type":"ImageObject","url":f"{SITE}/favicon.svg"}}}

def foot(related):
    items = "".join(f'<li><a href="{href}">{txt}</a></li>' for txt,href in related)
    return (f'</article>\n<div class="related"><h2>Related guides</h2><ul>{items}</ul></div>\n</main>\n'
            f'<footer class="foot">Estimates for planning only &mdash; your Leave and Earnings Statement (LES) '
            f'is the official source. Not affiliated with the U.S. Government or Department of Defense. &middot; '
            f'<a href="/">2026 Military Pay Calculator</a> &middot; <a href="/blog/">All articles</a></footer>\n</body></html>')

os.makedirs("blog", exist_ok=True)
ARTICLES = []  # (slug, title, desc, cardblurb)

def write(slug, title, desc, crumb, body_html, faq=None, related=None, blurb=""):
    ld = [article_ld(title, desc, slug)]
    body = body_html
    if faq:
        fh, fl = faq_block(faq); body += fh; ld.append(fl)
    jsonld = ld[0] if len(ld)==1 else {"@context":"https://schema.org","@graph":ld}
    html = head(title, desc, slug, crumb, jsonld) + body + foot(related or [])
    open(f"blog/{slug}", "w").write(html)
    ARTICLES.append((slug, title, desc, blurb or desc))
    print("wrote blog/"+slug)

# ===================== 1. 2026 PAY CHART (flagship) =====================
body = f'''<h1>2026 Military Pay Chart: Basic Pay for Every Rank</h1>
<p class="meta">Updated {DATE} &middot; Effective January 1, 2026</p>
<p class="lead">The 2026 military pay tables took effect on January 1, 2026, with a <strong>3.8% across-the-board raise</strong>
to basic pay. Below is the full 2026 monthly basic pay chart for enlisted members, warrant officers, and commissioned
officers, straight from the Department of Defense rates.</p>
<p>Basic pay is only one part of your paycheck. Most service members also receive tax-free allowances
(<a href="/blog/2026-bah-rates-explained.html">BAH</a> for housing and BAS for food) plus any special and incentive pays.
To see your full take-home pay, use the free <a href="/">2026 military pay calculator</a>.</p>

<h2>2026 Enlisted Basic Pay (E-1 to E-9)</h2>
{pay_table(["E-1","E-2","E-3","E-4","E-5","E-6","E-7","E-8","E-9"])}
<p class="callout">An E-1 with less than 4 months of service earns a slightly lower rate. All figures are gross monthly
basic pay, rounded to the nearest dollar.</p>

<h2>2026 Warrant Officer Basic Pay (W-1 to W-5)</h2>
{pay_table(["W-1","W-2","W-3","W-4","W-5"])}

<h2>2026 Commissioned Officer Basic Pay (O-1 to O-10)</h2>
{pay_table(["O-1","O-2","O-3","O-4","O-5","O-6","O-7","O-8","O-9","O-10"])}
<p class="callout">Pay for O-7 through O-10 is capped at Level II of the Executive Schedule ($18,808.20/month in 2026).
Officers with prior enlisted service (O-1E, O-2E, O-3E) receive a higher rate &mdash; check the calculator for those.</p>

<h2>How to read the pay chart</h2>
<p>Find your <strong>pay grade</strong> in the left column, then read across to your <strong>years of service</strong>.
Basic pay rises with both rank and time in service, but each grade eventually hits a ceiling (for example, an E-5's
basic pay stops increasing after 12 years). Years of service for pay is based on your pay entry base date, not just
your time in your current rank.</p>

<h2>What the pay chart does not include</h2>
<ul>
<li><strong>BAH</strong> (Basic Allowance for Housing) &mdash; tax-free, varies by ZIP code, grade, and dependents.</li>
<li><strong>BAS</strong> (Basic Allowance for Subsistence) &mdash; $476.95/month enlisted, $328.48/month officer in 2026.</li>
<li><strong>Special &amp; incentive pays</strong> &mdash; hazardous duty, flight, sea, family separation, and more.</li>
</ul>
<p>Because BAH and BAS are tax-free, your real take-home pay is usually higher than the basic-pay number alone.</p>
{cta("Add your ZIP code and allowances to see your real 2026 monthly take-home pay.", "/")}
'''
write("2026-military-pay-chart.html",
      "2026 Military Pay Chart: Basic Pay for Every Rank (E-1 to O-10)",
      "Full 2026 military basic pay chart with the 3.8% raise — monthly pay for every enlisted, warrant, and officer rank by years of service.",
      "2026 Pay Chart", body,
      faq=[("How much is the 2026 military pay raise?","Basic pay increased <b>3.8%</b> for 2026, effective January 1, 2026."),
           ("When does the 2026 pay raise take effect?","The new rates took effect <b>January 1, 2026</b> and appear on the mid-January paycheck."),
           ("Is BAH included in the pay chart?","No. The basic pay chart shows base pay only. BAH and BAS are separate tax-free allowances on top of basic pay.")],
      related=[("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html"),
               ("How much does an E-4 make in 2026?","/blog/how-much-does-an-e4-make-2026.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html")],
      blurb="The full 2026 basic pay chart (3.8% raise) for every enlisted, warrant, and officer rank.")

# ===================== 2. E-5 =====================
body = f'''<h1>How Much Does an E-5 Make in 2026?</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">In 2026 a <strong>Sergeant / Petty Officer Second Class (E-5)</strong> earns between
<strong>{money(BP["E-5"]["<2"])} and {money(BP["E-5"]["12"])} per month</strong> in basic pay, depending on years of
service &mdash; plus tax-free BAH and BAS that push real take-home pay much higher.</p>

<h2>2026 E-5 basic pay by years of service</h2>
{rank_table("E-5")}
<p>An E-5's basic pay maxes out at {money(BP["E-5"]["12"])}/month after 12 years of service. A typical E-5 with
<strong>4 years of service earns {money(BP["E-5"]["4"])}/month</strong> in basic pay (about ${int(round(BP["E-5"]["4"]*12)):,}/year).</p>

<h2>E-5 total pay: basic pay + allowances</h2>
<p>Basic pay is just the start. Most E-5s also receive:</p>
<ul>
<li><strong>BAH</strong> &mdash; tax-free housing allowance based on your ZIP code and whether you have dependents. This can add anywhere from ~$1,200 to over $4,000/month in high-cost areas.</li>
<li><strong>BAS</strong> &mdash; $476.95/month tax-free food allowance.</li>
</ul>
<p>For example, an E-5 with 4 years and dependents stationed in San Diego receives roughly
{money(BP["E-5"]["4"])} basic + ~$3,987 BAH + $476.95 BAS &asymp; <strong>$8,400/month</strong> in total entitlements,
with take-home around $7,600/month after taxes and TSP. Your numbers depend heavily on location.</p>
{cta("See your exact E-5 take-home pay — pre-filled for E-5, just add your ZIP.", deep("E-5"))}

<h2>Why take-home pay is higher than it looks</h2>
<p>Because <strong>BAH and BAS are not taxed</strong>, a large share of an E-5's compensation is tax-free. Only basic
pay (and taxable special pays) are subject to federal income tax, Social Security, and Medicare. Many states also exempt
military pay entirely.</p>
'''
write("how-much-does-an-e5-make-2026.html",
      "How Much Does an E-5 Make in 2026? (Pay + BAH + Take-Home)",
      f"A 2026 E-5 earns {money(BP['E-5']['<2'])}–{money(BP['E-5']['12'])}/month basic pay plus tax-free BAH and BAS. See full E-5 pay by years of service and total take-home.",
      "E-5 Pay", body,
      faq=[("How much does an E-5 make in 2026?",f"An E-5 earns <b>{money(BP['E-5']['<2'])} to {money(BP['E-5']['12'])} per month</b> in basic pay in 2026, plus tax-free BAH and BAS."),
           ("How much does an E-5 with 4 years make?",f"About <b>{money(BP['E-5']['4'])} per month</b> in basic pay, or roughly ${int(round(BP['E-5']['4']*12)):,} per year, before adding BAH and BAS."),
           ("Is E-5 pay taxed?","Only basic pay and taxable special pays are taxed. BAH and BAS are tax-free, and many states exempt military pay.")],
      related=[("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("How much does an E-4 make in 2026?","/blog/how-much-does-an-e4-make-2026.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html")],
      blurb=f"A 2026 E-5 makes {money(BP['E-5']['<2'])}–{money(BP['E-5']['12'])}/mo basic pay — plus BAH & BAS.")

# ===================== 3. E-4 =====================
body = f'''<h1>How Much Does an E-4 Make in 2026?</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">In 2026 a <strong>Corporal / Specialist / Petty Officer Third Class (E-4)</strong> earns between
<strong>{money(BP["E-4"]["<2"])} and {money(BP["E-4"]["6"])} per month</strong> in basic pay, plus tax-free BAH and BAS.</p>

<h2>2026 E-4 basic pay by years of service</h2>
{rank_table("E-4", cols=("<2","2","3","4","6","8","10"))}
<p>An E-4's basic pay tops out at {money(BP["E-4"]["6"])}/month after 6 years. A common E-4 with 3 years earns
<strong>{money(BP["E-4"]["3"])}/month</strong> in basic pay (about ${int(round(BP["E-4"]["3"]*12)):,}/year).</p>

<h2>E-4 total pay with allowances</h2>
<p>On top of basic pay, an E-4 typically receives tax-free <strong>BAH</strong> (varies by ZIP code and dependents)
and <strong>BAS</strong> ($476.95/month). In many locations an E-4's total monthly entitlements land in the
$4,500&ndash;$7,000 range once housing is included.</p>
{cta("See your exact E-4 take-home pay — pre-filled for E-4, just add your ZIP.", deep("E-4"))}

<h2>How E-4 pay grows</h2>
<p>The fastest way to increase your pay is promotion: moving from E-4 to <a href="/blog/how-much-does-an-e5-make-2026.html">E-5</a>
raises basic pay immediately, and E-5 pay keeps climbing with years of service well past where E-4 stops.</p>
'''
write("how-much-does-an-e4-make-2026.html",
      "How Much Does an E-4 Make in 2026? (Pay + BAH + Take-Home)",
      f"A 2026 E-4 earns {money(BP['E-4']['<2'])}–{money(BP['E-4']['6'])}/month basic pay plus tax-free BAH and BAS. Full E-4 pay by years of service.",
      "E-4 Pay", body,
      faq=[("How much does an E-4 make in 2026?",f"An E-4 earns <b>{money(BP['E-4']['<2'])} to {money(BP['E-4']['6'])} per month</b> in basic pay in 2026, plus tax-free BAH and BAS."),
           ("How much does an E-4 with 3 years make?",f"About <b>{money(BP['E-4']['3'])} per month</b> in basic pay, plus allowances.")],
      related=[("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html")],
      blurb=f"A 2026 E-4 makes {money(BP['E-4']['<2'])}–{money(BP['E-4']['6'])}/mo basic pay — plus BAH & BAS.")

# ===================== 4. BAH =====================
body = f'''<h1>2026 BAH Rates: How Basic Allowance for Housing Works</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead"><strong>Basic Allowance for Housing (BAH)</strong> is a tax-free allowance that helps cover the cost of
housing when you don't live in government quarters. For 2026, BAH rates rose about <strong>4.2% on average</strong>,
though the change varies a lot by location.</p>

<h2>What determines your BAH rate</h2>
<p>BAH is set by three factors:</p>
<ul>
<li><strong>Location</strong> &mdash; specifically the ZIP code where you live/work, grouped into Military Housing Areas (MHAs). High-cost cities pay far more.</li>
<li><strong>Pay grade</strong> &mdash; higher ranks receive higher BAH.</li>
<li><strong>Dependents</strong> &mdash; there is a "with dependents" and a "without dependents" rate (the amount doesn't change with the number of dependents).</li>
</ul>
{cta("Enter your ZIP code to look up your 2026 BAH and full take-home pay.", "/")}

<h2>Is BAH taxable?</h2>
<p><strong>No.</strong> BAH is not subject to federal income tax. This is why it's such a valuable part of military
compensation &mdash; a service member receiving $2,000/month in BAH keeps the full $2,000, unlike taxable wages.</p>

<h2>How to look up your exact BAH</h2>
<p>The official source is the DoD BAH rate lookup at travel.dod.mil. The easiest way is to enter your ZIP code into the
<a href="/">military pay calculator</a>, which resolves your location automatically and combines BAH with your basic
pay, BAS, taxes, and deductions to show your real monthly take-home.</p>

<h2>BAH for Reserve and Guard members</h2>
<p>On active-duty orders of 30+ days, reservists receive the local BAH rate. For shorter periods (and for some training),
a separate non-locality rate called <strong>BAH RC/Transit</strong> applies. See our
<a href="/blog/reserve-drill-pay-explained.html">reserve drill pay guide</a> for details.</p>
'''
write("2026-bah-rates-explained.html",
      "2026 BAH Rates Explained: Basic Allowance for Housing by ZIP",
      "How 2026 BAH works: tax-free housing allowance set by ZIP code, pay grade, and dependents. 2026 rates rose ~4.2%. Look up your BAH instantly.",
      "BAH Rates", body,
      faq=[("Is BAH taxable?","No. BAH is not subject to federal income tax, which makes it one of the most valuable parts of military pay."),
           ("How much did BAH go up in 2026?","BAH rose about <b>4.2% on average</b> for 2026, though the change varies by location."),
           ("Does BAH change with number of dependents?","No. There is one 'with dependents' rate and one 'without dependents' rate per grade and location; it does not scale with how many dependents you have.")],
      related=[("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html"),
               ("Reserve & Guard drill pay explained","/blog/reserve-drill-pay-explained.html")],
      blurb="How 2026 BAH works — tax-free, set by ZIP, grade, and dependents.")

# ===================== 5. Drill pay =====================
e5 = BP["E-5"]["4"]; perp = e5/30
body = f'''<h1>Reserve &amp; National Guard Drill Pay Explained (2026)</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Reserve and National Guard pay works differently from active duty. Instead of a monthly salary, you're paid
by the <strong>drill period</strong> &mdash; and each period is worth <strong>1/30 of a month's basic pay</strong>.</p>

<h2>How drill pay is calculated</h2>
<p>One 4-hour <strong>drill period</strong> = 1/30 of your monthly basic pay. A normal drill weekend is
<strong>4 periods</strong> (two on Saturday, two on Sunday), so a weekend pays about 4 days of basic pay. A typical year
includes about <strong>48 drill periods</strong> (one weekend a month) plus <strong>~14 days of Annual Training</strong>.</p>
<p>Example: a 2026 <strong>E-5 with 4 years</strong> has monthly basic pay of {money(e5)}, so:</p>
<ul>
<li>One drill period &asymp; <strong>{money(perp)}</strong></li>
<li>One drill weekend (4 periods) &asymp; <strong>{money(perp*4)}</strong></li>
<li>48 drill periods/year &asymp; <strong>{money(perp*48)}</strong></li>
</ul>
<p class="callout">Drills pay <strong>basic pay only</strong> &mdash; no BAH or BAS. Annual Training, however, is paid like
active duty (basic pay + BAS + BAH).</p>
{cta("Switch to reserve mode and estimate your drill pay + retirement points.", deep(mode="reserve"))}

<h2>Annual Training and BAH</h2>
<p>During Annual Training (AT) you're on active-duty orders and earn daily basic pay plus BAS and BAH. For orders under
30 days, a non-locality rate (BAH RC/Transit) applies; 30+ days uses your local BAH rate.</p>

<h2>Retirement points and "good years"</h2>
<p>Reservists earn <strong>retirement points</strong>, not just pay: 1 point per drill period, 1 per AT day, plus 15
membership points per year. A year with <strong>50+ points is a "good year,"</strong> and 20 good years generally
qualify you for Reserve retired pay starting around age 60. Your total career points &divide; 360 approximates your
equivalent years of service for the pension formula.</p>
'''
write("reserve-drill-pay-explained.html",
      "Reserve & National Guard Drill Pay Explained (2026)",
      "How Reserve and Guard drill pay works in 2026: each drill period pays 1/30 of monthly basic pay. Calculate drill pay, Annual Training, and retirement points.",
      "Drill Pay", body,
      faq=[("How is drill pay calculated?","Each 4-hour drill period pays <b>1/30 of your monthly basic pay</b>. A normal drill weekend is 4 periods."),
           ("How much is one drill weekend?",f"For a 2026 E-5 with 4 years, a 4-period weekend is about <b>{money(perp*4)}</b>. It scales with your rank and years of service."),
           ("What is a good year for reserve retirement?","A year with at least <b>50 retirement points</b>. You earn 1 point per drill period, 1 per Annual Training day, and 15 membership points per year.")],
      related=[("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html")],
      blurb="How Reserve/Guard drill pay works — 1/30 of basic pay per period, plus retirement points.")

# ===================== BLOG INDEX =====================
cards = ""
for slug,title,desc,blurb in ARTICLES:
    cards += f'<li><a href="/blog/{slug}"><strong>{title}</strong></a><br><span class="bl">{blurb}</span></li>'
idx_ld = {"@context":"https://schema.org","@type":"CollectionPage","name":"Military Pay Guides & 2026 Pay Charts",
          "url":f"{SITE}/blog/"}
idx = head("Military Pay Guides & 2026 Pay Charts | militarypaytool.com",
           "Free guides to 2026 U.S. military pay: pay charts by rank, BAH rates, drill pay, and take-home pay for active duty and reserve.",
           "", "Articles", idx_ld).replace('<div class="crumb"><a href="/">Home</a> &rsaquo; <a href="/blog/">Articles</a> &rsaquo; Articles</div>',
           '<div class="crumb"><a href="/">Home</a> &rsaquo; Articles</div>')
idx += f'''<h1>Military Pay Guides</h1>
<p class="lead">Free, plain-English guides to how U.S. military pay works in 2026 &mdash; for active duty and Reserve/National Guard.</p>
<style>.bloglist{{list-style:none;padding:0}} .bloglist li{{padding:14px 0;border-bottom:1px solid var(--line)}} .bloglist .bl{{color:var(--muted);font-size:.9rem}}</style>
<ul class="bloglist">{cards}</ul>
{cta("Skip the reading — calculate your 2026 take-home pay now.", "/")}
'''
idx += foot([("2026 Military Pay Calculator (home)","/")])
# fix canonical/og url for index (slug empty -> /blog/)
idx = idx.replace(f"{SITE}/blog/\"", f"{SITE}/blog/\"")
open("blog/index.html","w").write(idx)
print("wrote blog/index.html")

# ===================== SITEMAP =====================
urls = [("/","1.0"),("/blog/","0.9")] + [(f"/blog/{s}","0.8") for s,_,_,_ in ARTICLES]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for loc,pri in urls:
    sm += f'  <url><loc>{SITE}{loc}</loc><lastmod>{DATE}</lastmod><priority>{pri}</priority></url>\n'
sm += '</urlset>\n'
open("sitemap.xml","w").write(sm)
print("wrote sitemap.xml with", len(urls), "urls")
print("\nARTICLES:", [a[0] for a in ARTICLES])
