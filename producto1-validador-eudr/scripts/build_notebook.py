import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# EUDR supplier geometry validator
### Demo: Product 1 of the EUDR portfolio

This notebook runs the validator against a supplier file that is **synthetic and deliberately dirty**
(set in real forestry areas of Corrientes and Misiones, Argentina, with fictitious names and
coordinates) to show the full flow: **ingestion → validation → conforming GeoJSON → quality report**.

See `README.md` for the regulatory detail of each check."""))

cells.append(nbf.v4.new_code_cell(
"""import sys, os
sys.path.insert(0, os.path.abspath(".."))

from main import run
import pandas as pd
pd.set_option("display.max_colwidth", 100)"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Run the validator on the supplier Excel spreadsheet

"Long" format: one row per vertex. 15 parcels, some valid, others with deliberately
seeded errors (missing coordinates, inconsistent country, overlapping
parcels, etc.)."""))

cells.append(nbf.v4.new_code_cell(
"""result = run("../data/synthetic_supplier_spreadsheet.xlsx", "../outputs/demo_excel")

print(f"Parcels in the output GeoJSON: {result['n_output_features']}")
print(f"Parcels excluded due to blocking error: {result['n_excluded_parcels']}")
print(f"Total findings: {len(result['findings'])}")"""))

cells.append(nbf.v4.new_markdown_cell("## 2. View the findings as a table"))

cells.append(nbf.v4.new_code_cell(
"""rows = [
    {"Severity": f.severity, "ParcelID": f.parcel_id, "Code": f.code,
     "Message": f.message, "Basis": f.reference}
    for f in sorted(result["findings"], key=lambda f: f.sort_key())
]
df_findings = pd.DataFrame(rows)
df_findings"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Filter only the blocking errors

These are the parcels that did **not** make it into `output.geojson`. They are documented here so
the supplier can correct them."""))

cells.append(nbf.v4.new_code_cell(
"""df_findings[df_findings["Severity"] == "ERROR"]"""))

cells.append(nbf.v4.new_markdown_cell("## 4. Inspect the output GeoJSON (conforming to v1.5)"))

cells.append(nbf.v4.new_code_cell(
"""import json

with open("../outputs/demo_excel/output.geojson", encoding="utf-8") as f:
    out = json.load(f)

print(f"type: {out['type']}")
print(f"features: {len(out['features'])}")
print()
print(json.dumps(out["features"][0], indent=2, ensure_ascii=False))"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 5. View the quality report (Markdown version)

The same content is available as `quality_report.pdf` and `quality_report.xlsx` in the
output folder, designed for a compliance team working in Excel/SAP, not in notebooks."""))

cells.append(nbf.v4.new_code_cell(
"""from IPython.display import Markdown, display

with open("../outputs/demo_excel/quality_report.md", encoding="utf-8") as f:
    display(Markdown(f.read()))"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 6. Repeat with the raw GeoJSON file

Exercises the other ingestion path: a supplier that already sends GeoJSON, but with structural
errors (unclosed polygons, prohibited geometry types, incorrect property
capitalization, etc.)."""))

cells.append(nbf.v4.new_code_cell(
"""result_geojson = run("../data/synthetic_geojson_input.geojson", "../outputs/demo_geojson")

print(f"Parcels in the output GeoJSON: {result_geojson['n_output_features']}")
print(f"Parcels excluded due to blocking error: {result_geojson['n_excluded_parcels']}")
print(f"Total findings: {len(result_geojson['findings'])}")"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 7. Test set: automatic verification

`tests/run_validation_test.py` runs this same flow against the 37 deliberately seeded errors and
verifies, code by code, that the validator detects all of them. It can be run from here:"""))

cells.append(nbf.v4.new_code_cell(
"""!cd .. && python3 tests/run_validation_test.py"""))

nb["cells"] = cells
with open("notebooks/demo.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("Notebook written to notebooks/demo.ipynb")
