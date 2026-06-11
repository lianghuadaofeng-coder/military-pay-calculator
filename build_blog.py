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
