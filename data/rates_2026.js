/* 2026 rates & constants. Sources: DFAS, DTMO, IRS (Rev. Proc. 2025-32 / OBBBA),
   SSA, VA (SGLI). Effective Jan 1, 2026 unless noted. */
window.RATES = {
  year: 2026,

  // Basic Allowance for Subsistence (monthly). Enlisted vs Officer (WO get officer rate).
  bas: { enlisted: 476.95, officer: 328.48 },

  // Selected special & incentive pays (monthly). Editable in the UI.
  specialPays: [
    { id: "fsa",  label: "Family Separation Allowance (FSA)",        amount: 300, taxable: true,
      note: "Paid when away from dependents 30+ days." },
    { id: "idp",  label: "Hostile Fire / Imminent Danger Pay (IDP)", amount: 225, taxable: true,
      note: "$225/mo (prorated by days in 2026). Tax-free in a combat zone." },
    { id: "hdip", label: "Hazardous Duty Incentive Pay (HDIP)",      amount: 150, taxable: true,
      note: "Non-crewmember hazardous duty (e.g., demolition, toxic fuels)." },
    { id: "jump", label: "Parachute (Jump) Pay",                      amount: 150, taxable: true,
      note: "$150/mo standard; HALO is $225/mo." },
    { id: "dive", label: "Diving Duty Pay",                           amount: 240, taxable: true,
      note: "Up to $340/mo depending on qualification." },
    { id: "flight", label: "Aviation Incentive / Flight Pay (ACIP)",  amount: 0,   taxable: true,
      note: "Officer ACIP $125–$1,000/mo; enlisted flight pay $150–$400/mo. Enter your amount." },
    { id: "sea",  label: "Career Sea Pay",                            amount: 0,   taxable: true,
      note: "Up to ~$805/mo by grade and years of sea duty. Enter your amount." },
    { id: "sub",  label: "Submarine Duty Pay",                        amount: 0,   taxable: true,
      note: "Enlisted $75–$600; varies by grade/years. Enter your amount." },
    { id: "lang", label: "Foreign Language Proficiency Pay (FLPP)",   amount: 0,   taxable: true,
      note: "Up to ~$500/mo. Enter your amount." },
    { id: "other", label: "Other special / incentive pay",           amount: 0,   taxable: true,
      note: "Any additional taxable special pay." }
  ],

  // SGLI life insurance: $0.05 per $1,000 coverage / month + $1 TSGLI (effective Jul 1, 2025).
  sgli: { ratePer1000: 0.05, tsgli: 1.00, max: 500000, step: 50000 },

  // FICA (2026)
  fica: {
    ssRate: 0.062, ssWageBase: 184500,        // Social Security: 6.2% up to wage base
    medicareRate: 0.0145,                       // Medicare: 1.45%, no cap
    addlMedicareRate: 0.009, addlMedicareThreshold: 200000  // +0.9% over $200k (single threshold)
  },

  // Thrift Savings Plan elective deferral limit (2026)
  tspAnnualLimit: 24500,

  // Federal income tax — 2026 (IRS, post-OBBBA). Brackets are marginal.
  tax: {
    standardDeduction: { single: 16100, mfj: 32200, hoh: 24150, mfs: 16100 },
    brackets: {
      single: [
        [0,0.10],[12400,0.12],[50400,0.22],[105700,0.24],
        [201775,0.32],[256225,0.35],[640600,0.37]
      ],
      mfj: [
        [0,0.10],[24800,0.12],[100800,0.22],[211400,0.24],
        [403550,0.32],[512450,0.35],[768700,0.37]
      ],
      hoh: [
        [0,0.10],[17700,0.12],[67450,0.22],[105700,0.24],
        [201775,0.32],[256200,0.35],[640600,0.37]
      ],
      // MFS ≈ MFJ thresholds halved (top two derived); standard deduction $16,100.
      mfs: [
        [0,0.10],[12400,0.12],[50400,0.22],[105700,0.24],
        [201775,0.32],[256225,0.35],[384350,0.37]
      ]
    }
  },

  // Years-of-service columns present in the basic pay table.
  yosColumns: ["<2","2","3","4","6","8","10","12","14","16","18","20","22","24","26","30","34","38","40"],

  // Map a service member pay grade to its BAH rate column.
  bahColumnFor: function (grade) {
    if (grade === "O-8" || grade === "O-9" || grade === "O-10") return "O07";
    var m = grade.match(/^([EWO])-(\d+)(E)?$/);
    if (!m) return null;
    var n = ("0" + m[2]).slice(-2);
    return m[1] + n + (m[3] || "");
  }
};
