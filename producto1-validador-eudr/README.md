# Validador de geometrías de proveedores — EUDR

Producto 1 del portfolio EUDR de Leo Nahuel Romero (perfil GIS/forestal + gestión de
proveedores). Valida y convierte archivos de geolocalización de parcelas de
proveedores (Excel, CSV o GeoJSON) al formato exacto que exige el Information
System de la EUDR, y genera un informe de calidad legible por un equipo de
compliance — no por un especialista en teledetección.

**Por qué existe:** el relevamiento de mercado del proyecto mostró que los
equipos que hoy gestionan compliance EUDR trabajan en Excel y SAP, no en
herramientas geoespaciales. Reciben planillas de proveedores con coordenadas y
no tienen forma sistemática de saber si esos datos son presentables. Este
validador ataca exactamente ese problema.

## Qué hace

1. **Lee** un archivo de entrada en Excel (`.xlsx`), CSV o GeoJSON con
   parcelas de proveedores (madera, Cono Sur).
2. **Corre 20 chequeos** contra la especificación técnica oficial (ver tabla
   abajo), cada uno trazable a un artículo del reglamento o a una regla
   explícita de la especificación GeoJSON v1.5.
3. **Escribe** `output.geojson`: únicamente las parcelas sin errores
   bloqueantes, en el formato exacto que exige el Information System
   (`FeatureCollection`, WGS84, orden lon/lat, ≤6 decimales, propiedades con
   capitalización exacta).
4. **Genera un informe de calidad** en tres formatos — Markdown, PDF y Excel —
   con cada hallazgo explicado en lenguaje simple y su fundamento normativo.

## Por qué NO usa Google Earth Engine

Earth Engine sirve para analizar imágenes satelitales. Este producto valida
**archivos de proveedores**, no imágenes — es un problema de estructura de
datos y geometría, no de teledetección. Mezclarlo con GEE habría complicado el
producto sin sumar nada. GEE entra en el Producto 2 (screening de
deforestación), que sí analiza imágenes contra estas mismas parcelas ya
validadas.

## Instalación

```bash
pip install geopandas shapely pyproj pandas openpyxl reportlab pycountry
```

## Uso

```bash
python main.py ruta/al/archivo.xlsx -o carpeta_salida/
python main.py ruta/al/archivo.geojson -o carpeta_salida/
python main.py ruta/al/archivo.csv -o carpeta_salida/ --commodity madera
```

Salida en `carpeta_salida/`:
- `output.geojson` — parcelas aptas, listas para presentar
- `informe_calidad.md`, `.pdf`, `.xlsx` — mismo contenido en tres formatos

## Esquema de entrada tabular (Excel / CSV)

Formato "largo": una fila por **vértice**. Una parcela con 1 fila = punto; con
3 o más filas = polígono (no hace falta repetir el primer vértice al final,
el conversor cierra el anillo automáticamente).

| Columna | Obligatoria | Descripción |
|---|---|---|
| `ParcelID` | Sí | Identificador de la parcela. Agrupa las filas de un mismo polígono. |
| `Latitude`, `Longitude` | Sí | Grados decimales, WGS84. |
| `VertexOrder` | Solo para polígonos | Orden del vértice dentro del anillo. |
| `ProducerCountry` | Sí | Código ISO 3166-1 alpha-2 (ej. `AR`). |
| `ProducerName`, `ProductionPlace` | No | Identificación del productor/predio. |
| `Area` | Recomendada | Hectáreas. Si se omite en un punto, el sistema oficial asume 4 ha — el validador lo marca como advertencia. |
| `CommonName`, `ScientificName` | Recomendada (madera) | Exigido en la DDS por el Art. 4 del Reglamento 2024/3084. |

Los nombres de columna no distinguen mayúsculas/minúsculas y aceptan alias en
español (`pais`, `superficie`, `lugar`, etc. — ver `src/ingest.py`,
`_TABULAR_ALIASES`).

## Los 20 chequeos y su fundamento

| Código | Severidad | Qué chequea | Fundamento |
|---|---|---|---|
| `STRUCT_ROOT` | Error | Raíz debe ser `FeatureCollection` | EUDR GeoJSON File Description v1.5 — RFC 7946 |
| `GEOM_TYPE_PROHIBITED` | Error | Rechaza `LineString`, `MultiLineString`, `GeometryCollection` | v1.5 — Geometrías permitidas/prohibidas |
| `COORD_OUT_OF_RANGE` | Error | Lat fuera de ±90°, lon fuera de ±180° | v1.5 |
| `COORD_NOT_NUMERIC` | Error | Coordenada no numérica | v1.5 |
| `COORD_PRECISION` | Advertencia | Más de 6 decimales → riesgo de duplicados por redondeo | v1.5 — Precisión |
| `POLY_NOT_CLOSED` | Error | Primer punto ≠ último punto del anillo | v1.5 |
| `POLY_TOO_FEW_VERTICES` | Error | Polígono con menos de 4 pares de coordenadas | v1.5 |
| `POLY_HAS_HOLES` | Error | Polígono con anillo interior (hueco tipo "dona") | v1.5 — prohibido |
| `GEOM_SELF_INTERSECTION` | Error | Geometría auto-intersectada (tipo "ocho") | v1.5 |
| `PARCELS_OVERLAP` | Error | Dos parcelas del mismo archivo se superponen en área real | v1.5 |
| `COUNTRY_MISSING` | Error | Falta `ProducerCountry` | v1.5 — propiedad obligatoria |
| `COUNTRY_INVALID_ISO` | Error | No es un código ISO 3166-1 alpha-2 válido | v1.5 |
| `COUNTRY_MISMATCH` | Error | El país declarado no coincide con la ubicación real de la geometría (detecta, entre otras cosas, inversión lat/lon) | v1.5 |
| `AREA_NOT_NUMERIC` | Error | `Area` viene como texto, no como número | v1.5 |
| `AREA_MISMATCH` | Advertencia | `Area` declarada difiere >15% del área calculada de la geometría | v1.5 |
| `RULE_4HA_VIOLATION` | Error | Parcela de más de 4 ha declarada como `Point` en vez de polígono | Reglamento (UE) 2023/1115, Art. 9 |
| `POINT_NO_AREA` | Advertencia | `Point` sin `Area` → el sistema asume 4 ha por defecto (riesgo silencioso) | v1.5 |
| `SPECIES_MISSING` | Advertencia | Falta nombre común/científico de la especie (madera) | Reglamento de Ejecución (UE) 2024/3084, Art. 4 |
| `PROPERTY_CASE` | Advertencia | Nombre de propiedad con capitalización incorrecta → el sistema la ignora en silencio | v1.5 — sensible a mayúsculas |
| `FILE_TOO_LARGE` | Error | Archivo supera 25 MB por presentación | v1.5 |
| `DUPLICATE_PARCEL_ID` | Error | Dos parcelas comparten el mismo `ParcelID` | Regla propia del validador |

A estos se suman hallazgos de **ingesta** (solo para entrada tabular):
`ING_MISSING_LATLON`, `ING_TWO_VERTICES` (2 filas no forman ni punto ni
polígono válido), `ING_METADATA_INCONSISTENT` (metadatos distintos entre
vértices de una misma parcela), `ING_AUTOCLOSE` (nota informativa: el
polígono se cerró automáticamente).

## Qué significa "apto"

Una parcela es **apta** si no tiene ningún hallazgo de severidad *Error*.
Las advertencias no bloquean la presentación pero sí quedan documentadas —
por ejemplo, una parcela puede ser "apta" y aun así tener una advertencia de
`SPECIES_MISSING`. El GeoJSON de salida incluye únicamente las parcelas
aptas; las que tienen error bloqueante quedan fuera y deben corregirse en
origen.

## Limitaciones conocidas (documentadas a propósito, no descubiertas por un revisor)

- **`COUNTRY_MISMATCH` como detector de inversión lat/lon**: para coordenadas
  del Cono Sur, tanto la latitud como la longitud caen dentro de ±90°, así que
  un chequeo de rango solo no detecta una inversión lat/lon. Lo que sí la
  detecta es que el punto invertido cae fuera del país declarado — por eso el
  chequeo de coherencia geográfica es la defensa real contra ese error, no el
  chequeo de rango.
- **Fronteras de referencia**: el set de países cargado (`data/cono_sur_countries.geojson`)
  cubre Argentina, Brasil, Paraguay, Uruguay, Chile y Bolivia, con una
  tolerancia de ~0.08° (~9 km) para compensar la simplificación de la
  geometría de frontera. Un `ProducerCountry` fuera de ese set genera una
  advertencia (`COUNTRY_OUT_OF_REFERENCE_SET`), no un error, porque el
  validador no tiene cómo verificarlo.
- **`DUPLICATE_PARCEL_ID` y los conteos agregados**: si dos registros
  comparten el mismo `ParcelID`, el hallazgo se emite una vez por valor
  duplicado (no una vez por registro). En el caso puntual de un archivo con
  IDs duplicados, "parcelas con error" puede no coincidir exactamente con la
  cantidad de registros físicos afectados — el propio duplicado ya es la señal
  de que hay que corregir el ID antes de re-presentar.
- **`AREA_MISMATCH`** usa una proyección Albers Equal Area centrada en el Cono
  Sur para calcular hectáreas; es una aproximación suficiente para el
  chequeo, no un cálculo catastral.

## Set de prueba

`tests/build_synthetic_data.py` genera dos archivos de entrada sintéticos,
ambientados en zonas forestales reales de Corrientes y Misiones (coordenadas y
nombres de productor ficticios — nunca datos de un proveedor real
identificable), con **37 errores sembrados a propósito** (uno o más por cada
chequeo de la tabla de arriba) más 3 parcelas control sin ningún error.

`tests/run_validation_test.py` corre el validador contra ambos archivos y
verifica automáticamente que cada error sembrado fue detectado con el código
correcto, y que las parcelas control no dispararon ningún hallazgo. Para
volver a generar y correr todo:

```bash
python tests/build_synthetic_data.py
python tests/run_validation_test.py
```

## Estructura del proyecto

```
producto1-validador-eudr/
├── main.py                      # CLI
├── src/
│   ├── models.py                # Finding, IngestResult
│   ├── common.py                # constantes y chequeos de coordenadas compartidos
│   ├── ingest.py                # GeoJSON / CSV / Excel -> GeoDataFrame interno
│   ├── validators.py            # los 20 chequeos
│   ├── geojson_writer.py        # salida conforme a v1.5
│   └── report.py                # informe en Markdown / PDF / Excel
├── data/
│   └── cono_sur_countries.geojson   # fronteras de referencia (AR, BR, PY, UY, CL, BO)
├── tests/
│   ├── build_synthetic_data.py
│   ├── run_validation_test.py
│   └── expected_codes.json
├── notebooks/
│   └── demo.ipynb
└── ejemplos_salida/              # salida de ejemplo ya generada (planilla y GeoJSON)
```

## Próximos pasos del portfolio

Este producto fija el modelo de datos y el formato de salida que van a
reutilizar el Producto 2 (screening de deforestación contra JRC GFC2020 V3 en
Earth Engine) y el Producto 3 (scorecard de riesgo por proveedor). Ver
`plan-productos-portfolio.md` en la raíz del proyecto.
