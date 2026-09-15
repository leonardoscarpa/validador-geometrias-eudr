"""
Genera dos archivos de entrada sintéticos, ambientados en zonas forestales
reales de Corrientes y Misiones (Argentina) pero con coordenadas y nombres de
productor ficticios — nunca datos de un proveedor real identificable.

1. data/synthetic_geojson_input.geojson  -> ejercita el camino GeoJSON crudo
2. data/synthetic_planilla_proveedores.xlsx -> ejercita el camino tabular

Las parcelas "control" (sin errores sembrados) usan side_deg calculado con
side_deg_for_area_ha() para que el área declarada coincida con el área
geodésica real — así el chequeo de AREA_MISMATCH no dispara falsos positivos
en los controles.

También escribe tests/expected_codes.json con los códigos de hallazgo que
cada parcela DEBERÍA disparar.
"""

import json
import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

ANCHOR_CTES = (-28.05, -56.00)   # cerca de Virasoro, Corrientes
ANCHOR_MSNS = (-26.40, -54.60)   # cerca de Eldorado, Misiones


def side_deg_for_area_ha(lat, area_ha):
    """Lado (en grados) de un cuadrado centrado en `lat` cuya área geodésica
    aproximada es `area_ha` hectáreas. Aproximación esférica simple, suficiente
    para calibrar datos sintéticos (no para uso normativo)."""
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat))
    area_km2 = area_ha / 100.0
    # side_lat_deg * side_lon_deg * km_per_deg_lat * km_per_deg_lon = area_km2
    # con side_lat_deg == side_lon_deg == side:
    side = math.sqrt(area_km2 / (km_per_deg_lat * km_per_deg_lon))
    return side


expected = {}


def box_ha(anchor, dlat, dlon, area_ha, ndigits=6):
    """Caja cuadrada de área_ha hectáreas. Las coordenadas se redondean a
    `ndigits` decimales (igual que haría un proveedor real) para que estas
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
# 1) GeoJSON crudo
# ---------------------------------------------------------------------------

features = []


def add_feature(pid, geometry, props, codes):
    p = {"ParcelID": pid}
    p.update(props)
    features.append({"type": "Feature", "properties": p, "geometry": geometry})
    expected[pid] = codes


# --- controles válidos ---
add_feature("CTES-001", {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.00, 0.00, 4.2)]},
            {"ProducerName": "Forestal Don Aparicio", "ProducerCountry": "AR",
             "ProductionPlace": "Establecimiento La Loma", "Area": 4.2,
             "CommonName": "Pino", "ScientificName": "Pinus elliottii"}, [])

add_feature("CTES-002", {"type": "Point", "coordinates": [-56.02, -28.03]},
            {"ProducerName": "Forestal Don Aparicio", "ProducerCountry": "AR",
             "ProductionPlace": "Potrero Norte", "Area": 2.3,
             "CommonName": "Eucalipto", "ScientificName": "Eucalyptus grandis"}, [])

# --- tipos de geometría prohibidos ---
add_feature("CTES-003-LINESTRING",
            {"type": "LineString", "coordinates": [[-56.01, -28.06], [-56.00, -28.05]]},
            {"ProducerCountry": "AR", "ProductionPlace": "Linde Este", "Area": 3},
            ["GEOM_TYPE_PROHIBITED"])

add_feature("CTES-004-GEOMCOLLECTION",
            {"type": "GeometryCollection", "geometries": [
                {"type": "Point", "coordinates": [-56.0, -28.05]}]},
            {"ProducerCountry": "AR", "ProductionPlace": "Lote Mixto", "Area": 3},
            ["GEOM_TYPE_PROHIBITED"])

# --- polígono con hueco (outer 10ha, inner 2ha; declaramos el area neta aprox) ---
outer = box_ha(ANCHOR_CTES, 0.02, 0.00, 10.0)
inner = box_ha(ANCHOR_CTES, 0.02, 0.00, 2.0)
add_feature("CTES-005-HOLE", {"type": "Polygon", "coordinates": [outer, inner]},
            {"ProducerCountry": "AR", "ProductionPlace": "Rodal con isla nativa", "Area": 8},
            ["POLY_HAS_HOLES"])

# --- polígono sin cerrar (4ha) ---
ring_unclosed = box_ha(ANCHOR_CTES, 0.03, 0.00, 4.0)[:-1]
add_feature("CTES-006-UNCLOSED", {"type": "Polygon", "coordinates": [ring_unclosed]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 7", "Area": 4},
            ["POLY_NOT_CLOSED"])

# --- polígono auto-intersectado (bowtie), cerrado ---
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

# --- capitalización incorrecta de propiedades (4ha) ---
add_feature("CTES-008-PROPCASE",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.05, 0.00, 4.0)]},
            {"producercountry": "AR", "productionplace": "Cuartel 9", "area": 4},
            ["PROPERTY_CASE"])

# --- más de 6 decimales (coordenadas con precisión de GPS de 9 decimales genuina) ---
lat0, lon0 = ANCHOR_CTES[0] + 0.06, ANCHOR_CTES[1]
s = side_deg_for_area_ha(lat0, 4.0)
h = s / 2
extra = 0.0000001234567891  # empuja a >6 decimales de forma genuina, no por redondeo
ring_precise = [
    (lon0 - h + extra, lat0 - h + extra), (lon0 + h + extra, lat0 - h + extra),
    (lon0 + h + extra, lat0 + h + extra), (lon0 - h + extra, lat0 + h + extra),
    (lon0 - h + extra, lat0 - h + extra),
]
add_feature("CTES-009-PRECISION", {"type": "Polygon", "coordinates": [ring_precise]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 10", "Area": 4},
            ["COORD_PRECISION"])

# --- país declarado no coincide con la geometría real (punto en Brasil) ---
add_feature("CTES-010-COUNTRYMISMATCH", {"type": "Point", "coordinates": [-53.45, -24.90]},
            {"ProducerCountry": "AR", "ProductionPlace": "Supuesto lote correntino", "Area": 3},
            ["COUNTRY_MISMATCH"])

# --- código ISO inválido (4ha) ---
add_feature("CTES-011-INVALIDISO",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.07, 0.00, 4.0)]},
            {"ProducerCountry": "ARG", "ProductionPlace": "Cuartel 11", "Area": 4},
            ["COUNTRY_INVALID_ISO"])

# --- falta ProducerCountry (4ha) ---
add_feature("CTES-012-COUNTRYMISSING",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.08, 0.00, 4.0)]},
            {"ProductionPlace": "Cuartel 12", "Area": 4}, ["COUNTRY_MISSING"])

# --- Area como texto (4ha real, declarada como texto) ---
add_feature("CTES-013-AREASTRING",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.09, 0.00, 4.0)]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 13", "Area": "doce"},
            ["AREA_NOT_NUMERIC"])

# --- Point sin Area ---
add_feature("CTES-014-POINT-NOAREA", {"type": "Point", "coordinates": [-56.0, -28.10]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 14"},
            ["POINT_NO_AREA"])

# --- regla de 4 ha violada (Point con Area > 4) ---
add_feature("CTES-015-4HAVIOLATION", {"type": "Point", "coordinates": [-56.01, -28.11]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 15", "Area": 15},
            ["RULE_4HA_VIOLATION"])

# --- polígono con menos de 4 pares (degenerado) ---
lat0, lon0 = ANCHOR_CTES[0] + 0.10, ANCHOR_CTES[1]
degenerate = [(lon0 - 0.003, lat0), (lon0 + 0.003, lat0), (lon0 - 0.003, lat0)]
add_feature("CTES-016-TOOFEWVERTICES", {"type": "Polygon", "coordinates": [degenerate]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 16", "Area": 4},
            ["POLY_TOO_FEW_VERTICES"])

# --- dos parcelas superpuestas (10ha cada una, desplazadas 40% del lado para
#     garantizar overlap real sin importar la latitud) ---
_side_ctes_overlap = side_deg_for_area_ha(ANCHOR_CTES[0] + 0.11, 10.0)
ring_a = box_ha(ANCHOR_CTES, 0.11, 0.000, 10.0)
ring_b = box_ha(ANCHOR_CTES, 0.11, _side_ctes_overlap * 0.4, 10.0)
add_feature("CTES-017-OVERLAP-A", {"type": "Polygon", "coordinates": [ring_a]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 17A", "Area": 10},
            ["PARCELS_OVERLAP"])
add_feature("CTES-017-OVERLAP-B", {"type": "Polygon", "coordinates": [ring_b]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 17B", "Area": 10},
            ["PARCELS_OVERLAP"])

# --- falta nombre común/científico (madera), 4ha ---
add_feature("CTES-018-NOSPECIES",
            {"type": "Polygon", "coordinates": [box_ha(ANCHOR_CTES, 0.12, 0.00, 4.0)]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 18", "Area": 4},
            ["SPECIES_MISSING"])

# --- coordenada fuera de rango ---
add_feature("CTES-019-OUTOFRANGE", {"type": "Point", "coordinates": [-56.0, -95.0]},
            {"ProducerCountry": "AR", "ProductionPlace": "Cuartel 19", "Area": 2},
            ["COORD_OUT_OF_RANGE"])

# --- ParcelID duplicado (dos features, mismo id, cada una 4ha) ---
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

# --- área declarada muy distinta del área real (geometría 15ha, declarada 2ha) ---
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
# 2) Planilla Excel (formato tabular largo)
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
    """4 vértices (lat, lon) de un rectángulo de área_ha hectáreas, SIN repetir
    el primero al final (así ejercitamos el auto-cierre en la ingesta).
    Redondeadas a `ndigits` decimales por el mismo motivo que en box_ha()."""
    lat0 = anchor[0] + dlat
    lon0 = anchor[1] + dlon
    side = side_deg_for_area_ha(lat0, area_ha)
    h = side / 2
    verts = [(lat0 - h, lon0 - h), (lat0 - h, lon0 + h),
             (lat0 + h, lon0 + h), (lat0 + h, lon0 - h)]
    return [(round(lat, ndigits), round(lon, ndigits)) for lat, lon in verts]


# --- controles válidos ---
add_point_row("MSNS-001", ANCHOR_MSNS[0], ANCHOR_MSNS[1] + 0.01, area=1.8,
              place="Chacra 3", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-001"] = []

verts = rect_vertices_latlon(ANCHOR_MSNS, 0.00, 0.03, 4.3)
add_polygon_rows("MSNS-002", [verts[2], verts[0], verts[3], verts[1]],
                  order=[3, 1, 4, 2], area=4.3, place="Chacra 5",
                  common="Eucalipto", sci="Eucalyptus grandis")
tab_expected["MSNS-002"] = ["ING_AUTOCLOSE"]

# --- falta lat/lon ---
rows.append(dict(ParcelID="MSNS-003-MISSINGLATLON", VertexOrder=None, Latitude=None,
                  Longitude=ANCHOR_MSNS[1], ProducerCountry="AR", ProducerName="Yerbatera San Ignacio",
                  ProductionPlace="Chacra 7", Area=2, CommonName="Pino", ScientificName="Pinus taeda"))
tab_expected["MSNS-003-MISSINGLATLON"] = ["ING_MISSING_LATLON"]

# --- exactamente 2 vértices ---
add_polygon_rows("MSNS-004-TWOVERTICES", [
    (ANCHOR_MSNS[0] + 0.05, ANCHOR_MSNS[1]), (ANCHOR_MSNS[0] + 0.051, ANCHOR_MSNS[1] + 0.001)],
    area=3, place="Chacra 9")
tab_expected["MSNS-004-TWOVERTICES"] = ["ING_TWO_VERTICES"]

# --- metadatos inconsistentes entre vértices ---
verts = rect_vertices_latlon(ANCHOR_MSNS, 0.06, 0.00, 4.5)
for o, (lat, lon) in enumerate(verts, start=1):
    rows.append(dict(ParcelID="MSNS-005-INCONSISTENT", VertexOrder=o, Latitude=lat, Longitude=lon,
                      ProducerCountry=("AR" if o < 3 else "BR"), ProducerName="Yerbatera San Ignacio",
                      ProductionPlace="Chacra 11", Area=4.5, CommonName="Pino", ScientificName="Pinus taeda"))
tab_expected["MSNS-005-INCONSISTENT"] = ["ING_METADATA_INCONSISTENT"]

# --- lat/lon invertidos (swap) ---
lat_ok, lon_ok = ANCHOR_MSNS[0] + 0.07, ANCHOR_MSNS[1]
add_point_row("MSNS-006-LATLONSWAP", lat=lon_ok, lon=lat_ok, area=2, place="Chacra 13",
              common="Pino", sci="Pinus taeda")
tab_expected["MSNS-006-LATLONSWAP"] = ["COUNTRY_MISMATCH"]

# --- más de 6 decimales (genuino) ---
extra = 0.0000001234567891
add_point_row("MSNS-007-PRECISION", ANCHOR_MSNS[0] + 0.08 + extra,
              ANCHOR_MSNS[1] + extra, area=2, place="Chacra 15",
              common="Pino", sci="Pinus taeda")
tab_expected["MSNS-007-PRECISION"] = ["COORD_PRECISION"]

# --- Point con Area > 4ha ---
add_point_row("MSNS-008-4HAVIOLATION", ANCHOR_MSNS[0] + 0.09, ANCHOR_MSNS[1], area=8,
              place="Chacra 17", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-008-4HAVIOLATION"] = ["RULE_4HA_VIOLATION"]

# --- Point sin Area ---
add_point_row("MSNS-009-NOAREA", ANCHOR_MSNS[0] + 0.10, ANCHOR_MSNS[1], area=None,
              place="Chacra 19", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-009-NOAREA"] = ["POINT_NO_AREA"]

# --- dos parcelas superpuestas (12ha cada una, desplazadas 40% del lado) ---
_side_msns_overlap = side_deg_for_area_ha(ANCHOR_MSNS[0] + 0.11, 12.0)
verts_a = rect_vertices_latlon(ANCHOR_MSNS, 0.11, 0.000, 12.0)
verts_b = rect_vertices_latlon(ANCHOR_MSNS, 0.11, _side_msns_overlap * 0.4, 12.0)
add_polygon_rows("MSNS-010-OVERLAP-A", verts_a, area=12, place="Chacra 21A",
                  common="Pino", sci="Pinus taeda")
add_polygon_rows("MSNS-010-OVERLAP-B", verts_b, area=12, place="Chacra 21B",
                  common="Pino", sci="Pinus taeda")
tab_expected["MSNS-010-OVERLAP-A"] = ["PARCELS_OVERLAP"]
tab_expected["MSNS-010-OVERLAP-B"] = ["PARCELS_OVERLAP"]

# --- ISO inválido ---
add_point_row("MSNS-011-INVALIDISO", ANCHOR_MSNS[0] + 0.12, ANCHOR_MSNS[1], country="ZZ",
              area=2, place="Chacra 23", common="Pino", sci="Pinus taeda")
tab_expected["MSNS-011-INVALIDISO"] = ["COUNTRY_INVALID_ISO"]

# --- falta especie (madera) ---
add_point_row("MSNS-012-NOSPECIES", ANCHOR_MSNS[0] + 0.13, ANCHOR_MSNS[1], area=2,
              place="Chacra 25")
tab_expected["MSNS-012-NOSPECIES"] = ["SPECIES_MISSING"]

# --- Area declarada muy distinta del área calculada (geometría 15ha, declarada 1.5) ---
verts = rect_vertices_latlon(ANCHOR_MSNS, 0.14, 0.00, 15.0)
add_polygon_rows("MSNS-013-AREAMISMATCH", verts, area=1.5, place="Chacra 27",
                  common="Pino", sci="Pinus taeda")
tab_expected["MSNS-013-AREAMISMATCH"] = ["AREA_MISMATCH"]

# --- polígono auto-intersectado por orden de vértices mal cargado ---
verts = rect_vertices_latlon(ANCHOR_MSNS, 0.15, 0.00, 4.0)
bowtie_order = [verts[0], verts[2], verts[1], verts[3]]
add_polygon_rows("MSNS-014-SELFINTERSECT", bowtie_order, area=4, place="Chacra 29",
                  common="Pino", sci="Pinus taeda")
tab_expected["MSNS-014-SELFINTERSECT"] = ["GEOM_SELF_INTERSECTION"]

df = pd.DataFrame(rows)
xlsx_path = os.path.join(DATA_DIR, "synthetic_planilla_proveedores.xlsx")
df.to_excel(xlsx_path, index=False, sheet_name="Parcelas")
print(f"Escrito {xlsx_path} ({df['ParcelID'].nunique()} parcelas, {len(df)} filas)")

with open(os.path.join(os.path.dirname(__file__), "expected_codes.json"), "w", encoding="utf-8") as f:
    json.dump({"geojson": expected, "tabular": tab_expected}, f, ensure_ascii=False, indent=2)
print("Escrito tests/expected_codes.json")
