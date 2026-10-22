# EUDR supplier geometry validator

Product 1 of Leonardo Scarpa's EUDR portfolio (GIS/forestry profile plus supplier
management). It validates and converts supplier parcel geolocation files
(Excel, CSV or GeoJSON) into the exact format required by the EUDR Information
System, and produces a quality report that a compliance team can read, not only
a remote sensing specialist.

**Try it in the browser (nothing to install):**
https://leonardoscarpa.github.io/validador-geometrias-eudr/producto1-validador-eudr/eudr_geometry_validator_en.html

**Why it exists:** the market research for this project showed that the teams
handling EUDR compliance today work in Excel and SAP, not in geospatial tools.
They receive supplier spreadsheets with coordinates and have no systematic way
to know whether that data can be submitted. This validator attacks exactly that
problem.

## What it does

1. **Reads** an input file in Excel (`.xlsx`), CSV or GeoJSON with supplier
   parcels (wood, Southern Cone).
2. **Runs 20 checks** against the official technical specification (see the
   table below), each one traceable to an article of the regulation or to an
   explicit rule of the GeoJSON v1.5 specification.
3. **Writes** `output.geojson`: only the parcels without blocking errors, in
   the exact format required by the Information System (`FeatureCollection`,
   WGS84, lon/lat order, at most 6 decimals, exact property capitalization).
4. **Generates a quality report** in three formats (Markdown, PDF and Excel)
   with every finding explained in plain language and its regulatory basis.

## Why it does NOT use Google Earth Engine

Earth Engine analyzes satellite imagery. This product validates **supplier
files**, not imagery. It is a data structure and geometry problem, not a
remote sensing one. Mixing it with Earth Engine would have complicated the
product without adding anything. Earth Engine enters in Product 2 (deforestation
screening), which does analyze imagery against these same, already validated
parcels.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py path/to/file.xlsx -o output_folder/
python main.py path/to/file.geojson -o output_folder/
python main.py path/to/file.csv -o output_folder/ --commodity wood
```

Output in `output_folder/`:
- `output.geojson`: ready parcels, ready to submit
- `quality_report.md`, `.pdf`, `.xlsx`: same content in three formats

A ready-made example of this output, generated from the synthetic spreadsheet,
is in `example_outputs/`.

## Tabular input schema (Excel / CSV)

"Long" format: one row per **vertex**. A parcel with 1 row is a point; with 3
or more rows it is a polygon (the first vertex does not need to be repeated at
the end, the converter closes the ring automatically).

| Column | Required | Description |
|---|---|---|
| `ParcelID` | Yes | Parcel identifier. Groups the rows of one polygon. |
| `Latitude`, `Longitude` | Yes | Decimal degrees, WGS84. |
| `VertexOrder` | Polygons only | Order of the vertex within the ring. |
| `ProducerCountry` | Yes | ISO 3166-1 alpha-2 code (e.g. `AR`). |
| `ProducerName`, `ProductionPlace` | No | Producer / farm identification. |
| `Area` | Recommended | Hectares. If omitted on a point, the official system assumes 4 ha. The validator flags it as a warning. |
| `CommonName`, `ScientificName` | Recommended (wood) | Required in the DDS by Art. 4 of Regulation 2024/3084. |

Column names are case-insensitive and accept a few aliases (`lat`, `lon`,
`country`, `hectares`, etc.; see `_TABULAR_ALIASES` in `src/ingest.py`).

## The 20 checks and their basis

| Code | Severity | What it checks | Basis |
|---|---|---|---|
| `STRUCT_ROOT` | Error | Root must be a `FeatureCollection` | EUDR GeoJSON File Description v1.5, RFC 7946 |
| `GEOM_TYPE_PROHIBITED` | Error | Rejects `LineString`, `MultiLineString`, `GeometryCollection` | v1.5, allowed/prohibited geometries |
| `COORD_OUT_OF_RANGE` | Error | Latitude outside ±90°, longitude outside ±180° | v1.5 |
| `COORD_NOT_NUMERIC` | Error | Non-numeric coordinate | v1.5 |
| `COORD_PRECISION` | Warning | More than 6 decimals, risk of duplicates through rounding | v1.5, precision |
| `POLY_NOT_CLOSED` | Error | First point differs from the last point of the ring | v1.5 |
| `POLY_TOO_FEW_VERTICES` | Error | Polygon with fewer than 4 coordinate pairs | v1.5 |
| `POLY_HAS_HOLES` | Error | Polygon with an interior ring (a "donut" hole) | v1.5, prohibited |
| `GEOM_SELF_INTERSECTION` | Error | Self-intersecting geometry (figure-eight shape) | v1.5 |
| `PARCELS_OVERLAP` | Error | Two parcels in the same file overlap in real area | v1.5 |
| `COUNTRY_MISSING` | Error | `ProducerCountry` is missing | v1.5, required property |
| `COUNTRY_INVALID_ISO` | Error | Not a valid ISO 3166-1 alpha-2 code | v1.5 |
| `COUNTRY_MISMATCH` | Error | The declared country does not match the real location of the geometry (detects, among other things, a lat/lon swap) | v1.5 |
| `AREA_NOT_NUMERIC` | Error | `Area` comes as text, not as a number | v1.5 |
| `AREA_MISMATCH` | Warning | Declared `Area` differs by more than 15% from the computed area of the geometry | v1.5 |
| `RULE_4HA_VIOLATION` | Error | Parcel larger than 4 ha declared as a `Point` instead of a polygon | Regulation (EU) 2023/1115, Art. 9 |
| `POINT_NO_AREA` | Warning | `Point` without `Area`: the system assumes 4 ha by default (silent risk) | v1.5 |
| `SPECIES_MISSING` | Warning | Common/scientific species name missing (wood) | Implementing Regulation (EU) 2024/3084, Art. 4 |
| `PROPERTY_CASE` | Warning | Property name with wrong capitalization: the system silently ignores it | v1.5, case-sensitive |
| `FILE_TOO_LARGE` | Error | File exceeds 25 MB per submission | v1.5 |
| `DUPLICATE_PARCEL_ID` | Error | Two parcels share the same `ParcelID` | Validator's own rule |

On top of these there are **ingestion** findings (tabular input only):
`ING_MISSING_LATLON`, `ING_TWO_VERTICES` (2 rows form neither a valid point nor
a valid polygon), `ING_METADATA_INCONSISTENT` (different metadata across the
vertices of one parcel), `ING_AUTOCLOSE` (informational note: the polygon was
closed automatically).

Multipart geometries (`MultiPolygon`, `MultiPoint`) are checked part by part for
closure, holes, vertex count and coordinate range/precision, and findings say
which part they refer to.

## What "ready" means

A parcel is **ready** if it has no finding of severity *Error*. Warnings do not
block submission but are documented. For example, a parcel can be "ready" and
still carry a `SPECIES_MISSING` warning. The output GeoJSON contains only the
ready parcels; those with a blocking error are left out and must be corrected at
the source.

## Known limitations (documented on purpose, not discovered by a reviewer)

- **`COUNTRY_MISMATCH` as a lat/lon swap detector**: for Southern Cone
  coordinates, both latitude and longitude fall within ±90°, so a range check
  alone cannot detect a lat/lon swap. What does detect it is that the swapped
  point falls outside the declared country. The geographic consistency check is
  therefore the real defense against that error, not the range check.
- **Reference borders**: the loaded country set (`data/cono_sur_countries.geojson`)
  covers Argentina, Brazil, Paraguay, Uruguay, Chile and Bolivia, with a
  tolerance of about 0.08° (~9 km) to compensate for border geometry
  simplification. A `ProducerCountry` outside that set produces a warning
  (`COUNTRY_OUT_OF_REFERENCE_SET`), not an error, because the validator has no
  way to verify it.
- **`DUPLICATE_PARCEL_ID` and aggregate counts**: if two records share the same
  `ParcelID`, the finding is emitted once per duplicated value (not once per
  record). For a file with duplicate IDs, "parcels with error" may not match the
  number of physical records affected exactly. The duplicate itself is already
  the signal that the ID must be corrected before resubmitting.
- **`AREA_MISMATCH`** uses an Albers Equal Area projection centered on the
  Southern Cone to compute hectares. It is an approximation good enough for the
  check, not a cadastral calculation.
- **`MultiPoint` and the 4 ha rule**: a `MultiPoint` is not yet evaluated
  against the 4 ha rule that applies to a single `Point`.
- **`ParcelID` in the output**: the output GeoJSON contains only the properties
  of the v1.5 set (plus species names). `ParcelID` is not part of that set, so it
  appears in the quality report but not in `output.geojson`.

## Test set

`tests/build_synthetic_data.py` generates two synthetic input files set in real
forestry areas of Corrientes and Misiones (fictitious coordinates and producer
names, never data from a real, identifiable supplier), with **37 deliberately
seeded errors** (one or more for every check in the table above) plus 3 control
parcels with no errors.

`tests/run_validation_test.py` runs the validator against both files and
automatically verifies that every seeded error was detected with the right
code, and that the control parcels triggered no findings. To regenerate and
run everything:

```bash
python tests/build_synthetic_data.py
python tests/run_validation_test.py
```

## Project structure

```
producto1-validador-eudr/
├── main.py                      # CLI
├── src/
│   ├── models.py                # Finding, IngestResult
│   ├── common.py                # shared constants and coordinate checks
│   ├── ingest.py                # GeoJSON / CSV / Excel -> internal GeoDataFrame
│   ├── validators.py            # the 20 checks
│   ├── geojson_writer.py        # output conforming to v1.5
│   └── report.py                # Markdown / PDF / Excel report
├── data/
│   ├── cono_sur_countries.geojson           # reference borders (AR, BR, PY, UY, CL, BO)
│   ├── synthetic_geojson_input.geojson      # synthetic dirty GeoJSON input
│   └── synthetic_supplier_spreadsheet.xlsx  # synthetic dirty spreadsheet input
├── tests/
│   ├── build_synthetic_data.py
│   ├── run_validation_test.py
│   └── expected_codes.json
├── notebooks/
│   └── demo.ipynb
├── example_outputs/             # sample output already generated (from the spreadsheet)
└── eudr_geometry_validator_en.html   # the browser version
```

## Next steps in the portfolio

This product fixes the data model and output format that Product 2
(deforestation screening against JRC GFC2020 V3 in Earth Engine) and Product 3
(supplier risk scorecard) build on. See the root `README.md` of the repository.
