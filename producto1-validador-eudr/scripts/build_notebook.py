import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Validador de geometrías de proveedores — EUDR
### Demo — Producto 1 del portfolio EUDR

Este notebook corre el validador contra un archivo de proveedores **sintético y sucio a propósito**
(ambientado en zonas forestales reales de Corrientes y Misiones, Argentina, con nombres y coordenadas
ficticias) para mostrar el flujo completo: **ingesta → validación → GeoJSON conforme → informe de calidad**.

Ver `README.md` para el detalle normativo de cada chequeo."""))

cells.append(nbf.v4.new_code_cell(
"""import sys, os
sys.path.insert(0, os.path.abspath(".."))

from main import run
import pandas as pd
pd.set_option("display.max_colwidth", 100)"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 1. Correr el validador sobre la planilla Excel de proveedores

Formato "largo": una fila por vértice. 15 parcelas, algunas válidas, otras con errores
sembrados a propósito (falta de coordenadas, país inconsistente, superposición entre
parcelas, etc.)."""))

cells.append(nbf.v4.new_code_cell(
"""result = run("../data/synthetic_planilla_proveedores.xlsx", "../outputs/demo_excel")

print(f"Parcelas en el GeoJSON de salida: {result['n_output_features']}")
print(f"Parcelas excluidas por error bloqueante: {result['n_excluded_parcels']}")
print(f"Hallazgos totales: {len(result['findings'])}")"""))

cells.append(nbf.v4.new_markdown_cell("## 2. Ver los hallazgos como tabla"))

cells.append(nbf.v4.new_code_cell(
"""rows = [
    {"Severidad": f.severity, "ParcelID": f.parcel_id, "Código": f.code,
     "Mensaje": f.message, "Fundamento": f.reference}
    for f in sorted(result["findings"], key=lambda f: f.sort_key())
]
df_findings = pd.DataFrame(rows)
df_findings"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 3. Filtrar solo los errores bloqueantes

Estas son las parcelas que **no** entraron al `output.geojson` — quedaron documentadas acá para que
el proveedor las corrija."""))

cells.append(nbf.v4.new_code_cell(
"""df_findings[df_findings["Severidad"] == "ERROR"]"""))

cells.append(nbf.v4.new_markdown_cell("## 4. Inspeccionar el GeoJSON de salida (conforme a v1.5)"))

cells.append(nbf.v4.new_code_cell(
"""import json

with open("../outputs/demo_excel/output.geojson", encoding="utf-8") as f:
    out = json.load(f)

print(f"type: {out['type']}")
print(f"features: {len(out['features'])}")
print()
print(json.dumps(out["features"][0], indent=2, ensure_ascii=False))"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 5. Ver el informe de calidad (versión Markdown)

Mismo contenido está disponible en `informe_calidad.pdf` y `informe_calidad.xlsx` dentro de la
carpeta de salida — pensados para un equipo de compliance que trabaja en Excel/SAP, no en notebooks."""))

cells.append(nbf.v4.new_code_cell(
"""from IPython.display import Markdown, display

with open("../outputs/demo_excel/informe_calidad.md", encoding="utf-8") as f:
    display(Markdown(f.read()))"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 6. Repetir con el archivo GeoJSON crudo

Ejercita el otro camino de ingesta: un proveedor que ya manda GeoJSON, pero con errores
estructurales (polígonos sin cerrar, tipos de geometría prohibidos, capitalización de
propiedades incorrecta, etc.)."""))

cells.append(nbf.v4.new_code_cell(
"""result_geojson = run("../data/synthetic_geojson_input.geojson", "../outputs/demo_geojson")

print(f"Parcelas en el GeoJSON de salida: {result_geojson['n_output_features']}")
print(f"Parcelas excluidas por error bloqueante: {result_geojson['n_excluded_parcels']}")
print(f"Hallazgos totales: {len(result_geojson['findings'])}")"""))

cells.append(nbf.v4.new_markdown_cell(
"""## 7. Set de prueba: verificación automática

`tests/run_validation_test.py` corre esto mismo contra los 37 errores sembrados a propósito y
verifica, código por código, que el validador los detecta todos. Se puede correr desde acá:"""))

cells.append(nbf.v4.new_code_cell(
"""!cd .. && python3 tests/run_validation_test.py"""))

nb["cells"] = cells
with open("notebooks/demo.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("Notebook escrito en notebooks/demo.ipynb")
