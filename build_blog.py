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
def money2(v): return "$"+format(v, ",.2f")

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

def breadcrumb_ld(slug, crumb):
    return {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"Military Pay Guides","item":SITE+"/blog/"},
        {"@type":"ListItem","position":3,"name":crumb,"item":f"{SITE}/blog/{slug}"}]}

def foot(related):
    items = "".join(f'<li><a href="{href}">{txt}</a></li>' for txt,href in related)
    return (f'</article>\n<div class="related"><h2>Related guides</h2><ul>{items}</ul></div>\n</main>\n'
            f'<footer class="foot">Estimates for planning only &mdash; your Leave and Earnings Statement (LES) '
            f'is the official source. Not affiliated with the U.S. Government or Department of Defense. &middot; '
            f'<a href="/">2026 Military Pay Calculator</a> &middot; <a href="/blog/">All articles</a></footer>\n</body></html>')

os.makedirs("blog", exist_ok=True)
ARTICLES = []  # (slug, title, desc, cardblurb)

def write(slug, title, desc, crumb, body_html, faq=None, related=None, blurb=""):
    ld = [article_ld(title, desc, slug), breadcrumb_ld(slug, crumb)]
    body = body_html
    if faq:
        fh, fl = faq_block(faq); body += fh; ld.append(fl)
    jsonld = {"@context":"https://schema.org","@graph":ld}
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

# ===================== RANK ARTICLE HELPER =====================
DEFAULT_RELATED = [("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
                   ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
                   ("2026 military pay raise (3.8%)","/blog/2026-military-pay-raise.html")]

def rank_article(grade, name, slug, cols, ex_col, branch, related=None):
    vals=[BP[grade][c] for c in cols if BP[grade].get(c) is not None]
    lo,hi=money(min(vals)),money(max(vals))
    ex=BP[grade][ex_col]; exyr=int(round(ex*12))
    an="an" if name[0].upper() in "AEIOU" else "a"
    bas = "$476.95/month (enlisted)" if grade[0]=="E" else "$328.48/month (officer)"
    excol_lbl = "less than 2 years" if ex_col=="<2" else f"{ex_col} years"
    body=f'''<h1>How Much Does {name} ({grade}) Make in 2026?</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">In 2026 <strong>{name} ({grade})</strong> earns between <strong>{lo} and {hi} per month</strong> in
basic pay, depending on years of service &mdash; plus tax-free BAH and BAS that raise real take-home pay further.</p>
<p>{branch}</p>
<h2>2026 {grade} basic pay by years of service</h2>
{rank_table(grade, cols)}
<p>{an.capitalize()} {grade} with {excol_lbl} of service earns <strong>{money(ex)}/month</strong> in basic pay
(about ${exyr:,}/year) before allowances.</p>
{cta(f"See your exact {grade} take-home pay &mdash; pre-filled for {grade}, just add your ZIP.", deep(grade))}
<h2>{grade} pay beyond basic pay</h2>
<p>Basic pay is only part of the paycheck. Most {grade}s also receive tax-free <strong>BAH</strong> (housing &mdash;
varies by ZIP code and dependents) and <strong>BAS</strong> ({bas}). Because allowances are not taxed, a {grade}'s real
take-home pay is noticeably higher than the basic-pay figure alone.</p>
'''
    first=name.split("/")[0].strip()
    faq=[(f"How much does {grade} make in 2026?",
          f"{an.capitalize()} {grade} ({first}) earns <b>{lo} to {hi} per month</b> in basic pay in 2026, plus tax-free BAH and BAS."),
         (f"How much does a {grade} make with {ex_col if ex_col!='<2' else 'under 2'} years?",
          f"About <b>{money(ex)} per month</b> in basic pay, plus allowances.")]
    write(slug, f"How Much Does {name} ({grade}) Make in 2026?",
          f"A 2026 {grade} ({first}) earns {lo}-{hi}/month basic pay plus tax-free BAH and BAS. Full {grade} pay by years of service and take-home.",
          f"{grade} Pay", body, faq=faq, related=related or DEFAULT_RELATED,
          blurb=f"A 2026 {grade} ({first}) makes {lo}&ndash;{hi}/mo basic pay, plus BAH &amp; BAS.")

# ===================== 6 RANK ARTICLES =====================
rank_article("E-1","a Private / Airman Basic / Seaman Recruit","how-much-does-an-e1-make-2026.html",
             ["<2"], "<2",
             "E-1 is the entry rank you hold in basic training and your first months of service. E-1 pay is a single flat rate that does not change with years of service.")
rank_article("E-3","a Private First Class / Lance Corporal / Airman First Class","how-much-does-an-e3-make-2026.html",
             ["<2","2","3","4"], "2",
             "E-3 is typically reached within the first year or two of service.")
rank_article("E-6","a Staff Sergeant / Petty Officer First Class","how-much-does-an-e6-make-2026.html",
             ["<2","2","4","6","8","10","12","14","16","18","20"], "8",
             "E-6 is a senior non-commissioned officer (NCO) grade, usually reached after 6&ndash;10 years.")
rank_article("E-7","a Sergeant First Class / Gunnery Sergeant / Chief Petty Officer","how-much-does-an-e7-make-2026.html",
             ["<2","2","4","6","8","10","12","14","16","18","20","22","24"], "12",
             "E-7 is a senior NCO grade and a major career milestone, typically reached after 10&ndash;14 years.")
rank_article("O-1","a Second Lieutenant / Ensign","how-much-does-an-o1-make-2026.html",
             ["<2","2","3"], "<2",
             "O-1 is the entry commissioned-officer grade for new lieutenants and ensigns straight out of commissioning. O-1 basic pay stops increasing after 3 years (most officers promote to O-2 well before then).")
rank_article("O-3","a Captain / Lieutenant","how-much-does-an-o3-make-2026.html",
             ["<2","2","3","4","6","8","10","12","14"], "4",
             "O-3 (Army/Air Force/Marine Captain or Navy Lieutenant) is the rank most company-grade officers hold for several years.")

# ===================== 7. PAY RAISE =====================
def inc(g,c):
    v=BP[g][c]; return v - v/1.038
body=f'''<h1>2026 Military Pay Raise: 3.8% Increase Explained</h1>
<p class="meta">Updated {DATE} &middot; Effective January 1, 2026</p>
<p class="lead">Military basic pay rose <strong>3.8% for 2026</strong>, effective January 1, 2026. The increase applies to
every rank and shows up on the mid-January paycheck.</p>
<h2>What the 3.8% raise means in dollars</h2>
<p>The percentage is the same for everyone, but the dollar amount depends on your basic pay. A few examples (per month):</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>Rank (years)</th><th>2026 basic pay</th><th>Monthly raise</th></tr></thead><tbody>
<tr><td>E-4 (over 4)</td><td>{money(BP["E-4"]["4"])}</td><td>+{money(inc("E-4","4"))}</td></tr>
<tr><td>E-5 (over 6)</td><td>{money(BP["E-5"]["6"])}</td><td>+{money(inc("E-5","6"))}</td></tr>
<tr><td>E-7 (over 12)</td><td>{money(BP["E-7"]["12"])}</td><td>+{money(inc("E-7","12"))}</td></tr>
<tr><td>O-3 (over 6)</td><td>{money(BP["O-3"]["6"])}</td><td>+{money(inc("O-3","6"))}</td></tr>
</tbody></table></div>
<h2>How the military pay raise is set</h2>
<p>By law, the annual military pay raise is tied to the <strong>Employment Cost Index (ECI)</strong>, which tracks
private-sector wage growth. Congress and the President can approve a different figure, but 3.8% is the 2026 increase to
basic pay.</p>
<h2>What about BAH and BAS?</h2>
<p>Allowances change on their own schedules. <strong>BAH</strong> is updated each January based on local housing costs
(up about 4.2% on average for 2026), and <strong>BAS</strong> rose 2.4% (to $476.95 enlisted / $328.48 officer). So your
total raise can differ from 3.8% depending on where you live.</p>
{cta("See your 2026 pay with the new rates applied.", "/")}
'''
write("2026-military-pay-raise.html",
      "2026 Military Pay Raise: 3.8% Increase Explained",
      "The 2026 military pay raise is 3.8%, effective January 1, 2026. See what the increase means in dollars by rank, plus BAH and BAS changes.",
      "Pay Raise", body,
      faq=[("How much is the 2026 military pay raise?","Basic pay increased <b>3.8%</b> for 2026."),
           ("When does the 2026 pay raise start?","It took effect <b>January 1, 2026</b> and appears on the mid-January paycheck."),
           ("Did BAH and BAS also increase?","Yes. BAH rose about 4.2% on average and BAS rose 2.4% to $476.95 (enlisted) and $328.48 (officer).")],
      related=[("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("2026 BAS rates explained","/blog/2026-bas-rates.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html")],
      blurb="The 2026 raise is 3.8% — see the dollar increase by rank.")

# ===================== 8. BAS =====================
body=f'''<h1>2026 BAS Rates: Basic Allowance for Subsistence</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">For 2026, <strong>Basic Allowance for Subsistence (BAS)</strong> is <strong>$476.95/month for enlisted</strong>
members and <strong>$328.48/month for officers</strong> &mdash; a 2.4% increase over 2025. BAS is tax-free.</p>
<h2>2026 BAS rates</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Category</th><th>2026 monthly BAS</th></tr></thead><tbody>
<tr><td>Enlisted</td><td>$476.95</td></tr>
<tr><td>Officer</td><td>$328.48</td></tr>
</tbody></table></div>
<h2>What BAS is for</h2>
<p>BAS is meant to offset the cost of a service member's own meals. Unlike BAH, it does <strong>not</strong> vary by rank
(every enlisted member gets the same rate; every officer gets the same rate) or by location, and it is the same whether or
not you have dependents.</p>
<h2>Is BAS taxable?</h2>
<p>No &mdash; like BAH, <strong>BAS is not subject to federal income tax</strong>. It appears as a separate tax-free line
on your Leave and Earnings Statement (LES).</p>
<h2>Who receives BAS?</h2>
<p>Most active-duty members receive full BAS. Some enlisted members in certain meal situations (for example, those required
to eat in a government dining facility) may have BAS partially offset. Officers always receive the officer rate.</p>
{cta("See your full 2026 pay including BAS, BAH, and taxes.", "/")}
'''
write("2026-bas-rates.html",
      "2026 BAS Rates: Basic Allowance for Subsistence ($476.95 / $328.48)",
      "2026 BAS rates: $476.95/month for enlisted and $328.48/month for officers, up 2.4%. BAS is tax-free and does not vary by rank or location.",
      "BAS Rates", body,
      faq=[("What is the 2026 BAS rate?","$476.95/month for enlisted members and $328.48/month for officers."),
           ("Is BAS taxable?","No. BAS is not subject to federal income tax."),
           ("Does BAS change with rank?","No. All enlisted members receive the same BAS rate, and all officers receive the same rate, regardless of grade or location.")],
      related=[("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("2026 military pay raise (3.8%)","/blog/2026-military-pay-raise.html")],
      blurb="2026 BAS: $476.95 enlisted, $328.48 officer — tax-free.")

# ===================== 9. BAH with vs without dependents =====================
body=f'''<h1>BAH With vs Without Dependents: What's the Difference?</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Every BAH rate comes in two versions: <strong>with dependents</strong> and <strong>without dependents</strong>.
The with-dependents rate is higher &mdash; often <strong>$200&ndash;$600+ more per month</strong> &mdash; but it does not
change based on how many dependents you have.</p>
<h2>How the two rates work</h2>
<p>For each pay grade and location, the Department of Defense publishes one "with dependents" rate and one "without
dependents" rate. If you have <em>any</em> qualifying dependent (a spouse or child), you receive the higher rate. Having
three children pays the same BAH as having one.</p>
<h2>How much more is the with-dependents rate?</h2>
<p>The gap varies by grade and location, but the with-dependents rate is typically a few hundred dollars per month higher.
Junior enlisted members usually see the largest percentage difference. Enter your ZIP code and toggle dependent status in
the <a href="/">calculator</a> to see the exact difference for your situation.</p>
{cta("Compare your BAH with and without dependents by ZIP code.", "/")}
<h2>Special situations</h2>
<ul>
<li><strong>Dual-military couples:</strong> rules determine who claims the with-dependents rate; both generally cannot claim
the same dependent.</li>
<li><strong>Geographic bachelor:</strong> if your family lives apart from your duty station, special rules may apply.</li>
<li><strong>Single with no dependents:</strong> you receive the without-dependents rate, and junior members may live in
the barracks and not receive BAH at all.</li>
</ul>
<p>BAH is tax-free either way &mdash; see our <a href="/blog/2026-bah-rates-explained.html">2026 BAH guide</a> for the basics.</p>
'''
write("bah-with-vs-without-dependents.html",
      "BAH With vs Without Dependents: What's the Difference?",
      "The with-dependents BAH rate is higher than without dependents — often $200–$600+/month more — but it doesn't change with the number of dependents. Compare by ZIP.",
      "BAH Dependents", body,
      faq=[("How much more is BAH with dependents?","It varies by grade and location, but the with-dependents rate is typically a few hundred dollars per month higher than the without-dependents rate."),
           ("Does BAH increase with more children?","No. BAH pays the same with-dependents rate whether you have one dependent or several."),
           ("Is BAH taxable?","No. BAH is tax-free for both the with- and without-dependents rates.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html")],
      blurb="With-dependents BAH is higher — but doesn't scale with number of dependents.")

# ===================== 10. States that don't tax military pay =====================
body=f'''<h1>States That Don't Tax Military Pay (2026)</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Where you claim <strong>legal residence</strong> determines whether your military pay is taxed by a state.
Nine states have <strong>no state income tax at all</strong>, and many more fully exempt active-duty military pay.</p>
<h2>States with no income tax (military pay included)</h2>
<p>These nine states do not tax wage income, so military pay is state-tax-free:</p>
<ul>
<li>Alaska</li><li>Florida</li><li>Nevada</li><li>New Hampshire</li><li>South Dakota</li>
<li>Tennessee</li><li>Texas</li><li>Washington</li><li>Wyoming</li>
</ul>
<p class="callout tip">Because of this, many service members establish <strong>legal residence</strong> in a no-tax state
(such as Texas or Florida) while stationed elsewhere &mdash; legal under the Servicemembers Civil Relief Act (SCRA).</p>
<h2>States that exempt active-duty military pay</h2>
<p>Beyond the nine no-tax states, a large and growing number of states <strong>fully exempt active-duty military pay</strong>
from income tax even though they tax other income. The exact list and conditions change over time, so confirm with your
state's current rules or a base legal/tax office.</p>
<h2>How "state of legal residence" works</h2>
<p>Thanks to the SCRA, you keep your <strong>state of legal residence (SLR / home of record domicile)</strong> when you move
on military orders &mdash; you are not forced to switch to the state where you're stationed. Your SLR is the state that taxes
your military pay (or doesn't).</p>
{cta("Set your state in the calculator to see your real take-home pay.", "/")}
<p style="margin-top:14px"><em>This is general information, not tax advice. Verify your situation with a qualified tax
professional or your installation's legal office.</em></p>
'''
write("states-that-dont-tax-military-pay.html",
      "States That Don't Tax Military Pay (2026)",
      "Nine states have no income tax (Alaska, Florida, Nevada, New Hampshire, South Dakota, Tennessee, Texas, Washington, Wyoming), and many more exempt active-duty military pay.",
      "State Taxes", body,
      faq=[("Which states don't tax military pay?","Nine states have no income tax at all: Alaska, Florida, Nevada, New Hampshire, South Dakota, Tennessee, Texas, Washington, and Wyoming. Many other states also fully exempt active-duty military pay."),
           ("Can I keep a no-tax state as my residence while stationed elsewhere?","Yes. Under the Servicemembers Civil Relief Act (SCRA) you keep your state of legal residence when you move on military orders."),
           ("Is military pay taxed federally?","Yes, basic pay and taxable special pays are subject to federal income tax, but BAH and BAS are tax-free.")],
      related=[("2026 military pay chart (all ranks)","/blog/2026-military-pay-chart.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html")],
      blurb="The 9 no-income-tax states + how military state residence (SCRA) works.")

# ===================== 6 MORE RANK ARTICLES =====================
rank_article("E-2","a Private / Seaman Apprentice / Airman","how-much-does-an-e2-make-2026.html",
             ["<2"], "<2",
             "E-2 is typically reached after about six months of service. E-2 basic pay is a single flat rate that does not change with years of service.")
rank_article("E-8","a Master Sergeant / First Sergeant / Senior Chief Petty Officer","how-much-does-an-e8-make-2026.html",
             ["8","10","12","14","16","18","20","22","24","26"], "16",
             "E-8 is a senior enlisted leadership grade, typically reached after 14&ndash;18 years of service. The pay table for E-8 starts at 8 years of service.")
rank_article("E-9","a Sergeant Major / Master Chief / Chief Master Sergeant","how-much-does-an-e9-make-2026.html",
             ["10","12","14","16","18","20","22","24","26"], "20",
             "E-9 is the highest enlisted pay grade, normally reached after 18&ndash;22 years. The pay table for E-9 starts at 10 years of service.")
rank_article("O-2","a First Lieutenant / Lieutenant Junior Grade","how-much-does-an-o2-make-2026.html",
             ["<2","2","3","4","6"], "2",
             "O-2 is usually reached about 18&ndash;24 months after commissioning. O-2 basic pay stops increasing after 6 years (most officers promote to O-3 before then).")
rank_article("O-4","a Major / Lieutenant Commander","how-much-does-an-o4-make-2026.html",
             ["<2","2","3","4","6","8","10","12","14","16","18"], "10",
             "O-4 is a field-grade officer rank, typically reached around the 10-year mark.")
rank_article("O-5","a Lieutenant Colonel / Commander","how-much-does-an-o5-make-2026.html",
             ["<2","2","3","4","6","8","10","12","14","16","18","20","22"], "16",
             "O-5 is a senior field-grade rank, often a battalion-command or ship-command level, typically reached around 15&ndash;17 years.")

# ===================== TOPIC: TSP =====================
body=f'''<h1>Military TSP Explained: Matching, Limits &amp; Roth vs Traditional (2026)</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">The <strong>Thrift Savings Plan (TSP)</strong> is the military's 401(k)-style retirement account. Under the
Blended Retirement System (BRS), the government adds up to <strong>5% of your basic pay</strong> on top of your own
contributions &mdash; free money if you contribute at least 5%.</p>
<h2>How the BRS match works</h2>
<ul>
<li><strong>1% automatic</strong> &mdash; the government deposits 1% of basic pay even if you contribute nothing.</li>
<li><strong>Up to 4% matching</strong> &mdash; dollar-for-dollar on your first 3%, 50 cents per dollar on the next 2%.</li>
<li><strong>Total: 5%</strong> of basic pay when you contribute 5% yourself.</li>
</ul>
<p class="callout tip">Rule of thumb: contribute <strong>at least 5% of basic pay</strong>. Anything less leaves matching
money on the table.</p>
<h2>2026 contribution limit</h2>
<p>The elective deferral limit for 2026 is <strong>$24,500</strong>. Members in a combat zone may be able to contribute
beyond that toward the higher annual additions limit (tax-exempt contributions).</p>
<h2>Roth vs Traditional TSP</h2>
<ul>
<li><strong>Traditional</strong>: contributions reduce taxable income now; withdrawals taxed in retirement.</li>
<li><strong>Roth</strong>: contributions are taxed now; qualified withdrawals are tax-free later.</li>
</ul>
<p>Junior members in low tax brackets often favor <strong>Roth</strong> (you pay little tax today), and combat-zone pay
contributed to Roth can be tax-free going in <em>and</em> coming out. Higher earners may prefer Traditional. The
<a href="/">calculator</a> lets you toggle Roth vs Traditional and see the paycheck impact.</p>
{cta("Model your TSP contribution and see the paycheck impact.", "/")}
'''
write("military-tsp-explained.html",
      "Military TSP Explained: BRS Matching, 2026 Limits, Roth vs Traditional",
      "How the military TSP works in 2026: BRS gives up to 5% of basic pay in government contributions, the elective limit is $24,500, and Roth vs Traditional changes your paycheck.",
      "TSP", body,
      faq=[("How much does the military match in TSP?","Under BRS the government contributes up to <b>5% of basic pay</b>: 1% automatic plus up to 4% matching when you contribute 5%."),
           ("What is the 2026 TSP contribution limit?","The elective deferral limit is <b>$24,500</b> for 2026."),
           ("Should I do Roth or Traditional TSP?","Junior members in low tax brackets often favor Roth; higher earners may prefer Traditional. Combat-zone contributions to Roth can be tax-free in and out.")],
      related=[("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("Combat zone tax exclusion","/blog/combat-zone-tax-exclusion.html")],
      blurb="BRS matches up to 5% of basic pay — how TSP works and the 2026 limit.")

# ===================== TOPIC: CZTE =====================
body=f'''<h1>Combat Zone Tax Exclusion (CZTE): How Combat Pay Becomes Tax-Free</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Serve even <strong>one day</strong> in a designated combat zone during a month and your military pay for
that entire month can be <strong>excluded from federal income tax</strong>. For enlisted members and warrant officers,
the exclusion is unlimited; for officers it's capped.</p>
<h2>Who gets what</h2>
<ul>
<li><strong>Enlisted &amp; warrant officers:</strong> all basic pay and most special pays for the month are federally tax-free.</li>
<li><strong>Commissioned officers:</strong> the exclusion is capped at the highest enlisted basic pay rate plus $225
hostile-fire/imminent-danger pay (about <strong>$10,954/month in 2026</strong>). Pay above the cap is taxed normally.</li>
</ul>
<h2>What CZTE does <em>not</em> change</h2>
<p class="callout"><strong>FICA still applies.</strong> Social Security (6.2%) and Medicare (1.45%) are still withheld from
basic pay even in a combat zone. BAH and BAS were already tax-free.</p>
<h2>Side benefits</h2>
<ul>
<li><strong>Roth TSP supercharge:</strong> combat-zone pay contributed to Roth TSP is tax-free going in and, if qualified, tax-free coming out.</li>
<li><strong>Higher TSP ceiling:</strong> combat-zone months allow contributions beyond the normal elective limit.</li>
<li><strong>State taxes:</strong> most states follow the federal exclusion, and many exempt military pay anyway.</li>
</ul>
{cta("Toggle 'Combat Zone Tax Exclusion' in the calculator to see your deployed take-home pay.", "/")}
'''
write("combat-zone-tax-exclusion.html",
      "Combat Zone Tax Exclusion (CZTE): How Combat Pay Becomes Tax-Free",
      "One day in a designated combat zone makes the whole month's military pay federally tax-free — unlimited for enlisted, capped near $10,954/month for officers in 2026. FICA still applies.",
      "CZTE", body,
      faq=[("Is combat pay tax-free?","Yes. Pay earned in a designated combat zone is excluded from federal income tax — fully for enlisted members and warrant officers, capped for officers."),
           ("Do I pay Social Security and Medicare in a combat zone?","Yes. FICA (6.2% Social Security + 1.45% Medicare) still applies to basic pay even when CZTE makes it income-tax-free."),
           ("How much of an officer's pay is excluded?","Up to the highest enlisted basic pay plus $225 IDP — about $10,954/month in 2026. Pay above that is taxed normally.")],
      related=[("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Military TSP explained","/blog/military-tsp-explained.html"),
               ("States that don't tax military pay","/blog/states-that-dont-tax-military-pay.html")],
      blurb="One day in a combat zone = the whole month federally tax-free (officers capped).")

# ===================== TOPIC: RETIREMENT =====================
body=f'''<h1>Military Retirement: BRS vs High-3, and What 20 Years Is Worth</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Military retired pay is a percentage of your <strong>"High-3"</strong> &mdash; the average of your highest
36 months of basic pay. Which percentage depends on your retirement system: the legacy <strong>High-3 system (2.5%/year)</strong>
or the <strong>Blended Retirement System (2.0%/year + TSP matching)</strong>.</p>
<h2>The two systems at a glance</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>&nbsp;</th><th>Legacy High-3</th><th>BRS</th></tr></thead><tbody>
<tr><td>Who</td><td>Entered service before 2018 (didn't opt in to BRS)</td><td>Entered 2018 or later (and opt-ins)</td></tr>
<tr><td>Multiplier</td><td>2.5% &times; years</td><td>2.0% &times; years</td></tr>
<tr><td>20-year pension</td><td>50% of High-3</td><td>40% of High-3</td></tr>
<tr><td>TSP match</td><td>None</td><td>Up to 5% of basic pay</td></tr>
<tr><td>Continuation pay</td><td>No</td><td>Yes (mid-career bonus)</td></tr>
</tbody></table></div>
<h2>A concrete 20-year example</h2>
<p>An <a href="/blog/how-much-does-an-e7-make-2026.html">E-7</a> retiring at 20 years with a High-3 average around
{money(BP["E-7"]["18"])}/month would receive roughly <strong>{money(BP["E-7"]["18"]*0.5)}/month under High-3</strong> (50%)
or <strong>{money(BP["E-7"]["18"]*0.4)}/month under BRS</strong> (40%) &mdash; plus whatever their TSP grew to, which for
BRS members with full matching can be substantial.</p>
<p class="callout">Retired pay is based on <strong>basic pay only</strong> &mdash; BAH and BAS don't count toward the pension.
That's one reason promotions and time in service matter so much in your last years.</p>
<h2>Reserve retirement is different</h2>
<p>Reserve/Guard members earn <strong>points</strong> instead of straight years, and retired pay generally starts around
age 60. See our <a href="/blog/reserve-drill-pay-explained.html">drill pay &amp; retirement points guide</a>.</p>
{cta("See how a promotion or more years changes your basic pay (and future pension).", "/")}
'''
write("military-retirement-brs-vs-high3.html",
      "Military Retirement: BRS vs High-3 — What 20 Years Is Worth",
      "Military pensions pay 2.5%/year (High-3) or 2.0%/year + TSP match (BRS) of your highest-36-month average basic pay. A 20-year E-7 gets roughly 40–50% of High-3.",
      "Retirement", body,
      faq=[("How much is military retirement after 20 years?","Under the legacy High-3 system, 20 years pays <b>50%</b> of your highest-36-month average basic pay. Under BRS it's <b>40%</b>, plus TSP matching along the way."),
           ("What is the BRS multiplier?","2.0% per year of service, versus 2.5% under the legacy High-3 system."),
           ("Does BAH count toward retirement?","No. Retired pay is calculated from basic pay only — allowances like BAH and BAS are excluded.")],
      related=[("How much does an E-7 make in 2026?","/blog/how-much-does-an-e7-make-2026.html"),
               ("Military TSP explained","/blog/military-tsp-explained.html"),
               ("Reserve drill pay & retirement points","/blog/reserve-drill-pay-explained.html")],
      blurb="20 years = 40–50% of your High-3 basic pay. BRS vs legacy, explained.")

# ===================== TOPIC: SGLI =====================
body=f'''<h1>SGLI in 2026: Coverage, Cost, and How It Hits Your Paycheck</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead"><strong>Servicemembers' Group Life Insurance (SGLI)</strong> covers up to <strong>$500,000</strong> for
<strong>$0.05 per $1,000 of coverage per month</strong>, plus a flat $1 for TSGLI. Maximum coverage costs
<strong>$26/month</strong>, deducted automatically from your pay.</p>
<h2>2026 SGLI premiums by coverage level</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Coverage</th><th>Monthly premium (incl. $1 TSGLI)</th></tr></thead><tbody>
<tr><td>$500,000 (max)</td><td>$26.00</td></tr>
<tr><td>$400,000</td><td>$21.00</td></tr>
<tr><td>$300,000</td><td>$16.00</td></tr>
<tr><td>$200,000</td><td>$11.00</td></tr>
<tr><td>$100,000</td><td>$6.00</td></tr>
<tr><td>$50,000 (min)</td><td>$3.50</td></tr>
</tbody></table></div>
<p>Coverage is elected in <strong>$50,000 increments</strong>. New members are automatically enrolled at the maximum;
you can reduce or decline in writing (think hard before doing so &mdash; SGLI is far cheaper than comparable civilian
term life for most members).</p>
<h2>What else to know</h2>
<ul>
<li><strong>TSGLI</strong> ($1/month) pays for certain traumatic injuries.</li>
<li><strong>FSGLI</strong> covers spouses (up to $100,000) and children (free) for a separate small premium.</li>
<li>After separation, SGLI converts to <strong>VGLI</strong> within set deadlines.</li>
</ul>
{cta("See SGLI and every other deduction in your full paycheck breakdown.", "/")}
'''
write("sgli-cost-2026.html",
      "SGLI in 2026: $500k Coverage for $26/Month — Rates by Coverage Level",
      "SGLI costs $0.05 per $1,000 of coverage plus $1 TSGLI in 2026 — $26/month for the $500,000 maximum. Premium table by coverage level and how it hits your paycheck.",
      "SGLI", body,
      faq=[("How much does SGLI cost in 2026?","$0.05 per $1,000 of coverage plus $1 TSGLI — the $500,000 maximum costs <b>$26 per month</b>."),
           ("How much SGLI coverage can I get?","Up to $500,000, elected in $50,000 increments. New members are auto-enrolled at the maximum."),
           ("Is SGLI worth it?","For most members yes — it's significantly cheaper than comparable civilian term life insurance and has no health screening.")],
      related=[("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Military TSP explained","/blog/military-tsp-explained.html"),
               ("2026 military pay raise","/blog/2026-military-pay-raise.html")],
      blurb="SGLI: $26/mo for $500k — 2026 premium table by coverage level.")

# ===================== DEEP-DIVE PAY ARTICLES (batch: pay mechanics) =====================
import datetime as _dt

# --- 1. Military pay dates 2026 (computed) ---
_HOLIDAYS_2026 = {(1,1),(1,19),(2,16),(5,25),(6,19),(7,3),(9,7),(10,12),(11,11),(11,26),(12,25)}
def _is_biz(d):
    return d.weekday() < 5 and (d.month, d.day) not in _HOLIDAYS_2026
def _payday(d):
    while not _is_biz(d):
        d -= _dt.timedelta(days=1)
    return d
_rows = ""
for m in range(1, 13):
    mid = _payday(_dt.date(2026, m, 15))
    if m == 12:
        eom_target = _dt.date(2027, 1, 1); eom = _dt.date(2026, 12, 31)
        while not _is_biz(eom): eom -= _dt.timedelta(days=1)
    else:
        eom_target = _dt.date(2026, m + 1, 1); eom = _payday(eom_target)
    fmt = lambda d: d.strftime("%a, %b %-d")
    note_mid = "" if mid.day == 15 else " (15th falls on a weekend/holiday)"
    note_eom = "" if eom == eom_target else " (1st falls on a weekend/holiday)"
    _rows += (f"<tr><td>{_dt.date(2026,m,1).strftime('%B')}</td>"
              f"<td>{fmt(mid)}{note_mid}</td><td>{fmt(eom)}{note_eom}</td></tr>")
body = f'''<h1>2026 Military Pay Dates: When You Actually Get Paid</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Active-duty members are paid twice a month: <strong>mid-month (the 15th)</strong> and
<strong>end of month (the 1st of the next month)</strong>. When a payday lands on a weekend or federal holiday,
DFAS pays on the <strong>preceding business day</strong> &mdash; so some months you get paid early.</p>
<h2>2026 payday calendar</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Month earned</th><th>Mid-month payday</th>
<th>End-of-month payday</th></tr></thead><tbody>{_rows}</tbody></table></div>
<p class="callout">Each deposit is roughly <strong>half of your monthly net pay</strong>. The end-of-month payment for
December 2026 arrives <strong>December 31, 2026</strong> because January 1 is a holiday &mdash; which can shift taxable
income between years.</p>
<h2>Why your deposit may land a day later</h2>
<p>These are the official DFAS pay dates. Some banks post the deposit the moment it arrives (and a few credit unions
post military pay <em>one business day early</em>), while others wait until the official date &mdash; so two members with
the same payday can see money on different days.</p>
<h2>Reserve &amp; Guard pay timing</h2>
<p>Drill pay doesn't follow the 1st/15th cycle &mdash; it's processed after your unit certifies the drill period,
typically <strong>7&ndash;14 days after the drill weekend</strong>. See our
<a href="/blog/reserve-drill-pay-explained.html">drill pay guide</a>.</p>
{cta("See exactly how much lands in each deposit — calculate your take-home pay.", "/")}
'''
write("military-pay-dates-2026.html",
      "2026 Military Pay Dates: Full Payday Calendar (1st & 15th Rules)",
      "Active duty is paid on the 15th and the 1st — moved earlier when those fall on a weekend or holiday. Full 2026 military payday calendar with every adjusted date.",
      "Pay Dates", body,
      faq=[("When does the military get paid?","On the <b>15th</b> (mid-month) and the <b>1st of the following month</b> (end-of-month). If a payday falls on a weekend or federal holiday, you're paid the preceding business day."),
           ("Is each military paycheck half a month's pay?","Yes — each of the two monthly deposits is roughly half of your monthly net pay."),
           ("Why did my pay arrive early this month?","When the 1st or 15th lands on a weekend or holiday, DFAS pays on the prior business day, so the deposit arrives one to three days early.")],
      related=[("How to read your LES","/blog/how-to-read-your-les.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Reserve drill pay explained","/blog/reserve-drill-pay-explained.html")],
      blurb="The full 2026 payday calendar — and why some deposits arrive early.")

# --- 2. How to read your LES ---
body = f'''<h1>How to Read Your LES (Leave and Earnings Statement)</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Your <strong>LES</strong> is the military's pay stub, published monthly in myPay. Most pay problems are
caught by members who read it &mdash; here's what every section means and the five things worth checking each month.</p>
<h2>The three money columns</h2>
<ul>
<li><strong>ENTITLEMENTS</strong> &mdash; everything you earn: Basic Pay, BAH, BAS, special pays (FSA, HDIP, flight pay...).
Each item is listed separately, which is how you confirm a new entitlement actually started.</li>
<li><strong>DEDUCTIONS</strong> &mdash; everything taken out: federal taxes (FITW), <strong>FICA &mdash; Social Security</strong>
and <strong>FICA &mdash; Medicare</strong>, state taxes (SITW), <strong>SGLI</strong>, mid-month pay (the money you already
received on the 15th appears here as a deduction), TSP contributions, and any debt collections.</li>
<li><strong>ALLOTMENTS</strong> &mdash; payments you set up voluntarily (insurance, savings, support payments).</li>
</ul>
<p class="callout">The math: <strong>Entitlements &minus; Deductions &minus; Allotments = End-of-month pay (=NET AMT)</strong>.
Your mid-month deposit was an advance on the same month, which is why it shows as a deduction.</p>
<h2>Other blocks worth understanding</h2>
<ul>
<li><strong>LEAVE</strong> &mdash; BF BAL (balance carried forward), ERND, USED, CR BAL (current balance), and
<strong>USE/LOSE</strong> &mdash; days you forfeit on October 1 if not taken (the cap is generally 60 days).</li>
<li><strong>FED TAXES / STATE TAXES</strong> &mdash; your filing status and the wage bases. <strong>WAGE YTD</strong> here is
your <em>taxable</em> pay only &mdash; it's much lower than total compensation because BAH/BAS are tax-free.</li>
<li><strong>TSP</strong> &mdash; your contribution percentages and YTD totals; BRS members should confirm
<strong>Agency/Service contributions</strong> are posting (that's the match).</li>
<li><strong>BAQ TYPE / DEPNS</strong> &mdash; your BAH category and dependent status; <strong>PEBD</strong> (pay entry base
date) drives your years-of-service pay steps.</li>
<li><strong>REMARKS</strong> &mdash; the fine print where starts/stops/debts are explained. Read it every month.</li>
</ul>
<h2>Five things to check every month</h2>
<ol>
<li>BAH rate and ZIP match where you actually live (<a href="/bah/">look yours up</a>).</li>
<li>Years-of-service step &mdash; did your pay bump at your 2/3/4/6... year mark (check PEBD)?</li>
<li>Special pays started/stopped when they should (deployments, flight status, etc.).</li>
<li>TSP percentage and the 5% match (BRS) actually posting.</li>
<li>USE/LOSE leave before the October 1 cutoff.</li>
</ol>
{cta("Cross-check your LES against an independent estimate of your pay.", "/")}
'''
write("how-to-read-your-les.html",
      "How to Read Your LES: Every Section of the Military Pay Stub",
      "A plain-English walkthrough of the Leave and Earnings Statement: entitlements, deductions, allotments, leave block, tax blocks, TSP, and the 5 things to verify every month.",
      "LES Guide", body,
      faq=[("What is an LES?","The Leave and Earnings Statement is the military's monthly pay stub, available in myPay. It lists entitlements, deductions, allotments, leave balance, taxes, and TSP."),
           ("Why does mid-month pay show as a deduction?","Because the LES covers the whole month: the money you already received on the 15th is subtracted so the end-of-month deposit equals the remainder."),
           ("What does USE/LOSE mean on my LES?","Leave days above the carryover cap that will be forfeited on October 1 if you don't use them.")],
      related=[("2026 military pay dates","/blog/military-pay-dates-2026.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Military TSP explained","/blog/military-tsp-explained.html")],
      blurb="Every LES section decoded — and the 5 things to verify monthly.")

# --- 3. Basic training pay ---
e1m = BP.get("E-1m",{}).get("<2", 2226)
body = f'''<h1>Basic Training Pay: What Recruits Earn in 2026</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Yes, you're paid during basic training. In 2026 a brand-new recruit earns <strong>{money(e1m)}/month</strong>
(E-1 with under 4 months of service), rising to <strong>{money(BP["E-1"]["<2"])}/month</strong> after 4 months. Many
recruits enter at E-2 or E-3 and earn more from day one.</p>
<h2>2026 pay during initial training</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Grade at entry</th><th>Monthly basic pay</th></tr></thead><tbody>
<tr><td>E-1 (first 4 months)</td><td>{money(e1m)}</td></tr>
<tr><td>E-1 (after 4 months)</td><td>{money(BP["E-1"]["<2"])}</td></tr>
<tr><td>E-2 (enlistment program credit)</td><td>{money(BP["E-2"]["<2"])}</td></tr>
<tr><td>E-3 (college credits / referrals / JROTC)</td><td>{money(BP["E-3"]["<2"])}</td></tr>
</tbody></table></div>
<p>Pay accrues from your <strong>first day of active duty</strong> (the day you ship), not from when paperwork catches up.</p>
<h2>When the first paycheck arrives</h2>
<p>Military pay lands on the <a href="/blog/military-pay-dates-2026.html">1st and 15th</a>. Your first deposit typically
arrives on the <strong>first regular payday after in-processing</strong> &mdash; usually 2&ndash;4 weeks in &mdash; and it
includes all back pay owed since day one. Direct deposit is mandatory, so open a bank account before you ship.</p>
<h2>What you keep during basic</h2>
<ul>
<li><strong>Meals and housing are provided</strong>, so most of your basic pay is yours (no BAH/BAS at this stage for
single recruits living in the barracks).</li>
<li><strong>Recruits with dependents</strong> generally receive <a href="/blog/2026-bah-rates-explained.html">BAH</a>
for the location where the family lives &mdash; a major difference worth verifying on your first LES.</li>
<li>Expect small deductions: taxes, <a href="/blog/sgli-cost-2026.html">SGLI</a> ($26/month at full coverage), and
initial uniform-related charges depending on branch.</li>
</ul>
{cta("Estimate a first-year paycheck — pick E-1, E-2 or E-3 and your situation.", deep("E-1"))}
'''
write("basic-training-pay-2026.html",
      "Basic Training Pay 2026: What Recruits Earn (and When It Arrives)",
      f"Recruits earn {money(e1m)}/month at E-1 in 2026 (first 4 months), more at E-2/E-3. When the first paycheck arrives, what's deducted, and BAH for recruits with families.",
      "Recruit Pay", body,
      faq=[("Do you get paid in basic training?",f"Yes. Pay starts your first day of active duty — {money(e1m)}/month for a new E-1 in 2026, more for E-2/E-3 entrants."),
           ("When is the first military paycheck?","Usually on the first regular payday (1st or 15th) after in-processing — typically 2–4 weeks after shipping — including all back pay from day one."),
           ("Do recruits with families get BAH?","Generally yes — recruits with dependents receive BAH based on where the family lives, even while the member is in the barracks.")],
      related=[("How much does an E-1 make in 2026?","/blog/how-much-does-an-e1-make-2026.html"),
               ("2026 military pay dates","/blog/military-pay-dates-2026.html"),
               ("How to read your LES","/blog/how-to-read-your-les.html")],
      blurb=f"Recruits earn {money(e1m)}/mo at E-1 — when the first deposit lands and what's deducted.")

# --- 4. Warrant officer pay ---
body = f'''<h1>Warrant Officer Pay 2026: W-1 to W-5 Charts</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Warrant officers are the military's technical specialists, and their pay reflects it: in 2026 a
<strong>W-1 starts at {money(BP["W-1"]["<2"])}/month</strong>, while a <strong>senior W-5 earns up to
{money(BP["W-5"]["38"])}/month</strong> &mdash; plus the same tax-free BAH and BAS as other officers.</p>
<h2>2026 warrant officer basic pay (monthly)</h2>
{pay_table(["W-1","W-2","W-3","W-4","W-5"])}
<p class="callout">W-5 pay begins at 20 years of service &mdash; chief warrant officers five are, by definition, deep-career
specialists. Note that W-2 at 10 years ({money(BP["W-2"]["10"])}) out-earns an O-1 with the same time.</p>
<h2>How warrant pay compares</h2>
<ul>
<li><strong>vs senior enlisted:</strong> a new W-1 ({money(BP["W-1"]["<2"])}) starts above an
<a href="/blog/how-much-does-an-e6-make-2026.html">E-6 with 8 years</a> ({money(BP["E-6"]["8"])}).</li>
<li><strong>vs commissioned officers:</strong> mid-career warrants (W-3/W-4) overlap with O-3/O-4 pay, and prior-enlisted
warrants typically carry many years of service into the table &mdash; meaning they enter at a high column, not the left edge.</li>
<li><strong>Allowances:</strong> warrant officers receive the <em>officer</em> BAS rate ($328.48 in 2026) and BAH at their
own W-grade rates.</li>
</ul>
<h2>Flight pay for Army aviators</h2>
<p>Most Army helicopter pilots are warrant officers and may receive Aviation Incentive Pay on top of basic pay &mdash;
see our <a href="/blog/military-special-pays-guide.html">special pays guide</a>.</p>
{cta("Calculate full warrant officer take-home — pick your W grade and ZIP.", deep("W-2"))}
'''
write("warrant-officer-pay-2026.html",
      "Warrant Officer Pay 2026: W-1 to W-5 Charts & Comparisons",
      f"2026 warrant officer pay: W-1 starts at {money(BP['W-1']['<2'])}/month, W-5 tops out at {money(BP['W-5']['38'])}. Full W-1–W-5 tables plus comparisons to enlisted and officer pay.",
      "Warrant Pay", body,
      faq=[("How much does a warrant officer make in 2026?",f"From {money(BP['W-1']['<2'])}/month for a new W-1 to {money(BP['W-5']['38'])}/month for a W-5 with 38 years, plus tax-free BAH and BAS."),
           ("Do warrant officers get officer BAS?","Yes — warrant officers receive the officer BAS rate ($328.48/month in 2026) and BAH at their own W-grade rates."),
           ("Do warrant officers out-earn enlisted?",f"Generally yes at the same point in a career — a starting W-1 ({money(BP['W-1']['<2'])}) earns more than an E-6 over 8 years ({money(BP['E-6']['8'])}).")],
      related=[("Prior-enlisted officer pay (O-1E/O-2E/O-3E)","/blog/prior-enlisted-officer-pay.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Special pays guide","/blog/military-special-pays-guide.html")],
      blurb=f"W-1 starts at {money(BP['W-1']['<2'])}/mo; W-5 tops {money(BP['W-5']['38'])} &mdash; full tables.")

# --- 5. Prior-enlisted officer pay ---
body = f'''<h1>O-1E, O-2E, O-3E: Prior-Enlisted Officer Pay Explained (2026)</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Commission after enlisted service and the military doesn't reset your paycheck. With <strong>over 4 years
of prior enlisted (or warrant) service</strong>, you're paid on the special <strong>O-1E / O-2E / O-3E</strong> scales
&mdash; worth <strong>several hundred dollars a month</strong> more than standard O-1/O-2/O-3 pay.</p>
<h2>2026 prior-enlisted officer pay (monthly)</h2>
{pay_table(["O-1E","O-2E","O-3E"], cols=["8","10","12","14","16","18","20","22"])}
<h2>How much the "E" is worth</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Comparison (over 8 yrs)</th><th>Standard</th><th>Prior-enlisted</th><th>Monthly difference</th></tr></thead><tbody>
<tr><td>O-1 vs O-1E</td><td>{money(BP["O-1"]["8"])}</td><td>{money(BP["O-1E"]["8"])}</td><td>+{money(BP["O-1E"]["8"]-BP["O-1"]["8"])}</td></tr>
<tr><td>O-2 vs O-2E</td><td>{money(BP["O-2"]["8"])}</td><td>{money(BP["O-2E"]["8"])}</td><td>+{money(BP["O-2E"]["8"]-BP["O-2"]["8"])}</td></tr>
<tr><td>O-3 vs O-3E</td><td>{money(BP["O-3"]["8"])}</td><td>{money(BP["O-3E"]["8"])}</td><td>+{money(BP["O-3E"]["8"]-BP["O-3"]["8"])}</td></tr>
</tbody></table></div>
<p class="callout">You also keep your full <strong>years of service</strong> for pay purposes &mdash; a prior E-5 who
commissions at the 8-year mark starts as an O-1E in the "over 8" column, not at the left edge of the table.</p>
<h2>Who qualifies</h2>
<p>The E-scales require <strong>more than 4 years of active service as an enlisted member or warrant officer</strong>
before commissioning. At O-4 and above the E-scales end &mdash; everyone merges onto the standard officer table (your
years of service still carry over).</p>
{cta("Model your commissioning jump — compare O-1E pay against your current enlisted pay.", deep("O-1E"))}
'''
write("prior-enlisted-officer-pay.html",
      "O-1E / O-2E / O-3E: Prior-Enlisted Officer Pay Explained (2026)",
      f"Officers with 4+ years of prior enlisted service earn the higher O-1E/O-2E/O-3E scales — an O-1E over 8 years makes {money(BP['O-1E']['8'])} vs {money(BP['O-1']['8'])} for a standard O-1.",
      "O-1E Pay", body,
      faq=[("What is O-1E pay?",f"O-1E is the pay scale for O-1s with more than 4 years of prior enlisted or warrant service. Over 8 years it pays {money(BP['O-1E']['8'])}/month versus {money(BP['O-1']['8'])} for a standard O-1."),
           ("Who qualifies for the E pay scales?","Commissioned officers with more than 4 years of active enlisted or warrant officer service. The scales exist for O-1E, O-2E, and O-3E only."),
           ("Do I keep my years of service when I commission?","Yes — your pay entry base date carries over, so you enter the officer table at your real years-of-service column.")],
      related=[("Warrant officer pay 2026","/blog/warrant-officer-pay-2026.html"),
               ("How much does an O-1 make in 2026?","/blog/how-much-does-an-o1-make-2026.html"),
               ("How much does an O-3 make in 2026?","/blog/how-much-does-an-o3-make-2026.html")],
      blurb=f"Prior-enlisted officers earn the E-scales: O-1E over 8 yrs = {money(BP['O-1E']['8'])} (+{money(BP['O-1E']['8']-BP['O-1']['8'])} vs O-1).")

# --- 6. Special pays guide ---
body = f'''<h1>Military Special &amp; Incentive Pays: The 2026 Guide</h1>
<p class="meta">Updated {DATE}</p>
<p class="lead">Beyond basic pay and allowances, dozens of <strong>special and incentive pays</strong> reward specific
duties, skills, and hardships. Here are the ones most members actually see, with 2026 amounts.</p>
<h2>The common ones</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Special pay</th><th>2026 monthly amount</th><th>Who gets it</th></tr></thead><tbody>
<tr><td>Family Separation Allowance (FSA)</td><td>$300</td><td>Away from dependents 30+ consecutive days (deployment, unaccompanied tour)</td></tr>
<tr><td>Hostile Fire / Imminent Danger Pay</td><td>up to $225</td><td>Designated danger areas; IDP prorated by qualifying days</td></tr>
<tr><td>Hazardous Duty Incentive Pay (HDIP)</td><td>$150</td><td>Demolition, toxic fuels, flight deck and other hazardous duties</td></tr>
<tr><td>Parachute (Jump) Pay</td><td>$150 / $225 HALO</td><td>Airborne-status members; higher rate for military free-fall</td></tr>
<tr><td>Diving Duty Pay</td><td>up to $340</td><td>Qualified divers, by qualification level</td></tr>
<tr><td>Aviation Incentive Pay (Flight Pay)</td><td>$125&ndash;$1,000</td><td>Rated officers by years of aviation service; career enlisted flyers $150&ndash;$400</td></tr>
<tr><td>Career Sea Pay</td><td>up to ~$805</td><td>Assigned to sea duty, scales with grade and cumulative sea time</td></tr>
<tr><td>Submarine Duty Pay</td><td>$75&ndash;$600</td><td>Submariners, by grade and years</td></tr>
<tr><td>Foreign Language Proficiency Pay</td><td>up to ~$500</td><td>Tested proficiency in needed languages; more for multiple languages</td></tr>
</tbody></table></div>
<h2>Three rules that matter</h2>
<ul>
<li><strong>They're taxable</strong> &mdash; unlike BAH/BAS, special pays are subject to federal income tax and FICA...
<em>unless</em> you're in a combat zone, where the <a href="/blog/combat-zone-tax-exclusion.html">CZTE</a> makes them
federally tax-free (enlisted fully; officers capped).</li>
<li><strong>They stack</strong> &mdash; a deployed airborne soldier can draw FSA + IDP + jump pay simultaneously
($675/month on top of basic pay and allowances).</li>
<li><strong>They start and stop with orders</strong> &mdash; check your <a href="/blog/how-to-read-your-les.html">LES</a>
the month after any status change; missing start/stop actions are among the most common pay errors.</li>
</ul>
<h2>Bonuses are separate</h2>
<p>Enlistment, reenlistment (SRB), and retention bonuses are lump-sum <em>bonuses</em>, not monthly special pays &mdash;
they're also taxable (and also combat-zone excludable if earned in a qualifying month).</p>
{cta("Add your special pays in the calculator and see the after-tax difference.", "/")}
'''
write("military-special-pays-guide.html",
      "Military Special & Incentive Pays: 2026 Amounts (FSA, Jump, Sea, Flight…)",
      "2026 special pay amounts: FSA $300, danger pay $225, jump pay $150–$225, dive up to $340, flight pay $125–$1,000, sea pay ~$805, language pay ~$500 — and the tax rules.",
      "Special Pays", body,
      faq=[("What is Family Separation Allowance?","FSA pays <b>$300/month</b> when you're away from your dependents for more than 30 consecutive days on orders — deployments, unaccompanied tours, or long TDYs."),
           ("Are special pays taxable?","Yes — special and incentive pays are taxable (unlike BAH/BAS), except in a designated combat zone where the combat-zone tax exclusion applies."),
           ("Can special pays stack?","Yes. Qualifying for several at once (e.g., FSA + danger pay + jump pay) pays all of them simultaneously.")],
      related=[("Combat zone tax exclusion","/blog/combat-zone-tax-exclusion.html"),
               ("How to read your LES","/blog/how-to-read-your-les.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html")],
      blurb="FSA $300, jump $150, flight up to $1,000 &mdash; every common special pay with 2026 amounts.")

# ===================== PCS & FAMILY MONEY BATCH =====================
_D2 = "2026-06-10"
_b = open('data/bah_2025.js').read()
_BAHD = json.loads(_b[_b.index('=')+1:_b.rstrip().rstrip(';').rfind('}')+1])
_GI = _BAHD['meta']['grades']
def bah_rate(mha, col, dep="with"):
    return _BAHD[dep][mha][_GI.index(col)]

# --- DLA ---
body = f'''<h1>Dislocation Allowance (DLA): The PCS Money Nobody Tells You About</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Every PCS move comes with a one-time, <strong>tax-free</strong> payment called the
<strong>Dislocation Allowance</strong> &mdash; meant to cover the costs the government doesn't reimburse directly
(deposits, curtains, that first grocery run). In 2026 it's worth <strong>thousands of dollars</strong>, and you usually
have to know to ask for it.</p>
<h2>2026 DLA amounts (examples)</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Grade</th><th>With dependents</th><th>Without dependents</th></tr></thead><tbody>
<tr><td>E-1 through E-6</td><td>$3,548.02</td><td>$2,389.42 (E-5 rate; varies slightly by grade)</td></tr>
</tbody></table></div>
<p>Rates rise with pay grade (senior officers receive more) and are set each calendar year &mdash; the figures above are
from the official 2026 DTMO table effective January 1, 2026. Look up your exact grade on the DTMO DLA page.</p>
<h2>The rules that matter</h2>
<ul>
<li><strong>It's an entitlement, but payment isn't automatic</strong> &mdash; you typically request DLA through your
travel claim (or as an advance before the move). Members miss it by not filing.</li>
<li><strong>Tax-free</strong> &mdash; DLA is excluded from gross income, even if it exceeds what you actually spent.</li>
<li><strong>One per move</strong> (with limited exceptions), and generally <strong>not payable</strong> for a first PCS
from initial training to the first duty station, or on separation/retirement moves.</li>
<li><strong>Dependent rate</strong> follows whether dependents relocate with you.</li>
</ul>
<h2>Stack it with the rest of your PCS money</h2>
<p>DLA is separate from travel per diem, mileage (MALT), and Temporary Lodging Expense (TLE). A typical E-5 family PCS
can put <strong>$4,000&ndash;$6,000+</strong> of combined entitlements in play &mdash; money that softens the
out-of-pocket hit of <a href="/blog/bah-reform-95-to-100.html">housing costs</a> at the new duty station.</p>
{cta("Moving this summer? Check your new BAH by ZIP before you sign a lease.", "/")}
'''
write("dislocation-allowance-dla-2026.html",
      "Dislocation Allowance (DLA) 2026: The Tax-Free PCS Payment Explained",
      "DLA pays E-1–E-6 families $3,548.02 tax-free per PCS move in 2026 ($2,389.42 single E-5). Who qualifies, when it's NOT paid, and how to claim it.",
      "DLA", body,
      faq=[("How much is DLA in 2026?","For E-1 through E-6 with dependents, $3,548.02; an E-5 without dependents receives $2,389.42. Rates rise with pay grade — check the official DTMO table for yours."),
           ("Is DLA taxable?","No. DLA is excluded from gross income even if the payment exceeds your actual moving costs."),
           ("Do I get DLA on my first move from basic training?","Generally no — DLA is not payable for the move from initial training to your first duty station, nor for separation or retirement moves.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("BAH rates by location","/bah/"),
               ("How to read your LES","/blog/how-to-read-your-les.html")],
      blurb="The tax-free PCS payment: $3,548 for an E-5 family in 2026 &mdash; and when it's NOT paid.")

# --- BNA ---
body = f'''<h1>Basic Needs Allowance (BNA): The Military's Food-Security Benefit</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The <strong>Basic Needs Allowance</strong> is a monthly payment for service members whose gross household
income falls below <strong>150% of the federal poverty guidelines</strong> for their household size. It exists because
some junior enlisted families &mdash; especially large ones in high-cost areas &mdash; struggle with food costs.</p>
<h2>How it works</h2>
<ul>
<li><strong>Screening is annual:</strong> the services screen members (and re-screen at major life changes) and notify
those who appear to qualify; you can also apply through your finance office.</li>
<li><strong>The allowance tops you up:</strong> BNA pays roughly the difference between household income and the
150%-of-poverty threshold, spread across monthly payments.</li>
<li><strong>It's taxable</strong> &mdash; unlike BAH/BAS, BNA counts as taxable income.</li>
</ul>
<h2>The BAH problem &mdash; and the proposed fix</h2>
<p>Today's eligibility math counts <strong>tax-free BAH as income</strong>, which pushes most families above the
threshold and is the main reason few members receive BNA. The
<a href="/blog/fy2027-ndaa-pay-benefits.html">FY2027 NDAA</a> passed by the House Armed Services Committee in June 2026
would <strong>remove BAH from the calculation</strong> &mdash; potentially making thousands more junior families
eligible. We're tracking it on the <a href="/blog/2027-military-pay-raise-tracker.html">2027 pay tracker</a>.</p>
<h2>Should you check?</h2>
<p>If you're <strong>E-1 to E-4 with several dependents</strong>, it costs nothing to ask your finance office for a BNA
screening &mdash; especially if the BAH exclusion becomes law in December.</p>
{cta("Estimate your full pay picture — basic pay, BAH, BAS and take-home.", "/")}
'''
write("basic-needs-allowance-explained.html",
      "Basic Needs Allowance (BNA): Who Qualifies and the BAH Fix Coming",
      "BNA tops up military households below 150% of the federal poverty line. Counting tax-free BAH as income blocks most families — the FY2027 NDAA would change that.",
      "BNA", body,
      faq=[("What is the Basic Needs Allowance?","A monthly allowance for service members whose gross household income is below 150% of the federal poverty guidelines for their household size."),
           ("Why do so few families get BNA?","Because BAH currently counts as income in the eligibility math, pushing most households over the threshold. The FY2027 NDAA proposes excluding BAH."),
           ("Is BNA taxable?","Yes — unlike BAH and BAS, the Basic Needs Allowance is taxable income.")],
      related=[("FY2027 NDAA benefits roundup","/blog/fy2027-ndaa-pay-benefits.html"),
               ("How much does an E-4 make in 2026?","/blog/how-much-does-an-e4-make-2026.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html")],
      blurb="The food-security top-up most families can't get yet &mdash; and the FY2027 fix.")

# --- Dual military BAH ---
sd_e5 = bah_rate("CA038","E05","without"); sd_e6 = bah_rate("CA038","E06","without"); sd_e6d = bah_rate("CA038","E06","with")
body = f'''<h1>Dual-Military Couples: How BAH Actually Works When Both Serve</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">When two service members marry, the money rules change in their favor in one big way:
<strong>each member keeps their own BAH</strong>. A dual-military couple usually banks <em>two</em> housing allowances
against <em>one</em> rent payment.</p>
<h2>The core rules</h2>
<ul>
<li><strong>No dependents:</strong> each member receives the <strong>without-dependents</strong> rate for their own grade.
Example (San Diego rates): an E-5 ({money(sd_e5)}) married to an E-6 ({money(sd_e6)}) brings in
<strong>{money(sd_e5+sd_e6)}/month</strong> combined &mdash; tax-free.</li>
<li><strong>With children:</strong> one member &mdash; typically the senior &mdash; claims the
<strong>with-dependents</strong> rate ({money(sd_e6d)} for an E-6 in San Diego); the other still draws their own
without-dependents rate. The same child can't be claimed by both.</li>
<li><strong>Stationed apart:</strong> each member draws BAH for their own duty location, and who claims the children
follows the dependency determination.</li>
</ul>
<h2>Why this is such a strong financial position</h2>
<p>Two BAHs + one rent = a structural savings engine. The couple above clears {money(sd_e5+sd_e6)}/month in tax-free
housing money; renting at {money(3200)} would leave <strong>{money(sd_e5+sd_e6-3200)}/month</strong> to keep &mdash;
on top of two basic pays, two BAS payments, and two TSP matches.</p>
<p class="callout">BAH is payable when living off base. Dual-military couples in privatized base housing typically
forfeit one BAH as rent &mdash; run the numbers before choosing base housing.</p>
{cta("Run both of your pay profiles and compare living on vs off base.", "/")}
'''
write("dual-military-couples-bah.html",
      "Dual-Military Couples & BAH: Two Allowances, One Rent",
      f"Both members keep their own BAH: a San Diego E-5+E-6 couple draws {money(sd_e5+sd_e6)}/month tax-free. How the with-dependents rate works with kids, and stationed-apart rules.",
      "Dual Military", body,
      faq=[("Do dual-military couples both get BAH?","Yes. Each member receives BAH at their own grade — both at the without-dependents rate if there are no children."),
           ("Who claims the with-dependents rate when we have kids?","One member (typically the senior) claims the with-dependents rate; the other keeps their own without-dependents rate. Both cannot claim the same dependent."),
           ("What if we're stationed in different cities?","Each member draws BAH for their own duty location.")],
      related=[("BAH with vs without dependents","/blog/bah-with-vs-without-dependents.html"),
               ("BAH rates by location","/bah/"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html")],
      blurb=f"Two BAHs, one rent: a SD E-5+E-6 couple banks {money(sd_e5+sd_e6)}/mo tax-free.")

# --- RMC / civilian equivalent ---
_b5=BP["E-5"]["4"]; _bah5=bah_rate("CA038","E05","with"); _bas=476.95
_ann = (_b5+_bah5+_bas)*12
body = f'''<h1>What's Your Military Pay Worth in Civilian Salary? (RMC Explained)</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Comparing a job offer to military pay using basic pay alone is the classic mistake. The honest comparison
is <strong>Regular Military Compensation (RMC)</strong>: basic pay + BAH + BAS <em>plus the tax advantage</em> of the
allowances being tax-free.</p>
<h2>A real example: E-5, 4 years, San Diego, with dependents</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Component</th><th>Monthly</th><th>Annual</th></tr></thead><tbody>
<tr><td>Basic pay (taxable)</td><td>{money(_b5)}</td><td>{money(_b5*12)}</td></tr>
<tr><td>BAH (tax-free)</td><td>{money(_bah5)}</td><td>{money(_bah5*12)}</td></tr>
<tr><td>BAS (tax-free)</td><td>{money(_bas)}</td><td>{money(_bas*12)}</td></tr>
<tr><td><strong>Cash compensation</strong></td><td><strong>{money(_b5+_bah5+_bas)}</strong></td><td><strong>{money(_ann)}</strong></td></tr>
</tbody></table></div>
<p>Because {money((_bah5+_bas)*12)} of that arrives <strong>tax-free</strong>, a civilian would need to earn meaningfully
more than {money(_ann)} to take home the same amount &mdash; typically <strong>{money(_ann*1.06)}&ndash;{money(_ann*1.12)}</strong>
depending on filing status and state. And that's before counting free health care, the TSP match, and the pension.</p>
<h2>What RMC still leaves out</h2>
<ul>
<li><strong>Health care</strong> &mdash; Tricare for a family vs $6,000&ndash;$25,000/year in civilian premiums + deductibles.</li>
<li><strong>Retirement</strong> &mdash; the <a href="/blog/military-retirement-brs-vs-high3.html">BRS pension + 5% TSP match</a>.</li>
<li><strong>Special pays</strong>, <a href="/blog/dislocation-allowance-dla-2026.html">PCS entitlements</a>, and education benefits (GI Bill, tuition assistance).</li>
</ul>
<p class="callout">Location changes the math drastically: the same E-5 in a low-cost area draws far less BAH. Always
compare offers against <em>your</em> ZIP code, not a national average.</p>
{cta("Compute your own RMC — basic + BAH (by ZIP) + BAS, with taxes handled correctly.", "/")}
'''
write("military-pay-civilian-equivalent-rmc.html",
      "What's Military Pay Worth in Civilian Salary? RMC Explained",
      f"An E-5 with 4 years in San Diego earns {money(_ann)}/year in cash compensation — worth {money(_ann*1.06)}+ in civilian salary after the tax advantage, before health care and pension.",
      "RMC", body,
      faq=[("What is Regular Military Compensation?","RMC = basic pay + BAH + BAS + the federal tax advantage of the tax-free allowances. It's the honest baseline for comparing military pay to civilian salaries."),
           ("How much civilian salary equals E-5 pay?",f"An E-5 over 4 years with dependents in San Diego receives about {money(_ann)}/year in cash; a civilian would typically need {money(_ann*1.06)}–{money(_ann*1.12)} to match the take-home, before benefits."),
           ("Why is military take-home higher than it looks?","Because BAH and BAS are tax-free — a large slice of compensation never touches federal income tax.")],
      related=[("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("States that don't tax military pay","/blog/states-that-dont-tax-military-pay.html")],
      blurb=f"E-5 in San Diego = {money(_ann)}/yr cash &mdash; what that's really worth in civilian salary.")

# --- COLA ---
body = f'''<h1>Military COLA Explained: CONUS vs Overseas (and the Tax Catch)</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead"><strong>Cost-of-Living Allowance (COLA)</strong> offsets high day-to-day prices &mdash; groceries, gas,
services &mdash; in expensive duty locations. It's separate from BAH (which only covers housing), and there are two very
different flavors.</p>
<h2>OCONUS COLA (overseas)</h2>
<ul>
<li>Paid in <strong>high-cost overseas locations</strong> (Japan, Germany, and similar; Hawaii and Alaska have their own version).</li>
<li>Amount depends on <strong>location, grade, years of service, and dependents</strong>, and adjusts with exchange rates
&mdash; it can change several times a year.</li>
<li><strong>Tax-free.</strong></li>
</ul>
<h2>CONUS COLA (stateside)</h2>
<ul>
<li>Paid only in a <strong>small list of high-cost U.S. areas</strong> where local prices far exceed the national average.</li>
<li>Typically <strong>much smaller</strong> than overseas COLA.</li>
<li><strong>Taxable</strong> &mdash; the rare allowance that is, set by statute (unlike BAH/BAS).</li>
</ul>
<p class="callout">Quick rule: <strong>overseas COLA is tax-free; stateside (CONUS) COLA is taxable.</strong> If you're
entering a COLA amount into a pay calculator, know which one you're getting.</p>
<h2>How to find your rate</h2>
<p>Rates are published by the Defense Travel Management Office (travel.dod.mil) with lookup tools for both programs.
Enter the monthly amount into the <a href="/">calculator</a>'s COLA field to see the paycheck impact alongside your
<a href="/bah/">BAH</a> and BAS.</p>
{cta("Add your COLA and see your true monthly take-home.", "/")}
'''
write("military-cola-explained.html",
      "Military COLA Explained: CONUS vs Overseas Rules (and Taxes)",
      "COLA offsets high local prices — overseas COLA is tax-free and adjusts with exchange rates; stateside CONUS COLA is smaller and taxable. How rates are set and where to look yours up.",
      "COLA", body,
      faq=[("Is military COLA taxable?","Overseas (OCONUS) COLA is tax-free. Stateside (CONUS) COLA is taxable — it's the rare military allowance that is."),
           ("What determines my COLA amount?","Location, pay grade, years of service, and number of dependents; overseas rates also adjust with currency exchange rates."),
           ("Is COLA the same as BAH?","No. BAH covers housing; COLA offsets non-housing living costs like groceries and services in expensive areas.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("BAH rates by location","/bah/"),
               ("What's military pay worth in civilian salary?","/blog/military-pay-civilian-equivalent-rmc.html")],
      blurb="Overseas COLA is tax-free; CONUS COLA is taxable &mdash; the rules in plain English.")

# ===================== DEPLOYMENT / BONUS / HISTORY / PROMOTION BATCH =====================
def _fed_single(annual_taxable):
    ti = max(0, annual_taxable - 16100)
    br = [(0,.10),(12400,.12),(50400,.22),(105700,.24),(201775,.32),(256225,.35),(640600,.37)]
    tax = 0
    for i,(lo,rt) in enumerate(br):
        hi = br[i+1][0] if i+1 < len(br) else float("inf")
        if ti > lo: tax += (min(ti,hi)-lo)*rt
    return tax

# deployment example: E-5 @4yrs, San Diego, with dependents, single filer, 5% trad TSP, SGLI max
_db   = BP["E-5"]["4"]; _dbah = bah_rate("CA038","E05","with"); _dbas = 476.95
_dtsp = _db*0.05
_home_gross = _db+_dbah+_dbas
_home_fed   = _fed_single((_db-_dtsp)*12)/12
_home_ded   = _home_fed + _db*.062 + _db*.0145 + _dtsp + 26
_home_net   = _home_gross - _home_ded
_dep_specials = 300+225   # FSA + IDP
_dep_gross  = _home_gross + _dep_specials
_dep_fica   = (_db+_dep_specials)*.062 + (_db+_dep_specials)*.0145
_dep_ded    = _dep_fica + _dtsp + 26
_dep_net    = _dep_gross - _dep_ded
_dep_gain   = _dep_net - _home_net

body = f'''<h1>How Deployment Changes Your Paycheck: A Real Example</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Deploy to a designated combat zone and three things hit your LES at once: <strong>new special pays
start</strong>, <strong>federal income tax stops</strong>, and your allowances keep flowing. Here's the full math for a
typical E-5 &mdash; deployed pay is often <strong>$700&ndash;$900/month higher</strong>, all of it saveable.</p>
<h2>The example: E-5, 4 years, family in San Diego</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Monthly item</th><th>Home station</th><th>Deployed (combat zone)</th></tr></thead><tbody>
<tr><td>Basic pay</td><td>{money(_db)}</td><td>{money(_db)}</td></tr>
<tr><td>BAH (family stays put)</td><td>{money(_dbah)}</td><td>{money(_dbah)}</td></tr>
<tr><td>BAS</td><td>{money(_dbas)}</td><td>{money(_dbas)}</td></tr>
<tr><td>Family Separation Allowance</td><td>&mdash;</td><td>$300</td></tr>
<tr><td>Hostile Fire / Imminent Danger Pay</td><td>&mdash;</td><td>$225</td></tr>
<tr><td>Federal income tax</td><td>&minus;{money(_home_fed)}</td><td><strong>$0 (CZTE)</strong></td></tr>
<tr><td>FICA (still applies)</td><td>&minus;{money(_db*.062+_db*.0145)}</td><td>&minus;{money(_dep_fica)}</td></tr>
<tr><td>TSP (5%) + SGLI</td><td>&minus;{money(_dtsp+26)}</td><td>&minus;{money(_dtsp+26)}</td></tr>
<tr><td><strong>Net take-home</strong></td><td><strong>{money(_home_net)}</strong></td><td><strong>{money(_dep_net)}</strong></td></tr>
</tbody></table></div>
<p>That's <strong>+{money(_dep_gain)}/month</strong> &mdash; roughly {money(_dep_gain*9)} over a nine-month deployment,
before the spending drop that usually comes with deployed life.</p>
<h2>Don't miss these two multipliers</h2>
<ul>
<li><strong>Savings Deposit Program (SDP):</strong> deployed members can deposit up to <strong>$10,000</strong> and earn
a guaranteed <strong>10% annual interest</strong> while in theater &mdash; the best risk-free return available anywhere.</li>
<li><strong>Roth TSP while tax-free:</strong> combat-zone pay contributed to <a href="/blog/military-tsp-explained.html">Roth TSP</a>
goes in untaxed and comes out untaxed &mdash; a double exemption you can't get any other way.</li>
</ul>
<p class="callout">Officers: the <a href="/blog/combat-zone-tax-exclusion.html">CZTE is capped</a> at about $10,954/month
in 2026 &mdash; pay above the cap is still taxed. Enlisted and warrant officers have no cap.</p>
{cta("Toggle CZTE and add FSA/IDP in the calculator to model your own deployment.", "/")}
'''
write("deployment-pay-explained.html",
      "How Deployment Changes Your Paycheck: Real E-5 Example (2026)",
      f"Deployed to a combat zone, a typical E-5 takes home {money(_dep_net)}/month vs {money(_home_net)} at home — +{money(_dep_gain)}/month from CZTE, FSA and danger pay. Full math inside.",
      "Deployment Pay", body,
      faq=[("How much more do you make deployed?",f"For a typical E-5 with a family, about {money(_dep_gain)} more per month — federal tax stops (CZTE) and FSA ($300) plus danger pay ($225) start."),
           ("Is all deployed pay tax-free?","Federal income tax stops for enlisted members (officers are capped near $10,954/month in 2026), but Social Security and Medicare are still withheld."),
           ("What is the Savings Deposit Program?","Deployed members can deposit up to $10,000 into the SDP and earn a guaranteed 10% annual interest while deployed.")],
      related=[("Combat zone tax exclusion","/blog/combat-zone-tax-exclusion.html"),
               ("Special pays guide","/blog/military-special-pays-guide.html"),
               ("Military TSP explained","/blog/military-tsp-explained.html")],
      blurb=f"A deployed E-5 nets +{money(_dep_gain)}/mo &mdash; the full before/after LES math.")

# --- bonuses & taxes ---
body = f'''<h1>Military Bonuses and Taxes: What You Actually Keep</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Enlistment and reenlistment bonuses are real money &mdash; tens of thousands of dollars &mdash; but the
amount that hits your account is smaller than the number on the contract, unless you time it right.</p>
<h2>The main bonus types</h2>
<ul>
<li><strong>Enlistment bonus</strong> &mdash; for shipping into critical jobs; amounts vary by service, MOS/rating, and
contract length (commonly $5,000&ndash;$50,000 for the hardest-to-fill jobs).</li>
<li><strong>Selective Reenlistment Bonus (SRB)</strong> &mdash; for staying in critical skills; calculated from monthly
basic pay &times; years of additional service &times; a skill multiplier, often paid half upfront and the rest in
annual installments.</li>
<li><strong>Other incentives</strong> &mdash; officer retention, aviation/medical continuation pay, and similar programs.</li>
</ul>
<h2>How bonuses are taxed</h2>
<ul>
<li>Bonuses are <strong>taxable income</strong>, and DFAS withholds federal tax at the flat
<strong>22% supplemental-wage rate</strong> up front (plus FICA, plus state where applicable).</li>
<li>The 22% is <em>withholding</em>, not your final bill &mdash; many junior members whose real bracket is 10&ndash;12%
get a chunk back at tax time.</li>
<li><strong>The combat-zone play:</strong> a bonus earned in a month you're in a designated combat zone is covered by the
<a href="/blog/combat-zone-tax-exclusion.html">CZTE</a> &mdash; <strong>reenlisting while deployed can make the entire
bonus federally tax-free</strong>. This is the single biggest legal tax move available to enlisted members.</li>
</ul>
<h2>Installments and clawbacks</h2>
<p>SRB installments are taxed in the year received. If you fail to complete the obligated service, unearned portions are
<strong>recouped</strong> &mdash; the government bills you back. Read the contract's installment schedule before counting
the full number.</p>
{cta("Model your monthly pay with and without the new contract — see the real difference.", "/")}
'''
write("military-bonuses-taxes.html",
      "Military Bonuses & Taxes: The 22% Withholding and the Combat-Zone Play",
      "Enlistment and reenlistment bonuses are taxed at a flat 22% withholding — but a bonus earned in a combat zone is federally tax-free. How SRB installments, refunds, and clawbacks work.",
      "Bonuses", body,
      faq=[("How are military bonuses taxed?","As taxable income with a flat 22% federal withholding up front, plus FICA. If your real bracket is lower, you get the difference back at tax time."),
           ("Are bonuses tax-free in a combat zone?","Yes — a bonus earned in a month you serve in a designated combat zone falls under the combat-zone tax exclusion. Reenlisting while deployed can make the whole bonus federally tax-free."),
           ("What happens to my bonus if I separate early?","Unearned portions are recouped — the government claws back the prorated amount for service you didn't complete.")],
      related=[("Combat zone tax exclusion","/blog/combat-zone-tax-exclusion.html"),
               ("Deployment pay explained","/blog/deployment-pay-explained.html"),
               ("How to read your LES","/blog/how-to-read-your-les.html")],
      blurb="22% withholding, installment rules, clawbacks &mdash; and the deployed-reenlistment tax play.")

# --- pay raise history ---
_hist = [("2017","2.1%"),("2018","2.4%"),("2019","2.6%"),("2020","3.1%"),("2021","3.0%"),
         ("2022","2.7%"),("2023","4.6%"),("2024","5.2%"),("2025","4.5% + targeted junior-enlisted raise (April)"),
         ("2026","3.8%"),("2027","proposed 7% / 6% / 5% tiered")]
_hrows = "".join(f"<tr><td>{y}</td><td>{r}</td></tr>" for y,r in _hist)
body = f'''<h1>Military Pay Raise History: 2017&ndash;2027</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Military raises are tied by law to the <strong>Employment Cost Index (ECI)</strong> &mdash; private-sector
wage growth &mdash; unless Congress votes a different number. Here's the last decade, and where 2027 is heading.</p>
<h2>Year-by-year raises</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Year</th><th>Basic pay raise</th></tr></thead><tbody>{_hrows}</tbody></table></div>
<h2>The two big breaks from the pattern</h2>
<ul>
<li><strong>2025: the junior-enlisted catch-up.</strong> On top of the 4.5% January raise, Congress gave
<strong>E-4s and below a targeted additional raise in April 2025</strong> (roughly 10% extra, ~14.5% combined) after years
of reports on junior-enlisted food insecurity. It permanently lifted the bottom of the pay table.</li>
<li><strong>2027: the tiered proposal.</strong> Instead of one number, the pending FY2027 NDAA uses
<strong>7% / 6% / 5% tiers</strong> favoring junior troops &mdash; track it on our
<a href="/blog/2027-military-pay-raise-tracker.html">2027 raise tracker</a>.</li>
</ul>
<h2>Raises compound</h2>
<p>A raise isn't a one-year event &mdash; every future raise multiplies on top of it. From 2023 through 2026 alone, basic
pay grew about <strong>19%</strong> compounded (4.6% &times; 5.2% &times; 4.5% &times; 3.8%), and pension math uses your
final years' basic pay &mdash; so each raise also lifts <a href="/blog/military-retirement-brs-vs-high3.html">retired pay</a>.</p>
{cta("See what the current pay table means for your exact rank and years.", "/")}
'''
write("military-pay-raise-history.html",
      "Military Pay Raise History 2017–2027: Every Year's Increase",
      "A decade of military raises: from 2.1% in 2017 to 5.2% in 2024, the 2025 junior-enlisted catch-up, 3.8% in 2026, and the proposed tiered 7%/6%/5% for 2027.",
      "Raise History", body,
      faq=[("How is the military pay raise determined?","By default it matches the Employment Cost Index (ECI) measure of private-sector wage growth; Congress can legislate a different figure."),
           ("What was the biggest recent military raise?","2024's 5.2% was the largest across-the-board raise in over two decades; junior enlisted got an even larger targeted increase in April 2025."),
           ("What is the 2027 military pay raise?","Still a proposal: 7% for E-5 and below, 6% for E-6 through O-3, and 5% for O-4 and above, pending the FY2027 NDAA.")],
      related=[("2027 pay raise tracker","/blog/2027-military-pay-raise-tracker.html"),
               ("2026 military pay raise (3.8%)","/blog/2026-military-pay-raise.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html")],
      blurb="2.1% (2017) &rarr; 5.2% (2024) &rarr; tiered 7/6/5 proposal (2027) &mdash; the full decade.")

# --- promotion value ---
_p56b = BP["E-6"]["8"] - BP["E-5"]["8"]
_p56bah = bah_rate("CA038","E06","with") - bah_rate("CA038","E05","with")
_p67b = BP["E-7"]["12"] - BP["E-6"]["12"]
body = f'''<h1>What a Promotion Is Really Worth: E-5 to E-6 in Dollars</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Promotions pay twice: a bigger basic-pay number today, and a higher pay <em>curve</em> for the rest of
your career &mdash; plus a quieter bump most people forget: <strong>BAH goes up with your grade too</strong>.</p>
<h2>The immediate raise: E-5 &rarr; E-6 at 8 years</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Monthly item</th><th>E-5 (over 8)</th><th>E-6 (over 8)</th><th>Gain</th></tr></thead><tbody>
<tr><td>Basic pay</td><td>{money(BP["E-5"]["8"])}</td><td>{money(BP["E-6"]["8"])}</td><td>+{money(_p56b)}</td></tr>
<tr><td>BAH (San Diego, w/ dependents)</td><td>{money(bah_rate("CA038","E05","with"))}</td><td>{money(bah_rate("CA038","E06","with"))}</td><td>+{money(_p56bah)} (tax-free)</td></tr>
<tr><td><strong>Total monthly gain</strong></td><td></td><td></td><td><strong>+{money(_p56b+_p56bah)}</strong></td></tr>
</tbody></table></div>
<p>That's about <strong>{money((_p56b+_p56bah)*12)}/year</strong> &mdash; and because part of it is tax-free BAH, the
take-home impact is bigger than a same-size civilian raise.</p>
<h2>The career effect: the curve keeps climbing</h2>
<p>E-5 basic pay <strong>stops growing at 12 years</strong> ({money(BP["E-5"]["12"])}); E-6 keeps stepping up to 20+
years ({money(BP["E-6"]["20"])}), and E-7 to 26+. Staying an E-5 from year 12 to year 20 forfeits roughly
<strong>{money((BP["E-6"]["20"]-BP["E-5"]["20"])*12*4 + (BP["E-6"]["14"]-BP["E-5"]["14"])*12*4)}</strong> in basic pay
alone versus making E-6 &mdash; before counting BAH and the pension effect.</p>
<h2>The retirement multiplier</h2>
<p>Retired pay uses your <strong>highest 36 months of basic pay</strong>. Pinning on E-7 ({money(BP["E-7"]["12"])} at 12
years, +{money(_p67b)} over E-6) in your final years raises the pension base for the rest of your life &mdash; see
<a href="/blog/military-retirement-brs-vs-high3.html">how retired pay is calculated</a>.</p>
{cta("Compare your current grade against the next one — same ZIP, same years.", "/")}
'''
write("promotion-value-e5-to-e6.html",
      "What a Promotion Is Worth: E-5 to E-6 in Real Dollars",
      f"E-5 to E-6 at 8 years is +{money(_p56b)}/month basic plus +{money(_p56bah)} tax-free BAH in San Diego — about {money((_p56b+_p56bah)*12)}/year, and the pay curve keeps climbing for 12 more years.",
      "Promotion Value", body,
      faq=[("How much more does an E-6 make than an E-5?",f"At 8 years of service, {money(_p56b)}/month more in basic pay — plus a higher BAH rate (+{money(_p56bah)} in San Diego) since BAH rises with grade."),
           ("Does BAH increase when I get promoted?","Yes. BAH is set per pay grade, so a promotion raises your housing allowance as well as basic pay."),
           ("Why do promotions matter for retirement?","Retired pay is based on your highest 36 months of basic pay, so late-career promotions permanently raise your pension.")],
      related=[("How much does an E-6 make in 2026?","/blog/how-much-does-an-e6-make-2026.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html")],
      blurb=f"E-5&rarr;E-6 = +{money(_p56b+_p56bah)}/mo (incl. BAH bump) &mdash; and a steeper curve for 12 more years.")

# ===================== CAREER COMPARISON / NICHE BAH / TAX FILING BATCH =====================
def _yoscol(g, yrs):
    best = None
    for c, v in BP[g].items():
        if c == "<2":
            t = 0
        else:
            try: t = int(c)
            except ValueError: continue
        if yrs >= t and v is not None:
            if best is None or t > best[0]: best = (t, c)
    return best[1] if best else None

def _cum_basic(path, years=20):
    # path: list of (grade, start_year); returns cumulative basic pay over `years`
    total = 0
    for y in range(years):
        g = None
        for grade, start in path:
            if y >= start: g = grade
        col = _yoscol(g, y + 0.5)
        total += BP[g][col] * 12
    return total

_enl_path = [("E-1",0),("E-2",0.5),("E-3",1.5),("E-4",3),("E-5",5),("E-6",9),("E-7",14)]
_off_path = [("O-1",0),("O-2",2),("O-3",4),("O-4",10),("O-5",16)]
_enl20 = _cum_basic(_enl_path); _off20 = _cum_basic(_off_path)
_rs = open('data/reserve_2025.js').read()
_RCT = json.loads(_rs[_rs.index('=')+1:_rs.rstrip().rstrip(';').rfind('}')+1])['rct']
def _rct(g,k): return _RCT[g][k]

body = f'''<h1>Officer vs Enlisted Pay: 20-Year Career Earnings Compared</h1>
<p class="meta">Updated {_D2} &middot; Computed from the 2026 pay table</p>
<p class="lead">Over a 20-year career the basic-pay gap between an officer and an enlisted member is real but smaller than
most people assume &mdash; and allowances, bonuses, and reaching top pay sooner narrow it further. Using the 2026 table
and typical promotion timelines, here's how <strong>basic pay</strong> stacks up.</p>
<h2>Estimated 20-year basic pay (2026 rates)</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Path</th><th>Typical track</th><th>20-year basic pay</th></tr></thead><tbody>
<tr><td>Enlisted</td><td>E-1 &rarr; E-7 (SFC/GySgt/CPO)</td><td>~{money(_enl20)}</td></tr>
<tr><td>Officer</td><td>O-1 &rarr; O-5 (LtCol/CDR)</td><td>~{money(_off20)}</td></tr>
<tr><td><strong>Difference</strong></td><td></td><td><strong>~{money(_off20-_enl20)}</strong> over 20 years</td></tr>
</tbody></table></div>
<p class="callout">These are <em>basic pay</em> estimates using 2026 rates held flat and standard promotion points. Real
careers vary, and future raises lift both paths. They exclude BAH, BAS, special pays, and bonuses.</p>
<h2>What the basic-pay gap leaves out</h2>
<ul>
<li><strong>Allowances are similar in kind.</strong> Both get tax-free BAH and BAS; an officer's BAH is higher, but a
senior enlisted member in a high-cost area still draws substantial housing money.</li>
<li><strong>Enlisted reach top pay sooner.</strong> An E-7 hits a strong pay band years before an officer reaches O-5,
and many enlisted members earn reenlistment <a href="/blog/military-bonuses-taxes.html">bonuses</a> officers don't.</li>
<li><strong>The pension scales with both.</strong> 20 years pays a percentage of final basic pay either way &mdash; see
<a href="/blog/military-retirement-brs-vs-high3.html">how retirement is calculated</a>.</li>
<li><strong>Prior-enlisted officers</strong> get the best of both via the
<a href="/blog/prior-enlisted-officer-pay.html">O-1E/O-2E/O-3E scales</a>.</li>
</ul>
{cta("Compare any two ranks for yourself — same ZIP, same years of service.", "/")}
'''
write("officer-vs-enlisted-pay-career.html",
      "Officer vs Enlisted Pay: 20-Year Career Earnings Compared (2026)",
      f"Over 20 years at 2026 rates, a typical enlisted (E-1 to E-7) career earns about {money(_enl20)} in basic pay vs {money(_off20)} for an officer (O-1 to O-5) - a gap of about {money(_off20-_enl20)}.",
      "Officer vs Enlisted", body,
      faq=[("Do officers make a lot more than enlisted?",f"Over a typical 20-year career at 2026 rates, an officer (O-1 to O-5) earns roughly {money(_off20)} in basic pay versus {money(_enl20)} for enlisted (E-1 to E-7) - about {money(_off20-_enl20)} more, before allowances and bonuses."),
           ("Is the officer-enlisted pay gap as big as people think?","Not entirely - both receive tax-free allowances, enlisted reach top pay bands sooner and earn reenlistment bonuses, and the pension scales with both paths."),
           ("How can enlisted members get officer pay?","By commissioning; with 4+ years prior service they are paid on the higher O-1E/O-2E/O-3E scales and keep their years of service.")],
      related=[("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Prior-enlisted officer pay (O-1E)","/blog/prior-enlisted-officer-pay.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html")],
      blurb=f"20 years: enlisted ~{money(_enl20)} vs officer ~{money(_off20)} in basic pay &mdash; and what closes the gap.")

# --- Partial BAH & BAH-Diff (niche data) ---
body = f'''<h1>BAH-Diff and Partial BAH: The Housing Allowances Almost Nobody Explains</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Most members know BAH and BAH RC/Transit. But two smaller housing allowances &mdash;
<strong>BAH-Diff</strong> and <strong>Partial BAH</strong> &mdash; quietly appear on LESs in specific situations, and the
amounts are easy to miss. Here's exactly who gets them, with the 2025 figures.</p>
<h2>Partial BAH (single members in the barracks)</h2>
<p>If you're <strong>without dependents and living in government quarters</strong> (barracks/dorms), you don't get full
BAH &mdash; but you do get a small <strong>Partial BAH</strong>. The rates are tiny and grade-based:</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>Grade</th><th>Monthly Partial BAH (2025)</th></tr></thead><tbody>
<tr><td>E-5</td><td>{money2(_rct("E-5","partial"))}</td></tr>
<tr><td>E-6</td><td>{money2(_rct("E-6","partial"))}</td></tr>
<tr><td>E-7</td><td>{money2(_rct("E-7","partial"))}</td></tr>
<tr><td>O-3</td><td>{money2(_rct("O-3","partial"))}</td></tr>
<tr><td>O-4</td><td>{money2(_rct("O-4","partial"))}</td></tr>
</tbody></table></div>
<p>Partial BAH rates have been fixed for decades, which is why they look so small &mdash; a few dollars to a few tens of
dollars a month.</p>
<h2>BAH-Diff (members paying child support while in quarters)</h2>
<p><strong>BAH-Diff</strong> is for members <strong>without primary custody who pay child support</strong> and live in
government quarters. It bridges the gap between the with- and without-dependents rates. 2025 examples:</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>Grade</th><th>Monthly BAH-Diff (2025)</th></tr></thead><tbody>
<tr><td>E-5</td><td>{money2(_rct("E-5","diff"))}</td></tr>
<tr><td>E-6</td><td>{money2(_rct("E-6","diff"))}</td></tr>
<tr><td>E-7</td><td>{money2(_rct("E-7","diff"))}</td></tr>
<tr><td>O-3</td><td>{money2(_rct("O-3","diff"))}</td></tr>
</tbody></table></div>
<p class="callout">A key rule: your child-support payment must be <strong>at least equal to the BAH-Diff amount</strong> to
qualify. Move out of quarters and you generally shift to regular BAH instead.</p>
<h2>How these fit the bigger picture</h2>
<p>For the main rates &mdash; full locality BAH and the reserve <strong>BAH RC/Transit</strong> table &mdash; see our
<a href="/blog/2026-bah-rates-explained.html">2026 BAH guide</a> and <a href="/bah/">BAH-by-location</a> pages.</p>
{cta("Living off base? Look up your full BAH by ZIP and see your real take-home.", "/")}
'''
write("partial-bah-and-bah-diff.html",
      "BAH-Diff and Partial BAH Explained (2025 Rates)",
      "Partial BAH (single members in the barracks) and BAH-Diff (members paying child support in quarters) are the housing allowances nobody explains. Who qualifies, with 2025 amounts by grade.",
      "Partial BAH", body,
      faq=[("What is Partial BAH?","A small housing allowance for members without dependents who live in government quarters and therefore don't receive full BAH. Rates are grade-based and have been fixed for decades."),
           ("What is BAH-Diff?","BAH-Differential is paid to members without primary custody who pay child support and live in government quarters; the child-support payment must be at least the BAH-Diff amount to qualify."),
           ("Do barracks residents get any BAH?","Yes - a small Partial BAH, even though they don't receive full BAH while living in government quarters.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("BAH with vs without dependents","/blog/bah-with-vs-without-dependents.html"),
               ("Reserve drill pay & BAH RC/Transit","/blog/reserve-drill-pay-explained.html")],
      blurb="Partial BAH and BAH-Diff: the two housing allowances almost nobody explains, with 2025 rates.")

# --- Military tax filing guide ---
body = f'''<h1>Military Tax Filing: Free Filing, Deadlines &amp; State Residency (2026)</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Military taxes have rules civilians don't &mdash; free filing software, automatic deadline extensions for
the deployed, and a spouse-residency law that can erase a state tax bill. Here's what actually saves you money.</p>
<h2>1. File for free with MilTax</h2>
<p><strong>MilTax</strong> (via Military OneSource) is free tax software built for military life &mdash; it handles
combat pay, multistate moves, and rental situations, with no income limit, plus free consultations with tax pros. Most
members should never pay for tax software.</p>
<h2>2. What's taxable vs not</h2>
<ul>
<li><strong>Taxable:</strong> basic pay, most <a href="/blog/military-special-pays-guide.html">special pays</a>, bonuses,
and <a href="/blog/military-cola-explained.html">CONUS COLA</a>.</li>
<li><strong>Tax-free:</strong> BAH, BAS, overseas COLA, <a href="/blog/dislocation-allowance-dla-2026.html">DLA</a> and
most PCS allowances, and all pay excluded under the <a href="/blog/combat-zone-tax-exclusion.html">combat-zone exclusion</a>.</li>
</ul>
<h2>3. Deployed? Your deadline moves automatically</h2>
<p>Serving in a combat zone gives you an <strong>automatic extension</strong>: the normal April deadline is pushed to at
least <strong>180 days after you leave the zone</strong> (plus the days you had left before deploying). No form required,
and the same extension covers IRA contributions and many IRS actions.</p>
<h2>4. The spouse residency rule (MSRRA)</h2>
<p>Under the <strong>Military Spouses Residency Relief Act</strong>, a military spouse can keep the servicemember's state
of legal residence for tax purposes &mdash; so a couple domiciled in a <a href="/blog/states-that-dont-tax-military-pay.html">no-tax
state</a> like Texas or Florida can keep the spouse's income state-tax-free even after a PCS to a taxing state.</p>
<h2>5. Don't leave these on the table</h2>
<ul>
<li><strong>Earned Income Tax Credit:</strong> you can elect to <em>include</em> nontaxable combat pay when it raises your
EITC &mdash; a rare case where combat pay helps your refund.</li>
<li><strong>Saver's Credit</strong> for TSP contributions at lower incomes.</li>
<li><strong>Moving deductions</strong> for PCS costs the military didn't reimburse (still available to active duty).</li>
</ul>
{cta("Know your taxable vs tax-free pay before you file — see the breakdown in the calculator.", "/")}
'''
write("military-tax-filing-guide.html",
      "Military Tax Filing 2026: Free MilTax, Combat-Zone Extensions & MSRRA",
      "Military tax guide: file free with MilTax, automatic 180-day combat-zone deadline extensions, the MSRRA spouse-residency rule, and credits like EITC with combat pay.",
      "Tax Filing", body,
      faq=[("How can military members file taxes for free?","MilTax through Military OneSource is free tax software with no income limit, built for combat pay, PCS moves, and multistate situations, plus free tax-pro consultations."),
           ("Do deployed troops get a tax deadline extension?","Yes - serving in a combat zone gives an automatic extension of at least 180 days after leaving the zone, with no form required."),
           ("What is the MSRRA spouse residency rule?","The Military Spouses Residency Relief Act lets a spouse keep the servicemember's state of legal residence for tax purposes, which can keep their income tax-free in a no-tax home state.")],
      related=[("States that don't tax military pay","/blog/states-that-dont-tax-military-pay.html"),
               ("Combat zone tax exclusion","/blog/combat-zone-tax-exclusion.html"),
               ("Military bonuses & taxes","/blog/military-bonuses-taxes.html")],
      blurb="Free MilTax filing, automatic combat-zone extensions, and the MSRRA spouse-residency tax break.")

# ===================== TOTAL COMPENSATION / HIDDEN BENEFITS BATCH =====================
# --- Tricare value ---
body = f'''<h1>What Military Health Care Is Really Worth (Tricare's Hidden Paycheck)</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Tricare almost never shows up on your LES, but it's one of the largest pieces of military compensation.
For a family, comparable civilian health coverage runs <strong>$15,000&ndash;$25,000 a year</strong> &mdash; money you'd
have to earn, and be taxed on, in the civilian world.</p>
<h2>What you actually pay</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Plan</th><th>Active-duty monthly premium</th><th>Typical costs</th></tr></thead><tbody>
<tr><td>Tricare Prime (active duty)</td><td>$0</td><td>$0 for the member; minimal/no copays for the family in-network</td></tr>
<tr><td>Tricare Select (active-duty family)</td><td>$0</td><td>Small copays per visit; annual deductible</td></tr>
<tr><td>Tricare Dental (family)</td><td>~$11&ndash;$38</td><td>Low cost-share for most procedures</td></tr>
</tbody></table></div>
<p>Active-duty members and their families pay <strong>no monthly medical premium</strong>. Compare that to a civilian
employee's average share of a family plan &mdash; often <strong>$6,000&ndash;$7,000/year in premiums alone</strong>,
before deductibles that routinely top $3,000.</p>
<h2>Putting a number on it</h2>
<p>A fair estimate of the employer-equivalent value of active-duty family medical + dental coverage is
<strong>$18,000&ndash;$25,000 per year</strong>. Because you don't pay for it <em>and</em> don't pay tax on it, matching
it as a civilian could require <strong>$22,000&ndash;$33,000 of pre-tax salary</strong>. That's on top of your
<a href="/blog/military-pay-civilian-equivalent-rmc.html">cash compensation (RMC)</a>.</p>
<h2>It doesn't stop at separation</h2>
<ul>
<li><strong>Transitional care (TAMP)</strong> bridges you for 180 days after active duty in many cases.</li>
<li><strong>Retirees</strong> keep Tricare for life at modest cost &mdash; a benefit worth six figures over a retirement.</li>
<li><strong>VA care</strong> for service-connected conditions is separate and additional.</li>
</ul>
{cta("See your cash compensation — then add Tricare's value on top.", "/")}
'''
write("tricare-value-military-health-care.html",
      "What Military Health Care Is Worth: Tricare's Hidden Paycheck",
      "Active-duty families pay $0 in medical premiums - comparable civilian coverage costs $15,000-$25,000/year. The employer-equivalent value of Tricare and how to add it to your pay.",
      "Tricare Value", body,
      faq=[("How much is Tricare worth?","For an active-duty family, the employer-equivalent value of Tricare medical and dental coverage is roughly $18,000-$25,000 per year - and you pay no premium and no tax on it."),
           ("Do active-duty families pay for Tricare?","No monthly medical premium for active-duty members or their families on Tricare Prime/Select; dental is a small monthly cost."),
           ("Does Tricare continue after I leave?","Transitional coverage (TAMP) can bridge 180 days after active duty, and retirees keep Tricare at modest cost.")],
      related=[("What's military pay worth in civilian salary?","/blog/military-pay-civilian-equivalent-rmc.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html")],
      blurb="Tricare is worth $18k&ndash;$25k/yr to a family &mdash; the paycheck that never hits your LES.")

# --- GI Bill value ---
body = f'''<h1>The GI Bill Is a Six-Figure Benefit: Here's the Math</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The Post-9/11 GI Bill is the most valuable education benefit in America &mdash; and for a member using it at
a high-cost school, it's worth <strong>well over $100,000</strong>. Counting it (and Tuition Assistance you use while
serving) is essential to understanding total military compensation.</p>
<h2>What the Post-9/11 GI Bill covers (at 100%)</h2>
<ul>
<li><strong>Tuition &amp; fees:</strong> full in-state public tuition, or up to a national cap at private schools (with the
Yellow Ribbon Program often covering the rest).</li>
<li><strong>Monthly housing allowance (MHA):</strong> based on the BAH rate for an <strong>E-5 with dependents</strong> at
your school's ZIP code &mdash; paid <em>to you</em> while enrolled.</li>
<li><strong>Books stipend:</strong> up to $1,000 per year.</li>
</ul>
<h2>Putting a number on 36 months of benefits</h2>
<p>At a public university, tuition + the E-5 housing allowance + books over a four-year degree commonly totals
<strong>$100,000&ndash;$160,000+</strong> in tax-free benefits, depending on location. In an expensive metro the housing
allowance alone can exceed <strong>$30,000/year</strong> &mdash; tied to the same
<a href="/blog/2026-bah-rates-explained.html">BAH rates</a> our calculator uses.</p>
<h2>Two more multipliers</h2>
<ul>
<li><strong>Transferability:</strong> career members can transfer unused benefits to a spouse or child &mdash; effectively
a tax-free college fund worth six figures.</li>
<li><strong>Tuition Assistance (TA):</strong> while serving, TA covers up to $250/semester-hour ($4,500/year) so you can
finish a degree <em>without</em> touching the GI Bill &mdash; then keep the GI Bill for later or transfer it.</li>
</ul>
{cta("The GI Bill housing stipend uses E-5 BAH — look up the rate for any school's ZIP.", "/")}
'''
write("gi-bill-value-explained.html",
      "The GI Bill Is a Six-Figure Benefit: The Real Math",
      "The Post-9/11 GI Bill is worth $100,000-$160,000+: full tuition, a monthly housing allowance based on E-5 BAH at your school, and a books stipend - plus transfer to a spouse or child.",
      "GI Bill Value", body,
      faq=[("How much is the GI Bill worth?","For a four-year degree, the Post-9/11 GI Bill commonly totals $100,000-$160,000+ in tax-free benefits - full in-state tuition, a monthly housing allowance based on E-5 BAH, and a books stipend."),
           ("How is the GI Bill housing allowance calculated?","It uses the BAH rate for an E-5 with dependents at your school's ZIP code, paid to you while enrolled."),
           ("Can I give my GI Bill to my kids?","Yes - career members can transfer unused Post-9/11 GI Bill benefits to a spouse or children, subject to a service commitment.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("What's military pay worth in civilian salary?","/blog/military-pay-civilian-equivalent-rmc.html"),
               ("BAH rates by location","/bah/")],
      blurb="The Post-9/11 GI Bill is worth $100k&ndash;$160k+ &mdash; tuition + E-5 housing stipend + transfer.")

# --- Total compensation vs civilian ---
_tcb5=BP["E-5"]["4"]; _tcbah=bah_rate("CA038","E05","with"); _tcbas=476.95
_tccash=(_tcb5+_tcbah+_tcbas)*12
_tctri=21000; _tctsp=_tcb5*12*0.05; _tcpen=_tcb5*12*0.10
_tctotal=_tccash+_tctri+_tctsp+_tcpen
body = f'''<h1>Military Total Compensation vs a Civilian Salary: The Honest Comparison</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">"I could make more as a civilian" is sometimes true &mdash; but only if you compare the <em>whole</em>
package. Cash is just the start; the tax-free allowances, free health care, retirement match, and pension accrual add up
fast. Here's a full-stack estimate for a mid-career E-5.</p>
<h2>Total compensation: E-5, 4 years, San Diego, family</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Component</th><th>Annual value</th><th>Taxed?</th></tr></thead><tbody>
<tr><td>Basic pay</td><td>{money(_tcb5*12)}</td><td>Yes</td></tr>
<tr><td>BAH (housing)</td><td>{money(_tcbah*12)}</td><td>No</td></tr>
<tr><td>BAS (food)</td><td>{money(_tcbas*12)}</td><td>No</td></tr>
<tr><td>Tricare (family medical+dental, est.)</td><td>~{money(_tctri)}</td><td>No</td></tr>
<tr><td>TSP match (BRS, 5% of basic)</td><td>~{money(_tctsp)}</td><td>Tax-deferred</td></tr>
<tr><td>Pension accrual (est. value/yr)</td><td>~{money(_tcpen)}</td><td>Deferred</td></tr>
<tr><td><strong>Total package</strong></td><td><strong>~{money(_tctotal)}</strong></td><td></td></tr>
</tbody></table></div>
<p class="callout">Roughly <strong>{money((_tcbah+_tcbas)*12+_tctri)}</strong> of this arrives <strong>tax-free</strong>.
After accounting for the tax advantage, a civilian would generally need a salary in the
<strong>{money(_tctotal*1.1)}&ndash;{money(_tctotal*1.2)}</strong> range to match the same lifestyle &mdash; before
counting 30 days of paid leave, education benefits, and base services.</p>
<h2>When civilian really does pay more</h2>
<ul>
<li><strong>High-demand technical fields</strong> (software, cyber, medicine) can out-earn military cash by a lot &mdash;
though often without the pension or job security.</li>
<li><strong>Low-cost-of-living areas</strong> shrink the BAH advantage, narrowing the gap.</li>
<li><strong>The pension is the wildcard:</strong> reach 20 years and the lifetime annuity is worth hundreds of thousands
&mdash; reach 19 and it's $0 under the legacy system (BRS softens this with the portable TSP).</li>
</ul>
<h2>The honest takeaway</h2>
<p>For most enlisted members in most locations, total military compensation is <strong>competitive with or better than</strong>
an equivalent civilian job once benefits are counted &mdash; and far more stable. Run <em>your</em> numbers, in
<em>your</em> ZIP code, before making the call.</p>
{cta("Start with your cash compensation — then layer benefits on top.", "/")}
'''
write("military-total-compensation-vs-civilian.html",
      "Military Total Compensation vs Civilian Salary: Full-Stack Math",
      f"A mid-career E-5 family's total package is worth ~{money(_tctotal)}/year once you count tax-free BAH/BAS, Tricare (~$21k), the TSP match, and pension accrual - like a {money(_tctotal*1.1)}+ civilian salary.",
      "Total Comp", body,
      faq=[("Is military pay better than civilian pay?",f"Once you count tax-free allowances, free Tricare, the TSP match, and pension accrual, a mid-career E-5 family's package is worth roughly {money(_tctotal)}/year - competitive with or better than an equivalent civilian job in most locations."),
           ("What is military total compensation?","The full package: basic pay + tax-free BAH and BAS + Tricare + TSP match + pension accrual + leave and education benefits - not just the basic-pay number."),
           ("When does a civilian job pay more?","In high-demand technical fields or low-cost-of-living areas where the BAH advantage shrinks - though usually without the military pension and job security.")],
      related=[("What's military pay worth in civilian salary?","/blog/military-pay-civilian-equivalent-rmc.html"),
               ("What military health care is worth","/blog/tricare-value-military-health-care.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html")],
      blurb=f"A mid-career E-5 family's full package &asymp; {money(_tctotal)}/yr &mdash; the honest civilian comparison.")

# ===================== TRANSITION / VA / FAMILY BATCH =====================
# --- VA disability compensation (2026 rates) ---
_VA = [("10%","$180.42"),("20%","$356.66"),("30%","$552.47"),("40%","$795.84"),("50%","$1,132.90"),
       ("60%","$1,435.02"),("70%","$1,808.45"),("80%","$2,102.15"),("90%","$2,362.30"),("100%","$3,938.58")]
_varows = "".join(f"<tr><td>{r}</td><td>{a}</td></tr>" for r,a in _VA)
body = f'''<h1>2026 VA Disability Compensation Rates: The Complete Pay Chart</h1>
<p class="meta">Updated {_D2} &middot; Rates effective December 1, 2025</p>
<p class="lead">VA disability compensation is a <strong>monthly, tax-free</strong> payment for veterans with service-connected
conditions. For 2026 the rates rose <strong>2.8%</strong> (matching the Social Security COLA), ranging from
<strong>$180.42/month at 10%</strong> to <strong>$3,938.58/month at 100%</strong> for a veteran with no dependents.</p>
<h2>2026 VA disability rates (veteran alone, no dependents)</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Rating</th><th>Monthly payment</th></tr></thead><tbody>{_varows}</tbody></table></div>
<p class="callout">These payments are <strong>completely tax-free</strong> &mdash; federal and state. A 100% rating is worth
about <strong>$47,000/year tax-free</strong>, equivalent to a much larger taxable salary.</p>
<h2>How dependents change it</h2>
<p>At <strong>30% and above</strong>, you receive extra for a spouse, children, and dependent parents. At 10% and 20% the
rate is flat regardless of dependents. A 100%-rated veteran with a spouse and two children receives noticeably more than
the single-veteran figure above.</p>
<h2>The "VA math" nobody expects</h2>
<p>VA ratings <strong>don't add</strong> &mdash; they combine using "whole-person" math. Two 50% conditions don't make
100%; they combine to 75% (rounded to the nearest 10 &rarr; 80%). This is why veterans with several mid-size ratings
often land lower than they expect. Use a combined-ratings calculator before assuming a total.</p>
<h2>How it relates to military retirement</h2>
<p>VA disability is <strong>separate from</strong> military retired pay. Historically the two were offset, but
<strong>Concurrent Retirement and Disability Pay (CRDP)</strong> now lets many 20-year retirees with a 50%+ rating receive
<em>both</em> in full &mdash; a major boost to <a href="/blog/military-retirement-brs-vs-high3.html">retirement income</a>.</p>
{cta("Planning your transition? Estimate your active-duty pay now and VA later.", "/")}
'''
write("2026-va-disability-rates.html",
      "2026 VA Disability Compensation Rates: Complete Tax-Free Pay Chart",
      "2026 VA disability rates rose 2.8%: from $180.42/month at 10% to $3,938.58 at 100% (veteran alone), all tax-free. Full chart, how dependents and CRDP work, and VA combined-ratings math.",
      "VA Disability", body,
      faq=[("How much is 100% VA disability in 2026?","$3,938.58 per month for a veteran with no dependents — about $47,000 per year, completely tax-free. More with a spouse or children."),
           ("Is VA disability pay taxable?","No. VA disability compensation is exempt from both federal and state income tax."),
           ("Do VA ratings add together?","No. Multiple ratings combine using whole-person math, not simple addition — two 50% conditions combine to roughly 80%, not 100%.")],
      related=[("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("Military separation & severance pay","/blog/military-separation-severance-pay.html"),
               ("Military total compensation vs civilian","/blog/military-total-compensation-vs-civilian.html")],
      blurb="2026 VA disability: $180/mo (10%) to $3,939/mo (100%), tax-free &mdash; plus the combined-ratings catch.")

# --- Separation / severance pay ---
_sevb = BP["E-5"]["6"]
_sev = _sevb * 12 * 0.10 * 6
body = f'''<h1>Military Separation Pay &amp; Severance: What You Get When You Leave Early</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Leave the military before 20 years and, depending on <em>how</em> you separate, you may receive a lump-sum
<strong>separation or severance payment</strong>. The amounts reach into the tens of thousands &mdash; but the rules,
taxes, and recoupment traps catch people off guard.</p>
<h2>The main types</h2>
<ul>
<li><strong>Involuntary Separation Pay (ISP):</strong> for members involuntarily separated (e.g., not selected for
retention) with 6+ years. <em>Full</em> ISP = <strong>10% &times; years of service &times; 12 &times; monthly basic pay</strong>.</li>
<li><strong>Disability Severance Pay:</strong> a lump sum for members separated for a disability rated under 30% and not
eligible to retire &mdash; 2 months of basic pay per year of service (minimums apply).</li>
<li><strong>Voluntary Separation Pay (VSP):</strong> offered during drawdowns to encourage voluntary departure.</li>
</ul>
<h2>A worked example</h2>
<p>An <a href="/blog/how-much-does-an-e5-make-2026.html">E-5 with 6 years</a> ({money(_sevb)}/month basic) involuntarily
separated with full ISP would receive about:</p>
<p style="font-size:1.1rem"><strong>10% &times; 6 years &times; 12 &times; {money(_sevb)} = {money(_sev)}</strong> (lump sum, before taxes).</p>
<h2>The catches</h2>
<ul>
<li><strong>It's taxable</strong> &mdash; withheld at the 22% supplemental rate, though combat-zone-earned portions follow
the <a href="/blog/combat-zone-tax-exclusion.html">CZTE</a>.</li>
<li><strong>VA recoupment:</strong> if you later receive VA disability or military retired pay, the government often
<strong>recoups</strong> separation pay from those future benefits &mdash; you don't always keep both.</li>
<li><strong>Half rate:</strong> some separations qualify only for <em>half</em> ISP, and a service obligation in the
Reserves is usually attached.</li>
</ul>
{cta("Know your monthly basic pay — it drives every separation formula.", "/")}
'''
write("military-separation-severance-pay.html",
      "Military Separation & Severance Pay: Amounts, Taxes & Recoupment",
      f"Involuntary Separation Pay = 10% x years x 12 x monthly basic. An E-5 with 6 years gets about {money(_sev)}. How disability severance, taxes, and VA recoupment work.",
      "Separation Pay", body,
      faq=[("How is military separation pay calculated?","Full Involuntary Separation Pay = 10% x years of service x 12 x monthly basic pay. An E-5 with 6 years receives roughly "+money(_sev)+", before taxes."),
           ("Is separation pay taxable?","Yes — it's withheld at the 22% supplemental rate, except portions earned in a combat zone, which follow the combat-zone tax exclusion."),
           ("Will I have to pay back separation pay?","Often partially — if you later receive VA disability or military retired pay, the government typically recoups separation pay from those benefits.")],
      related=[("2026 VA disability rates","/blog/2026-va-disability-rates.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("Combat zone tax exclusion","/blog/combat-zone-tax-exclusion.html")],
      blurb=f"Involuntary Separation Pay &asymp; {money(_sev)} for an E-5/6yr &mdash; and the VA recoupment trap.")

# --- Military family allowances ---
body = f'''<h1>Military Family Money: Allowances &amp; Programs Beyond BAH</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Beyond <a href="/blog/2026-bah-rates-explained.html">BAH</a> and BAS, military families can tap a stack of
allowances and programs that quietly add up &mdash; for child care, special-needs care, spouse careers, and family
separation. Here's the field guide.</p>
<h2>Direct pay for families</h2>
<ul>
<li><strong>Family Separation Allowance (FSA):</strong> <strong>$300/month</strong> when duty keeps you away from
dependents 30+ days &mdash; see the <a href="/blog/military-special-pays-guide.html">special pays guide</a>.</li>
<li><strong>BAH "with dependents" rate:</strong> a higher housing allowance the moment you have a spouse or child &mdash;
how it works in <a href="/blog/bah-with-vs-without-dependents.html">with vs without dependents</a>.</li>
<li><strong>Basic Needs Allowance:</strong> a monthly top-up for lower-income families &mdash; the
<a href="/blog/basic-needs-allowance-explained.html">BNA</a>.</li>
</ul>
<h2>Child care help</h2>
<ul>
<li><strong>Military Child Care Fee Assistance:</strong> subsidies that offset the cost of off-base child care when a CDC
slot isn't available &mdash; often hundreds of dollars a month.</li>
<li><strong>CDC subsidized rates:</strong> on-base Child Development Centers charge on an income-based sliding scale.</li>
</ul>
<h2>Special-needs families (EFMP)</h2>
<p>The <strong>Exceptional Family Member Program</strong> coordinates assignments and care for families with special
medical or educational needs, and can unlock respite care hours &mdash; not cash, but real dollar value.</p>
<h2>Spouse careers</h2>
<ul>
<li><strong>MyCAA:</strong> up to <strong>$4,000</strong> in tuition assistance for eligible military spouses pursuing
licenses, certifications, or associate degrees in portable career fields.</li>
<li><strong>SECO &amp; the Military Spouse Employment Partnership</strong> connect spouses to remote- and
relocation-friendly employers.</li>
<li><strong>MSRRA</strong> keeps a spouse's tax residency with the servicemember &mdash; see the
<a href="/blog/military-tax-filing-guide.html">tax filing guide</a>.</li>
</ul>
<p class="callout">None of these show up in a basic pay chart, but for a family they can be worth thousands of dollars a
year on top of cash compensation.</p>
{cta("Start with your cash pay — basic, BAH and BAS — then layer family programs on top.", "/")}
'''
write("military-family-allowances-guide.html",
      "Military Family Money: Allowances & Programs Beyond BAH (2026)",
      "Beyond BAH and BAS: Family Separation Allowance ($300/mo), child care fee assistance, EFMP, MyCAA ($4,000 spouse tuition), and the Basic Needs Allowance — the family money field guide.",
      "Family Money", body,
      faq=[("What allowances do military families get?","Beyond BAH and BAS: Family Separation Allowance ($300/month), the higher with-dependents BAH rate, the Basic Needs Allowance, child care fee assistance, EFMP support, and MyCAA spouse tuition."),
           ("What is MyCAA?","My Career Advancement Account provides up to $4,000 in tuition assistance for eligible military spouses pursuing licenses, certifications, or associate degrees."),
           ("Is there help with military child care costs?","Yes — Military Child Care Fee Assistance subsidizes off-base care when an on-base CDC slot isn't available, and CDCs charge on an income-based sliding scale.")],
      related=[("BAH with vs without dependents","/blog/bah-with-vs-without-dependents.html"),
               ("Basic Needs Allowance explained","/blog/basic-needs-allowance-explained.html"),
               ("Special pays guide (incl. FSA)","/blog/military-special-pays-guide.html")],
      blurb="FSA, child-care fee assistance, EFMP, MyCAA &mdash; the family money beyond BAH and BAS.")

# ===================== HOUSING / GUARD BATCH =====================
# --- VA Home Loan & BAH ---
_vlb = BP["E-5"]["6"]; _vlbah = bah_rate("CA038","E05","with"); _vlbas = 476.95
_vl_income = (_vlb+_vlbah+_vlbas)*12
body = f'''<h1>VA Home Loan &amp; BAH: How Your Housing Allowance Buys a House</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The VA home loan is one of the most powerful benefits in the military &mdash; <strong>$0 down, no PMI</strong>,
and competitive rates. The quiet superpower behind it: lenders count your tax-free <strong>BAH and BAS as income</strong>,
which can dramatically boost how much house you qualify for.</p>
<h2>Why BAH supercharges your application</h2>
<p>Mortgage lenders qualify you on a debt-to-income ratio. Because BAH and BAS are
<a href="/blog/2026-bah-rates-explained.html">tax-free</a>, many lenders "gross them up" &mdash; treating, say,
{money(_vlbah)} of BAH as worth even more in equivalent taxable income. For an
<a href="/blog/how-much-does-an-e5-make-2026.html">E-5 with 6 years</a> in San Diego, total qualifying income looks
like:</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>Income source</th><th>Monthly</th><th>Annual</th></tr></thead><tbody>
<tr><td>Basic pay</td><td>{money(_vlb)}</td><td>{money(_vlb*12)}</td></tr>
<tr><td>BAH</td><td>{money(_vlbah)}</td><td>{money(_vlbah*12)}</td></tr>
<tr><td>BAS</td><td>{money(_vlbas)}</td><td>{money(_vlbas*12)}</td></tr>
<tr><td><strong>Total qualifying income</strong></td><td><strong>{money(_vlb+_vlbah+_vlbas)}</strong></td><td><strong>{money(_vl_income)}</strong></td></tr>
</tbody></table></div>
<h2>The VA loan advantages</h2>
<ul>
<li><strong>No down payment</strong> on most purchases &mdash; rare anywhere else.</li>
<li><strong>No private mortgage insurance (PMI)</strong> &mdash; saves hundreds a month versus a low-down conventional loan.</li>
<li><strong>A one-time VA funding fee</strong> (financed into the loan; waived for veterans with a
<a href="/blog/2026-va-disability-rates.html">service-connected disability rating</a>).</li>
<li><strong>Reusable</strong> &mdash; the benefit isn't one-and-done.</li>
</ul>
<h2>The BAH "house hack"</h2>
<p>Buy with a VA loan and your BAH can effectively cover the mortgage. Buy a duplex/multi-unit (VA allows up to 4 units if
you live in one) and rent the others, and BAH plus rental income can <strong>pay the whole note</strong> &mdash; a common
way service members build wealth on a single enlistment.</p>
<p class="callout">Run the numbers first: BAH covers 95% of <em>rental</em> cost by design, not a mortgage with taxes,
insurance, and maintenance. Use the <a href="/">calculator</a> to confirm your exact BAH before house-shopping.</p>
{cta("Look up your BAH by ZIP — it's the number lenders will use.", "/")}
'''
write("va-home-loan-and-bah.html",
      "VA Home Loan & BAH: How Your Housing Allowance Buys a House",
      f"Lenders count tax-free BAH and BAS as income on a VA loan — an E-5 in San Diego shows {money(_vl_income)}/year qualifying income. $0 down, no PMI, and the BAH house-hack explained.",
      "VA Loan", body,
      faq=[("Does BAH count as income for a VA loan?","Yes — lenders count tax-free BAH and BAS as qualifying income, and often gross them up, which significantly increases how much house you qualify for."),
           ("Do VA loans require a down payment?","No — most VA purchase loans require $0 down and charge no private mortgage insurance (PMI)."),
           ("Can I use BAH to buy a rental property?","Yes — the VA allows up to a 4-unit property if you live in one unit; BAH plus rental income can cover the mortgage, a popular wealth-building move.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("BAH rates by location","/bah/"),
               ("On-base vs off-base housing","/blog/on-base-vs-off-base-housing.html")],
      blurb="Lenders count BAH/BAS as income &mdash; $0 down, no PMI, and the BAH house-hack.")

# --- On-base vs off-base ---
_obb = bah_rate("CA038","E05","with")
body = f'''<h1>On-Base vs Off-Base Housing: The BAH Decision That Pays You</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Choosing where to live isn't just about commute &mdash; it decides whether your
<a href="/blog/2026-bah-rates-explained.html">BAH</a> lands in <em>your</em> pocket or goes straight back to housing.
Here's the money math.</p>
<h2>How the money flows</h2>
<ul>
<li><strong>On-base (government or privatized housing):</strong> you typically <strong>forfeit your entire BAH</strong> as
rent &mdash; an automatic allotment equal to your with-dependents rate. Utilities are often included; it's simple and
predictable, but you keep $0 of the allowance.</li>
<li><strong>Off-base:</strong> you receive the <strong>full BAH</strong> and pay your own rent/mortgage. If you find
housing for <em>less</em> than your BAH, you <strong>keep the difference</strong> &mdash; tax-free.</li>
</ul>
<h2>A quick example (E-5, San Diego, with dependents)</h2>
<p>BAH of <strong>{money(_obb)}/month</strong>. Live on base &rarr; you keep $0 of it (rent + utilities covered). Rent off
base for {money(_obb-400)} &rarr; you pocket <strong>{money(400)}/month tax-free</strong> &mdash; about
{money(400*12)}/year &mdash; but you now manage utilities, deposits, and renter's insurance.</p>
<h2>The honest trade-offs</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Factor</th><th>On base</th><th>Off base</th></tr></thead><tbody>
<tr><td>Keep leftover BAH?</td><td>No</td><td>Yes (if rent &lt; BAH)</td></tr>
<tr><td>Utilities</td><td>Usually included</td><td>You pay (often)</td></tr>
<tr><td>Commute</td><td>Short</td><td>Varies</td></tr>
<tr><td>Maintenance</td><td>Handled for you</td><td>Landlord/you</td></tr>
<tr><td>Upfront costs</td><td>Minimal</td><td>Deposits, setup</td></tr>
</tbody></table></div>
<p class="callout">There's no universal winner: in pricey markets where rent &ge; BAH, on-base predictability can beat
going off base; in cheaper markets, off-base members frequently keep a few hundred dollars a month.</p>
{cta("Look up your exact BAH — then compare it to local rents before you decide.", "/")}
'''
write("on-base-vs-off-base-housing.html",
      "On-Base vs Off-Base Housing: The BAH Decision That Pays You",
      f"Live on base and you forfeit your full BAH as rent; live off base and you keep any BAH left over after rent — tax-free. The money math, with an E-5 San Diego example.",
      "Housing Choice", body,
      faq=[("Do you keep BAH if you live on base?","Generally no — on-base or privatized housing takes your full BAH as rent via allotment, though utilities are often included."),
           ("Can you make money on BAH?","Yes — if you live off base and your rent is less than your BAH, you keep the difference tax-free."),
           ("Is on-base or off-base housing better financially?","It depends on local rents: where rent meets or exceeds BAH, on-base predictability often wins; in cheaper markets, off-base members usually keep leftover BAH.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("VA home loan & BAH","/blog/va-home-loan-and-bah.html"),
               ("BAH rates by location","/bah/")],
      blurb="Live on base = forfeit BAH; off base = keep what's left of it, tax-free. The full trade-off.")

# --- National Guard pay ---
_ngperp = BP["E-5"]["4"]/30
body = f'''<h1>National Guard Pay Explained: Drill, Title 32, Title 10 &amp; Activations</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">National Guard pay works like the Reserve for normal drilling &mdash; but the Guard has a twist civilians
and reservists don't deal with: <strong>state activations</strong> under Title 32 and Title 10, which change how (and by
whom) you're paid.</p>
<h2>Normal drilling: same as the Reserve</h2>
<p>For monthly drill, Guard pay is identical to <a href="/blog/reserve-drill-pay-explained.html">Reserve drill pay</a>:
each 4-hour drill period pays <strong>1/30 of monthly basic pay</strong>. A 2026 E-5 with 4 years earns about
<strong>{money(_ngperp)}/drill period</strong>, ~{money(_ngperp*4)} per drill weekend, plus Annual Training. You also earn
<a href="/blog/reserve-drill-pay-explained.html">retirement points</a> toward a "good year."</p>
<h2>The activation statuses that change your pay</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Status</th><th>Who controls / pays</th><th>Pay &amp; benefits</th></tr></thead><tbody>
<tr><td>Drill (IDT)</td><td>State, federally funded</td><td>Basic pay per drill period only</td></tr>
<tr><td>Annual Training</td><td>Federal</td><td>Active-duty pay + BAS + BAH (RC/Transit or locality)</td></tr>
<tr><td>Title 32 (state, fed-funded)</td><td>Governor, federal money</td><td>Full active-duty pay &amp; allowances; can count toward benefits</td></tr>
<tr><td>Title 10 (federal active)</td><td>President/SecDef</td><td>Full active-duty pay &amp; allowances; deployments, federal benefits</td></tr>
<tr><td>State Active Duty (SAD)</td><td>Governor, state money</td><td>Paid under state rules (varies by state) &mdash; not federal pay</td></tr>
</tbody></table></div>
<h2>Why the status matters for your wallet</h2>
<ul>
<li><strong>Title 10 / Title 32 orders of 30+ days</strong> bring full <a href="/blog/2026-bah-rates-explained.html">BAH</a>,
BAS, and often <a href="/blog/combat-zone-tax-exclusion.html">tax exclusions</a> if deployed &mdash; a big pay bump over drilling.</li>
<li><strong>State Active Duty</strong> (hurricane, wildfire, civil response) pays under <em>state</em> law, which can be
much less than federal active-duty pay &mdash; check your state's rate.</li>
<li><strong>Healthcare &amp; retirement credit</strong> differ by status &mdash; 90+ days on federal orders can trigger
post-9/11 GI Bill eligibility tiers and TRICARE.</li>
</ul>
{cta("On orders? Switch to reserve mode and add a ZIP to estimate activated pay.", deep(mode="reserve"))}
'''
write("national-guard-pay-explained.html",
      "National Guard Pay: Drill, Title 32 vs Title 10, and Activations",
      f"National Guard drill pay matches the Reserve (1/30 of basic per period, ~{money(_ngperp)} for an E-5), but Title 32, Title 10, and State Active Duty change your pay and benefits. Full breakdown.",
      "Guard Pay", body,
      faq=[("Is National Guard pay the same as the Reserve?","For monthly drill, yes — both pay 1/30 of monthly basic pay per drill period. The Guard differs when activated under Title 32, Title 10, or State Active Duty."),
           ("What is the difference between Title 32 and Title 10?","Title 32 is state-controlled but federally funded duty; Title 10 is federal active duty (deployments). Both pay full active-duty pay and allowances; benefits eligibility can differ."),
           ("Does State Active Duty pay the same as federal orders?","Not necessarily — State Active Duty is paid under state law and rates, which are often lower than federal active-duty pay.")],
      related=[("Reserve drill pay explained","/blog/reserve-drill-pay-explained.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("Deployment pay explained","/blog/deployment-pay-explained.html")],
      blurb=f"Guard drill = Reserve (~{money(_ngperp)}/period), but Title 32/10/SAD change everything when activated.")

# ===================== BRANCH / AVIATION / SEA BATCH =====================
# --- Branch pay comparison ---
body = f'''<h1>Does Military Pay Differ by Branch? Army vs Navy vs Air Force vs Marines</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Short answer: <strong>no</strong>. Base pay, BAH, and BAS are identical across the Army, Navy, Air Force,
Marine Corps, Space Force, and Coast Guard. A 2026 <a href="/blog/how-much-does-an-e5-make-2026.html">E-5 with 4 years</a>
earns <strong>{money(BP["E-5"]["4"])}/month</strong> in basic pay whether they're a Soldier, Sailor, Airman, Marine,
Guardian, or Coast Guardsman.</p>
<h2>What's identical across all branches</h2>
<ul>
<li><strong>Basic pay</strong> &mdash; set DoD-wide by pay grade and years of service (see the
<a href="/blog/2026-military-pay-chart.html">2026 pay chart</a>).</li>
<li><strong>BAH</strong> &mdash; set by ZIP code, grade, and dependents &mdash; not by branch.</li>
<li><strong>BAS</strong> &mdash; $476.95 enlisted / $328.48 officer in 2026.</li>
<li><strong>Most special pays, allowances, retirement, and Tricare.</strong></li>
</ul>
<h2>Where branches actually differ</h2>
<p>Total pay can differ not because of the branch, but because of <strong>what you do and where you go</strong>:</p>
<ul>
<li><strong>Job-specific special pays:</strong> sea pay and sub pay are common in the Navy and Coast Guard; jump pay in
the Army and Marines; flight pay across services for aviators. See the
<a href="/blog/military-special-pays-guide.html">special pays guide</a>.</li>
<li><strong>Deployment frequency</strong> drives <a href="/blog/combat-zone-tax-exclusion.html">tax-free combat pay</a>,
FSA, and danger pay &mdash; which varies by mission, not service emblem.</li>
<li><strong>Bonuses</strong> are set per critical job, so a high-demand rating in one branch can out-pay a common MOS in
another &mdash; same pay table, different <a href="/blog/military-bonuses-taxes.html">bonus</a>.</li>
<li><strong>Promotion speed</strong> varies by branch and career field, which changes how fast you climb the same chart.</li>
</ul>
<p class="callout">So "Army pay vs Air Force pay" really comes down to your job, deployments, bonuses, and promotion
timing &mdash; not a different paycheck for the same rank.</p>
{cta("Pick your rank, years, and ZIP — the same calculator works for every branch.", "/")}
'''
write("does-military-pay-differ-by-branch.html",
      "Does Military Pay Differ by Branch? Army vs Navy vs Air Force vs Marines",
      f"No — basic pay, BAH, and BAS are identical across all branches. A 2026 E-5 earns {money(BP['E-5']['4'])}/month regardless of service. What actually changes total pay: job, deployments, and bonuses.",
      "Branch Pay", body,
      faq=[("Does the Air Force pay more than the Army?","No. Basic pay, BAH, and BAS are identical across all U.S. military branches for the same rank and years of service. Differences come from job-specific special pays, bonuses, deployments, and promotion speed."),
           ("Do Marines get paid less than other branches?","No — Marines earn the same base pay and allowances as every other branch for the same grade and time in service."),
           ("Why do people say one branch pays more?","Because total pay varies by job (special pays), bonuses for critical skills, deployment frequency, and how fast you promote — not the branch itself.")],
      related=[("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("Special pays guide","/blog/military-special-pays-guide.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html")],
      blurb="Pay is identical across branches &mdash; what really differs is job, deployments, and bonuses.")

# --- Aviation / flight pay ---
body = f'''<h1>Military Flight Pay: ACIP, Aviation Bonus &amp; What Pilots Make</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Military pilots earn the same <a href="/blog/2026-military-pay-chart.html">basic pay</a> as any other
officer at their rank &mdash; then stack <strong>Aviation Career Incentive Pay (ACIP)</strong> and, often, a large
<strong>Aviation Bonus</strong> on top. Together these can add tens of thousands of dollars a year.</p>
<h2>Aviation Career Incentive Pay (ACIP) &mdash; "flight pay"</h2>
<p>ACIP is monthly continuous pay for rated officers, scaling with <strong>years of aviation service</strong>:</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>Years of aviation service</th><th>Monthly ACIP (officer)</th></tr></thead><tbody>
<tr><td>2 or fewer</td><td>$150</td></tr>
<tr><td>Over 6</td><td>$700</td></tr>
<tr><td>Over 10</td><td>up to $1,000</td></tr>
<tr><td>14&ndash;22 (peak)</td><td>$1,000 (max)</td></tr>
<tr><td>Over 24</td><td>tapers back down</td></tr>
</tbody></table></div>
<p>Enlisted aircrew receive <strong>Career Enlisted Flyer Incentive Pay (CEFIP)</strong>, roughly $150&ndash;$400/month
by years of service.</p>
<h2>The Aviation Bonus (the big one)</h2>
<p>To retain pilots, the services offer an <strong>Aviation Bonus (AvB)</strong> &mdash; an annual contract payment for
committing additional years. Amounts vary by airframe and need but commonly run <strong>$15,000&ndash;$35,000 per year</strong>,
with the highest rates for fighter and other hard-to-retain communities. It's taxable (and combat-zone excludable).</p>
<h2>Putting it together</h2>
<p>An O-3 aviator with ~8 years might earn O-3 basic pay ({money(BP["O-3"]["8"])}/month) + ACIP (~$840) + a prorated
Aviation Bonus &mdash; plus tax-free BAH and BAS. Flight pay is taxable; the allowances are not.</p>
{cta("Add your flight pay and bonus amounts in the calculator's special-pay fields.", "/")}
'''
write("military-flight-pay-acip-aviation-bonus.html",
      "Military Flight Pay: ACIP, Aviation Bonus & What Pilots Make (2026)",
      "Military pilots earn basic pay plus Aviation Career Incentive Pay (up to $1,000/month) and an Aviation Bonus of $15,000–$35,000/year. How flight pay scales and what aviators really make.",
      "Flight Pay", body,
      faq=[("How much is military flight pay?","Aviation Career Incentive Pay scales from $150/month early to a $1,000/month maximum at peak years for officers; enlisted aircrew get $150–$400/month. A separate Aviation Bonus adds $15,000–$35,000/year."),
           ("How much do military pilots make?","Basic pay for their rank plus ACIP (up to $1,000/month), often a large Aviation Bonus, and tax-free BAH and BAS — frequently well over $120,000/year in total compensation for a mid-career pilot."),
           ("Is flight pay taxable?","Yes — ACIP and the Aviation Bonus are taxable, except portions earned in a combat zone. BAH and BAS remain tax-free.")],
      related=[("Special pays guide","/blog/military-special-pays-guide.html"),
               ("How much does an O-3 make in 2026?","/blog/how-much-does-an-o3-make-2026.html"),
               ("Warrant officer pay 2026","/blog/warrant-officer-pay-2026.html")],
      blurb="ACIP up to $1,000/mo + a $15k&ndash;$35k/yr Aviation Bonus &mdash; what pilots really make.")

# --- Sea pay & sub pay ---
body = f'''<h1>Career Sea Pay &amp; Submarine Duty Pay: The Navy's Extra Money</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Sailors and Coast Guardsmen who serve at sea &mdash; and submariners in particular &mdash; earn special
pays that surface members don't. <strong>Career Sea Pay</strong> and <strong>Submarine Duty Pay</strong> can add several
hundred dollars a month, and they grow with experience.</p>
<h2>Career Sea Pay (CSP)</h2>
<ul>
<li>Paid to members <strong>assigned to a ship or ship-based unit</strong>, scaling with pay grade and
<strong>cumulative years of sea duty</strong> &mdash; the more sea time over a career, the higher the rate.</li>
<li>Rates run from modest amounts up to roughly <strong>$800/month</strong> for senior, sea-heavy careers.</li>
<li>A <strong>Career Sea Pay Premium</strong> adds extra after long consecutive periods at sea.</li>
</ul>
<h2>Submarine Duty Pay</h2>
<ul>
<li>Paid to qualified submariners, scaling by <strong>grade and years of service</strong> &mdash; commonly
<strong>$75&ndash;$600+/month</strong>.</li>
<li>Reflects the demanding, isolated nature of submarine deployments.</li>
<li>Nuclear-trained personnel may <em>also</em> draw nuclear-field special pays and bonuses on top.</li>
</ul>
<h2>How it stacks</h2>
<p>A Navy <a href="/blog/how-much-does-an-e6-make-2026.html">E-6</a> on sea duty could draw E-6 basic pay
({money(BP["E-6"]["10"])}/month at 10 years) + Career Sea Pay + (if a submariner) Sub Duty Pay + tax-free BAH and BAS.
These special pays are <strong>taxable</strong>, but combat-zone deployments can exclude them.</p>
<p class="callout">Sea and sub pay are why two E-6s with identical rank and time in service can take home very different
amounts &mdash; it's the <a href="/blog/military-special-pays-guide.html">special pays</a>, not the base pay.</p>
{cta("Enter your sea pay and sub pay in the calculator to see your real take-home.", "/")}
'''
write("career-sea-pay-submarine-duty-pay.html",
      "Career Sea Pay & Submarine Duty Pay: The Navy's Extra Money (2026)",
      "Career Sea Pay (up to ~$800/month) and Submarine Duty Pay ($75–$600+/month) reward Navy and Coast Guard members at sea, scaling with grade and years of sea duty. How they stack and are taxed.",
      "Sea Pay", body,
      faq=[("How much is Navy sea pay?","Career Sea Pay scales with pay grade and cumulative years of sea duty, from modest amounts up to roughly $800/month for senior, sea-heavy careers, plus a premium for long stretches at sea."),
           ("How much is submarine duty pay?","Submarine Duty Pay commonly runs $75–$600+ per month by grade and years of service; nuclear-trained submariners may also receive nuclear special pays."),
           ("Is sea pay taxable?","Yes — Career Sea Pay and Submarine Duty Pay are taxable, except portions earned in a designated combat zone.")],
      related=[("Special pays guide","/blog/military-special-pays-guide.html"),
               ("How much does an E-6 make in 2026?","/blog/how-much-does-an-e6-make-2026.html"),
               ("Does military pay differ by branch?","/blog/does-military-pay-differ-by-branch.html")],
      blurb="Career Sea Pay (up to ~$800/mo) and Sub Duty Pay ($75&ndash;$600+) &mdash; the Navy's extra money.")

# ===================== PRACTICAL MONEY BATCH =====================
# --- PPM / DITY move ---
body = f'''<h1>PPM (DITY) Moves: How to Make Money on a Military Move</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">When you PCS, the government will move you &mdash; or pay <em>you</em> to do it yourself. A
<strong>Personally Procured Move (PPM</strong>, formerly DITY) reimburses you <strong>95% of what the government would
have paid</strong> a contractor. Move efficiently and the leftover is profit &mdash; often <strong>thousands of dollars</strong>.</p>
<h2>How the money works</h2>
<ul>
<li>The military calculates the <strong>Government Constructive Cost (GCC)</strong> &mdash; what a contracted move of your
authorized weight would cost.</li>
<li>You're paid <strong>95% of the GCC</strong> as your PPM incentive, regardless of what you actually spend.</li>
<li>Your <strong>profit = 95% of GCC &minus; your real costs</strong> (truck rental, fuel, boxes, labor, tolls).</li>
</ul>
<h2>A realistic example</h2>
<p>Say your GCC for a mid-distance move of 8,000 lbs is $6,000. Your PPM incentive is <strong>$5,700</strong>. Rent a
truck and do it yourself for $2,200 and you keep about <strong>$3,500</strong> &mdash; though part of the
<em>incentive</em> is taxable income (the portion above your documented expenses). Keep every receipt.</p>
<h2>Don't leave these on the table</h2>
<ul>
<li><strong>Advance Operating Allowance:</strong> request up to 60% of your estimated incentive upfront to cover truck and supplies.</li>
<li><strong>Weight tickets:</strong> empty and full certified weigh tickets are mandatory &mdash; no tickets, no payment.</li>
<li><strong>Pro-gear:</strong> professional gear and a spouse's pro-gear don't count against your weight allowance.</li>
<li><strong>Partial PPM:</strong> let the government move the heavy stuff and PPM the rest &mdash; you still profit on your portion.</li>
</ul>
<h2>How it fits your PCS money</h2>
<p>PPM profit stacks with your tax-free <a href="/blog/dislocation-allowance-dla-2026.html">Dislocation Allowance</a>,
travel per diem, and mileage &mdash; a well-run PCS can net <strong>$5,000&ndash;$10,000+</strong> in combined
entitlements and PPM profit.</p>
{cta("Heading to a new duty station? Look up your new BAH before you sign a lease.", "/")}
'''
write("ppm-dity-move-make-money.html",
      "PPM (DITY) Moves: How to Make Money on a Military PCS",
      "A Personally Procured Move pays you 95% of the government's move cost — do it cheaply and keep the difference, often thousands. How the GCC, advance, weight tickets, and taxes work.",
      "PPM Move", body,
      faq=[("How much can you make on a PPM/DITY move?","You're paid 95% of what the government would pay a contractor; profit is that amount minus your real costs (truck, fuel, supplies) — commonly a few thousand dollars on a typical move."),
           ("Is PPM money taxable?","The portion of your incentive above your documented moving expenses is taxable income — keep all receipts to minimize the taxable amount."),
           ("Do I need weight tickets for a PPM?","Yes — certified empty and full weigh tickets are mandatory; without them you won't be paid.")],
      related=[("Dislocation Allowance (DLA) 2026","/blog/dislocation-allowance-dla-2026.html"),
               ("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("BAH rates by location","/bah/")],
      blurb="A PPM pays 95% of the government move cost &mdash; do it cheap and pocket thousands.")

# --- Selling leave / terminal leave ---
_slb = BP["E-5"]["6"]; _slday = _slb/30
body = f'''<h1>Selling Military Leave vs Terminal Leave: What 30 Days Is Worth</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">When you separate or retire, accrued leave is money. You can <strong>sell it back</strong> for cash or burn
it as <strong>terminal leave</strong> &mdash; and for most people, terminal leave is worth noticeably more. Here's the math.</p>
<h2>What a day of leave is worth</h2>
<p>Selling leave pays <strong>1 day of basic pay per day of leave</strong> &mdash; basic pay only, no BAH or BAS. For a
2026 <a href="/blog/how-much-does-an-e5-make-2026.html">E-5 with 6 years</a> ({money(_slb)}/month basic):</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>Leave sold</th><th>Cash (basic pay only, taxable)</th></tr></thead><tbody>
<tr><td>1 day</td><td>{money(_slday)}</td></tr>
<tr><td>10 days</td><td>{money(_slday*10)}</td></tr>
<tr><td>30 days</td><td>{money(_slday*30)}</td></tr>
<tr><td>60 days (career cap)</td><td>{money(_slday*60)}</td></tr>
</tbody></table></div>
<h2>Why terminal leave usually wins</h2>
<p>On <strong>terminal leave</strong>, you stay on active duty and keep drawing your <em>full</em> paycheck &mdash; basic
pay <strong>plus tax-free BAH and BAS</strong> &mdash; while you're already done working (often job-hunting or starting a
civilian job). Selling leave only pays the basic-pay portion. For our E-5 with BAH, 30 days of terminal leave is worth
hundreds more than selling the same 30 days, because you keep the allowances.</p>
<h2>The rules and limits</h2>
<ul>
<li><strong>60-day career cap</strong> on selling leave (war-time exceptions aside) &mdash; sell beyond that and it's lost.</li>
<li>Sold leave is <strong>taxable</strong> (22% withholding); terminal-leave allowances stay tax-free.</li>
<li>You can <strong>combine</strong>: take terminal leave and sell whatever you can't burn before your separation date.</li>
<li>Don't lose leave to <strong>use/lose</strong> each October &mdash; see <a href="/blog/how-to-read-your-les.html">how to read your LES</a>.</li>
</ul>
{cta("Know your basic pay — it sets exactly what each leave day is worth.", "/")}
'''
write("selling-military-leave-terminal-leave.html",
      "Selling Military Leave vs Terminal Leave: What 30 Days Is Worth",
      f"Selling leave pays 1 day of basic pay per day (60-day career cap) — {money(_slday*30)} for an E-5's 30 days. Why terminal leave usually wins by keeping tax-free BAH and BAS.",
      "Selling Leave", body,
      faq=[("How much is military leave worth?",f"Selling leave pays one day of basic pay per day of leave (basic pay only). For a 2026 E-5 with 6 years, 30 days is about {money(_slday*30)}, before taxes."),
           ("Is it better to sell leave or take terminal leave?","Terminal leave usually wins — you keep drawing full pay including tax-free BAH and BAS while on leave, whereas selling leave pays only the basic-pay portion."),
           ("How many days of leave can I sell?","Up to 60 days over a career (outside special wartime authorities); leave sold is taxed at the 22% supplemental rate.")],
      related=[("How to read your LES","/blog/how-to-read-your-les.html"),
               ("Military separation & severance pay","/blog/military-separation-severance-pay.html"),
               ("How much does an E-5 make in 2026?","/blog/how-much-does-an-e5-make-2026.html")],
      blurb=f"Selling leave = 1 day basic pay/day ({money(_slday*30)} for 30 days) &mdash; but terminal leave usually wins.")

# --- Paycheck troubleshooting ---
body = f'''<h1>Why Is My Military Paycheck Different This Month? 9 Common Reasons</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Your deposit looked smaller (or bigger) than usual and nothing obvious changed. Military pay shifts for
a handful of predictable reasons &mdash; here's how to diagnose it from your <a href="/blog/how-to-read-your-les.html">LES</a>.</p>
<h2>Common reasons your pay changed</h2>
<ol>
<li><strong>Mid-month vs end-of-month split.</strong> You're paid twice a month; the two halves aren't always equal,
especially the month a change takes effect. See the <a href="/blog/military-pay-dates-2026.html">2026 pay calendar</a>.</li>
<li><strong>A pay started or stopped.</strong> FSA, flight pay, sea pay, or hardship pay beginning/ending with orders is the
#1 cause &mdash; check the ENTITLEMENTS and REMARKS sections.</li>
<li><strong>Years-of-service step.</strong> Hitting your 2/3/4/6-year mark bumps basic pay (driven by your PEBD).</li>
<li><strong>Promotion (or reduction).</strong> A new rank changes both basic pay and BAH.</li>
<li><strong>BAH change.</strong> A PCS, a dependency change (marriage, new child), or moving on/off base all change BAH.</li>
<li><strong>Tax-withholding change.</strong> A new W-4, a state-of-residence change, or crossing a wage threshold.</li>
<li><strong>TSP change.</strong> Adjusting your contribution %, or hitting the annual limit (contributions stop, pay rises).</li>
<li><strong>A debt or allotment.</strong> A new allotment, a tuition-assistance recoupment, or a pay debt collection.</li>
<li><strong>Leave sold or advance pay.</strong> Selling leave, taking advance pay, or a PPM advance shows up as a one-time swing.</li>
</ol>
<h2>How to diagnose it in 60 seconds</h2>
<p>Pull this month's and last month's LES side by side and compare line by line. The difference is almost always a single
new or missing ENTITLEMENT or DEDUCTION &mdash; the <strong>REMARKS</strong> block usually explains starts, stops, and debts.
If a special pay stopped that shouldn't have, see your finance office with your orders.</p>
{cta("Compare your LES against an independent estimate of what you should be paid.", "/")}
'''
write("why-is-my-military-paycheck-different.html",
      "Why Is My Military Paycheck Different This Month? 9 Reasons",
      "Military pay changes for predictable reasons: mid/end-month split, a special pay starting or stopping, a years-of-service step, BAH change, tax or TSP changes, or a new debt/allotment. How to diagnose it.",
      "Paycheck Changed", body,
      faq=[("Why is my military paycheck smaller this month?","Most often a special pay stopped (FSA, flight, sea pay), a new deduction or debt started, a TSP/tax change, or simply the mid-month vs end-of-month split. Compare this and last month's LES line by line."),
           ("Why did my pay go up?","Common causes: a years-of-service pay step, a promotion, a BAH increase from a PCS or dependency change, or hitting your TSP annual limit so contributions stopped."),
           ("Where do I see what changed on my LES?","The ENTITLEMENTS and DEDUCTIONS lines show what's different; the REMARKS section explains starts, stops, and debts.")],
      related=[("How to read your LES","/blog/how-to-read-your-les.html"),
               ("2026 military pay dates","/blog/military-pay-dates-2026.html"),
               ("Special pays guide","/blog/military-special-pays-guide.html")],
      blurb="9 predictable reasons your deposit changed &mdash; and how to diagnose it from your LES.")

# ===================== MILITARY MONEY-MOVES BATCH =====================
# --- Roth IRA vs TSP ---
body = f'''<h1>Roth IRA vs TSP for Military: Where Should Your Money Go First?</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Service members have access to two excellent retirement accounts &mdash; the
<a href="/blog/military-tsp-explained.html">TSP</a> and a Roth IRA &mdash; and the order you fund them matters. For most
members, the winning sequence is: <strong>TSP to the match, then a Roth IRA, then back to the TSP.</strong></p>
<h2>The priority order (for most members)</h2>
<ol>
<li><strong>TSP up to 5%</strong> &mdash; capture the full BRS match first. It's an instant 100% return; never skip it.</li>
<li><strong>Roth IRA up to the annual limit</strong> &mdash; broader investment choices and easier early access to
contributions than the TSP.</li>
<li><strong>Back to the TSP</strong> &mdash; up to the elective limit ($24,500 in 2026), especially the ultra-low-cost
index funds.</li>
</ol>
<h2>How they compare</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>&nbsp;</th><th>TSP</th><th>Roth IRA</th></tr></thead><tbody>
<tr><td>2026 contribution limit</td><td>$24,500 (elective)</td><td>IRS IRA limit (separate)</td></tr>
<tr><td>Employer match</td><td>Up to 5% (BRS)</td><td>None</td></tr>
<tr><td>Investment choices</td><td>A handful of low-cost funds</td><td>Almost anything</td></tr>
<tr><td>Fees</td><td>Among the lowest anywhere</td><td>Varies by broker</td></tr>
<tr><td>Early access to contributions</td><td>Limited</td><td>Contributions withdrawable anytime</td></tr>
</tbody></table></div>
<h2>The deployed-Roth superpower</h2>
<p>In a combat zone, money you contribute to the <strong>Roth TSP</strong> goes in tax-free <em>and</em> comes out
tax-free &mdash; and combat-zone months let you exceed the normal elective limit. Deploying is the single best time to
max Roth contributions. See the <a href="/blog/combat-zone-tax-exclusion.html">combat-zone tax exclusion</a>.</p>
<p class="callout">Junior members usually favor <strong>Roth</strong> (you're in a low tax bracket now); higher earners may
split or lean Traditional. Either way, get the 5% TSP match first.</p>
{cta("Set your TSP percentage in the calculator and see the paycheck impact.", "/")}
'''
write("roth-ira-vs-tsp-military.html",
      "Roth IRA vs TSP for Military: The Right Funding Order",
      "For most service members: fund the TSP to the 5% match, then a Roth IRA, then back to the TSP ($24,500 limit in 2026). How they compare and the deployed-Roth tax superpower.",
      "Roth vs TSP", body,
      faq=[("Should I use the TSP or a Roth IRA first?","Fund the TSP up to 5% first to capture the full BRS match, then a Roth IRA for broader choices, then return to the TSP up to the $24,500 elective limit."),
           ("Can I have both a TSP and a Roth IRA?","Yes — they have separate contribution limits, so you can fund both in the same year."),
           ("Why is Roth good for junior military members?","Junior members are usually in a low tax bracket, so paying tax now (Roth) and withdrawing tax-free later is often the better deal — especially with combat-zone Roth contributions.")],
      related=[("Military TSP explained","/blog/military-tsp-explained.html"),
               ("Combat zone tax exclusion","/blog/combat-zone-tax-exclusion.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html")],
      blurb="Fund order: TSP to the 5% match &rarr; Roth IRA &rarr; back to TSP. Plus the deployed-Roth trick.")

# --- SCRA financial protections ---
body = f'''<h1>SCRA: The 6% Interest Cap and Money Protections You're Probably Not Using</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The <strong>Servicemembers Civil Relief Act (SCRA)</strong> is one of the most underused financial benefits
in the military. Its headline perk: a <strong>6% interest-rate cap</strong> on debts you took on <em>before</em> entering
active duty &mdash; and that's just the start.</p>
<h2>The 6% interest cap</h2>
<ul>
<li>Caps interest at <strong>6% APR</strong> on pre-service debts (credit cards, car loans, some student loans) for the
duration of active duty.</li>
<li>Interest above 6% is <strong>permanently forgiven</strong>, not deferred &mdash; the lender must reduce it.</li>
<li>You request it in writing with a copy of your orders; the cap applies retroactively to your active-duty start date.</li>
</ul>
<h2>The other protections</h2>
<ul>
<li><strong>Lease termination:</strong> break a housing or auto lease penalty-free on PCS or deployment orders of 90+ days.</li>
<li><strong>Foreclosure &amp; repossession protection:</strong> lenders generally need a court order to foreclose or
repossess during service.</li>
<li><strong>Default-judgment protection</strong> and the ability to <strong>stay (pause) civil proceedings.</strong></li>
<li><strong>Tax residency:</strong> the SCRA (with <a href="/blog/states-that-dont-tax-military-pay.html">MSRRA</a>) lets
you keep your home-state residency &mdash; see the <a href="/blog/military-tax-filing-guide.html">tax filing guide</a>.</li>
</ul>
<h2>Don't confuse it with the MLA</h2>
<p>The <strong>Military Lending Act (MLA)</strong> is different: it caps <em>new</em> consumer loans taken while serving at
a <strong>36% Military APR</strong>. SCRA covers <em>pre-service</em> debt at 6%; MLA covers <em>new</em> debt at 36%.
Use both.</p>
<p class="callout">Free, expert help is available at your installation's <strong>legal assistance office</strong> &mdash;
they'll send the SCRA letters for you at no cost.</p>
{cta("Free up cash flow — then put the savings toward your TSP or Roth.", "/")}
'''
write("scra-6-percent-interest-cap.html",
      "SCRA Explained: The 6% Interest Cap & Military Financial Protections",
      "The SCRA caps pre-service debt interest at 6% APR (excess is forgiven), allows penalty-free lease termination on orders, and blocks foreclosure/repossession. How to use it — and how it differs from the MLA.",
      "SCRA", body,
      faq=[("What is the SCRA 6% interest cap?","The Servicemembers Civil Relief Act caps interest at 6% APR on debts taken on before active duty; interest above 6% is permanently forgiven, not deferred. You request it in writing with your orders."),
           ("Can I break a lease under the SCRA?","Yes — you can terminate a housing or auto lease without penalty on PCS or deployment orders of 90 or more days."),
           ("What's the difference between SCRA and the MLA?","SCRA caps pre-service debt at 6%; the Military Lending Act caps new consumer loans taken while serving at a 36% Military APR.")],
      related=[("States that don't tax military pay","/blog/states-that-dont-tax-military-pay.html"),
               ("Military tax filing guide","/blog/military-tax-filing-guide.html"),
               ("Roth IRA vs TSP for military","/blog/roth-ira-vs-tsp-military.html")],
      blurb="The SCRA 6% cap forgives interest on pre-service debt &mdash; plus lease and foreclosure protections.")

# ===================== CURIOSITY-SEARCH BATCH =====================
# --- General / flag officer pay ---
body = f'''<h1>How Much Does a General Make? Flag Officer Pay (O-7 to O-10)</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">A <strong>four-star general or admiral (O-10)</strong> earns <strong>{money(BP["O-10"]["20"])}/month</strong>
in basic pay in 2026 &mdash; the maximum allowed by law. Generals and admirals hit a hard ceiling: military basic pay
can't exceed <strong>Level II of the Executive Schedule ($18,808.20/month, about $225,700/year)</strong>.</p>
<h2>2026 flag officer basic pay (monthly)</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Grade</th><th>Title (Army / Navy)</th><th>Over 20 yrs</th><th>Over 30 yrs</th></tr></thead><tbody>
<tr><td>O-7</td><td>Brigadier General / Rear Admiral (lower)</td><td>{money(BP["O-7"]["20"])}</td><td>{money(BP["O-7"]["30"])}</td></tr>
<tr><td>O-8</td><td>Major General / Rear Admiral</td><td>{money(BP["O-8"]["20"])}</td><td>{money(BP["O-8"]["30"])}</td></tr>
<tr><td>O-9</td><td>Lieutenant General / Vice Admiral</td><td>{money(BP["O-9"]["20"])}</td><td>{money(BP["O-9"]["30"])}</td></tr>
<tr><td>O-10</td><td>General / Admiral (4-star)</td><td>{money(BP["O-10"]["20"])}</td><td>{money(BP["O-10"]["30"])}</td></tr>
</tbody></table></div>
<p class="callout">Because of the Executive Schedule cap, an O-9 and an O-10 receive the <strong>same</strong> basic pay in
2026 ({money(BP["O-10"]["20"])}/month). The "raise" from three to four stars is about responsibility and retirement, not
the monthly basic-pay number.</p>
<h2>What a general's total compensation looks like</h2>
<p>On top of basic pay, generals receive tax-free <a href="/blog/2026-bah-rates-explained.html">BAH</a> and BAS, often
live in government quarters, and may receive Personal Money Allowances for senior positions. Total cash compensation for a
four-star runs roughly <strong>$235,000&ndash;$250,000+/year</strong> &mdash; substantial, but far below what equivalent
private-sector executives earn.</p>
<h2>The real payoff: the pension</h2>
<p>A general retiring at 30+ years under the legacy system can draw <strong>75% of their high-3 basic pay</strong> &mdash;
well over <strong>$160,000/year for life</strong>, plus COLA. See <a href="/blog/military-retirement-brs-vs-high3.html">how
military retirement is calculated</a>.</p>
{cta("Curious about any rank? Look up exact 2026 pay in the calculator.", deep("O-7"))}
'''
write("how-much-does-a-general-make.html",
      "How Much Does a General Make? 2026 Flag Officer Pay (O-7 to O-10)",
      f"A 4-star general or admiral (O-10) earns {money(BP['O-10']['20'])}/month in 2026 — capped at Executive Schedule Level II. Full O-7 to O-10 pay, total compensation, and the pension.",
      "General Pay", body,
      faq=[("How much does a 4-star general make?",f"In 2026, a four-star general or admiral (O-10) earns {money(BP['O-10']['20'])}/month in basic pay — the maximum allowed, capped at Executive Schedule Level II (about $225,700/year), plus tax-free allowances."),
           ("Why do O-9 and O-10 make the same pay?","Military basic pay is capped at Level II of the Executive Schedule ($18,808.20/month in 2026), and both grades hit that ceiling, so their basic pay is identical."),
           ("How much is a general's pension?","A general retiring at 30+ years under the legacy system can receive 75% of their high-3 basic pay — over $160,000/year for life, plus annual COLA.")],
      related=[("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("How much does an O-5 make in 2026?","/blog/how-much-does-an-o5-make-2026.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html")],
      blurb=f"A 4-star (O-10) earns {money(BP['O-10']['20'])}/mo &mdash; capped; O-9 and O-10 make the same.")

# --- Academy / ROTC cadet pay ---
body = f'''<h1>Military Academy &amp; ROTC Pay: What Cadets and Midshipmen Earn</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Yes &mdash; cadets and midshipmen get paid while they train to become officers, though not on the regular
pay table. <strong>Service academy</strong> students earn a monthly stipend; <strong>ROTC scholarship</strong> students
earn a smaller monthly allowance plus full tuition.</p>
<h2>Service academy pay (West Point, Annapolis, Air Force Academy, etc.)</h2>
<ul>
<li>Cadets/midshipmen receive a <strong>monthly stipend of roughly $1,200+</strong> (a percentage of O-1 basic pay), with
deductions for uniforms, books, and supplies in the early years.</li>
<li><strong>Tuition, room, and board are fully covered</strong> &mdash; the education itself is worth ~$300,000+.</li>
<li>In exchange, graduates commission as <a href="/blog/how-much-does-an-o1-make-2026.html">O-1 officers</a> with a
service obligation (typically 5 years).</li>
</ul>
<h2>ROTC pay (Army, Navy, Air Force ROTC)</h2>
<ul>
<li><strong>Monthly subsistence allowance</strong> for contracted cadets, commonly <strong>$300&ndash;$500/month</strong>,
rising by year in the program.</li>
<li><strong>Scholarships</strong> can cover full tuition plus a book stipend.</li>
<li><strong>Summer training</strong> is paid at a cadet rate.</li>
<li>Graduates commission as O-1s &mdash; or, for prior-enlisted ROTC, the higher
<a href="/blog/prior-enlisted-officer-pay.html">O-1E scale</a>.</li>
</ul>
<h2>Enlisted-to-officer programs</h2>
<p>Enlisted members selected for academy or ROTC programs may keep enlisted pay during training under certain programs &mdash;
a big financial advantage over starting from scratch. The real payoff arrives at commissioning: see
<a href="/blog/how-much-does-an-o1-make-2026.html">O-1 pay</a> and the
<a href="/blog/officer-vs-enlisted-pay-career.html">officer vs enlisted career comparison</a>.</p>
{cta("See what you'll earn the day you commission — look up O-1 pay.", deep("O-1"))}
'''
write("military-academy-rotc-cadet-pay.html",
      "Military Academy & ROTC Pay: What Cadets and Midshipmen Earn",
      "Service academy cadets earn ~$1,200+/month plus full tuition; ROTC scholarship cadets get $300–$500/month plus tuition. How cadet pay works and what you earn at commissioning.",
      "Cadet Pay", body,
      faq=[("Do you get paid at West Point or the Naval Academy?","Yes — service academy cadets and midshipmen receive a monthly stipend of roughly $1,200+ (a percentage of O-1 pay), with tuition, room, and board fully covered."),
           ("How much do ROTC cadets get paid?","Contracted ROTC cadets receive a monthly subsistence allowance of about $300–$500, rising by year in the program, often plus a full-tuition scholarship and a book stipend."),
           ("What do you earn after a military academy or ROTC?","You commission as an O-1 officer; with prior enlisted service you may qualify for the higher O-1E pay scale.")],
      related=[("How much does an O-1 make in 2026?","/blog/how-much-does-an-o1-make-2026.html"),
               ("Prior-enlisted officer pay (O-1E)","/blog/prior-enlisted-officer-pay.html"),
               ("Officer vs enlisted pay career","/blog/officer-vs-enlisted-pay-career.html")],
      blurb="Academy cadets earn ~$1,200+/mo + full tuition; ROTC $300&ndash;$500/mo &mdash; then commission as O-1.")

# --- Navy SEAL / special ops pay ---
_seb = BP["E-6"]["8"]
body = f'''<h1>How Much Does a Navy SEAL Make? Special Operations Pay Explained</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Navy SEALs &mdash; and special operators across the services &mdash; earn the <strong>same basic pay</strong>
as anyone at their rank, then <strong>stack special pays</strong> that few other jobs qualify for. The base salary isn't
unusual; the <em>extras</em> and deployment tempo are what add up.</p>
<h2>It starts with normal basic pay</h2>
<p>A SEAL who is an <a href="/blog/how-much-does-an-e6-make-2026.html">E-6 with 8 years</a> earns the standard
{money(_seb)}/month in basic pay &mdash; identical to any other E-6. Rank and years of service set the base, not the job.</p>
<h2>The special pays operators stack</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Special pay</th><th>Typical monthly amount</th></tr></thead><tbody>
<tr><td>Special Duty Assignment Pay (SDAP)</td><td>up to ~$750</td></tr>
<tr><td>Dive Pay</td><td>up to $340</td></tr>
<tr><td>Parachute (Jump) Pay / HALO</td><td>$150 / $225</td></tr>
<tr><td>Demolition (HDIP)</td><td>$150</td></tr>
<tr><td>Hostile Fire / Imminent Danger Pay (deployed)</td><td>up to $225</td></tr>
<tr><td>Family Separation Allowance (deployed)</td><td>$300</td></tr>
</tbody></table></div>
<p>Stacked, these can add <strong>$1,000&ndash;$1,800+/month</strong> on top of basic pay &mdash; and during a
<a href="/blog/deployment-pay-explained.html">combat-zone deployment</a>, much of it (plus basic pay) becomes
<a href="/blog/combat-zone-tax-exclusion.html">federally tax-free</a>.</p>
<h2>Plus bonuses</h2>
<p>SEALs and SWCC also receive sizable <strong>enlistment and reenlistment bonuses</strong> to retain the rating &mdash;
often among the largest in the Navy. Officers in special operations earn standard officer pay plus applicable special pays.</p>
<p class="callout">Bottom line: a mid-career SEAL's total compensation commonly runs well into the
<strong>six figures</strong> once allowances, special pays, deployments, and bonuses are counted &mdash; but the
<em>basic pay</em> is the same as any peer at that rank.</p>
{cta("Add SEAL special pays into the calculator's special-pay fields to see the total.", "/")}
'''
write("how-much-does-a-navy-seal-make.html",
      "How Much Does a Navy SEAL Make? Special Operations Pay (2026)",
      f"Navy SEALs earn standard basic pay for their rank ({money(_seb)}/month for an E-6) plus stacked special pays — SDAP, dive, jump, danger pay — adding $1,000–$1,800+/month, often tax-free when deployed.",
      "SEAL Pay", body,
      faq=[("How much does a Navy SEAL make?",f"A SEAL earns the same basic pay as any service member at their rank (e.g., {money(_seb)}/month for an E-6 with 8 years) plus stacked special pays — SDAP, dive, jump, and danger pay — that can add $1,000–$1,800+/month, often tax-free when deployed."),
           ("Do SEALs get paid more than regular Navy?","Their basic pay is identical for the same rank, but special duty assignment pay, dive/jump pay, deployment pays, and large reenlistment bonuses make total compensation significantly higher."),
           ("Is special operations pay tax-free?","The special pays are taxable normally, but during a combat-zone deployment most pay — basic and special — becomes federally tax-free under the combat-zone tax exclusion.")],
      related=[("Special pays guide","/blog/military-special-pays-guide.html"),
               ("Deployment pay explained","/blog/deployment-pay-explained.html"),
               ("How much does an E-6 make in 2026?","/blog/how-much-does-an-e6-make-2026.html")],
      blurb=f"SEALs earn standard rank pay + stacked special pays (+$1,000&ndash;$1,800/mo) &mdash; tax-free when deployed.")

# ===================== RETIREMENT-MECHANICS BATCH =====================
# --- BRS Continuation Pay ---
_cpb = BP["E-6"]["12"]
body = f'''<h1>BRS Continuation Pay: The Mid-Career Bonus Worth Thousands</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Under the Blended Retirement System, members hit a one-time payday around <strong>8&ndash;12 years</strong>
of service: <strong>Continuation Pay</strong>, a cash bonus in exchange for committing to a few more years. It's a
<strong>multiple of your monthly basic pay</strong> &mdash; often several thousand dollars, sometimes far more.</p>
<h2>How it works</h2>
<ul>
<li>Offered to BRS members near the <strong>12-year mark</strong> (the exact window is set by each service).</li>
<li>The payout is a <strong>multiplier &times; your monthly basic pay</strong>. The floor for active duty is
<strong>2.5&times;</strong>, but services can offer much higher multipliers for in-demand skills (sometimes up to
<strong>13&times;</strong>).</li>
<li>In exchange you agree to <strong>~4 more years</strong> of service.</li>
<li>It's <strong>taxable</strong> (22% withholding) &mdash; or tax-free if you take it in a
<a href="/blog/combat-zone-tax-exclusion.html">combat zone</a>.</li>
</ul>
<h2>What it's worth (example)</h2>
<p>An <a href="/blog/how-much-does-an-e6-make-2026.html">E-6 with 12 years</a> earns {money(_cpb)}/month in basic pay.
Continuation Pay would be at least:</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>Multiplier</th><th>Continuation Pay (lump sum)</th></tr></thead><tbody>
<tr><td>2.5&times; (active-duty floor)</td><td>{money(_cpb*2.5)}</td></tr>
<tr><td>5&times;</td><td>{money(_cpb*5)}</td></tr>
<tr><td>13&times; (high-demand max)</td><td>{money(_cpb*13)}</td></tr>
</tbody></table></div>
<h2>Should you take it?</h2>
<p>If you're staying anyway, Continuation Pay is essentially free money &mdash; and pairing it with your
<a href="/blog/military-tsp-explained.html">TSP</a> (the other half of BRS) can supercharge retirement savings. Reserve
members get a smaller multiplier. It's separate from reenlistment <a href="/blog/military-bonuses-taxes.html">bonuses</a>;
you can receive both.</p>
{cta("See your monthly basic pay — it sets your Continuation Pay amount.", "/")}
'''
write("brs-continuation-pay.html",
      "BRS Continuation Pay: The Mid-Career Bonus Explained (2026)",
      f"Continuation Pay is a BRS bonus at ~12 years: 2.5x to 13x your monthly basic pay for ~4 more years. An E-6 gets at least {money(_cpb*2.5)}. How it works and whether to take it.",
      "Continuation Pay", body,
      faq=[("What is BRS Continuation Pay?","A one-time cash bonus for Blended Retirement System members around 12 years of service, paid as a multiplier (2.5x active-duty floor, up to ~13x) of monthly basic pay in exchange for about 4 more years."),
           ("How much is Continuation Pay?",f"At least 2.5x your monthly basic pay on active duty — about {money(_cpb*2.5)} for an E-6 with 12 years — and much more for high-demand skills."),
           ("Is Continuation Pay taxable?","Yes, at the 22% supplemental rate — unless you elect to receive it in a combat zone, where it's tax-free.")],
      related=[("Military TSP explained","/blog/military-tsp-explained.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("Military bonuses & taxes","/blog/military-bonuses-taxes.html")],
      blurb=f"A BRS bonus at ~12 yrs: 2.5x&ndash;13x monthly basic pay (&ge;{money(_cpb*2.5)} for an E-6).")

# --- TSP funds explained ---
body = f'''<h1>TSP Funds Explained: G, F, C, S, I and the Lifecycle (L) Funds</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The <a href="/blog/military-tsp-explained.html">Thrift Savings Plan</a> offers a handful of ultra-low-cost
funds. Knowing what each one holds &mdash; and how the automatic <strong>Lifecycle (L) funds</strong> mix them &mdash;
is most of what you need to invest well.</p>
<h2>The five core funds</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Fund</th><th>What it holds</th><th>Risk</th></tr></thead><tbody>
<tr><td><strong>G Fund</strong></td><td>Government securities &mdash; never loses value</td><td>Lowest (but lowest growth)</td></tr>
<tr><td><strong>F Fund</strong></td><td>U.S. bond market index</td><td>Low&ndash;moderate</td></tr>
<tr><td><strong>C Fund</strong></td><td>S&amp;P 500 (large U.S. companies)</td><td>Higher / strong long-term growth</td></tr>
<tr><td><strong>S Fund</strong></td><td>Small & mid-cap U.S. stocks</td><td>Higher</td></tr>
<tr><td><strong>I Fund</strong></td><td>International developed-market stocks</td><td>Higher</td></tr>
</tbody></table></div>
<h2>The Lifecycle (L) funds: set-and-forget</h2>
<p>An <strong>L Fund</strong> automatically blends the five core funds based on a target retirement date (e.g., L 2055),
holding more stocks when you're young and shifting toward G/F as you approach the date. For most members, picking the
L Fund closest to when you'll need the money is a perfectly good one-decision strategy.</p>
<h2>The classic young-member mistake</h2>
<p class="callout">New members are <strong>auto-enrolled in an age-appropriate L Fund</strong> now &mdash; good. But for years
the default was the <strong>G Fund</strong>, where decades of would-be stock growth were lost to a fund that barely beats
inflation. If you're young and your money is sitting in G, you may be leaving a fortune on the table. Review your
allocation.</p>
<h2>Why TSP fees matter</h2>
<p>TSP expense ratios are among the lowest of any retirement plan anywhere &mdash; a fraction of typical mutual-fund fees.
Over a career, that fee gap alone can be worth tens of thousands of dollars. Combine the low fees with the
<a href="/blog/military-tsp-explained.html">5% BRS match</a> and a stock-heavy allocation when young, and the TSP is a
wealth-building machine.</p>
{cta("Set your TSP percentage in the calculator and watch your take-home update.", "/")}
'''
write("tsp-funds-explained.html",
      "TSP Funds Explained: G, F, C, S, I & Lifecycle (L) Funds",
      "What each TSP fund holds: G (government, never loses), F (bonds), C (S&P 500), S (small-cap), I (international), and the automatic Lifecycle L funds. Plus the young-member G-Fund mistake.",
      "TSP Funds", body,
      faq=[("What are the TSP funds?","Five core funds — G (government securities), F (bonds), C (S&P 500), S (small/mid-cap stocks), I (international stocks) — plus Lifecycle (L) funds that automatically blend them by target date."),
           ("Which TSP fund is best?","For long-term growth, stock funds (C, S, I) historically outperform; many members simply pick the Lifecycle (L) fund matching their retirement date. The G Fund is safe but barely beats inflation."),
           ("What's the TSP G Fund mistake?","Leaving money in the low-growth G Fund for decades when young — missing out on stock-market growth. New members are now auto-enrolled in an age-appropriate L Fund instead.")],
      related=[("Military TSP explained","/blog/military-tsp-explained.html"),
               ("Roth IRA vs TSP for military","/blog/roth-ira-vs-tsp-military.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html")],
      blurb="G/F/C/S/I and the Lifecycle funds &mdash; what each holds and the young-member G-Fund trap.")

# --- 2025 vs 2026 pay ---
def _d25(g,c): return BP[g][c]/1.038
body = f'''<h1>2025 vs 2026 Military Pay: What Actually Changed</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">2026 brought a <strong>3.8% basic pay raise</strong>, a 2.4% BAS bump, and a ~4.2% average BAH increase.
Here's exactly what changed from 2025 &mdash; and what it means for your paycheck.</p>
<h2>Basic pay: +3.8% (examples)</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Rank (years)</th><th>2025 basic pay</th><th>2026 basic pay</th><th>Monthly increase</th></tr></thead><tbody>
<tr><td>E-4 (over 4)</td><td>{money(_d25("E-4","4"))}</td><td>{money(BP["E-4"]["4"])}</td><td>+{money(BP["E-4"]["4"]-_d25("E-4","4"))}</td></tr>
<tr><td>E-5 (over 6)</td><td>{money(_d25("E-5","6"))}</td><td>{money(BP["E-5"]["6"])}</td><td>+{money(BP["E-5"]["6"]-_d25("E-5","6"))}</td></tr>
<tr><td>E-7 (over 12)</td><td>{money(_d25("E-7","12"))}</td><td>{money(BP["E-7"]["12"])}</td><td>+{money(BP["E-7"]["12"]-_d25("E-7","12"))}</td></tr>
<tr><td>O-3 (over 6)</td><td>{money(_d25("O-3","6"))}</td><td>{money(BP["O-3"]["6"])}</td><td>+{money(BP["O-3"]["6"]-_d25("O-3","6"))}</td></tr>
</tbody></table></div>
<h2>Allowances also changed</h2>
<ul>
<li><strong>BAS +2.4%:</strong> enlisted rose to <strong>$476.95/month</strong> and officers to <strong>$328.48</strong>.</li>
<li><strong>BAH +4.2% on average:</strong> your specific change depends on local rents &mdash; some areas rose much more,
others less. Look yours up in the <a href="/bah/">BAH rates by location</a> pages.</li>
<li><strong>Still 95% cost coverage:</strong> BAH continues to leave a small out-of-pocket share &mdash; see
<a href="/blog/bah-reform-95-to-100.html">BAH reform</a>.</li>
</ul>
<h2>What's next: the 2027 raise</h2>
<p>2026's 3.8% was an across-the-board raise. The proposed <a href="/blog/2027-military-pay-raise-tracker.html">2027 raise
is tiered</a> &mdash; 7% for E-5 and below, 6% for E-6&ndash;O-3, 5% for O-4+ &mdash; pending the FY2027 NDAA. Track it on
our 2027 page.</p>
{cta("See your 2026 pay with the current rates — basic, BAH, BAS and take-home.", "/")}
'''
write("2025-vs-2026-military-pay.html",
      "2025 vs 2026 Military Pay: What Changed (Raise, BAH, BAS)",
      "2026 brought a 3.8% basic pay raise, BAS +2.4% ($476.95/$328.48), and BAH +4.2% on average. See the 2025-to-2026 increase by rank and what's coming in 2027.",
      "2025 vs 2026", body,
      faq=[("How much did military pay go up from 2025 to 2026?","Basic pay rose 3.8%, BAS rose 2.4% (to $476.95 enlisted / $328.48 officer), and BAH rose about 4.2% on average — though BAH varies a lot by location."),
           ("What was the 2026 military pay raise?","A 3.8% across-the-board increase to basic pay, effective January 1, 2026."),
           ("Is the 2027 raise bigger?","The proposal is tiered and larger for junior troops: 7% for E-5 and below, 6% for E-6 to O-3, and 5% for O-4 and above — not yet law.")],
      related=[("2026 military pay raise (3.8%)","/blog/2026-military-pay-raise.html"),
               ("2027 pay raise tracker","/blog/2027-military-pay-raise-tracker.html"),
               ("Military pay raise history","/blog/military-pay-raise-history.html")],
      blurb="2026 vs 2025: +3.8% basic, +2.4% BAS, +4.2% BAH &mdash; the increase by rank.")

# ===================== RETIREMENT-PROTECTION / LEGAL BATCH =====================
# --- Survivor Benefit Plan (SBP) ---
body = f'''<h1>Survivor Benefit Plan (SBP): How It Protects Your Pension After Death</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Military retired pay <strong>stops when you die</strong> &mdash; unless you elect the
<strong>Survivor Benefit Plan</strong>. SBP turns your pension into a lifetime annuity for your spouse or children,
paying up to <strong>55% of your retired pay</strong> for the rest of their life.</p>
<h2>How SBP works</h2>
<ul>
<li>At retirement, you elect SBP coverage based on a chosen "base amount" (up to your full retired pay).</li>
<li>You pay a monthly <strong>premium of 6.5% of the covered base amount</strong>, deducted from retired pay (pre-tax).</li>
<li>If you die, your beneficiary receives <strong>55% of the base amount</strong> as a monthly annuity &mdash; with COLA
adjustments &mdash; for life.</li>
</ul>
<h2>Why it's hard to beat with private insurance</h2>
<p class="callout">SBP is <strong>inflation-protected, government-backed, and can't be outlived</strong>. Replicating a
COLA-adjusted lifetime annuity with private life insurance is usually far more expensive &mdash; which is why financial
counselors generally favor SBP for a spouse who'd depend on the pension.</p>
<h2>Key decision points</h2>
<ul>
<li><strong>It's a one-time, mostly irrevocable election</strong> at retirement &mdash; declining requires spouse consent.</li>
<li>Coverage can include a <strong>spouse, children, or former spouse</strong> (court-ordered in some
<a href="/blog/military-divorce-retirement-pay.html">divorces</a>).</li>
<li>SBP and <a href="/blog/2026-va-disability-rates.html">VA Dependency &amp; Indemnity Compensation (DIC)</a> interaction
changed in recent years &mdash; the old offset was phased out.</li>
</ul>
<p>SBP applies to the <a href="/blog/military-retirement-brs-vs-high3.html">retired pay</a> you earn at 20+ years &mdash;
estimate that pension first, then weigh the 6.5% premium against the protection it buys your family.</p>
{cta("Estimate your career pay and pension, then plan SBP around it.", "/")}
'''
write("survivor-benefit-plan-sbp.html",
      "Survivor Benefit Plan (SBP): Protect Your Military Pension After Death",
      "SBP turns military retired pay into a lifetime, COLA-adjusted annuity paying survivors up to 55% of retired pay for a 6.5% premium. How it works and why it's hard to beat with private insurance.",
      "SBP", body,
      faq=[("What is the Survivor Benefit Plan?","SBP is an elected annuity that continues part of your military retired pay to a survivor after you die — up to 55% of your chosen base amount, adjusted for inflation, for their lifetime."),
           ("How much does SBP cost?","The premium is 6.5% of the covered base amount, deducted pre-tax from retired pay."),
           ("Is SBP worth it?","For a spouse who would depend on the pension, usually yes — it's inflation-protected, government-backed, and can't be outlived, which is expensive to replicate with private insurance.")],
      related=[("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("CRDP & CRSC: concurrent receipt","/blog/crdp-crsc-concurrent-receipt.html"),
               ("Military divorce & retirement pay","/blog/military-divorce-retirement-pay.html")],
      blurb="SBP continues up to 55% of your pension to survivors for life (6.5% premium).")

# --- CRDP / CRSC concurrent receipt ---
body = f'''<h1>CRDP &amp; CRSC: Getting Both Military Retirement and VA Disability</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">For decades, military retirees had to <strong>waive part of their retired pay</strong> to receive
<a href="/blog/2026-va-disability-rates.html">VA disability compensation</a> &mdash; a dollar-for-dollar offset. Two
programs, <strong>CRDP</strong> and <strong>CRSC</strong>, now let many retirees receive <strong>both</strong>, adding
hundreds to thousands of dollars a month.</p>
<h2>The old problem: the VA offset</h2>
<p>Retired pay is taxable; VA disability is tax-free. Historically, every dollar of VA compensation reduced retired pay by
a dollar &mdash; you didn't truly receive both. CRDP and CRSC restore the offset amount.</p>
<h2>CRDP &mdash; Concurrent Retirement and Disability Pay</h2>
<ul>
<li>For retirees with <strong>20+ years</strong> (longevity retirement) and a VA rating of <strong>50% or higher</strong>.</li>
<li>Restores the offset so you receive <strong>full retired pay + full VA disability</strong>.</li>
<li><strong>Automatic</strong> &mdash; no application needed; it's taxable (the restored retired-pay portion).</li>
</ul>
<h2>CRSC &mdash; Combat-Related Special Compensation</h2>
<ul>
<li>For disabilities that are <strong>combat-related</strong> (combat, training, hazardous duty, instrumentality of war).</li>
<li>Available at <strong>any rating</strong> (10%+) and can apply to medical retirees, not just 20-year retirees.</li>
<li><strong>Tax-free</strong>, but you must <strong>apply</strong> through your branch.</li>
</ul>
<p class="callout">You can't receive CRDP and CRSC at the same time &mdash; but you can choose the one that pays more and
switch during the annual open season. For combat-related disabilities, CRSC is often the tax-free winner.</p>
<p>Both build on your <a href="/blog/military-retirement-brs-vs-high3.html">retired pay</a> and
<a href="/blog/2026-va-disability-rates.html">VA rating</a> &mdash; estimate those first.</p>
{cta("Estimate your retired pay base — the foundation for CRDP and CRSC.", "/")}
'''
write("crdp-crsc-concurrent-receipt.html",
      "CRDP & CRSC: Get Both Military Retirement and VA Disability",
      "CRDP and CRSC restore the VA offset so retirees can receive both retired pay and VA disability. CRDP (20 years, 50%+, automatic, taxable) vs CRSC (combat-related, any rating, tax-free, apply).",
      "CRDP/CRSC", body,
      faq=[("Can you get military retirement and VA disability at the same time?","Yes, through CRDP or CRSC, which restore the old dollar-for-dollar offset. CRDP is for 20-year retirees rated 50%+ (automatic, taxable); CRSC is for combat-related disabilities at any rating (tax-free, must apply)."),
           ("What is the difference between CRDP and CRSC?","CRDP restores retired pay for 20-year retirees with a 50%+ VA rating and is taxable; CRSC is tax-free but only for combat-related disabilities and requires an application. You can't receive both at once."),
           ("Is CRSC tax-free?","Yes — Combat-Related Special Compensation is tax-free, unlike CRDP.")],
      related=[("2026 VA disability rates","/blog/2026-va-disability-rates.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("Survivor Benefit Plan (SBP)","/blog/survivor-benefit-plan-sbp.html")],
      blurb="CRDP & CRSC let retirees collect retired pay + VA disability &mdash; one taxable, one tax-free.")

# --- Military divorce & pension ---
body = f'''<h1>Military Divorce &amp; Retirement Pay: The 10/10 Rule and USFSPA Explained</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">A military pension is often the largest marital asset, and dividing it in divorce follows special federal
rules. The <strong>Uniformed Services Former Spouses' Protection Act (USFSPA)</strong> &mdash; and the famous
<strong>"10/10 rule"</strong> &mdash; govern how it works.</p>
<h2>What USFSPA does</h2>
<p>USFSPA lets state courts treat <strong>"disposable retired pay" as marital property</strong> that can be divided in a
divorce. It does <em>not</em> automatically award a share &mdash; a court order does &mdash; but it permits the division.</p>
<h2>The 10/10 rule (a payment rule, not an eligibility rule)</h2>
<p class="callout">If the marriage overlapped with <strong>at least 10 years of creditable service</strong>, DFAS will pay
the former spouse's share <strong>directly</strong>. With less than 10/10 overlap, the former spouse can still be awarded
a share &mdash; but the <strong>retiree must pay it themselves</strong>; DFAS won't send it directly. The 10/10 rule is
about <em>who cuts the check</em>, not whether a share exists.</p>
<h2>Other rules people get wrong</h2>
<ul>
<li><strong>The "frozen benefit" rule:</strong> for divorces after December 2016, the former spouse's share is generally
based on the member's rank and service <em>at the time of divorce</em>, not at retirement.</li>
<li><strong>VA disability can't be divided:</strong> <a href="/blog/2026-va-disability-rates.html">VA compensation</a> and
CRSC are not divisible as marital property; waiving retired pay for VA can reduce the divisible amount.</li>
<li><strong>SBP for a former spouse:</strong> a court can order
<a href="/blog/survivor-benefit-plan-sbp.html">SBP</a> coverage for an ex-spouse (former-spouse election).</li>
<li><strong>The 20/20/20 rule</strong> (20 years married, 20 years service, 20 years overlap) preserves full military
benefits &mdash; Tricare, commissary &mdash; for the former spouse.</li>
</ul>
<p><em>This is general information, not legal advice &mdash; consult a military-divorce attorney.</em></p>
{cta("Estimate the retired pay at stake — the base for any division.", "/")}
'''
write("military-divorce-retirement-pay.html",
      "Military Divorce & Retirement Pay: The 10/10 Rule and USFSPA",
      "How military pensions are divided in divorce: USFSPA lets courts split disposable retired pay; the 10/10 rule decides whether DFAS pays the ex-spouse directly. Plus the frozen-benefit and 20/20/20 rules.",
      "Military Divorce", body,
      faq=[("What is the military 10/10 rule?","If the marriage overlapped at least 10 years of creditable service, DFAS pays the former spouse's awarded share of retired pay directly. With less overlap, a share can still be awarded but the retiree must pay it — it's about who pays, not eligibility."),
           ("Can an ex-spouse get part of my military pension?","Yes — under USFSPA, a state court can divide disposable retired pay as marital property, typically based on rank and service at the time of divorce for post-2016 cases."),
           ("Can VA disability be divided in a divorce?","No — VA disability compensation and CRSC are not divisible as marital property.")],
      related=[("Survivor Benefit Plan (SBP)","/blog/survivor-benefit-plan-sbp.html"),
               ("Military retirement: BRS vs High-3","/blog/military-retirement-brs-vs-high3.html"),
               ("2026 VA disability rates","/blog/2026-va-disability-rates.html")],
      blurb="Dividing a military pension: USFSPA + the 10/10 rule (who DFAS pays) explained.")

# ===================== UNCOVERED PAY COMPONENTS BATCH =====================
# --- Per diem / TDY ---
body = f'''<h1>Military Per Diem &amp; TDY Pay: How Travel Reimbursement Works</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">When you travel on temporary duty (TDY), the government covers your costs through <strong>per diem</strong> &mdash;
a daily allowance for <strong>lodging</strong> plus <strong>meals and incidental expenses (M&amp;IE)</strong>. Manage it
well and per diem can even leave a little in your pocket.</p>
<h2>The two parts of per diem</h2>
<ul>
<li><strong>Lodging:</strong> reimbursed for your <em>actual</em> cost up to the location's nightly cap. Spend less than the
cap and you only get what you spent (lodging isn't profit).</li>
<li><strong>M&amp;IE:</strong> a <strong>flat daily amount</strong> for the location &mdash; you keep it whether or not you
spend it all. This is where careful travelers come out ahead.</li>
</ul>
<h2>How the rates work</h2>
<ul>
<li>Rates are set by <strong>location</strong> (DTMO for OCONUS, GSA for CONUS) &mdash; high-cost cities pay more. The
standard CONUS rate covers most U.S. locations, with hundreds of higher-cost exceptions.</li>
<li><strong>Travel days</strong> (first and last) pay <strong>75% of the M&amp;IE</strong> rate.</li>
<li><strong>Government-provided meals</strong> reduce your M&amp;IE (the "proportional meal rate") &mdash; e.g., staying
where meals are furnished.</li>
<li>A <strong>government travel card (GTCC)</strong> is normally used for official travel expenses; file a voucher in DTS
to get reimbursed.</li>
</ul>
<h2>How it relates to your regular pay</h2>
<p class="callout">Per diem is <strong>reimbursement, not income</strong> &mdash; it's separate from basic pay, BAH, and BAS,
and it's <strong>not taxed</strong> when within the rates. You keep drawing your normal
<a href="/blog/how-much-does-an-e5-make-2026.html">pay and allowances</a> while TDY. Long TDYs (30+ days) can reduce the
flat per diem to a "long-term" rate.</p>
<h2>For Reserve &amp; Guard</h2>
<p>Annual Training and orders away from home often include per diem too &mdash; on top of your
<a href="/blog/reserve-drill-pay-explained.html">drill/AT pay</a>.</p>
{cta("Per diem is on top of your regular pay — estimate your base pay in the calculator.", "/")}
'''
write("military-per-diem-tdy-pay.html",
      "Military Per Diem & TDY Pay: How Travel Reimbursement Works",
      "TDY per diem covers lodging (actual cost up to a cap) plus a flat daily M&IE you keep — travel days pay 75%. Rates by location, government meals, the travel card, and how it's tax-free.",
      "Per Diem", body,
      faq=[("How does military per diem work?","Per diem reimburses lodging (your actual cost up to the location's nightly cap) plus a flat daily meals & incidental (M&IE) allowance you keep regardless of what you spend. Travel days pay 75% of M&IE."),
           ("Is per diem taxable?","No — per diem is reimbursement within the set rates, not income, so it isn't taxed and is separate from basic pay, BAH, and BAS."),
           ("Do you keep leftover per diem?","You keep leftover M&IE (the flat meals allowance), but lodging only reimburses what you actually spent up to the cap.")],
      related=[("Special pays guide","/blog/military-special-pays-guide.html"),
               ("Dislocation Allowance (DLA) 2026","/blog/dislocation-allowance-dla-2026.html"),
               ("How to read your LES","/blog/how-to-read-your-les.html")],
      blurb="TDY per diem: lodging up to a cap + a flat M&amp;IE you keep &mdash; tax-free, on top of normal pay.")

# --- Clothing allowance ---
body = f'''<h1>Military Clothing Allowance: Uniform Money Explained</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Enlisted members get money to maintain their uniforms &mdash; a yearly <strong>Clothing Replacement
Allowance</strong> &mdash; while officers receive a one-time uniform allowance. It's small compared to basic pay, but it's
real money that shows up on the LES.</p>
<h2>Enlisted: annual Clothing Replacement Allowance</h2>
<ul>
<li>Paid <strong>once a year</strong> (on your enlistment anniversary month) to replace worn-out uniform items.</li>
<li>The amount is set <strong>by service and gender</strong> and rises after the first three years (the "standard" rate);
it commonly runs in the <strong>$400&ndash;$650/year</strong> range, adjusted annually.</li>
<li>A higher initial issue happens at <a href="/blog/basic-training-pay-2026.html">basic training</a> (often provided
in-kind rather than cash).</li>
</ul>
<h2>Officers: one-time uniform allowance</h2>
<ul>
<li>Officers receive a <strong>one-time Uniform Allowance (around $400)</strong> upon first reporting to active duty &mdash;
officers buy their own uniforms and don't get the recurring enlisted allowance.</li>
<li>An <strong>additional active-duty uniform allowance</strong> may be paid to reserve/guard officers called to extended
active duty under certain conditions.</li>
</ul>
<h2>Special clothing allowances</h2>
<p>Members with unusual uniform requirements (civilian-clothes billets, special-duty assignments, certain overseas tours)
may receive <strong>Special or Civilian Clothing Allowances</strong> on top of the standard amount.</p>
<p class="callout">Clothing allowance is <strong>tax-free</strong> and separate from your
<a href="/blog/2026-military-pay-chart.html">basic pay</a> and <a href="/blog/2026-bah-rates-explained.html">allowances</a>.
It's easy to miss &mdash; check your <a href="/blog/how-to-read-your-les.html">LES</a> around your anniversary month.</p>
{cta("Clothing allowance is a small extra — see your full pay picture in the calculator.", "/")}
'''
write("military-clothing-allowance.html",
      "Military Clothing Allowance: Uniform Money Explained (2026)",
      "Enlisted members get an annual Clothing Replacement Allowance (about $400–$650/year, by service and gender); officers get a one-time ~$400 uniform allowance. How it works and where to find it on your LES.",
      "Clothing Allowance", body,
      faq=[("What is the military clothing allowance?","An annual Clothing Replacement Allowance for enlisted members to replace worn uniforms — commonly $400–$650/year by service and gender — plus a one-time ~$400 uniform allowance for officers."),
           ("Do officers get a clothing allowance?","Officers receive a one-time uniform allowance (about $400) when they first report to active duty, but not the recurring annual enlisted allowance."),
           ("Is the clothing allowance taxable?","No — the military clothing allowance is tax-free and separate from basic pay and other allowances.")],
      related=[("2026 military pay chart","/blog/2026-military-pay-chart.html"),
               ("How to read your LES","/blog/how-to-read-your-les.html"),
               ("Basic training pay 2026","/blog/basic-training-pay-2026.html")],
      blurb="Enlisted get ~$400&ndash;$650/yr to replace uniforms; officers a one-time ~$400 &mdash; tax-free.")

# ===================== HOME BUYING / VA LOAN BATCH =====================
_HB_REL = [("VA home loan & BAH","/blog/va-home-loan-and-bah.html"),
           ("VA loan vs conventional vs FHA","/blog/va-loan-vs-conventional-fha.html"),
           ("First-time military homebuyer guide","/blog/first-time-military-homebuyer-va-loan.html")]

# --- 1. First-time military homebuyer / VA loan step by step ---
body = f'''<h1>First-Time Military Homebuyer Guide: Buying with a VA Loan</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The <strong>VA home loan</strong> makes service members some of the most powerful buyers in any market:
<strong>$0 down, no PMI</strong>, competitive rates, and lenders count your tax-free
<a href="/blog/2026-bah-rates-explained.html">BAH</a> as income. Here's the whole process, start to finish.</p>
<h2>Step 1 &mdash; Confirm eligibility (COE)</h2>
<p>You qualify with enough active-duty, Guard, or Reserve service. Your lender can pull your
<strong>Certificate of Eligibility (COE)</strong> instantly online, or you can request it through VA.gov.</p>
<h2>Step 2 &mdash; Get pre-approved</h2>
<p>A lender reviews income, credit, and debts. Crucially, they count <strong>BAH and BAS as qualifying income</strong> &mdash;
and because they're tax-free, that income stretches further. Use a <a href="/">pay calculator</a> to know your exact BAH.</p>
<h2>Step 3 &mdash; Find a VA-savvy agent</h2>
<p>Pick a real-estate agent who closes VA loans regularly. They'll write offers that account for the VA appraisal and help
you negotiate seller concessions (the seller can pay closing costs).</p>
<h2>Step 4 &mdash; Make an offer &amp; VA appraisal</h2>
<p>Once under contract, the VA orders an appraisal that also checks the home meets minimum property requirements (safe,
sound, sanitary). This protects you from buying a money pit.</p>
<h2>Step 5 &mdash; Close</h2>
<p>You'll pay closing costs (often partly seller-paid) and the one-time
<a href="/blog/va-loan-funding-fee.html">VA funding fee</a> (financed into the loan, and waived if you have a
<a href="/blog/2026-va-disability-rates.html">service-connected disability rating</a>). No down payment required.</p>
<h2>Smart moves for military buyers</h2>
<ul>
<li><strong>Think about your next PCS</strong> &mdash; see <a href="/blog/buy-or-rent-duty-station.html">buy vs rent</a>.</li>
<li><strong>House-hack:</strong> buy a 2&ndash;4 unit, live in one, rent the rest &mdash; BAH plus rent can cover the mortgage.</li>
<li><strong>Reuse the benefit:</strong> the VA loan isn't one-and-done.</li>
</ul>
{cta("Know your BAH first — it's the income lenders use. Look it up by ZIP.", "/")}
'''
write("first-time-military-homebuyer-va-loan.html",
      "First-Time Military Homebuyer Guide: Buying with a VA Loan (2026)",
      "Buy your first home with a VA loan: $0 down, no PMI, BAH counts as income. The full step-by-step — COE, pre-approval, VA appraisal, funding fee, and closing.",
      "Homebuyer Guide", body,
      faq=[("How do I buy a house with a VA loan?","Get your Certificate of Eligibility, get pre-approved (lenders count tax-free BAH/BAS as income), find a VA-savvy agent, make an offer, complete the VA appraisal, and close — with $0 down and no PMI."),
           ("Do you need a down payment for a VA loan?","No — most VA purchase loans require no down payment and charge no private mortgage insurance."),
           ("What is a COE for a VA loan?","The Certificate of Eligibility proves you qualify for the VA loan benefit; lenders can usually pull it instantly, or you can request it on VA.gov.")],
      related=_HB_REL, blurb="VA loan step-by-step: COE, pre-approval (BAH counts), appraisal, funding fee, $0-down close.")

# --- 2. VA loan funding fee ---
body = f'''<h1>VA Loan Funding Fee (2026): Rates, Who's Exempt &amp; How to Avoid It</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The VA loan has no PMI, but it does charge a one-time <strong>funding fee</strong> that keeps the program
running. It's a percentage of the loan, <strong>financed into the mortgage</strong> &mdash; and many veterans pay
<strong>$0</strong> because they're exempt.</p>
<h2>2026 funding fee rates (purchase loans)</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Down payment</th><th>First use</th><th>Subsequent use</th></tr></thead><tbody>
<tr><td>Less than 5%</td><td>2.15%</td><td>3.3%</td></tr>
<tr><td>5% to 9.99%</td><td>1.5%</td><td>1.5%</td></tr>
<tr><td>10% or more</td><td>1.25%</td><td>1.25%</td></tr>
</tbody></table></div>
<p>On a $300,000 loan with nothing down, a first-use fee of 2.15% is <strong>$6,450</strong> &mdash; usually rolled into
the loan, not paid in cash.</p>
<h2>Who is exempt (pays $0)</h2>
<ul>
<li>Veterans receiving <a href="/blog/2026-va-disability-rates.html">VA disability compensation</a> (even a 10% rating).</li>
<li>Veterans eligible for disability comp but receiving retired pay instead.</li>
<li><strong>Purple Heart</strong> recipients on active duty.</li>
<li>Surviving spouses of members who died in service or from a service-connected disability.</li>
</ul>
<h2>How to lower or avoid it</h2>
<ul>
<li><strong>Get a disability rating:</strong> if you're owed one, it can waive the fee entirely &mdash; worth thousands.</li>
<li><strong>Put money down:</strong> 5%+ drops the rate, and it also avoids the higher subsequent-use rate.</li>
<li>The fee is the <em>only</em> ongoing-cost difference vs a no-PMI conventional loan &mdash; and one-time, unlike PMI.</li>
</ul>
{cta("Plan your purchase — start by checking your BAH and pay by ZIP.", "/")}
'''
write("va-loan-funding-fee.html",
      "VA Loan Funding Fee 2026: Rates, Exemptions & How to Avoid It",
      "The VA funding fee is 2.15% first use / 3.3% subsequent with $0 down (lower with a down payment). Veterans with a disability rating, Purple Heart recipients, and surviving spouses pay $0.",
      "VA Funding Fee", body,
      faq=[("How much is the VA funding fee in 2026?","2.15% of the loan for first use with less than 5% down (3.3% for subsequent use); it drops to 1.5% with 5% down and 1.25% with 10% down. It's usually financed into the loan."),
           ("Who is exempt from the VA funding fee?","Veterans receiving VA disability compensation, those eligible for it, Purple Heart recipients on active duty, and surviving spouses — they pay $0."),
           ("Can I avoid the VA funding fee?","Yes — a service-connected disability rating waives it entirely, and a down payment of 5% or more lowers the rate.")],
      related=_HB_REL, blurb="2.15% first use ($0 down), waived for disability/Purple Heart/surviving spouses.")

# --- 3. VA vs conventional vs FHA ---
body = f'''<h1>VA Loan vs Conventional vs FHA: Which Should Military Buyers Use?</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">If you're eligible, the <strong>VA loan usually wins</strong> &mdash; but not always. Here's an honest
comparison of the three main mortgage types for service members.</p>
<div class="tablewrap"><table class="pay"><thead><tr><th>&nbsp;</th><th>VA Loan</th><th>Conventional</th><th>FHA</th></tr></thead><tbody>
<tr><td>Down payment</td><td><strong>$0</strong></td><td>3&ndash;20%</td><td>3.5%</td></tr>
<tr><td>Mortgage insurance</td><td><strong>None</strong></td><td>PMI under 20% down</td><td>MIP (often for life of loan)</td></tr>
<tr><td>Upfront fee</td><td>Funding fee (financed, often waived)</td><td>None</td><td>1.75% upfront MIP</td></tr>
<tr><td>Credit flexibility</td><td>High (residual-income test)</td><td>Strictest</td><td>High</td></tr>
<tr><td>Who can use it</td><td>Eligible service members/vets</td><td>Anyone</td><td>Anyone</td></tr>
</tbody></table></div>
<h2>When the VA loan wins (most of the time)</h2>
<p>No down payment and no monthly mortgage insurance is hard to beat &mdash; the
<a href="/blog/va-loan-funding-fee.html">funding fee</a> is one-time (and $0 if you have a disability rating). Over a few
years, skipping PMI alone saves thousands.</p>
<h2>When conventional or FHA might fit</h2>
<ul>
<li><strong>Conventional:</strong> if you have 20% down (no PMI, no funding fee) or are buying a non-primary residence the
VA loan doesn't allow.</li>
<li><strong>FHA:</strong> rarely better than VA for those eligible, but an option if you've exhausted VA entitlement.</li>
<li><strong>Multiple properties:</strong> you can pair a VA loan on your home with conventional financing on a rental.</li>
</ul>
<p class="callout">Bottom line: if you qualify for VA and it's your primary home, start there. Lenders count your tax-free
<a href="/blog/2026-bah-rates-explained.html">BAH</a> as income on all three.</p>
{cta("Check the BAH lenders will use — look it up by ZIP.", "/")}
'''
write("va-loan-vs-conventional-fha.html",
      "VA Loan vs Conventional vs FHA: Best Mortgage for Military",
      "VA loan: $0 down, no PMI, one-time funding fee (often waived). Conventional needs more down or PMI; FHA has lifetime MIP. An honest comparison for military buyers.",
      "VA vs Conventional", body,
      faq=[("Is a VA loan better than conventional or FHA?","For eligible buyers on a primary home, usually yes — $0 down and no monthly mortgage insurance beat conventional (PMI under 20% down) and FHA (lifetime MIP). The VA funding fee is one-time and often waived."),
           ("When should military use a conventional loan?","If you have 20% down (avoiding PMI and the funding fee) or are buying a property the VA loan doesn't allow, such as a pure investment property."),
           ("Do all three count BAH as income?","Yes — lenders count tax-free BAH and BAS as qualifying income on VA, conventional, and FHA loans.")],
      related=_HB_REL, blurb="VA usually wins ($0 down, no PMI) &mdash; when conventional or FHA make sense instead.")

# --- 4. Buy or rent at duty station ---
_brbah = bah_rate("CA038","E05","with")
body = f'''<h1>Buy or Rent at Your Next Duty Station? The PCS Decision</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">Every PCS raises the question: rent, or use that $0-down <a href="/blog/va-home-loan-and-bah.html">VA loan</a>
to buy? The military twist is that you'll probably <strong>move again in 2&ndash;4 years</strong> &mdash; which changes the
math a lot.</p>
<h2>The case for buying</h2>
<ul>
<li><strong>$0 down</strong> removes the biggest barrier; your <a href="/bah/">BAH</a> can cover the mortgage.</li>
<li><strong>Build equity</strong> instead of paying a landlord; potential appreciation.</li>
<li><strong>House-hack:</strong> a multi-unit lets BAH + rent cover the note.</li>
<li><strong>Keep it as a rental</strong> when you PCS &mdash; BAH-priced markets often rent well.</li>
</ul>
<h2>The case for renting</h2>
<ul>
<li><strong>Transaction costs:</strong> buying and selling can total <strong>8&ndash;10% of the price</strong>. On a short
tour, appreciation may not cover that &mdash; you can lose money.</li>
<li><strong>Flexibility &amp; zero maintenance</strong> &mdash; renting with BAH is simple and predictable.</li>
<li><strong>Accidental-landlord risk:</strong> managing a rental from across the country (or overseas) is real work.</li>
</ul>
<h2>A simple rule of thumb</h2>
<p class="callout">The shorter your expected tour and the hotter/pricier the market, the more renting makes sense. The longer
you'll stay (or the more confident you are it'll cash-flow as a rental), the better buying looks. With a typical 3-year tour,
many members rent unless they plan to keep the home long-term.</p>
<p>Either way, know your <a href="/blog/2026-bah-rates-explained.html">BAH</a> first &mdash; it's your housing budget and the
income lenders use. Compare on-base too: <a href="/blog/on-base-vs-off-base-housing.html">on-base vs off-base</a>.</p>
{cta("Look up your new BAH by ZIP before you rent or buy.", "/")}
'''
write("buy-or-rent-duty-station.html",
      "Buy or Rent at Your Next Duty Station? The PCS Decision",
      "Should you use your VA loan to buy, or rent at your next base? $0 down and BAH-covered mortgages favor buying, but 8–10% transaction costs on a short tour favor renting. A clear framework.",
      "Buy or Rent", body,
      faq=[("Should I buy or rent at a new duty station?","Renting often wins on a short (2–3 year) tour because buying-and-selling costs run 8–10% of the price, which appreciation may not cover. Buying favors longer stays or homes that will cash-flow as a rental after you PCS."),
           ("Can BAH cover a mortgage?","Often yes — your BAH is your housing budget, and with a $0-down VA loan it can cover a mortgage, though a mortgage also includes taxes, insurance, and maintenance."),
           ("Is it smart to keep a house as a rental after PCS?","It can be, especially in markets that rent near BAH levels — but managing a long-distance rental is real work and risk.")],
      related=[("On-base vs off-base housing","/blog/on-base-vs-off-base-housing.html"),
               ("VA home loan & BAH","/blog/va-home-loan-and-bah.html"),
               ("BAH rates by location","/bah/")],
      blurb="$0-down VA loan vs 8&ndash;10% transaction costs on a 3-year tour &mdash; a clear buy-vs-rent framework.")

# --- 5. VA loan credit score & requirements ---
body = f'''<h1>VA Loan Requirements: Credit Score, Income &amp; the Residual Income Test</h1>
<p class="meta">Updated {_D2}</p>
<p class="lead">The VA doesn't set a minimum credit score &mdash; but lenders do, and the VA adds a unique
<strong>residual income</strong> test that helps service members qualify when other loans say no.</p>
<h2>Credit score</h2>
<ul>
<li><strong>The VA has no official minimum.</strong> Most lenders set an overlay around <strong>580&ndash;620</strong>;
some go lower with strong compensating factors.</li>
<li>Better scores get better rates &mdash; but VA loans are famously forgiving compared with conventional.</li>
</ul>
<h2>Debt-to-income (DTI)</h2>
<p>Lenders look at your monthly debts vs gross income. VA is flexible &mdash; a DTI over 41% is allowed if your
<strong>residual income</strong> is strong.</p>
<h2>The residual income test (VA's secret weapon)</h2>
<p class="callout">The VA requires you to have a minimum amount of <strong>cash left over each month</strong> after the
mortgage, debts, and basic living costs &mdash; varying by family size and region. Because tax-free
<a href="/blog/2026-bah-rates-explained.html">BAH and BAS</a> count as income, military buyers usually pass comfortably.
It's a big reason VA borrowers default less despite easier credit rules.</p>
<h2>Other requirements</h2>
<ul>
<li><strong>Certificate of Eligibility</strong> (service requirement met).</li>
<li><strong>Primary residence</strong> &mdash; you must intend to live there (multi-unit OK if you occupy one unit).</li>
<li>The home must pass the <strong>VA appraisal</strong> and minimum property requirements.</li>
</ul>
<p>Counting your exact BAH helps your numbers &mdash; look it up in the <a href="/">calculator</a> before you apply.</p>
{cta("See the BAH/BAS income lenders will use — by ZIP in the calculator.", "/")}
'''
write("va-loan-credit-score-requirements.html",
      "VA Loan Requirements 2026: Credit Score, DTI & Residual Income",
      "The VA sets no minimum credit score (lenders often want 580–620), allows higher DTI, and adds a residual-income test that tax-free BAH/BAS helps military buyers pass. Full VA loan requirements.",
      "VA Requirements", body,
      faq=[("What credit score do you need for a VA loan?","The VA has no official minimum; most lenders look for about 580–620, though some go lower with strong compensating factors."),
           ("What is the VA residual income test?","A VA rule requiring a minimum amount of monthly cash left after the mortgage, debts, and living costs (by family size and region). Tax-free BAH and BAS count as income, so military buyers usually pass."),
           ("Can I use a VA loan for an investment property?","Not a pure investment property — it must be your primary residence, though a 2–4 unit is allowed if you occupy one unit.")],
      related=_HB_REL, blurb="No VA minimum score (lenders ~580&ndash;620) + the residual-income test BAH helps you pass.")

# ===================== POLICY / NEWS INTERPRETATION PAGES =====================
NEWS_DATE = "2026-06-10"

def t27(g, c, pct):
    return BP[g][c] * (1 + pct)

# --- 1. 2027 pay raise tracker (flagship news page) ---
rows27 = ""
for g, c, pct in [("E-3","2",.07),("E-4","4",.07),("E-5","4",.07),("E-5","6",.07),
                  ("E-6","8",.06),("E-7","12",.06),("O-1","2",.06),("O-3","6",.06),
                  ("O-4","10",.05),("O-5","16",.05)]:
    yos = "&lt;2" if c=="<2" else c
    rows27 += (f"<tr><td>{g} (over {yos} yrs)</td><td>{int(pct*100)}%</td>"
               f"<td>{money(BP[g][c])}</td><td>{money(t27(g,c,pct))}</td>"
               f"<td>+{money(t27(g,c,pct)-BP[g][c])}</td></tr>")
body = f'''<h1>2027 Military Pay Raise: 7% / 6% / 5% Tiered Proposal (Tracker)</h1>
<p class="meta">Updated {NEWS_DATE} &middot; Status: <strong>proposal &mdash; not yet law</strong></p>
<p class="lead">The proposed <strong>2027 military pay raise is tiered</strong>: <strong>7% for E-5 and below, 6% for
E-6 through O-3, and 5% for O-4 and above</strong>, effective January 1, 2027. The House Armed Services Committee
approved it on <strong>June 5, 2026</strong> as part of the $1.15&nbsp;trillion FY2027 National Defense Authorization
Act (NDAA) &mdash; the next step is a House floor vote expected in mid-July.</p>
<p class="callout"><strong>Status tracker:</strong> White House budget request (April 2026) &rarr; ✅ House Armed
Services Committee markup passed (June 5, 2026) &rarr; ⏳ House floor vote (expected mid-July) &rarr; ⏳ Senate version
&rarr; ⏳ Conference &amp; President's signature (typically <strong>December 2026</strong>). Numbers can still change.</p>
<h2>Who gets which raise</h2>
<ul>
<li><strong>7%</strong> &mdash; junior enlisted, <strong>E-1 through E-5</strong></li>
<li><strong>6%</strong> &mdash; <strong>E-6 through O-3</strong> (senior enlisted and company-grade officers)</li>
<li><strong>5%</strong> &mdash; <strong>O-4 and above</strong> (field-grade and flag officers)</li>
</ul>
<p>This is the second time in recent years Congress has targeted bigger raises at junior troops, and it would
comfortably beat the across-the-board <a href="/blog/2026-military-pay-raise.html">3.8% raise of 2026</a>.</p>
<h2>What the proposal would mean in dollars (monthly basic pay)</h2>
<div class="tablewrap"><table class="pay"><thead><tr><th>Rank (years)</th><th>Proposed raise</th>
<th>2026 basic pay</th><th>Est. 2027 basic pay</th><th>Monthly gain</th></tr></thead><tbody>{rows27}</tbody></table></div>
<p class="callout">Estimates apply the proposed tier to the 2026 pay table and assume the same years-of-service steps.
Final 2027 tables will be published after the NDAA is signed; exact treatment of warrant officers will be confirmed in
the final law.</p>
{cta("See your current 2026 take-home pay while the 2027 raise works through Congress.", "/")}
<h2>When will it be final?</h2>
<p>The NDAA usually becomes law in <strong>late December</strong>, with the raise taking effect <strong>January 1,
2027</strong> and appearing on the mid-January paycheck. We'll update this page as the bill moves. Bookmark it or check
the <a href="/blog/fy2027-ndaa-pay-benefits.html">full FY2027 NDAA benefits roundup</a>.</p>
'''
write("2027-military-pay-raise-tracker.html",
      "2027 Military Pay Raise: 7%/6%/5% Tiered Proposal (Tracker & Charts)",
      "The proposed 2027 military pay raise is tiered: 7% for E-5 and below, 6% for E-6–O-3, 5% for O-4+. Passed House committee June 5, 2026. See estimated 2027 pay by rank.",
      "2027 Raise", body,
      faq=[("How much is the 2027 military pay raise?","The current proposal is tiered: <b>7% for E-5 and below, 6% for E-6 through O-3, and 5% for O-4 and above</b>, effective January 1, 2027. It is not yet law."),
           ("Is the 2027 pay raise approved?","Not yet. The House Armed Services Committee approved it on June 5, 2026; it still needs the House floor, the Senate, and the President's signature — typically completed in December."),
           ("Why do junior enlisted get a bigger raise?","Congress has prioritized junior-enlisted pay to address recruiting, retention, and food-insecurity concerns among the most junior troops.")],
      related=[("FY2027 NDAA: every pay & benefits change","/blog/fy2027-ndaa-pay-benefits.html"),
               ("2026 military pay chart (current rates)","/blog/2026-military-pay-chart.html"),
               ("2026 military pay raise (3.8%)","/blog/2026-military-pay-raise.html")],
      blurb="Proposed: 7% (E-5 &amp; below), 6% (E-6&ndash;O-3), 5% (O-4+) &mdash; tracker with estimated 2027 pay.")

# --- 2. FY2027 NDAA benefits roundup ---
body = f'''<h1>FY2027 NDAA: Every Pay &amp; Benefits Change That Affects Your Wallet</h1>
<p class="meta">Updated {NEWS_DATE} &middot; Based on the House Armed Services Committee bill passed June 5, 2026</p>
<p class="lead">The House Armed Services Committee approved the <strong>fiscal 2027 National Defense Authorization Act</strong>
on June 5, 2026 &mdash; a $1.15&nbsp;trillion bill packed with pay and quality-of-life provisions. Here's what's in it for
service members and families, in plain English. <em>Everything below is proposed, not yet law.</em></p>
<h2>1. Tiered pay raise: 7% / 6% / 5%</h2>
<p>The headline item: <strong>7% for E-5 and below, 6% for E-6 through O-3, 5% for O-4 and above</strong>, effective
January 1, 2027. Full details and estimated pay tables in our
<a href="/blog/2027-military-pay-raise-tracker.html">2027 pay raise tracker</a>.</p>
<h2>2. BAH no longer counts against food assistance (Basic Needs Allowance)</h2>
<p>The bill would <strong>remove BAH from the income calculation for the Basic Needs Allowance (BNA)</strong> &mdash; the
food-assistance benefit for low-income military families. Today, counting tax-free housing allowance as "income" pushes
many families above the eligibility line. Excluding it would make <strong>far more junior families eligible</strong>.
The same provision passed the House last year but was dropped from the final FY2026 bill &mdash; advocates are pushing
to keep it in this time.</p>
<h2>3. Bereavement leave for pregnancy loss</h2>
<p>Active-duty and reserve members would receive <strong>bereavement leave after a miscarriage or stillbirth</strong> —
a first for the military leave system.</p>
<h2>4. Health care access</h2>
<ul>
<li><strong>Physical therapy without a referral</strong> &mdash; direct access instead of waiting on a PCM referral.</li>
<li><strong>Tricare fixes</strong> &mdash; faster complaint processing and pharmacy audits.</li>
</ul>
<h2>5. Child care</h2>
<p>Expanded options, including allowing <strong>au pairs</strong> &mdash; aimed at the long waitlists at base CDCs.</p>
<h2>6. Bigger force</h2>
<p>End strength would grow by <strong>40,100 active-duty members</strong> across the services &mdash; relevant if you're
watching promotion timing and retention bonuses.</p>
<p class="callout"><strong>What happens next:</strong> House floor vote expected mid-July &rarr; Senate writes its own
version &rarr; the two are reconciled &rarr; signed into law, usually <strong>December 2026</strong>. Provisions can be
added or dropped at any stage &mdash; we'll keep this page updated.</p>
{cta("Calculate your current 2026 take-home pay while Congress finalizes 2027.", "/")}
'''
write("fy2027-ndaa-pay-benefits.html",
      "FY2027 NDAA: Every Pay & Benefits Change for Service Members",
      "The FY2027 NDAA passed House committee June 5, 2026: tiered 7%/6%/5% pay raise, BAH excluded from Basic Needs Allowance, bereavement leave, PT without referral, child care expansion.",
      "FY27 NDAA", body,
      faq=[("What is in the FY2027 NDAA for military pay?","A tiered raise (7% E-5 and below, 6% E-6–O-3, 5% O-4+), removing BAH from Basic Needs Allowance income calculations, bereavement leave for pregnancy loss, direct-access physical therapy, and expanded child care."),
           ("Is the FY2027 NDAA law yet?","No. The House Armed Services Committee passed it June 5, 2026. It still needs the full House, the Senate, and the President's signature — typically by late December."),
           ("What is the Basic Needs Allowance change?","The bill would stop counting tax-free BAH as income when determining eligibility for the Basic Needs Allowance, making many more junior enlisted families eligible for the food-assistance benefit.")],
      related=[("2027 pay raise tracker (7%/6%/5%)","/blog/2027-military-pay-raise-tracker.html"),
               ("BAH reform: from 95% back to 100%?","/blog/bah-reform-95-to-100.html"),
               ("2026 military pay chart","/blog/2026-military-pay-chart.html")],
      blurb="Plain-English breakdown of the June 5, 2026 House bill: raise, BNA fix, leave, health care.")

# --- 3. BAH reform: 95% -> 100% ---
body = f'''<h1>BAH Reform: From 95% Back to 100% &mdash; What's Actually Changing</h1>
<p class="meta">Updated {NEWS_DATE}</p>
<p class="lead">Since 2019, BAH has covered only <strong>95% of estimated housing costs</strong> &mdash; service members
absorb the other 5% out of pocket (about <strong>$93&ndash;$212 per month</strong> in 2026, depending on grade and
location). Momentum is building in Washington to fix that, and real money has already moved.</p>
<h2>Where things stand</h2>
<ul>
<li><strong>2026 rates:</strong> BAH rose <a href="/blog/2026-bah-rates-explained.html">about 4.2% on average</a> &mdash;
a smaller bump than the 5.4% increases of 2024 and 2025 &mdash; and still covers 95% of calculated costs.</li>
<li><strong>$2.9 billion supplemental:</strong> the 2025 "One Big Beautiful Bill" reconciliation package included
$2.9&nbsp;billion in extra BAH funding &mdash; the first concrete step toward restoring the benefit toward 100%.</li>
<li><strong>FY2026 NDAA study:</strong> Congress ordered a study on improving how BAH is calculated so rates keep up
with actual rental markets.</li>
<li><strong>Compensation review recommendations:</strong> the Pentagon's quadrennial compensation review recommended
replacing the current BAH model with a more reliable one &mdash; including scrapping the six housing profiles in favor
of a simpler bedroom-count standard.</li>
</ul>
<h2>Why the 5% matters</h2>
<p>Five percent sounds small, but BAH is the second-largest piece of most paychecks. For an E-5 with dependents in a
high-cost area, 5% of housing costs can be $150&ndash;$200+ every month &mdash; roughly an entire car payment over a year.
Restoring 100% coverage is effectively a tax-free raise concentrated where housing is most expensive.</p>
<h2>What it means for you right now</h2>
<ul>
<li>Nothing changes automatically &mdash; 2026 rates remain at 95% cost coverage.</li>
<li>If the reform advances, expect it through an NDAA or budget bill &mdash; watch the
<a href="/blog/fy2027-ndaa-pay-benefits.html">FY2027 NDAA</a>.</li>
<li>Your individual rate still depends on ZIP code, grade, and dependents &mdash; check yours on the
<a href="/bah/">BAH rates by location</a> pages or in the <a href="/">calculator</a>.</li>
</ul>
{cta("Look up your current BAH and full take-home pay by ZIP code.", "/")}
'''
write("bah-reform-95-to-100.html",
      "BAH Reform: From 95% Back to 100% — What's Actually Changing",
      "BAH covers only 95% of housing costs since 2019 — $93–$212/month out of pocket. A $2.9B funding boost, a congressional study, and Pentagon review recommendations point toward restoring 100%.",
      "BAH Reform", body,
      faq=[("Why does BAH only cover 95% of housing costs?","A 2019 cost-saving change set BAH at 95% of estimated local housing costs, leaving members to absorb the remaining 5% — about $93–$212 per month in 2026."),
           ("Is BAH going back to 100%?","Not yet, but momentum is building: a $2.9 billion supplemental was funded in 2025, Congress ordered a study of the BAH formula, and the Pentagon's compensation review recommended a better model."),
           ("How much is the 5% out-of-pocket in dollars?","Between roughly $93 and $212 per month in 2026, depending on pay grade and location.")],
      related=[("2026 BAH rates explained","/blog/2026-bah-rates-explained.html"),
               ("BAH rates by location (299 cities)","/bah/"),
               ("FY2027 NDAA benefits roundup","/blog/fy2027-ndaa-pay-benefits.html")],
      blurb="BAH has covered 95% since 2019 ($93&ndash;$212/mo out of pocket) &mdash; the push to restore 100%.")

# ===================== BLOG INDEX =====================
def _cat(slug):
    order=[("Policy News (2027 & Reform)",["2027","fy2027","bah-reform"]),
           ("Home Buying & VA Loans",["va-loan","va-home-loan","homebuyer","buy-or-rent","funding-fee"]),
           ("Reserve & National Guard",["reserve","national-guard"]),
           ("Pay Charts & Rank Pay",["how-much-does-an","how-much-does-a-general","navy-seal","academy-rotc","2026-military-pay-chart","warrant-officer-pay","prior-enlisted","officer-vs-enlisted","basic-training-pay","does-military-pay-differ","promotion-value"]),
           ("Special & Incentive Pays",["special-pays","flight-pay","sea-pay","submarine","deployment-pay","bonuses"]),
           ("Taxes",["combat-zone","states-that-dont","tax-filing"]),
           ("Retirement, Benefits & Total Comp",["tsp","retirement","sgli","roth","gi-bill","tricare","va-disability","separation-severance","total-compensation","civilian-equivalent-rmc","continuation","survivor-benefit","sbp","crdp","crsc"]),
           ("Paychecks, Moves & Money Moves",["pay-dates","how-to-read","why-is-my","military-pay-raise","2025-vs-2026","ppm","selling-military-leave","per-diem","scra","basic-needs"]),
           ("Allowances, BAH & Family",["bah","bas-rates","cola","on-base","dual-military","dislocation","family-allowances","partial-bah","clothing-allowance"]),
          ]
    for name,subs in order:
        if any(s in slug for s in subs): return name
    return "More Guides"

_DISPLAY = ["Pay Charts & Rank Pay","Allowances, BAH & Family","Home Buying & VA Loans",
            "Special & Incentive Pays","Reserve & National Guard","Taxes",
            "Retirement, Benefits & Total Comp","Paychecks, Moves & Money Moves",
            "Policy News (2027 & Reform)","More Guides"]
_buckets = {c:[] for c in _DISPLAY}
for slug,title,desc,blurb in ARTICLES:
    _buckets[_cat(slug)].append((slug,title,blurb))
import re as _re
def _anchor(c): return _re.sub(r'[^a-z0-9]+','-',c.lower()).strip('-')
_nav = " &middot; ".join(f'<a href="#{_anchor(c)}">{c}</a>' for c in _DISPLAY if _buckets[c])
_sections = ""
for c in _DISPLAY:
    items = _buckets[c]
    if not items: continue
    lis = "".join(f'<li><a href="/blog/{s}"><strong>{t}</strong></a><br><span class="bl">{b}</span></li>' for s,t,b in items)
    _sections += f'<h2 id="{_anchor(c)}">{c} <span style="color:var(--muted);font-weight:400;font-size:.9rem">({len(items)})</span></h2><ul class="bloglist">{lis}</ul>'
idx_ld = {"@context":"https://schema.org","@type":"CollectionPage","name":"Military Pay Guides & 2026 Pay Charts",
          "url":f"{SITE}/blog/"}
idx = head("Military Pay Guides & 2026 Pay Charts | militarypaytool.com",
           "Free guides to 2026 U.S. military pay: pay charts by rank, BAH rates, drill pay, taxes, benefits, and take-home pay for active duty and reserve.",
           "", "Articles", idx_ld).replace('<div class="crumb"><a href="/">Home</a> &rsaquo; <a href="/blog/">Articles</a> &rsaquo; Articles</div>',
           '<div class="crumb"><a href="/">Home</a> &rsaquo; Articles</div>')
idx += f'''<h1>Military Pay Guides</h1>
<p class="lead">Free, plain-English guides to how U.S. military pay works in 2026 &mdash; for active duty and Reserve/National Guard. {len(ARTICLES)} guides, organized by topic.</p>
<style>.bloglist{{list-style:none;padding:0;margin:0 0 8px}} .bloglist li{{padding:13px 0;border-bottom:1px solid var(--line)}} .bloglist .bl{{color:var(--muted);font-size:.9rem}} .catnav{{font-size:.85rem;line-height:2;margin:6px 0 18px}}</style>
<div class="catnav">{_nav}</div>
{_sections}
{cta("Skip the reading — calculate your 2026 take-home pay now.", "/")}
'''
idx += foot([("2026 Military Pay Calculator (home)","/")])
# fix canonical/og url for index (slug empty -> /blog/)
idx = idx.replace(f"{SITE}/blog/\"", f"{SITE}/blog/\"")
open("blog/index.html","w").write(idx)
print("wrote blog/index.html")

# ===================== SITEMAP =====================
urls = [("/","1.0"),("/es/","0.8"),("/blog/","0.9")] + [(f"/blog/{s}","0.8") for s,_,_,_ in ARTICLES]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for loc,pri in urls:
    sm += f'  <url><loc>{SITE}{loc}</loc><lastmod>{DATE}</lastmod><priority>{pri}</priority></url>\n'
sm += '</urlset>\n'
open("sitemap.xml","w").write(sm)
print("wrote sitemap.xml with", len(urls), "urls")
print("\nARTICLES:", [a[0] for a in ARTICLES])
