/* U.S. Military Pay Calculator — logic. All rates from data/*.js */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var BP = window.BASIC_PAY, BAH = window.BAH, R = window.RATES;

  // ---- formatting ----
  function usd(n)  { return "$" + Math.round(n).toLocaleString("en-US"); }
  function usd2(n) { return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

  // ---- state ----
  var state = {
    mode: "active",     // active | reserve
    dep: "with",        // with | without
    tspType: "trad",    // trad | roth
    atBasis: "rct",     // rct | locality  (reserve Annual Training housing)
    mhaCode: null,
    special: {}         // id -> amount override (number)
  };

  // ================= populate controls =================
  var GRADE_ORDER = (function () {
    var e = [], w = [], o = [];
    for (var i = 1; i <= 9; i++) if (BP["E-" + i]) e.push("E-" + i);
    for (var j = 1; j <= 5; j++) if (BP["W-" + j]) w.push("W-" + j);
    ["O-1", "O-2", "O-3", "O-4", "O-5", "O-6", "O-7", "O-8", "O-9", "O-10"].forEach(function (g) { if (BP[g]) o.push(g); });
    var oe = ["O-1E", "O-2E", "O-3E"].filter(function (g) { return BP[g]; });
    return { Enlisted: e, "Warrant Officer": w, Officer: o, "Officer (prior enlisted)": oe };
  })();

  (function fillGrades() {
    var sel = $("grade");
    Object.keys(GRADE_ORDER).forEach(function (group) {
      var og = document.createElement("optgroup"); og.label = group;
      GRADE_ORDER[group].forEach(function (g) {
        var o = document.createElement("option"); o.value = g; o.textContent = g; og.appendChild(o);
      });
      sel.appendChild(og);
    });
    sel.value = "E-5";
  })();

  // Build ZIP -> MHA lookup from the grouped data.
  var ZIP2MHA = {};
  (function buildZip() {
    var g = window.ZIP_MHA_GROUPS || {};
    Object.keys(g).forEach(function (mha) {
      var zips = g[mha].split(" ");
      for (var i = 0; i < zips.length; i++) ZIP2MHA[zips[i]] = mha;
    });
  })();

  (function fillMHA() {
    var dl = $("mhaList");
    var names = BAH.names;
    var items = Object.keys(names).map(function (code) { return { code: code, name: names[code] }; });
    items.sort(function (a, b) { return a.name < b.name ? -1 : 1; });
    var frag = document.createDocumentFragment();
    items.forEach(function (it) {
      var o = document.createElement("option");
      o.value = it.name + "  (" + it.code + ")";
      frag.appendChild(o);
    });
    dl.appendChild(frag);
    window.__MHA_BY_LABEL = {};
    items.forEach(function (it) { window.__MHA_BY_LABEL[(it.name + "  (" + it.code + ")").toLowerCase()] = it.code; });
  })();

  (function fillSGLI() {
    var sel = $("sgli");
    for (var c = R.sgli.max; c >= 0; c -= R.sgli.step) {
      var prem = c === 0 ? 0 : c / 1000 * R.sgli.ratePer1000 + R.sgli.tsgli;
      var o = document.createElement("option");
      o.value = c;
      o.textContent = (c === 0 ? "Declined ($0)" : usd(c) + " coverage — " + usd2(prem) + "/mo");
      sel.appendChild(o);
    }
    sel.value = R.sgli.max;
  })();

  (function fillSpecial() {
    var body = $("specialBody");
    R.specialPays.forEach(function (sp) {
      var row = document.createElement("label");
      row.className = "checkrow";
      row.innerHTML =
        '<input type="checkbox" data-sp="' + sp.id + '">' +
        '<span class="lbl">' + sp.label + '<small>' + sp.note + '</small></span>' +
        '<span class="amt"><input type="number" min="0" step="1" data-spamt="' + sp.id + '" value="' + sp.amount + '"></span>';
      body.appendChild(row);
      state.special[sp.id] = { on: false, amount: sp.amount, taxable: sp.taxable };
    });
  })();

  // States with no tax on wage/military income (AK FL NV NH SD TN TX WA WY).
  var NO_TAX_STATES = { AK:1, FL:1, NV:1, NH:1, SD:1, TN:1, TX:1, WA:1, WY:1 };
  var STATES = [["AL","Alabama"],["AK","Alaska"],["AZ","Arizona"],["AR","Arkansas"],["CA","California"],
    ["CO","Colorado"],["CT","Connecticut"],["DE","Delaware"],["DC","District of Columbia"],["FL","Florida"],
    ["GA","Georgia"],["HI","Hawaii"],["ID","Idaho"],["IL","Illinois"],["IN","Indiana"],["IA","Iowa"],
    ["KS","Kansas"],["KY","Kentucky"],["LA","Louisiana"],["ME","Maine"],["MD","Maryland"],["MA","Massachusetts"],
    ["MI","Michigan"],["MN","Minnesota"],["MS","Mississippi"],["MO","Missouri"],["MT","Montana"],["NE","Nebraska"],
    ["NV","Nevada"],["NH","New Hampshire"],["NJ","New Jersey"],["NM","New Mexico"],["NY","New York"],
    ["NC","North Carolina"],["ND","North Dakota"],["OH","Ohio"],["OK","Oklahoma"],["OR","Oregon"],
    ["PA","Pennsylvania"],["RI","Rhode Island"],["SC","South Carolina"],["SD","South Dakota"],["TN","Tennessee"],
    ["TX","Texas"],["UT","Utah"],["VT","Vermont"],["VA","Virginia"],["WA","Washington"],["WV","West Virginia"],
    ["WI","Wisconsin"],["WY","Wyoming"]];

  (function fillStates() {
    var sel = $("stateSel");
    var o0 = document.createElement("option"); o0.value = ""; o0.textContent = "— Select / other —"; sel.appendChild(o0);
    STATES.forEach(function (s) {
      var o = document.createElement("option");
      o.value = s[0]; o.textContent = s[1] + (NO_TAX_STATES[s[0]] ? " (no income tax)" : "");
      sel.appendChild(o);
    });
  })();

  function applyStateSel() {
    var st = $("stateSel").value;
    var noTax = !!NO_TAX_STATES[st];
    if (noTax) {
      $("stateRate").value = "0"; $("stateRate").disabled = true;
      $("stateRateField").style.opacity = ".55";
      $("stateNote").innerHTML = "<b>No state income tax</b> on military pay in this state — $0 withheld.";
    } else {
      $("stateRate").disabled = false;
      $("stateRateField").style.opacity = "1";
      $("stateNote").innerHTML = "Many states fully exempt active-duty military pay — enter <b>0</b> if yours does.";
    }
  }

  // ================= lookups =================
  function yosColumn(grade, years) {
    var cols = R.yosColumns, table = BP[grade] || {};
    var chosen = null;
    for (var i = 0; i < cols.length; i++) {
      var c = cols[i];
      var threshold = (c === "<2") ? 0 : parseInt(c, 10);
      if (years >= threshold && table[c] != null) chosen = c;
    }
    // fall back to the lowest populated column
    if (chosen == null) for (var k = 0; k < cols.length; k++) if (table[cols[k]] != null) { chosen = cols[k]; break; }
    return chosen;
  }

  function basicPay(grade, years, e1under4mo) {
    if (grade === "E-1" && e1under4mo && BP["E-1m"]) return BP["E-1m"]["<2"];
    var col = yosColumn(grade, years);
    return col ? BP[grade][col] : 0;
  }

  function maxEnlistedBasic() {
    var max = 0;
    ["E-1","E-2","E-3","E-4","E-5","E-6","E-7","E-8","E-9"].forEach(function (g) {
      var t = BP[g]; if (t) Object.keys(t).forEach(function (k) { if (t[k] > max) max = t[k]; });
    });
    return max;
  }

  function bahAmount(grade, dep) {
    if (state.bahManual != null && !isNaN(state.bahManual)) return state.bahManual;
    if (!state.mhaCode) return 0;
    var col = R.bahColumnFor(grade);
    var tbl = (dep === "with" ? BAH["with"] : BAH["without"])[state.mhaCode];
    if (!tbl || !col) return 0;
    var idx = BAH.meta.grades.indexOf(col);
    if (idx < 0) return 0;
    var v = tbl[idx];
    return v == null ? 0 : v;
  }

  function basAmount(grade) {
    return grade.charAt(0) === "E" ? R.bas.enlisted : R.bas.officer;
  }

  function fedTax(annualTaxable, filing) {
    var sd = R.tax.standardDeduction[filing] || R.tax.standardDeduction.single;
    var ti = Math.max(0, annualTaxable - sd);
    var br = R.tax.brackets[filing] || R.tax.brackets.single;
    var tax = 0;
    for (var i = 0; i < br.length; i++) {
      var lo = br[i][0], rate = br[i][1];
      var hi = (i + 1 < br.length) ? br[i + 1][0] : Infinity;
      if (ti > lo) tax += (Math.min(ti, hi) - lo) * rate; else break;
    }
    return tax;
  }

  function rctBAH(grade, dep) {
    var t = (window.BAH_RCT && window.BAH_RCT.rct) ? window.BAH_RCT.rct[grade] : null;
    if (!t) return 0;
    return dep === "with" ? t["with"] : t["without"];
  }

  // ================= reserve compute =================
  function computeReserve() {
    var grade = $("grade").value;
    var years = Math.max(0, parseInt($("yos").value, 10) || 0);
    var e1m = $("e1m").checked;
    var basic = basicPay(grade, years, e1m);
    var dailyBasic = basic / 30;

    var perPeriod = dailyBasic;                                  // 1 drill period = 1 day of basic
    var pMonth = Math.max(0, parseInt($("drillsMonth").value, 10) || 0);
    var pYear = Math.max(0, parseInt($("drillsYear").value, 10) || 0);
    var atDays = Math.max(0, parseInt($("atDays").value, 10) || 0);

    var monthlyDrill = pMonth * perPeriod;
    var annualDrill = pYear * perPeriod;

    // Annual Training (paid like active duty)
    var atBasic = atDays * dailyBasic;
    var basM = basAmount(grade);
    var atBAS = atDays * (basM / 30);
    var monthlyBAH = (state.atBasis === "locality") ? bahAmount(grade, state.dep) : rctBAH(grade, state.dep);
    var atBAH = atDays * (monthlyBAH / 30);
    var atTotal = atBasic + atBAS + atBAH;

    var grossAnnual = annualDrill + atTotal;

    // ---- deductions (annual) ----
    var taxableBase = annualDrill + atBasic;                     // BAH & BAS are non-taxable
    var tspPct = Math.min(100, Math.max(0, parseFloat($("tspPct").value) || 0));
    var tsp = Math.min(taxableBase * tspPct / 100, R.tspAnnualLimit);
    var tspTrad = (state.tspType === "trad") ? tsp : 0;

    // Federal tax = marginal tax on reserve pay stacked on top of civilian income
    var filing = $("filing").value;
    var civ = Math.max(0, parseFloat($("civIncome").value) || 0);
    var reserveTaxable = Math.max(0, taxableBase - tspTrad);
    var fed = fedTax(civ + reserveTaxable, filing) - fedTax(civ, filing);
    if (fed < 0) fed = 0;

    var ss = Math.min(taxableBase, R.fica.ssWageBase) * R.fica.ssRate;
    var medicare = taxableBase * R.fica.medicareRate;
    var addl = taxableBase > R.fica.addlMedicareThreshold
      ? (taxableBase - R.fica.addlMedicareThreshold) * R.fica.addlMedicareRate : 0;
    var fica = ss + medicare + addl;

    var stateRate = Math.max(0, parseFloat($("stateRate").value) || 0) / 100;
    var stateTax = taxableBase * stateRate;

    var cov = parseInt($("sgli").value, 10) || 0;
    var sgliM = cov === 0 ? 0 : (cov / 1000 * R.sgli.ratePer1000 + R.sgli.tsgli);
    var sgli = sgliM * 12;

    var totalDed = fed + fica + stateTax + tsp + sgli;
    var net = grossAnnual - totalDed;

    // ---- retirement points (anniversary year) ----
    var membership = 15;                       // 15 membership points/year
    var inactivePts = Math.min(pYear + membership, 130);  // IDT + membership capped at 130
    var yearPoints = inactivePts + atDays;     // AT days are active-duty points (uncapped)
    var career = Math.max(0, parseInt($("careerPoints").value, 10) || 0);
    var cumulative = career > 0 ? career + yearPoints : 0;
    var equivYears = (cumulative > 0 ? cumulative : yearPoints) / 360;

    renderReserve({
      grade: grade, basic: basic, perPeriod: perPeriod, pMonth: pMonth, pYear: pYear,
      monthlyDrill: monthlyDrill, annualDrill: annualDrill,
      atDays: atDays, atBasic: atBasic, atBAS: atBAS, atBAH: atBAH, atTotal: atTotal,
      atBasis: state.atBasis, monthlyBAH: monthlyBAH,
      grossAnnual: grossAnnual, taxableBase: taxableBase,
      fed: fed, ss: ss, medicare: medicare + addl, stateTax: stateTax, stateRate: stateRate * 100,
      tsp: tsp, tspType: state.tspType, sgli: sgli, cov: cov,
      totalDed: totalDed, net: net,
      drillPts: pYear, atPts: atDays, membership: membership, inactivePts: inactivePts,
      yearPoints: yearPoints, career: career, cumulative: cumulative, equivYears: equivYears
    });
  }

  // ================= main compute =================
  function compute() {
    if (state.mode === "reserve") return computeReserve();
    var grade = $("grade").value;
    var years = Math.max(0, parseInt($("yos").value, 10) || 0);
    var e1m = $("e1m").checked;

    // Entitlements (monthly)
    var basic = basicPay(grade, years, e1m);
    var bah = bahAmount(grade, state.dep);
    var bas = $("basOn").checked ? basAmount(grade) : 0;
    var cola = Math.max(0, parseFloat($("cola").value) || 0);

    // Special pays
    var specialTaxable = 0, specialNontax = 0, specialList = [];
    R.specialPays.forEach(function (sp) {
      var s = state.special[sp.id];
      if (s && s.on && s.amount > 0) {
        specialList.push({ label: sp.label, amount: s.amount, taxable: sp.taxable });
        if (sp.taxable) specialTaxable += s.amount; else specialNontax += s.amount;
      }
    });

    var grossEnt = basic + bah + bas + cola + specialTaxable + specialNontax;

    // ---- Deductions ----
    // TSP (% of basic pay), capped at annual elective limit / 12
    var tspPct = Math.min(100, Math.max(0, parseFloat($("tspPct").value) || 0));
    var tsp = basic * tspPct / 100;
    var tspMonthlyCap = R.tspAnnualLimit / 12;
    if (tsp > tspMonthlyCap) tsp = tspMonthlyCap;
    var tspTrad = (state.tspType === "trad") ? tsp : 0;

    // CZTE: basic + taxable specials become federally non-taxable (officers capped)
    var czte = $("czte").checked;
    var taxablePayMonthly = basic + specialTaxable; // before CZTE / TSP
    if (czte) {
      if (grade.charAt(0) === "E") {
        taxablePayMonthly = 0;
      } else {
        var cap = maxEnlistedBasic() + 225; // highest enlisted basic + IDP
        var excluded = Math.min(basic + specialTaxable, cap);
        taxablePayMonthly = Math.max(0, (basic + specialTaxable) - excluded);
      }
    }
    // Traditional TSP reduces federal taxable wages (not FICA)
    var monthlyTaxableForFed = Math.max(0, taxablePayMonthly - tspTrad);

    var filing = $("filing").value;
    var annualFed = fedTax(monthlyTaxableForFed * 12, filing);
    var fed = annualFed / 12;

    // FICA — on basic + taxable special pay (allowances excluded); CZTE does NOT exempt FICA
    var ficaWageM = basic + specialTaxable;
    var annualWage = ficaWageM * 12;
    var ss = Math.min(annualWage, R.fica.ssWageBase) * R.fica.ssRate / 12;
    var medicare = annualWage * R.fica.medicareRate / 12;
    var addl = annualWage > R.fica.addlMedicareThreshold
      ? (annualWage - R.fica.addlMedicareThreshold) * R.fica.addlMedicareRate / 12 : 0;
    var fica = ss + medicare + addl;

    // State tax (effective % applied to federally-taxable pay before CZTE? apply to basic+taxable specials)
    var stateRate = Math.max(0, parseFloat($("stateRate").value) || 0) / 100;
    var stateTax = (czte ? monthlyTaxableForFed : (basic + specialTaxable)) * stateRate;

    // SGLI
    var cov = parseInt($("sgli").value, 10) || 0;
    var sgli = cov === 0 ? 0 : (cov / 1000 * R.sgli.ratePer1000 + R.sgli.tsgli);

    var totalDed = fed + fica + stateTax + tsp + sgli;
    var net = grossEnt - totalDed;

    render({
      grade: grade, basic: basic, bah: bah, bas: bas, cola: cola,
      specialList: specialList, specialTaxable: specialTaxable, specialNontax: specialNontax,
      grossEnt: grossEnt,
      fed: fed, fica: fica, ss: ss, medicare: medicare, addl: addl,
      stateTax: stateTax, stateRate: stateRate * 100,
      tsp: tsp, tspType: state.tspType, sgli: sgli, cov: cov, czte: czte,
      totalDed: totalDed, net: net
    });
  }

  // ================= render =================
  function row(label, amount, opt) {
    opt = opt || {};
    var cls = opt.neg ? "neg" : (opt.pos ? "pos" : "");
    var tag = opt.tag ? ' <span class="tag">' + opt.tag + "</span>" : "";
    var val = (opt.neg ? "−" : "") + usd2(Math.abs(amount));
    return "<tr><td>" + label + tag + '</td><td class="r ' + cls + '">' + val + "</td></tr>";
  }
  function secRow(label) { return '<tr class="sec"><td colspan="2">' + label + "</td></tr>"; }

  function render(d) {
    var h = "";
    h += secRow("Entitlements");
    h += row("Basic Pay", d.basic, { pos: true, tag: "taxable" });
    h += row("BAH (housing)", d.bah, { pos: true, tag: "tax-free" });
    h += row("BAS (subsistence)", d.bas, { pos: true, tag: "tax-free" });
    if (d.cola > 0) h += row("COLA", d.cola, { pos: true, tag: "tax-free" });
    d.specialList.forEach(function (s) {
      h += row(s.label, s.amount, { pos: true, tag: (d.czte && s.taxable) ? "CZTE" : (s.taxable ? "taxable" : "tax-free") });
    });
    h += '<tr class="tot"><td>Gross monthly entitlements</td><td class="r">' + usd2(d.grossEnt) + "</td></tr>";

    h += secRow("Deductions");
    h += row("Federal income tax (est.)", d.fed, { neg: true });
    h += row("Social Security (6.2%)", d.ss, { neg: true });
    h += row("Medicare (1.45%)" + (d.addl > 0 ? " + 0.9%" : ""), d.medicare + d.addl, { neg: true });
    if (d.stateTax > 0) h += row("State income tax (" + d.stateRate.toFixed(1) + "%)", d.stateTax, { neg: true });
    if (d.tsp > 0) h += row("TSP contribution", d.tsp, { neg: true, tag: d.tspType === "trad" ? "pre-tax" : "Roth" });
    if (d.sgli > 0) h += row("SGLI" + (d.cov ? " (" + usd(d.cov) + ")" : ""), d.sgli, { neg: true });
    h += '<tr class="tot"><td>Total monthly deductions</td><td class="r neg">−' + usd2(d.totalDed) + "</td></tr>";

    h += '<tr class="tot"><td>Net monthly take-home</td><td class="r pos">' + usd2(d.net) + "</td></tr>";
    $("breakdown").innerHTML = h;

    $("netLab").textContent = "Estimated Monthly Take-Home";
    $("bdTitle").textContent = "Monthly Breakdown";
    $("netMonthly").textContent = usd(d.net);
    $("netSub").innerHTML = "Gross entitlements <b>" + usd(d.grossEnt) + "</b> · Deductions <b>−" + usd(d.totalDed) + "</b>";
    $("netAnnualLine").innerHTML = "Annual take-home: <b>" + usd(d.net * 12) + "</b> &nbsp;·&nbsp; Annual gross: <b>" + usd(d.grossEnt * 12) + "</b>";

    var taxFica = d.fed + d.fica + d.stateTax;
    var rate = d.grossEnt > 0 ? (taxFica / d.grossEnt * 100) : 0;
    $("effRate").textContent = "Effective tax + FICA rate: " + rate.toFixed(1) + "%  (of gross entitlements)";

    // insights
    var taxFree = d.bah + d.bas + d.cola + d.specialNontax + (d.czte ? d.basic + d.specialTaxable : 0);
    var freePct = d.grossEnt > 0 ? taxFree / d.grossEnt * 100 : 0;
    var homePct = d.grossEnt > 0 ? d.net / d.grossEnt * 100 : 0;
    $("insight").innerHTML =
      "💡 <b>" + freePct.toFixed(0) + "%</b> of your gross pay is tax-free" +
      (d.czte ? " (allowances + combat-zone pay)." : " (BAH, BAS" + (d.cola > 0 ? ", COLA" : "") + ").") +
      '<div class="row2">' +
      '<span class="stat"><b>' + usd(d.net * 12) + "</b>annual take-home</span>" +
      '<span class="stat"><b>' + homePct.toFixed(0) + "%</b>kept after tax/FICA</span>" +
      '<span class="stat"><b>' + usd(taxFree) + "</b>/mo tax-free</span>" +
      "</div>";

    // composition bar
    var parts = [
      { k: "Basic Pay", v: d.basic, c: "#0b2545" },
      { k: "BAH", v: d.bah, c: "#2e6f8e" },
      { k: "BAS", v: d.bas, c: "#3a8a6e" },
      { k: "Special", v: d.specialTaxable + d.specialNontax, c: "#c9a227" },
      { k: "COLA", v: d.cola, c: "#8a6d3b" }
    ].filter(function (p) { return p.v > 0; });
    var bar = "", leg = "";
    parts.forEach(function (p) {
      var pct = d.grossEnt > 0 ? (p.v / d.grossEnt * 100) : 0;
      bar += '<span style="width:' + pct + '%;background:' + p.c + '"></span>';
      leg += '<span><i style="background:' + p.c + '"></i>' + p.k + " " + pct.toFixed(0) + "%</span>";
    });
    $("compBar").innerHTML = bar;
    $("compLegend").innerHTML = leg;
  }

  function renderReserve(d) {
    var weekend = 4 * d.perPeriod;
    var h = "";
    h += secRow("Drill Pay (Inactive Duty / IDT)");
    h += row("Pay per drill period (4 hrs)", d.perPeriod, { pos: true, tag: "1/30 basic" });
    h += row("Per drill weekend (4 periods)", weekend, { pos: true });
    h += row("Annual drill pay (" + d.pYear + " periods)", d.annualDrill, { pos: true, tag: "taxable" });
    h += secRow("Annual Training (" + d.atDays + " days)");
    h += row("Basic pay", d.atBasic, { pos: true, tag: "taxable" });
    h += row("BAS", d.atBAS, { pos: true, tag: "tax-free" });
    h += row("BAH (" + (d.atBasis === "locality" ? "locality" : "RC/Transit") + ")", d.atBAH, { pos: true, tag: "tax-free" });
    h += '<tr class="tot"><td>Gross annual reserve pay</td><td class="r">' + usd2(d.grossAnnual) + "</td></tr>";

    h += secRow("Deductions (annual)");
    h += row("Federal income tax (est.)", d.fed, { neg: true });
    h += row("Social Security (6.2%)", d.ss, { neg: true });
    h += row("Medicare (1.45%)", d.medicare, { neg: true });
    if (d.stateTax > 0) h += row("State income tax (" + d.stateRate.toFixed(1) + "%)", d.stateTax, { neg: true });
    if (d.tsp > 0) h += row("TSP contribution", d.tsp, { neg: true, tag: d.tspType === "trad" ? "pre-tax" : "Roth" });
    if (d.sgli > 0) h += row("SGLI" + (d.cov ? " (" + usd(d.cov) + ")" : "") + " ×12", d.sgli, { neg: true });
    h += '<tr class="tot"><td>Total annual deductions</td><td class="r neg">−' + usd2(d.totalDed) + "</td></tr>";
    h += '<tr class="tot"><td>Net annual take-home</td><td class="r pos">' + usd2(d.net) + "</td></tr>";

    // retirement points section
    function ptRow(label, n) { return "<tr><td>" + label + '</td><td class="r">' + n + " pts</td></tr>"; }
    var good = d.yearPoints >= 50;
    h += secRow("Retirement Points (anniversary year)");
    h += ptRow("Drill periods (1 pt each)", d.drillPts);
    h += ptRow("Annual Training (" + d.atPts + " days)", d.atPts);
    h += ptRow("Membership points", d.membership);
    h += '<tr class="tot"><td>Points this year' +
      '<span class="ptbadge ' + (good ? "good" : "bad") + '">' + (good ? "✓ Good year" : "✗ Below 50") +
      '</span></td><td class="r">' + d.yearPoints + " pts</td></tr>";
    if (d.cumulative > 0) {
      h += ptRow("Career points (incl. this year)", d.cumulative);
      h += '<tr class="tot"><td>Equivalent years of service</td><td class="r">' + d.equivYears.toFixed(2) + " yrs</td></tr>";
    }
    $("breakdown").innerHTML = h;

    $("bdTitle").textContent = "Annual Breakdown";
    $("netLab").textContent = "Estimated Annual Reserve Pay (gross)";
    $("netMonthly").textContent = usd(d.grossAnnual);
    $("netSub").innerHTML = "Per drill period <b>" + usd2(d.perPeriod) + "</b> · Per weekend (4) <b>" + usd2(weekend) + "</b>";
    $("netAnnualLine").innerHTML = "Annual take-home: <b>" + usd(d.net) + "</b> &nbsp;·&nbsp; Monthly drill: <b>" + usd(d.monthlyDrill) + "</b>";

    var parts = [
      { k: "Drill pay", v: d.annualDrill, c: "#0b2545" },
      { k: "AT basic", v: d.atBasic, c: "#2e6f8e" },
      { k: "AT allowances", v: d.atBAS + d.atBAH, c: "#3a8a6e" }
    ].filter(function (p) { return p.v > 0; });
    var bar = "", leg = "";
    parts.forEach(function (p) {
      var pct = d.grossAnnual > 0 ? (p.v / d.grossAnnual * 100) : 0;
      bar += '<span style="width:' + pct + '%;background:' + p.c + '"></span>';
      leg += '<span><i style="background:' + p.c + '"></i>' + p.k + " " + pct.toFixed(0) + "%</span>";
    });
    $("compBar").innerHTML = bar;
    $("compLegend").innerHTML = leg;
    $("effRate").textContent = "Effective tax + FICA rate: " +
      (d.grossAnnual > 0 ? ((d.fed + d.ss + d.medicare + d.stateTax) / d.grossAnnual * 100).toFixed(1) : "0") +
      "%  (of gross annual pay)";

    var taxFree = d.atBAS + d.atBAH;
    var freePct = d.grossAnnual > 0 ? taxFree / d.grossAnnual * 100 : 0;
    var homePct = d.grossAnnual > 0 ? d.net / d.grossAnnual * 100 : 0;
    $("insight").innerHTML =
      "💡 A drill weekend ≈ <b>" + usd(weekend) + "</b>; " + d.pYear + " drills/yr ≈ <b>" + usd(d.annualDrill) + "</b>." +
      '<div class="row2">' +
      '<span class="stat"><b>' + usd(d.net) + "</b>annual take-home</span>" +
      '<span class="stat"><b>' + homePct.toFixed(0) + "%</b>kept after tax/FICA</span>" +
      '<span class="stat"><b>' + d.yearPoints + " pts</b>retirement (" + (d.yearPoints >= 50 ? "good yr" : "&lt;50") + ")</span>" +
      "</div>";
  }

  // ================= events =================
  function onGradeChange() {
    var g = $("grade").value;
    $("e1mWrap").style.display = (g === "E-1") ? "block" : "none";
    $("basNote").textContent = "(" + (g.charAt(0) === "E" ? usd2(R.bas.enlisted) + " enlisted" : usd2(R.bas.officer) + " officer") + ")";
    compute();
  }
  $("grade").addEventListener("change", onGradeChange);
  ["yos", "e1m", "cola", "filing", "stateRate", "tspPct", "sgli", "basOn", "czte",
   "drillsMonth", "drillsYear", "atDays", "civIncome", "careerPoints"].forEach(function (id) {
    $(id).addEventListener("input", compute);
    $(id).addEventListener("change", compute);
  });
  $("stateSel").addEventListener("change", function () { applyStateSel(); compute(); });

  // duty-status mode (active vs reserve)
  function applyMode() {
    var reserve = state.mode === "reserve";
    $("reserveCard").style.display = reserve ? "" : "none";
    $("specialCard").style.display = reserve ? "none" : "";
    $("colaCard").style.display = reserve ? "none" : "";
    // CZTE / drill-only fields that don't apply to reserve estimate
    $("czte").closest(".field").style.display = reserve ? "none" : "";
    compute();
  }
  $("modeSeg").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    state.mode = b.getAttribute("data-mode");
    [].forEach.call(this.children, function (x) { var on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", on ? "true" : "false"); });
    applyMode();
  });
  // Annual Training housing basis
  $("atBahSeg").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    state.atBasis = b.getAttribute("data-at");
    [].forEach.call(this.children, function (x) { var on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", on ? "true" : "false"); });
    compute();
  });
  // keep drills/year in sync when drills/month changes (until user overrides year)
  $("drillsMonth").addEventListener("input", function () {
    var pm = parseInt(this.value, 10);
    if (!isNaN(pm)) $("drillsYear").value = pm * 12;
    compute();
  });

  // dependent segmented control
  $("depSeg").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    state.dep = b.getAttribute("data-dep");
    [].forEach.call(this.children, function (x) { var on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", on ? "true" : "false"); });
    compute();
  });
  // tsp type
  $("tspTypeSeg").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    state.tspType = b.getAttribute("data-tsp");
    [].forEach.call(this.children, function (x) { var on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", on ? "true" : "false"); });
    compute();
  });

  var DEFAULT_NOTE = "Enter your residence ZIP code — BAH is set by where you live.";
  function setMHA(code, noteHTML) {
    state.mhaCode = code || null;
    $("mhaNote").innerHTML = noteHTML || DEFAULT_NOTE;
    compute();
  }
  function resolvedNote(code, source) {
    var verb = source === "zip" ? "ZIP maps to" : "Selected";
    return verb + ": <b>" + BAH.names[code] + "</b> (" + code +
      ") &nbsp;<span style='color:var(--muted)'>— check the city is right; use manual entry if not.</span>";
  }

  // ZIP code -> MHA
  $("zipInput").addEventListener("input", function () {
    var z = this.value.replace(/\D/g, "").slice(0, 5);
    if (this.value !== z) this.value = z;
    if (z.length < 5) { setMHA(null); return; }
    var code = ZIP2MHA[z];
    if (code) {
      $("mhaInput").value = BAH.names[code] + "  (" + code + ")";
      setMHA(code, resolvedNote(code, "zip"));
    } else {
      $("mhaInput").value = "";
      setMHA(null, "<b>ZIP " + z + "</b> not found in the dataset — pick a city below or enter BAH manually.");
    }
  });

  // city / base name -> MHA
  $("mhaInput").addEventListener("input", function () {
    var code = window.__MHA_BY_LABEL[this.value.trim().toLowerCase()];
    if (code) { $("zipInput").value = ""; setMHA(code, resolvedNote(code, "city")); }
    else setMHA(null);
  });

  // manual BAH toggle
  $("bahManualToggle").addEventListener("click", function () {
    var w = $("bahManualWrap");
    var open = w.style.display === "none";
    w.style.display = open ? "block" : "none";
    this.textContent = (open ? "Use the built-in BAH lookup instead ▴" : "Don't see your area, or want exact rate? Enter BAH manually ▾");
    if (!open) { $("bahManual").value = ""; state.bahManual = null; }
    compute();
  });
  $("bahManual").addEventListener("input", function () {
    var v = this.value.trim();
    state.bahManual = v === "" ? null : parseFloat(v);
    compute();
  });

  // special pay rows
  $("specialBody").addEventListener("input", function (e) {
    var t = e.target;
    if (t.hasAttribute("data-sp")) state.special[t.getAttribute("data-sp")].on = t.checked;
    if (t.hasAttribute("data-spamt")) state.special[t.getAttribute("data-spamt")].amount = Math.max(0, parseFloat(t.value) || 0);
    compute();
  });

  // ================= persistence, share & print =================
  var CONTROL_IDS = ["grade", "yos", "e1m", "cola", "filing", "stateSel", "stateRate", "tspPct", "sgli",
    "basOn", "czte", "drillsMonth", "drillsYear", "atDays", "civIncome", "careerPoints", "bahManual", "zipInput", "mhaInput"];

  function setSeg(segId, attr, val) {
    var seg = $(segId); if (!seg) return;
    [].forEach.call(seg.children, function (b) {
      var on = b.getAttribute("data-" + attr) === val;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function snapshot() {
    var s = { mode: state.mode, dep: state.dep, tspType: state.tspType, atBasis: state.atBasis,
      mhaCode: state.mhaCode, bahManualOpen: $("bahManualWrap").style.display !== "none", special: {} };
    CONTROL_IDS.forEach(function (id) {
      var el = $(id); if (!el) return;
      s[id] = (el.type === "checkbox") ? el.checked : el.value;
    });
    R.specialPays.forEach(function (sp) {
      var x = state.special[sp.id]; s.special[sp.id] = { on: x.on, amount: x.amount };
    });
    return s;
  }

  function applySnapshot(s) {
    if (!s) return;
    if (s.mode) { state.mode = s.mode; setSeg("modeSeg", "mode", s.mode); }
    if (s.dep) { state.dep = s.dep; setSeg("depSeg", "dep", s.dep); }
    if (s.tspType) { state.tspType = s.tspType; setSeg("tspTypeSeg", "tsp", s.tspType); }
    if (s.atBasis) { state.atBasis = s.atBasis; setSeg("atBahSeg", "at", s.atBasis); }
    CONTROL_IDS.forEach(function (id) {
      if (!(id in s)) return; var el = $(id); if (!el) return;
      if (el.type === "checkbox") el.checked = !!s[id]; else el.value = s[id];
    });
    if (s.mhaCode) {
      state.mhaCode = s.mhaCode;
      if (BAH.names[s.mhaCode]) $("mhaNote").innerHTML = resolvedNote(s.mhaCode, "zip");
    }
    if (s.bahManualOpen) {
      $("bahManualWrap").style.display = "block";
      $("bahManualToggle").textContent = "Use the built-in BAH lookup instead ▴";
      if (s.bahManual) state.bahManual = parseFloat(s.bahManual);
    }
    if (s.special) R.specialPays.forEach(function (sp) {
      var sv = s.special[sp.id]; if (!sv) return;
      state.special[sp.id].on = !!sv.on; state.special[sp.id].amount = sv.amount;
      var cb = document.querySelector('[data-sp="' + sp.id + '"]');
      var am = document.querySelector('[data-spamt="' + sp.id + '"]');
      if (cb) cb.checked = !!sv.on; if (am) am.value = sv.amount;
    });
  }

  function saveState() { try { localStorage.setItem("milpay", JSON.stringify(snapshot())); } catch (e) {} }
  function loadState() {
    try {
      var s = null;
      if (location.hash.length > 1) s = JSON.parse(decodeURIComponent(location.hash.slice(1)));
      if (!s) s = JSON.parse(localStorage.getItem("milpay") || "null");
      if (s) applySnapshot(s);
    } catch (e) {}
  }

  document.addEventListener("input", saveState);
  document.addEventListener("change", saveState);
  document.addEventListener("click", function (e) { if (e.target.closest(".seg")) setTimeout(saveState, 0); });

  $("shareBtn").addEventListener("click", function () {
    var url = location.origin + location.pathname + "#" + encodeURIComponent(JSON.stringify(snapshot()));
    var btn = this;
    function ok() { var t = btn.textContent; btn.textContent = "✓ Link copied!"; setTimeout(function () { btn.textContent = t; }, 1800); }
    if (navigator.share) {
      navigator.share({ title: "U.S. Military Pay Calculator", text: "Estimate your 2026 military take-home pay (active duty & reserve)", url: url }).catch(function () {});
    } else if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(ok, function () { prompt("Copy this link:", url); });
    } else prompt("Copy this link:", url);
  });
  $("printBtn").addEventListener("click", function () { window.print(); });
  $("resetBtn").addEventListener("click", function () {
    try { localStorage.removeItem("milpay"); } catch (e) {}
    location.hash = ""; location.reload();
  });

  // ---- theme (dark / light, persisted; default follows system) ----
  function prefersDark() { return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches; }
  function applyTheme(t) {
    var html = document.documentElement;
    if (t === "dark" || t === "light") html.setAttribute("data-theme", t);
    else html.removeAttribute("data-theme");
    var effDark = t === "dark" || (!t && prefersDark());
    var b = $("themeBtn"); if (b) b.textContent = effDark ? "☀️" : "🌙";
  }
  (function initTheme() {
    var saved = null; try { saved = localStorage.getItem("milpay-theme"); } catch (e) {}
    applyTheme(saved);
    $("themeBtn").addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme");
      var effDark = cur === "dark" || (!cur && prefersDark());
      var next = effDark ? "light" : "dark";
      try { localStorage.setItem("milpay-theme", next); } catch (e) {}
      applyTheme(next);
    });
  })();

  // init
  $("yearBadge").textContent = R.year + " RATES";
  loadState();
  applyStateSel();    // sync state no-tax disabled state
  applyMode();        // sync card visibility to restored mode
  onGradeChange();    // sets E-1 field, BAS note, and computes

  // a11y: reflect current segmented-control state for screen readers
  [].forEach.call(document.querySelectorAll(".seg button"), function (b) {
    b.setAttribute("aria-pressed", b.classList.contains("on") ? "true" : "false");
  });
  // robustness: clamp every numeric input to its declared min/max
  [].forEach.call(document.querySelectorAll('input[type=number]'), function (el) {
    el.addEventListener("change", function () {
      if (el.value === "") return;
      var v = parseFloat(el.value);
      if (isNaN(v)) { el.value = ""; compute(); return; }
      var min = el.min !== "" ? parseFloat(el.min) : -Infinity;
      var max = el.max !== "" ? parseFloat(el.max) : Infinity;
      if (v < min) el.value = min; else if (v > max) el.value = max;
      compute();
    });
  });
})();
