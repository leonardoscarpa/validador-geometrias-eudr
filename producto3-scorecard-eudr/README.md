# Supplier Risk Scorecard — EUDR (Article 10)

Product 3 of the EUDR compliance portfolio. Aggregates supplier parcels
(not individual plots) into a documented risk level under Article 10 of
Regulation (EU) 2023/1115, combining the official country risk
classification with declared supply-chain signals: indigenous peoples
presence, intermediaries, mixing risk, prior non-compliance, and voluntary
certification.

Ships in two forms that share the exact same scoring logic:

- **Python package** — tested, run from the command line, produces
  Markdown + Excel reports.
- **Web app** (`web/`) — a single HTML file, no install, drag a spreadsheet
  in and get a color-coded, interactive result. Available in Spanish and
  English.

## Why this product exists

Article 10 requires assessing risk before deciding whether simplified due
diligence (Article 13) or mitigation measures (Article 11) apply. In
practice that step is usually a judgment call nobody wrote down. This turns
it into an auditable matrix: every risk point cites the exact Article 10
clause behind it.

## Quick start

### Python

```bash
pip install -r requirements.txt
python main.py data/proveedores_sinteticos.xlsx -o outputs/
```

Produces `outputs/scorecard.md` and `outputs/scorecard.xlsx` (the Excel
file uses live formulas, not hardcoded values, so it recalculates if you
edit the underlying data).

### Web app

Open `web/scorecard_eudr_web_en.html` (or the Spanish version,
`scorecard_eudr_web.html`) directly in a browser. Nothing to install,
nothing sent to any server. Don't have a file to test with? Use
`web/scorecard_input_example.xlsx` (English) or
`web/scorecard_input_ejemplo.xlsx` (Spanish) — already verified to load
correctly, including with the actual browser spreadsheet library
(SheetJS), not just with Python.

Live versions of the web app are also published via GitHub Pages — see the
repository root.

## Input schema

Same "long" tabular format as Product 1 (one row per vertex, `ParcelID`
groups parcels), plus these additional columns, which should stay
consistent across every parcel belonging to the same supplier:

| Column | Article 10 | Values |
|---|---|---|
| `ProducerName` | — | Supplier name (parcels are aggregated by this field) |
| `ContactName`, `ContactEmail`, `ContactPhone` | — | Web app only: lets you act on a flagged supplier, not just look at a number |
| `IndigenousPeoplesPresence` | (c) | Yes/No |
| `IndigenousConsultation` | (d) | Yes/No |
| `SupplyChainIntermediaries` | (i) | number |
| `MixingRiskDeclared` | (j) | Yes/No |
| `PriorNonComplianceIncidents` | (l) | number |
| `VoluntaryCertification` | (n) | text (e.g. "FSC") or empty |

## Scoring methodology

| Component | Article 10 | Points |
|---|---|---|
| Country: low / standard / high risk (Reg. 2025/1093) | (a) | 0 / 1 / 4 |
| Indigenous peoples present, no documented consultation | (c)(d)(e) | +2 |
| Indigenous peoples present, with documented consultation | (c)(d) | +0.5 |
| 1–2 intermediaries / 3+ intermediaries | (i) | +1 / +2 |
| Mixing risk declared | (j) | +2 |
| 1–2 / 3+ prior non-compliance incidents | (l) | +1 / +3 |
| Voluntary certification (FSC, etc.) | (n) | −1.5 |

Total → **Low** (<2) / **Medium** (2–5) / **High** (≥5).

**Terminology note, worth remembering in an interview:** "Low/Medium/High"
is the *supplier's* risk level, calculated here. It is different from
"Low/Standard/High," the *official country* classification from Regulation
2025/1093. Country is one input into the supplier score, not the whole
determination — a supplier in a "standard" country (like Argentina) can
still score "Low" if nothing else adds risk.

## Country reference: exact source

`src/country_risk.py` transcribes the Annex of Commission Implementing
Regulation (EU) 2025/1093 (22/05/2025) directly from EUR-Lex, not a
third-party summary. The regulation explicitly lists **low** and **high**
risk countries; everything else is **standard** by omission (Article 1(2)
of the regulation itself). For the Southern Cone: Chile and Uruguay are
low risk; Argentina, Brazil, Paraguay, and Bolivia are standard (none of
the four appear in the Annex).

## Aggregation rules: consistency across a supplier's parcels

If a supplier's parcels carry conflicting qualitative signals (say, one
parcel reports indigenous peoples presence and another doesn't), the
system never silently discards the risk signal: it takes whichever value
implies more risk and logs it as a warning. Same rule for multiple
countries: the higher-risk one is used for scoring, with a warning.

## Test suite

`tests/build_synthetic_data.py` generates 9 synthetic suppliers, each
covering one component of the score (a clean one, an exact Low/Medium
boundary case, a compound high-risk case, one with a mitigating
certification, one spanning two countries, one with no `ProducerName`).
`tests/test_scoring.py` verifies every computed score matches the expected
value calculated by hand.

The web app's JavaScript scoring engine is a direct port of the Python
logic. Before being embedded into the HTML files in this package, it was
tested against the same scenarios using Node.js, confirming identical
output to the Python version.

## Known gaps (documented on purpose, not hidden)

- No PDF export yet (Product 1 has one). Same `reportlab` pattern could be
  added if visual consistency across the portfolio matters.
- Article 10 criteria that are inherently qualitative and don't lend
  themselves to automated scoring (e.g., clause (k), conclusions of the
  Commission's expert group) are out of scope, not simulated.

## Folder structure

```
producto3-scorecard-eudr/
├── main.py                  CLI entry point
├── requirements.txt
├── src/
│   ├── country_risk.py      Regulation 2025/1093 Annex, transcribed
│   ├── ingest.py            Tabular parsing + per-supplier aggregation
│   ├── scoring.py           The Article 10 scoring engine
│   ├── report.py            Markdown / Excel report generation
│   └── models.py            RiskFactor / SupplierScore data classes
├── tests/
│   ├── build_synthetic_data.py
│   └── test_scoring.py
├── data/
│   └── proveedores_sinteticos.xlsx   synthetic test data (9 suppliers)
├── outputs/example_run/     a sample report already generated, for reference
└── web/
    ├── scorecard_eudr_web.html          web app, Spanish
    ├── scorecard_eudr_web_en.html       web app, English
    ├── scorecard_input_ejemplo.xlsx     sample input to upload, Spanish
    └── scorecard_input_example.xlsx     sample input to upload, English
```
