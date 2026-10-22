"""
Generates two synthetic input files set in real forestry areas of
Corrientes and Misiones (Argentina) but with fictitious coordinates and
producer names. Never data from a real, identifiable supplier.

1. data/synthetic_geojson_input.geojson  -> exercises the raw GeoJSON path
2. data/synthetic_supplier_spreadsheet.xlsx -> exercises the tabular path

The "control" parcels (no seeded errors) use a side_deg computed with
side_deg_for_area_ha() so the declared area matches the real geodesic
area, so the AREA_MISMATCH check does not fire false positives on the
controls.

It also writes tests/expected_codes.json with the finding codes that
each parcel SHOULD trigger.
"""

import json
import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

ANCHOR_CTES = (-28.05, -56.00)   # near Virasoro, Corrientes
ANCHOR_MSNS = (-26.40, -54.60)   # near Eldorado, Misiones


def side_deg_for_area_ha(lat, area_ha):
    """Side (in degrees) of a square centered at `lat` whose approximate
    geodesic area is `area_ha` hectares. Simple spherical approximation,
    enough to calibrate synthetic data (not for regulatory use)."""
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat))
    area_km2 = area_ha / 100.0
    # side_lat_deg * side_lon_deg * km_per_deg_lat * km_per_deg_lon = area_km2
    # with side_lat_deg == side_lon_deg == side:
    side = math.sqrt(area_km2 / (km_per_deg_lat * km_per_deg_lon))
    return side


expected = {}


def box_ha(anchor, dlat, dlon, area_ha, ndigits=6):
    """Square box of area_ha hectares. Coordinates are rounded to
    `ndigits` decimals (as a real supplier would do) so these
    parcelas NO disparen COORD_PRECISION por accidente — ese hallazgo se
    reserva para el caso de prueba dedicado (CTES-009-PRECISION)."""
    lat0 = anchor[0] + dlat
    lon0 = anchor[1] + dlon
    side = side_deg_for_area_ha(lat0, area_ha)
    h = side / 2
    ring = [
        (lon0 - h, lat0 - h), (lon0 + h, lat0 - h),
        (lon0 + h, lat0 + h), (lon0 - h, lat0 + h), (lon0 - h, lat0 - h),
    ]
    return [(round(lon, ndigits), round(lat, ndigits)) for lon, lat in ring]


# ---------------------------------------------------------------------------
# 1) Raw GeoJSON
# ---------------------------------------------------------------------------

features = []


def add_feature(pid, geometry, props, codes):
    p = {"ParcelID": pid}
    p.update(props)
    features.append({"type": "Feature", "properties": p, "geometry": geometry})
    expected[pid] = codes


# --- valid controls ---
add_feature("CTES-001", {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.00, 0.00, 4.2)]},
            {"ProducerName": "Forestal Don Aparicio", "ProducerCountry": "AR",
             "ProductionPlace": "Establecimiento La Loma", "Area": 4.2,
             "CommonName": "Pino", "ScientificName": "Pinus elliottii"}, [])

add_feature("CTES-002", {"type": "Point", "coordinates": [-56.02, -28.03]},
            {"ProducerName": "Forestal Don Aparicio", "ProducerCountry": "AR",
             "ProductionPlace": "Potrero Norte", "Area": 2.3,
             "CommonName": "Eucalipto", "ScientificName": "Eucalyptus grandis"}, [])

# --- prohibited geometry types ---
add_feature("CTES-003-LINESTRING",
            {"type": "LineString", "coordinates": [[-56.01, -28.06], [-56.00, -28.05]]},
            {"ProducerCountry": "AR", "ProductionPlace": "Linde Este", "Area": 3},
            ["GEOM_TYPE_PROHIBITED"])

add_feature("CTES-004-GEOMCOLLECTION",
            {"type": "GeometryCollection", "geometries": [
                {"type": "Point", "coordinates": [-56.0, -28.05]}]},
            {"ProducerCountry": "AR", "ProductionPlace": "Lote Mixto", "Area": 3},
            ["GEOM_TYPE_PROHIBITED"])

# --- polygon with a hole (outer 10ha, inner 2ha; we declare the approximate net area) ---
outer = box_ha(ANCHOR_CTES, 0.02, 0.00, 10.0)
inner = box_ha(ANCHOR_CTES, 0.02, 0.00, 2.0)
add_feature("CTES-005-HOLE", {"type": "Polygon", "coordinates": [outer, inner]},
            {"ProducerCountry": "AR", "ProductionPlace": "Rodal con isla nativa", "Area": 8},
            ["POLY_HAS_HOLES"])

# --- unclosed polygon (4ha) ---
ring_unclosed = box_ha(ANCHOR_CTES, 0.03, 0.00, 4.0)[:-1]
add_feature("CTES-006-UNCLOSED", {"type": "Polygon", "coordinates": [ring_unclosed]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 7", "Area": 4},
            ["POLY_NOT_CLOSED"])

# --- self-intersecting polygon (bowtie), closed ---
lat0, lon0 = ANCHOR_CTES[0] + 0.04, ANCHOR_CTES[1]
s = side_deg_for_area_ha(lat0, 4.0)
h = round(s / 2, 6)
bowtie = [
    (lon0 - h, lat0 - h), (lon0 + h, lat0 + h),
    (lon0 + h, lat0 - h), (lon0 - h, lat0 + h), (lon0 - h, lat0 - h),
]
add_feature("CTES-007-SELFINTERSECT", {"type": "Polygon", "coordinates": [bowtie]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 8", "Area": 4},
            ["GEOM_SELF_INTERSECTION"])

# --- incorrect property capitalization (4ha) ---
add_feature("CTES-008-PROPCASE",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.05, 0.00, 4.0)]},
            {"producercountry": "AR", "productionplace": "Cuartel 9", "area": 4},
            ["PROPERTY_CASE"])

# --- more than 6 decimals (genuine 9-decimal GPS precision coordinates) ---
lat0, lon0 = ANCHOR_CTES[0] + 0.06, ANCHOR_CTES[1]
s = side_deg_for_area_ha(lat0, 4.0)
h = s / 2
extra = 0.0000001234567891  # pushes to >6 decimals genuinely, not through rounding
ring_precise = [
    (lon0 - h + extra, lat0 - h + extra), (lon0 + h + extra, lat0 - h + extra),
    (lon0 + h + extra, lat0 + h + extra), (lon0 - h + extra, lat0 + h + extra),
    (lon0 - h + extra, lat0 - h + extra),
]
add_feature("CTES-009-PRECISION", {"type": "Polygon", "coordinates": [ring_precise]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 10", "Area": 4},
            ["COORD_PRECISION"])

# --- declared country does not match the real geometry (point in Brazil) ---
add_feature("CTES-010-COUNTRYMISMATCH", {"type": "Point", "coordinates": [-53.45, -24.90]},
            {"ProducerCountry": "AR", "ProductionPlace": "Supuesto lote correntino", "Area": 3},
            ["COUNTRY_MISMATCH"])

# --- invalid ISO code (4ha) ---
add_feature("CTES-011-INVALIDISO",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.07, 0.00, 4.0)]},
            {"ProducerCountry": "ARG", "ProductionPlace": "Cuartel 11", "Area": 4},
            ["COUNTRY_INVALID_ISO"])

# --- missing ProducerCountry (4ha) ---
add_feature("CTES-012-COUNTRYMISSING",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.08, 0.00, 4.0)]},
            {"ProductionPlace": "Cuartel 12", "Area": 4}, ["COUNTRY_MISSING"])

# --- Area as text (real 4ha, declared as text) ---
add_feature("CTES-013-AREASTRING",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.09, 0.00, 4.0)]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 13", "Area": "doce"},
            ["AREA_NOT_NUMERIC"])

# --- Point without Area ---
add_feature("CTES-014-POINT-NOAREA", {"type": "Point", "coordinates": [-56.0, -28.10]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 14"},
            ["POINT_NO_AREA"])

# --- 4 ha rule violated (Point with Area > 4) ---
add_feature("CTES-015-4HAVIOLATION", {"type": "Point", "coordinates": [-56.01, -28.11]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 15", "Area": 15},
            ["RULE_4HA_VIOLATION"])

# --- polygon with fewer than 4 pairs (degenerate) ---
lat0, lon0 = ANCHOR_CTES[0] + 0.10, ANCHOR_CTES[1]
degenerate = [(lon0 - 0.003, lat0), (lon0 + 0.003, lat0), (lon0 - 0.003, lat0)]
add_feature("CTES-016-TOOFEWVERTICES", {"type": "Polygon", "coordinates": [degenerate]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 16", "Area": 4},
            ["POLY_TOO_FEW_VERTICES"])

# --- two overlapping parcels (10ha each, shifted 40% of the side to
#     guarantee a real overlap regardless of latitude) ---
_side_ctes_overlap = side_deg_for_area_ha(ANCHOR_CTES[0] + 0.11, 10.0)
ring_a = box_ha(ANCHOR_CTES, 0.11, 0.000, 10.0)
ring_b = box_ha(ANCHOR_CTES, 0.11, _side_ctes_overlap * 0.4, 10.0)
add_feature("CTES-017-OVERLAP-A", {"type": "Polygon", "coordinates": [ring_a]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 17A", "Area": 10},
            ["PARCELS_OVERLAP"])
add_feature("CTES-017-OVERLAP-B", {"type": "Polygon", "coordinates": [ring_b]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 17B", "Area": 10},
            ["PARCELS_OVERLAP"])

# --- missing common/scientific name (wood), 4ha ---
add_feature("CTES-018-NOSPECIES",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.12, 0.00, 4.0)]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 18", "Area": 4},
            ["SPECIES_MISSING"])

# --- coordinate out of range ---
add_feature("CTES-019-OUTOFRANGE", {"type": "Point", "coordinates": [-56.0, -95.0]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 19", "Area": 2},
            ["COORD_OUT_OF_RANGE"])

# --- duplicate ParcelID (two features, same id, 4ha each) ---
ring1 = box_ha(ANCHOR_CTES, 0.13, 0.00, 4.0)
features.append({"type": "Feature", "properties": {
    "ParcelID": "CTES-020-DUP", "ProducerCountry": "AR",
    "ProductionPlace": "Cuartel 20 (primera)", "Area": 4,
    "CommonName": "Pino", "ScientificName": "Pinus taeda"},
    "geometry": {"type": "Polygon", "coordinates": [ring1]}})
ring2 = box_ha(ANCHOR_CTES, 0.14, 0.00, 4.0)
features.append({"type": "Feature", "properties": {
    "ParcelID": "CTES-020-DUP", "ProducerCountry": "AR",
    "ProductionPlace": "Cuartel 20 (segunda, error de carga)", "Area": 4,
    "CommonName": "Pino", "ScientificName": "Pinus taeda"},
    "geometry": {"type": "Polygon", "coordinates": [ring2]}})
expected["CTES-020-DUP"] = ["DUPLICATE_PARCEL_ID"]

# --- declared area very different from the real area (15ha geometry, declared 2ha) ---
add_feature("CTES-021-AREAMISMATCH",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.15, 0.00, 15.0)]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 21", "Area": 2,
             "CommonName": "Pino", "ScientificName": "Pinus taeda"},
            ["AREA_MISMATCH"])

fc = {"type": "FeatureCollection", "features": features}
geojson_path = os.path.join(DATA_DIR, "synthetic_geojson_input.geojson")
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(fc, f, ensure_ascii=False, indent=2)
print(f"Escrito {geojson_path} ({len(features)} features)")


# ---------------------------------------------------------------------------
# 2) Excel spreadsheet (long tabular format)
# ---------------------------------------------------------------------------

rows = []
tab_expected = {}


def add_point_row(pid, lat, lon, country="AR", name="Yerbatera San Ignacio",
                   place="", area=None, common=None, sci=None):
    rows.append(dict(ParcelID=pid, VertexOrder=None, Latitude=lat, Longitude=lon,
                      ProducerCountry=country, ProducerName=name, ProductionPlace=place,
                      Area=area, CommonName=common, ScientificName=sci))


def add_polygon_rows(pid, vertices_latlon, country="AR", name="Yerbatera San Ignacio",
                      place="", area=None, common=None, sci=None, order=None):
    order = order or list(range(1, len(vertices_latlon) + 1))
    for o, (lat, lon) in zip(order, vertices_latlon):
        rows.append(dict(ParcelID=pid, VertexOrder=o, Latitude=lat, Longitude=lon,
                          ProducerCountry=country, ProducerName=name, ProductionPlace=place,
                          Area=area, CommonName=common, ScientificName=sci))


def rect_vertices_latlon(anchor, dlat, dlon, area_ha, ndigits=6):
    """4 vertices (lat, lon) of a rectangle of area_ha hectares, WITHOUT repeating
    the first one at the end (so we exercise auto-closing in ingestion).
    Redondeadas a `ndigits` decimales por el mismo motivo que en box_ha()."""
    lat0 = anchor[0] + dlat
    lon0 = anchor[1] + dlon
    side = side_deg_for_area_ha(lat0, area_ha)
    h = side / 2
    verts = [(lat0 - h, lon0 - h), (lat0 - h, lon0 + h),
             (lat0 + h, lon0 + h), (lat0 + h, lon0 - h)]
    return [(round(lat, ndigits), round(lon, ndigits)) for lat, lon in verts]


# --- valid controls ---
add_point_row("MSNS-001", ANCHOR_MSNS[0], ANCHOR_MSNS[1] + 0.01, area=1.8,
              place="Chacra 3", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-001"] = []

verts = rect_vertices_latlon(ANCHOR_MSNS, 0.00, 0.03, 4.3)
add_polygon_rows("MSNS-002", [verts[2], verts[0], verts[3], verts[1]],
                  order=[3, 1, 4, 2], area=4.3, place="Chacra 5",
                  common="Eucalipto", sci="Eucalyptus grandis")
tab_expected["MSNS-002"] = ["ING_AUTOCLOSE"]

# --- missing lat/lon ---
rows.append(dict(ParcelID="MSNS-003-MISSINGLATLON", VertexOrder=None, Latitude=None,
                  Longitude=ANCHOR_MSNS[1], ProducerCountry="AR", ProducerName="Yerbatera San Ignacio",
                  ProductionPlace="Chacra 7", Area=2, CommonName="Pino", ScientificName="Pinus taeda"))
tab_expected["MSNS-003-MISSINGLATLON"] = ["ING_MISSING_LATLON"]

# --- exactly 2 vertices ---
add_polygon_rows("MSNS-004-TWOVERTICES", [
    (ANCHOR_MSNS[0] + 0.05, ANCHOR_MSNS[1]), (ANCHOR_MSNS[0] + 0.051, ANCHOR_MSNS[1] + 0.001)],
    area=3, place="Chacra 9")
tab_expected["MSNS-004-TWOVERTICES"] = ["ING_TWO_VERTICES"]

# --- inconsistent metadata across vertices ---
verts = rect_vertices_latlon(ANCHOR_MSNS, 0.06, 0.00, 4.5)
for o, (lat, lon) in enumerate(verts, start=1):
    rows.append(dict(ParcelID="MSNS-005-INCONSISTENT", VertexOrder=o, Latitude=lat, Longitude=lon,
                      ProducerCountry=("AR" if o < 3 else "BR"), ProducerName="Yerbatera San Ignacio",
                      ProductionPlace="Chacra 11", Area=4.5, CommonName="Pino", ScientificName="Pinus taeda"))
tab_expected["MSNS-005-INCONSISTENT"] = ["ING_METADATA_INCONSISTENT"]

# --- swapped lat/lon ---
lat_ok, lon_ok = ANCHOR_MSNS[0] + 0.07, ANCHOR_MSNS[1]
add_point_row("MSNS-006-LATLONSWAP", lat=lon_ok, lon=lat_ok, area=2, place="Chacra 13",
              common="Pino", sci="Pinus taeda")
tab_expected["MSNS-006-LATLONSWAP"] = ["COUNTRY_MISMATCH"]

# --- more than 6 decimals (genuine) ---
extra = 0.0000001234567891
add_point_row("MSNS-007-PRECISION", ANCHOR_MSNS[0] + 0.08 + extra,
              ANCHOR_MSNS[1] + extra, area=2, place="Chacra 15",
              common="Pino", sci="Pinus taeda")
tab_expected["MSNS-007-PRECISION"] = ["COORD_PRECISION"]

# --- Point with Area > 4ha ---
add_point_row("MSNS-008-4HAVIOLATION", ANCHOR_MSNS[0] + 0.09, ANCHOR_MSNS[1], area=8,
              place="Chacra 17", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-008-4HAVIOLATION"] = ["RULE_4HA_VIOLATION"]

# --- Point without Area ---
add_point_row("MSNS-009-NOAREA", ANCHOR_MSNS[0] + 0.10, ANCHOR_MSNS[1], area=None,
              place="Chacra 19", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-009-NOAREA"] = ["POINT_NO_AREA"]

# --- two overlapping parcels (12ha each, shifted 40% of the side) ---
_side_msns_overlap = side_deg_for_area_ha(ANCHOR_MSNS[0] + 0.11, 12.0)
verts_a = rect_vertices_latlon(ANCHOR_MSNS, 0.11, 0.000, 12.0)
verts_b = rect_vertices_latlon(ANCHOR_MSNS, 0.11, _side_msns_overlap * 0.4, 12.0)
add_polygon_rows("MSNS-010-OVERLAP-A", verts_a, area=12, place="Chacra 21A",
                  common="Pino", sci="Pinus taeda")
add_polygon_rows("MSNS-010-OVERLAP-B", verts_b, area=12, place="Chacra 21B",
                  common="Pino", sci="Pinus taeda")
tab_expected["MSNS-010-OVERLAP-A"] = ["PARCELS_OVERLAP"]
tab_expected["MSNS-010-OVERLAP-B"] = ["PARCELS_OVERLAP"]

# --- invalid ISO ---
add_point_row("MSNS-011-INVALIDISO", ANCHOR_MSNS[0] + 0.12, ANCHOR_MSNS[1], country="ZZ",
              area=2, place="Chacra 23", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-011-INVALIDISO"] = ["COUNTRY_INVALID_ISO"]

# --- missing species (wood) ---
add_point_row("MSNS-012-NOSPECIES", ANCHOR_MSNS[0] + 0.13, ANCHOR_MSNS[1], area=2,
              place="Chacra 25")
tab_expected["MSNS-012-NOSPECIES"] = ["SPECIES_MISSING"]

# --- declared Area very different from computed area (15ha geometry, declared 1.5) ---
verts = rect_vertices_latlon(ANCHOR_MSNS, 0.14, 0.00, 15.0)
add_polygon_rows("MSNS-013-AREAMISMATCH", verts, area=1.5, place="Chacra 27",
                  common="Pino", sci="Pinus taeda")
tab_expected["MSNS-013-AREAMISMATCH"] = ["AREA_MISMATCH"]

# --- self-intersecting polygon due to wrongly entered vertex order ---
verts = rect_vertices_latlon(ANCHOR_MSNS, 0.15, 0.00, 4.0)
bowtie_order = [verts[0], verts[2], verts[1], verts[3]]
add_polygon_rows("MSNS-014-SELFINTERSECT", bowtie_order, area=4, place="Chacra 29",
                  common="Pino", sci="Pinus taeda")
tab_expected["MSNS-014-SELFINTERSECT"] = ["GEOM_SELF_INTERSECTION"]

df = pd.DataFrame(rows)
xlsx_path = os.path.join(DATA_DIR, "synthetic_supplier_spreadsheet.xlsx")
df.to_excel(xlsx_path, index=False, sheet_name="Parcelas")
print(f"Escrito {xlsx_path} ({df['ParcelID'].nunique()} parcelas, {len(df)} filas)")

with open(os.path.join(os.path.dirname(__file__), "expected_codes.json"), "w", encoding="utf-8") as f:
    json.dump({"geojson": expected, "tabular": tab_expected}, f, ensure_ascii=False, indent=2)
print("Escrito tests/expected_codes.json")
