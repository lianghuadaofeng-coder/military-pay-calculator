#!/usr/bin/env python3
# Generate es/index.html (Spanish calculator) from index.html.
# Static UI text is translated here; dynamic strings come from i18n.js (window.LANG="es").
import os, re

src = open("index.html", encoding="utf-8").read()
h = src

# ---- head / meta / paths / lang ----
h = h.replace('<html lang="en">', '<html lang="es">')
h = h.replace('window.LANG="en";', 'window.LANG="es";')
h = h.replace('src="data/', 'src="/data/')
h = h.replace('src="i18n.js"', 'src="/i18n.js"')
h = h.replace('src="app.js"', 'src="/app.js"')
h = h.replace('href="favicon.svg"', 'href="/favicon.svg"')
h = h.replace('rel="canonical" href="https://militarypaytool.com/"',
              'rel="canonical" href="https://militarypaytool.com/es/"')
h = h.replace('property="og:url" content="https://militarypaytool.com/"',
              'property="og:url" content="https://militarypaytool.com/es/"')
h = h.replace('<title>U.S. Military Pay Calculator 2026 — Active Duty & Reserve Take-Home Pay</title>',
              '<title>Calculadora de Paga Militar de EE. UU. 2026 — Servicio Activo y Reserva</title>')
h = h.replace('content="Free 2026 U.S. military pay calculator. Estimate monthly and annual take-home pay — basic pay, BAH by ZIP code, BAS, special pays, COLA, federal/FICA/state tax, TSP and SGLI. Supports active duty and Reserve/National Guard drill pay and retirement points."',
              'content="Calculadora gratuita de paga militar de EE. UU. 2026. Calcula el neto mensual y anual: paga básica, BAH por código postal, BAS, pagas especiales, COLA, impuestos federales/FICA/estatales, TSP y SGLI. Incluye paga de instrucción de Reserva/Guardia Nacional y puntos de retiro."')
# language switcher: mark ES active
h = h.replace('<a href="/" style="color:#fff;font-weight:700;text-decoration:none" aria-current="page">EN</a> · <a href="/es/" style="color:#c7d2e3;text-decoration:none">ES</a>',
              '<a href="/" style="color:#c7d2e3;text-decoration:none">EN</a> · <a href="/es/" style="color:#fff;font-weight:700;text-decoration:none" aria-current="page">ES</a>')
# drop the English FAQPage JSON-LD (visible FAQ is translated; avoid mismatched schema)
h = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "FAQPage".*?</script>',
           '', h, count=1, flags=re.S)

# ---- ordered (en -> es) static-text replacements ----
REPL = [
 # header
 ('<h1>U.S. Military Pay Calculator</h1>', '<h1>Calculadora de Paga Militar de EE. UU.</h1>'),
 ('Estimate your monthly &amp; annual military compensation and take-home pay',
  'Calcula tu paga militar mensual y anual y el neto a cobrar'),
 ('>Guides</a>', '>Guías</a>'),
 ('>2026 RATES</div>', '>2026 TARIFAS</div>'),
 # card 1
 ('</span> Service Profile', '</span> Perfil de servicio'),
 ('Duty status', 'Situación de servicio'),
 ('>Active Duty<', '>Servicio activo<'),
 ('>Reserve / National Guard<', '>Reserva / Guardia Nacional<'),
 ('>Pay grade</label>', '>Grado/rango</label>'),
 ('Years of service <span class="hint">(total active)</span>',
  'Años de servicio <span class="hint">(activo total)</span>'),
 ('E-1 with less than 4 months of service (lower rate)',
  'E-1 con menos de 4 meses de servicio (tasa menor)'),
 ('Dependent status <span class="hint">(affects BAH)</span>',
  'Estado de dependientes <span class="hint">(afecta el BAH)</span>'),
 ('>With dependents<', '>Con dependientes<'),
 ('>Without dependents<', '>Sin dependientes<'),
 # reserve card
 ('</span> Reserve / Guard Service', '</span> Servicio de reserva / guardia'),
 ('Drill periods / month <span class="hint">(weekend = 4)</span>',
  'Períodos de instrucción / mes <span class="hint">(fin de semana = 4)</span>'),
 ('Drill periods / year <span class="hint">(typical 48)</span>',
  'Períodos de instrucción / año <span class="hint">(típico 48)</span>'),
 ('Annual Training days <span class="hint">(typical 14)</span>',
  'Días de entrenamiento anual <span class="hint">(típico 14)</span>'),
 ('>AT housing basis</label>', '>Base de vivienda del EA</label>'),
 ('>Orders &lt; 30 days<', '>Órdenes &lt; 30 días<'),
 ('>≥ 30 days<', '>≥ 30 días<'),
 ('Other annual income <span class="hint">(civilian)</span>',
  'Otro ingreso anual <span class="hint">(civil)</span>'),
 ('Career points so far <span class="hint">(optional)</span>',
  'Puntos de carrera hasta ahora <span class="hint">(opcional)</span>'),
 ('Reserve pay is taxed on top of civilian income — enter your civilian gross so the\n          federal tax estimate uses your real marginal bracket. "Career points so far" projects your\n          retirement-point total (÷360 = equivalent years of service for age-60 retired pay).',
  'La paga de reserva se grava sobre tu ingreso civil — ingresa tu bruto civil para que la estimación\n          de impuestos use tu tramo marginal real. "Puntos de carrera hasta ahora" proyecta tu total de\n          puntos de retiro (÷360 = años equivalentes de servicio para el retiro a los 60).'),
 ('One drill period (4 hrs) pays <b>1/30 of monthly basic pay</b>; a normal drill weekend is 4 periods.\n          Drills pay basic pay only (no BAH/BAS). Annual Training is paid like active duty (basic + BAS + BAH).\n          AT under 30 days uses the BAH RC/Transit table; 30+ days uses your locality BAH (enter a ZIP below).',
  'Un período de instrucción (4 h) paga <b>1/30 de la paga básica mensual</b>; un fin de semana son 4 períodos.\n          La instrucción paga solo la básica (sin BAH/BAS). El Entrenamiento Anual se paga como servicio activo (básica + BAS + BAH).\n          El EA de menos de 30 días usa la tabla BAH RC/Tránsito; 30+ días usa tu BAH local (ingresa un código postal abajo).'),
 # card 2
 ('</span> Housing (BAH) &amp; Subsistence (BAS)', '</span> Vivienda (BAH) y alimentación (BAS)'),
 ('>ZIP code</label>', '>Código postal</label>'),
 ('or search by city / base <span class="hint">(optional)</span>',
  'o buscar por ciudad / base <span class="hint">(opcional)</span>'),
 ('placeholder="e.g. San Diego, Fort Liberty…"', 'placeholder="p. ej. San Diego, Fort Liberty…"'),
 ('>Enter your residence ZIP code — BAH is set by where you live.</div>',
  '>Ingrese su código postal de residencia — el BAH depende de dónde vive.</div>'),
 ('Or browse <a href="/bah/">BAH rates for 300+ locations</a>.',
  'O explora <a href="/bah/">tasas de BAH para 300+ ubicaciones</a>.'),
 ("Don't see your area, or want exact rate? Enter BAH manually ▾",
  '¿No ve su zona o quiere la tasa exacta? Ingrese el BAH manualmente ▾'),
 ('Monthly BAH (from the official DoD BAH calculator)',
  'BAH mensual (de la calculadora oficial de BAH del DoD)'),
 ('placeholder="e.g. 2850"', 'placeholder="p. ej. 2850"'),
 ('Look up your exact rate at travel.dod.mil → BAH Rate Lookup, then paste it here.',
  'Busca tu tasa exacta en travel.dod.mil → BAH Rate Lookup y pégala aquí.'),
 ('BAH rates below are the official <b>2025</b> DoD rates (the latest complete dataset publicly downloadable).\n          All other figures use <b>2026</b> rates. 2026 BAH averages ~4.2% higher — use the manual field for an exact 2026 amount.',
  'Las tasas de BAH son las oficiales del DoD de <b>2025</b> (el último conjunto completo descargable públicamente).\n          Las demás cifras usan tasas de <b>2026</b>. El BAH de 2026 sube ~4.2% en promedio — usa el campo manual para un monto exacto de 2026.'),
 ('Receive BAS (Basic Allowance for Subsistence)', 'Recibir BAS (asignación de alimentación)'),
 # card 3
 ('</span> Special &amp; Incentive Pays', '</span> Pagas especiales y de incentivo'),
 ('>(optional)</span>', '>(opcional)</span>'),
 # card 4
 ('</span> COLA (Cost-of-Living Allowance)', '</span> COLA (ajuste por costo de vida)'),
 ('Monthly COLA <span class="hint">(CONUS or OCONUS, if any)</span>',
  'COLA mensual <span class="hint">(CONUS u OCONUS, si aplica)</span>'),
 ('COLA is location/grade/dependent-specific and <b>tax-free</b>. Look up your amount on the\n            DTMO CONUS or Overseas COLA calculator and enter the monthly total here.',
  'El COLA depende de ubicación/grado/dependientes y es <b>libre de impuestos</b>. Busca tu monto en la\n            calculadora COLA (CONUS o en el extranjero) del DTMO e ingresa el total mensual aquí.'),
 # card 5
 ('</span> Deductions &amp; Taxes', '</span> Deducciones e impuestos'),
 ('>Federal filing status</label>', '>Estado civil fiscal federal</label>'),
 ('>Single</option>', '>Soltero/a</option>'),
 ('>Married filing jointly</option>', '>Casado/a declaración conjunta</option>'),
 ('>Head of household</option>', '>Cabeza de familia</option>'),
 ('>Married filing separately</option>', '>Casado/a declaración separada</option>'),
 ('>State of legal residence</label>', '>Estado de residencia legal</label>'),
 ('State income tax <span class="hint">(your effective %)</span>',
  'Impuesto estatal <span class="hint">(tu % efectivo)</span>'),
 ('Many states fully exempt active-duty military pay — enter <b>0</b> if yours does.',
  'Muchos estados exoneran totalmente la paga militar en servicio activo — escriba <b>0</b> si el suyo lo hace.'),
 ('TSP contribution <span class="hint">(% of basic pay)</span>',
  'Aporte al TSP <span class="hint">(% de la paga básica)</span>'),
 ('>Traditional</button>', '>Tradicional</button>'),
 ('Traditional lowers taxable income; Roth does not. Capped at the 2026 elective limit.',
  'La tradicional reduce el ingreso imponible; la Roth no. Tope: el límite electivo de 2026.'),
 ('>SGLI life insurance coverage</label>', '>Cobertura de seguro de vida SGLI</label>'),
 ('Combat Zone Tax Exclusion (CZTE)', 'Exclusión fiscal por zona de combate (CZTE)'),
 ('Basic pay &amp; most special pays become federally tax-free (officers capped). FICA still applies.',
  'La paga básica y la mayoría de pagas especiales quedan libres de impuesto federal (oficiales con tope). FICA sigue aplicando.'),
 # toolbar
 ('>🔗 Copy share link</button>', '>🔗 Copiar enlace</button>'),
 ('>🖨 Print / Save PDF</button>', '>🖨 Imprimir / Guardar PDF</button>'),
 ('title="Toggle dark mode" aria-label="Toggle dark mode"', 'title="Cambiar modo oscuro" aria-label="Cambiar modo oscuro"'),
 ('title="Reset all inputs">↺ Reset</button>', 'title="Reiniciar todo">↺ Reiniciar</button>'),
 # results (static fallbacks; JS overwrites on compute)
 ('>Estimated Monthly Take-Home</div>', '>Cobro mensual estimado</div>'),
 ('>Monthly Breakdown</h2>', '>Desglose mensual</h2>'),
 ('Effective tax + FICA rate: —', 'Tasa efectiva de impuestos + FICA: —'),
 # embed credit + card
 ('★ Free calculator by <a href="https://militarypaytool.com" target="_blank" rel="noopener">militarypaytool.com</a> — 2026 U.S. military pay, active duty &amp; reserve',
  '★ Calculadora gratuita de <a href="https://militarypaytool.com" target="_blank" rel="noopener">militarypaytool.com</a> — paga militar de EE. UU. 2026, servicio activo y reserva'),
 ('>Embed this calculator</h2>', '>Inserta esta calculadora</h2>'),
 ('Run a military blog or unit page? Drop this calculator into your site — free, no attribution required (but appreciated):',
  '¿Tienes un blog militar o página de unidad? Inserta esta calculadora en tu sitio — gratis, sin atribución requerida (pero se agradece):'),
 ('>Copy</button>', '>Copiar</button>'),
 # FAQ
 ('>2026 Military Pay — Common Questions</h2>', '>Paga Militar 2026 — Preguntas frecuentes</h2>'),
 ('A quick guide to how U.S. military compensation works in 2026, for active duty and Reserve/National Guard.\n        For rank-by-rank pay charts and deeper guides, see our <a href="/blog/">2026 military pay articles</a>.',
  'Una guía rápida de cómo funciona la paga militar de EE. UU. en 2026, para servicio activo y Reserva/Guardia Nacional.\n        Para tablas por rango y guías detalladas (en inglés), vea nuestros <a href="/blog/">artículos de paga militar 2026</a>.'),
 ('<summary>How is military pay calculated?</summary>', '<summary>¿Cómo se calcula la paga militar?</summary>'),
 ('Your pay starts with <b>basic pay</b>, set by your pay grade (E-1 to O-10) and years of service.\n            On top of that you receive <b>allowances</b> — most importantly <b>BAH</b> (housing) and <b>BAS</b> (food) — plus any\n            <b>special &amp; incentive pays</b>. Basic pay and special pays are taxable; allowances are not. After federal/state\n            income tax, Social Security and Medicare (FICA), TSP and SGLI, what\'s left is your <b>take-home pay</b>.',
  'Tu paga empieza con la <b>paga básica</b>, según tu grado (E-1 a O-10) y años de servicio.\n            Además recibes <b>asignaciones</b> — sobre todo <b>BAH</b> (vivienda) y <b>BAS</b> (alimentación) — más cualquier\n            <b>paga especial o de incentivo</b>. La básica y las especiales son imponibles; las asignaciones no. Tras los impuestos\n            federales/estatales, el Seguro Social y Medicare (FICA), el TSP y el SGLI, lo que queda es tu <b>neto a cobrar</b>.'),
 ('<summary>How much does an E-5 make in 2026?</summary>', '<summary>¿Cuánto gana un E-5 en 2026?</summary>'),
 ('In 2026 an <b>E-5 with 4 years</b> of service earns about <b>$3,947/month</b> in basic pay (~$47,400/year),\n            following the 3.8% pay raise. On top of that come tax-free <b>BAH</b> (varies by ZIP code and dependents) and\n            <b>$476.95/month BAS</b>. Total compensation commonly lands around <b>$5,000–$8,500/month</b> depending on duty location\n            and dependent status. Enter your grade and ZIP above for an exact estimate.',
  'En 2026 un <b>E-5 con 4 años</b> de servicio gana unos <b>$3,947/mes</b> de paga básica (~$47,400/año),\n            tras el aumento del 3.8%. A eso se suma el <b>BAH</b> libre de impuestos (varía por código postal y dependientes) y\n            <b>$476.95/mes de BAS</b>. La compensación total suele rondar <b>$5,000–$8,500/mes</b> según la ubicación y\n            los dependientes. Ingresa tu grado y código postal arriba para una estimación exacta.'),
 ('<summary>What is BAH and how is it determined?</summary>', '<summary>¿Qué es el BAH y cómo se determina?</summary>'),
 ('<b>Basic Allowance for Housing</b> is a <b>tax-free</b> allowance based on three things: your <b>duty ZIP code</b>,\n            your <b>pay grade</b>, and whether you have <b>dependents</b>. It\'s meant to cover local rental housing costs, so it\'s much\n            higher in expensive areas. This calculator looks it up automatically from your ZIP.',
  'La <b>Asignación Básica de Vivienda (BAH)</b> es una asignación <b>libre de impuestos</b> basada en tres factores: tu <b>código postal</b>,\n            tu <b>grado</b> y si tienes <b>dependientes</b>. Cubre el costo local de alquiler, así que es mucho\n            mayor en zonas caras. Esta calculadora lo busca automáticamente por tu código postal.'),
 ('<summary>Is BAH (and BAS) taxable?</summary>', '<summary>¿El BAH (y el BAS) es imponible?</summary>'),
 ('No. <b>BAH, BAS, and most allowances are not subject to federal income tax.</b> That\'s why your real\n            take-home pay is higher than the basic-pay figure alone suggests — a large share of military compensation is tax-free.',
  'No. <b>El BAH, el BAS y la mayoría de asignaciones no pagan impuesto federal.</b> Por eso tu neto real\n            es mayor de lo que sugiere la paga básica sola — gran parte de la compensación militar es libre de impuestos.'),
 ('<summary>How is Reserve / National Guard drill pay calculated?</summary>',
  '<summary>¿Cómo se calcula la paga de instrucción de Reserva/Guardia Nacional?</summary>'),
 ('Each 4-hour <b>drill period</b> pays <b>1/30 of your monthly basic pay</b>. A normal drill weekend is\n            <b>4 periods</b> (≈4 days of basic pay), and a typical year has about <b>48 drill periods</b> plus <b>~14 days of Annual\n            Training</b>. Drills pay basic pay only; Annual Training is paid like active duty (basic + BAS + BAH). Switch to\n            <b>Reserva / Guardia Nacional</b> mode above to estimate it.',
  'Cada <b>período de instrucción</b> de 4 horas paga <b>1/30 de tu paga básica mensual</b>. Un fin de semana normal son\n            <b>4 períodos</b> (≈4 días de paga básica), y un año típico tiene unos <b>48 períodos</b> más <b>~14 días de Entrenamiento\n            Anual</b>. La instrucción paga solo la básica; el Entrenamiento Anual se paga como servicio activo (básica + BAS + BAH). Cambia al\n            modo <b>Reserva / Guardia Nacional</b> arriba para estimarlo.'),
 ('<summary>What is a "good year" for reserve retirement?</summary>',
  '<summary>¿Qué es un "buen año" para el retiro de reserva?</summary>'),
 ('A <b>"good year"</b> is any anniversary year in which you earn at least <b>50 retirement points</b>. You earn\n            <b>1 point per drill period</b>, <b>1 point per Annual Training day</b>, and <b>15 membership points</b> per year. Twenty good\n            years generally qualify you for Reserve retired pay (starting around age 60). Total career points ÷ 360 ≈ your equivalent\n            years of service for the pension formula.',
  'Un <b>"buen año"</b> es cualquier año aniversario en el que ganes al menos <b>50 puntos de retiro</b>. Ganas\n            <b>1 punto por período de instrucción</b>, <b>1 punto por día de Entrenamiento Anual</b> y <b>15 puntos por membresía</b> al año. Veinte buenos\n            años suelen darte derecho al retiro de Reserva (a partir de los 60). Puntos de carrera totales ÷ 360 ≈ tus años\n            equivalentes de servicio para la fórmula de la pensión.'),
 ('<summary>How much of military pay goes to taxes?</summary>', '<summary>¿Cuánto de la paga militar se va en impuestos?</summary>'),
 ('Only <b>basic pay and taxable special pays</b> are taxed — not BAH/BAS. You\'ll see <b>federal income tax</b>,\n            <b>Social Security (6.2%</b> up to the wage base) and <b>Medicare (1.45%)</b>. Many states fully exempt active-duty military pay.\n            Pay earned in a designated <b>combat zone</b> can be excluded from federal income tax (FICA still applies).',
  'Solo <b>la paga básica y las pagas especiales imponibles</b> tributan — no el BAH/BAS. Verás <b>impuesto federal</b>,\n            <b>Seguro Social (6.2%</b> hasta la base salarial) y <b>Medicare (1.45%)</b>. Muchos estados exoneran totalmente la paga militar activa.\n            La paga ganada en una <b>zona de combate</b> designada puede excluirse del impuesto federal (FICA sigue aplicando).'),
 ('<summary>What deductions come out of each paycheck?</summary>', '<summary>¿Qué deducciones salen de cada cheque?</summary>'),
 ('Common deductions are <b>federal &amp; state income tax</b>, <b>FICA</b> (Social Security + Medicare),\n            your optional <b>TSP</b> retirement contribution, and <b>SGLI</b> life insurance (about <b>$26/month</b> for the maximum\n            $500,000 of coverage). This calculator subtracts all of these to show your net take-home.',
  'Las deducciones comunes son <b>impuesto federal y estatal</b>, <b>FICA</b> (Seguro Social + Medicare),\n            tu aporte opcional de retiro al <b>TSP</b> y el seguro de vida <b>SGLI</b> (unos <b>$26/mes</b> por la cobertura máxima\n            de $500,000). Esta calculadora resta todo esto para mostrar tu neto a cobrar.'),
 ('Estimates only — your Leave and Earnings Statement (LES) is the official source. Not affiliated with the U.S. Government or DoD.',
  'Solo estimaciones — tu Hoja de Pagos (LES) es la fuente oficial. No afiliado al Gobierno de EE. UU. ni al DoD.'),
 # footer
 ('Data sources &amp; important notes', 'Fuentes de datos y notas importantes'),
 ('<b>Basic Pay:</b> 2026 DFAS pay table (3.8% raise), rounded to the nearest dollar; senior officers capped at Executive Schedule Level II ($18,808.20/mo).',
  '<b>Paga básica:</b> tabla DFAS 2026 (aumento 3.8%), redondeada al dólar; oficiales superiores con tope en el Nivel II del Executive Schedule ($18,808.20/mes).'),
 ('<b>BAS:</b> 2026 — Enlisted $476.95, Officer $328.48.', '<b>BAS:</b> 2026 — Tropa $476.95, Oficial $328.48.'),
 ('<b>BAH:</b> Official DoD 2025 rates (latest complete public dataset). ZIP→location mapping covers ~98.8% of U.S. ZIP codes; assignments can shift over time, so verify the resolved city. For an exact 2026 amount use the manual field and the official BAH Rate Lookup at travel.dod.mil.',
  '<b>BAH:</b> tasas oficiales del DoD de 2025 (último conjunto público completo). El mapeo código postal→ubicación cubre ~98.8% de los códigos de EE. UU.; las asignaciones cambian con el tiempo, verifica la ciudad. Para un monto exacto de 2026 usa el campo manual y el BAH Rate Lookup oficial en travel.dod.mil.'),
 ('<b>Taxes:</b> 2026 IRS brackets &amp; standard deduction (post-OBBBA). Federal figure is an estimated annual tax liability divided by 12 — not exact W-4 withholding. BAH, BAS and COLA are non-taxable.',
  '<b>Impuestos:</b> tramos del IRS 2026 y deducción estándar (post-OBBBA). La cifra federal es una obligación anual estimada dividida entre 12 — no la retención exacta del W-4. BAH, BAS y COLA no tributan.'),
 ('<b>FICA:</b> Social Security 6.2% up to $184,500; Medicare 1.45% (+0.9% over $200k). Applies to basic &amp; special pay even in a combat zone.',
  '<b>FICA:</b> Seguro Social 6.2% hasta $184,500; Medicare 1.45% (+0.9% sobre $200k). Aplica a paga básica y especial incluso en zona de combate.'),
 ('<b>SGLI:</b> $0.05 per $1,000/mo + $1.00 TSGLI.', '<b>SGLI:</b> $0.05 por $1,000/mes + $1.00 TSGLI.'),
 ('<b>Reserve / Guard:</b> Drill pay = 1/30 of monthly basic pay per 4-hour drill period (weekend = 4 periods); drills pay basic only. Annual Training is paid like active duty (basic + BAS + BAH); under 30 days uses the 2025 BAH RC/Transit table, 30+ days uses locality BAH. Reserve federal tax is estimated as the marginal tax stacked on the civilian income you enter.',
  '<b>Reserva / Guardia:</b> paga de instrucción = 1/30 de la paga básica mensual por período de 4 horas (fin de semana = 4 períodos); la instrucción paga solo la básica. El Entrenamiento Anual se paga como servicio activo (básica + BAS + BAH); menos de 30 días usa la tabla BAH RC/Tránsito 2025, 30+ días usa el BAH local. El impuesto federal de reserva se estima como el impuesto marginal sobre el ingreso civil que ingresas.'),
 ('<b>Disclaimer:</b> This is an unofficial estimate for planning only and is not affiliated with the U.S. Government or DoD.\n    Your actual Leave and Earnings Statement (LES) is the authoritative source. State tax treatment and individual circumstances vary.',
  '<b>Aviso:</b> esto es una estimación no oficial solo para planificación y no está afiliado al Gobierno de EE. UU. ni al DoD.\n    Tu Hoja de Pagos (LES) real es la fuente autoritativa. El trato fiscal estatal y las circunstancias individuales varían.'),
 ('<b>Guides:</b>', '<b>Guías:</b>'),
]

missed = []
for en, es in REPL:
    if en in h:
        h = h.replace(en, es)
    else:
        missed.append(en[:60])

os.makedirs("es", exist_ok=True)
open("es/index.html", "w", encoding="utf-8").write(h)
print("wrote es/index.html (%d bytes)" % len(h))
if missed:
    print("WARNING — %d phrases did not match (left in English):" % len(missed))
    for m in missed: print("   -", m)
else:
    print("all phrases matched ✓")
# remaining English UI text (rough check)
for probe in ["Service Profile", "With dependents", "Federal filing", "Copy share link", "Estimated Monthly"]:
    if probe in h: print("   still-EN:", probe)
