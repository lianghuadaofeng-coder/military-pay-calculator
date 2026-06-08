# U.S. Military Pay Calculator (2026)

**🔗 Live: https://lianghuadaofeng-coder.github.io/military-pay-calculator/**

A single-page web calculator that estimates a U.S. service member's **monthly and annual
compensation and take-home pay** — Basic Pay, BAH, BAS, special/incentive pays, COLA,
and the major deductions (federal tax, FICA, state tax, TSP, SGLI). All UI is in English.

## Run it

No build step. Either:

- **Double-click `index.html`** (opens from disk — data files load via `<script>` tags, so it works offline), or
- Serve the folder: `node server.js` then open <http://localhost:8123>.

## Files

```
index.html            UI + styling
app.js                calculator logic
server.js             tiny static file server (local preview)
data/
  basic_pay_2026.js   2026 DFAS basic pay table (all grades × years of service)
  bah_2025.js         BAH rates (all ~300 MHAs × grade × dependent status)
  zip_mha.js          ZIP code → MHA mapping (~40,800 ZIPs) for BAH lookup
  reserve_2025.js     BAH RC/Transit (non-locality) table for Reserve/Guard
  rates_2026.js       BAS, special pays, tax brackets, FICA, SGLI, TSP limit
```

## Data vintage & sources

| Component | Year | Source |
|-----------|------|--------|
| Basic Pay | **2026** (3.8% raise) | DFAS 2026 pay table, rounded to nearest dollar; flag officers capped at Exec. Schedule Level II ($18,808.20/mo) |
| BAS | **2026** | DFAS — $476.95 enlisted / $328.48 officer |
| Special & incentive pays | **2026** | DFAS / Military.com defaults (user-editable) |
| Federal tax brackets & standard deduction | **2026** | IRS (post-OBBBA) |
| FICA | **2026** | SSA — SS 6.2% to $184,500; Medicare 1.45% (+0.9% > $200k) |
| SGLI | **2026** | VA — $0.05 / $1,000 / mo + $1 TSGLI |
| **BAH** | **2025** | DTMO official `BAH-PDF-Excel-2025` (the latest *complete* dataset publicly downloadable) |

### State tax & insights

- **State of legal residence** dropdown: the 9 states with no wage income tax (AK, FL, NV, NH, SD,
  TN, TX, WA, WY) auto-set state tax to **$0**. Other states keep a manual effective-% field (state
  brackets and military exemptions vary too much to hard-code reliably) with a reminder that many
  states fully exempt active-duty pay.
- **Insight panel**: shows what share of gross pay is tax-free, your take-home ratio, annual
  take-home, and (in reserve mode) per-weekend / annual drill totals.

### Save, share & print

- **Auto-save** — every input is persisted to `localStorage`, so your scenario is still there
  when you reopen the page.
- **Copy share link** — encodes the full input state into a URL fragment; open it on any device
  to reproduce the exact scenario (great for comparing offers or sharing with a spouse/recruiter).
- **Print / Save PDF** — a print stylesheet hides the form and prints a clean breakdown sheet.
- **Reset** — clears saved state and returns to defaults.

### Active Duty vs Reserve / National Guard

A **Duty status** toggle switches the whole calculator between two pay models:

- **Active Duty** — monthly entitlements (Basic Pay + BAH + BAS + special pays + COLA) minus deductions.
- **Reserve / Guard** — drill-based. One 4-hour **drill period** pays **1/30 of monthly basic pay**
  (a normal weekend = 4 periods, ~48/year); drills pay basic pay only. **Annual Training** (default
  14 days) is paid like active duty: daily basic + BAS + BAH (BAH RC/Transit for orders < 30 days,
  locality BAH for 30+). Because reserve pay is taxed on top of civilian earnings, the reserve view
  asks for **other annual income** and estimates federal tax as the *marginal* amount on that stack.
  It also estimates **retirement points** for the anniversary year (1 per drill period + 1 per AT day
  + 15 membership, inactive points capped at 130), flags a **"good year"** (≥50 points), and — given
  your career points so far — projects cumulative points and equivalent years of service (÷360).

### BAH lookup by ZIP code

BAH is set by where the member **lives**, so the app takes a residence **ZIP code**, resolves it
to a Military Housing Area (MHA), and looks up the rate by grade + dependent status. A city/base
search box is also provided. The ZIP→MHA map (`zip_mha.js`) is derived from the DoD
`sorted_zipmha` file (2015 vintage — the only complete copy publicly committed) and covers
~98.8% of U.S. ZIP codes. ZIP-to-MHA assignments are fairly stable but can change, so the UI
displays the resolved city for verification and keeps a manual BAH override. To refresh it,
extract `sorted_zipmhaYY.txt` from the official `BAH-ASCII-YYYY.zip` and regroup by MHA.

### Why BAH is 2025

The official complete 2026 BAH dataset (`BAH-ASCII-2026.zip` / `2026_BAH_Rates.xlsx`)
is served behind an Akamai edge that blocks automated download, and it was not yet in the
Internet Archive at build time. The app therefore ships the **complete official 2025 table**
and exposes a **"Enter BAH manually"** field so any user can paste their exact current rate
from the official lookup. 2026 rates average ~4.2% higher (varies by location).

## Swapping in 2026 BAH later

The BAH data layer is a single drop-in file. When the official 2026 file is reachable:

1. Download `BAH-PDF-Excel-2026.zip` (or `BAH-ASCII-2026.zip`) from
   `travel.dod.mil → BAH → BAH Rates for All Locations and Pay Grades`.
2. Convert the `With` / `Without` sheets to the same JSON shape used by `data/bah_2025.js`:
   ```js
   window.BAH = {
     meta:  { year:2026, effective:"2026-01-01", source:"…",
              grades:["E01","E02",…,"O01","…","O07"] },   // column order
     names: { "CA038":"SAN DIEGO, CA", … },                // MHA code → name
     with:    { "CA038":[rateE01, rateE02, …], … },        // arrays match meta.grades
     without: { "CA038":[…], … }
   };
   ```
   (The `data/` build used Python + openpyxl on the official `.xlsx`; the grade column
   order is `E01–E09, W01–W05, O01E,O02E,O03E, O01–O07`.)
3. Save as `data/bah_2026.js`, point the `<script>` tag in `index.html` to it, and
   remove the 2025 warning banner (`#bahYearWarn`) plus the `BADGE`/footer note about BAH.

No other code changes are needed — `app.js` reads `meta.grades` for column mapping.

## Accessibility & robustness

- Segmented toggles expose `role="group"` + `aria-pressed`; the take-home figure is an `aria-live`
  region so screen readers announce updates; visible `:focus-visible` outlines throughout.
- Responsive down to 375px (single column; paired inputs stack under 480px).
- All numeric inputs are clamped to their valid min/max on change.

## Verification

Calculations are cross-checked against independent hand computations: a full active-duty scenario
(matches to the cent), the combat-zone officer exclusion cap, FICA continuing under CZTE, the
additional 0.9% Medicare above $200k, and the TSP elective-deferral cap (monthly for active,
annual for reserve). Basic pay is whole-dollar (±$1/mo vs the official $0.10-rounded table).

## Disclaimer

Unofficial estimate for planning only; not affiliated with the U.S. Government or DoD.
Your **LES** is the authoritative source. Federal tax shown is an estimated annual liability
÷ 12, not exact W-4 withholding. State tax treatment of military pay varies by state of
legal residence (many states exempt it entirely).
