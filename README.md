# EUDR Compliance Portfolio

Three working tools for the EU Deforestation Regulation (Regulation (EU)
2023/1115), built around real regulatory text and real data, not mockups.
Each one targets a specific, documented step of the compliance process:
geometry validation, risk assessment (Article 10), and deforestation
screening against the 31 December 2020 cutoff (Article 9).

Enforcement for large and medium operators begins **30 December 2026**.

## Try them now

No install, no account, no file required to just look around. Click any
link below, it opens directly in your browser.

| | Product | What it does | Try it |
|---|---|---|---|
| 1 | **Geometry Validator** | Checks supplier parcel files (Excel, CSV, or GeoJSON) against the EU's official technical spec for the EUDR Information System: coordinate precision, the 4-hectare polygon rule, inverted lat/lon coordinates, and 17 other checks, each one explained in plain language with the regulation article behind it. | [**Open the app**](https://leonardoscarpa.github.io/validador-geometrias-eudr/producto1-validador-eudr/eudr_geometry_validator_en.html) |
| 2 | **Deforestation Screening** | Checks parcels against the cutoff date using real Google Earth Engine satellite data (JRC Tropical Moist Forest), not a single 2020 snapshot. Shows real results from an actual run, including a genuinely surprising one. | [**View the results**](https://leonardoscarpa.github.io/validador-geometrias-eudr/producto2_resultados_en.html) |
| 3 | **Supplier Risk Scorecard** | Turns a supplier list into a documented Article 10 risk score, color-coded on an interactive map with contact details on hand, country classification pulled straight from the EU's own regulation (2025/1093). | [**Open the app**](https://leonardoscarpa.github.io/validador-geometrias-eudr/scorecard_eudr_web_en.html) |

Products 1 and 3 are fully interactive: upload your own file, or use the
sample data linked below. Product 2 can't run live in a browser (it needs
an authenticated Earth Engine session), so it shows the real output of an
actual run instead of a demo.

**No file handy to test with?**

- Product 1 sample data: [synthetic_planilla_proveedores.xlsx](https://raw.githubusercontent.com/leonardoscarpa/validador-geometrias-eudr/main/producto1-validador-eudr/data/synthetic_planilla_proveedores.xlsx)
- Product 3 sample data: [scorecard_input_example.xlsx](https://raw.githubusercontent.com/leonardoscarpa/validador-geometrias-eudr/main/producto3-scorecard-eudr/web/scorecard_input_example.xlsx)

## Why these three, specifically

Compliance teams handling the EUDR today mostly work in Excel. Coordinates
get copied by hand, risk gets assessed by judgment calls nobody writes
down, and satellite verification (where it exists at all) is a black box
bought from a vendor. These three tools attack that gap directly: they
take the same spreadsheet-based workflow these teams already use, and add
the structure, citations, and satellite verification that make a decision
defensible to an inspector.

## The methodology, briefly

- **No area threshold.** Article 9 disqualifies a parcel automatically at
  any trace of deforestation, not at some tolerated percentage. All three
  tools mirror that rule exactly, even though it makes for a less
  forgiving demo than a threshold-based one would.
- **Country risk vs. supplier risk, kept separate.** Product 3 scores each
  *supplier* Low/Medium/High. That is a different scale from the
  *country's* official Low/Standard/High classification under Regulation
  2025/1093. Conflating the two would be a real, noticeable error in a
  compliance interview, so the tool and its documentation keep them
  visibly distinct.
- **Wood-specific rules, applied.** Article 2 requires wood specifically
  to be harvested without inducing forest degradation after the cutoff,
  not just grown on land that wasn't deforested. Product 2 checks both
  deforestation and degradation layers for exactly this reason.
- **Honest about what a "compliant" result means.** A screening result
  reflects "no change detected in this specific area," not a guarantee
  for an entire region. Each product's own README documents this, and the
  UI itself says so, not just the fine print.

Full methodology, data sources, and known limitations for each product are
documented in its own folder: [`producto1-validador-eudr/`](producto1-validador-eudr/),
[`producto2-ScreeningDeforestation-EUDR/`](producto2-ScreeningDeforestation-EUDR/),
[`producto3-scorecard-eudr/`](producto3-scorecard-eudr/).

## Background

Built by Leonardo Scarpa, whose background sits at the intersection of
conservation biology, geomatics/GIS, and supplier management. This
portfolio is where the three come together.

Open to feedback, and happy to talk compliance, supply chain traceability,
or roles at this intersection.
