"""Constantes y helpers de bajo nivel compartidos por ingest.py y validators.py."""

from .models import Finding, ERROR, WARNING

# Nombres de propiedad EXACTOS que exige la especificación GeoJSON v1.5 del
# Information System (más CommonName/ScientificName, que agregamos para
# madera por el Art. 4 del Reglamento de Ejecución 2024/3084 — no son parte
# del esquema base, pero el sistema ignora silenciosamente propiedades
# adicionales sintácticamente válidas, así que no rompen conformidad).
CANONICAL_PROPS = [
    "ProducerName",
    "ProducerCountry",
    "ProductionPlace",
    "Area",
    "CommonName",
    "ScientificName",
]

PROHIBITED_GEOM_TYPES = {"LineString", "MultiLineString", "GeometryCollection"}
ALLOWED_GEOM_TYPES = {"Point", "MultiPoint", "Polygon", "MultiPolygon"}

MAX_DECIMALS = 6
MAX_FILE_SIZE_MB = 25

REF_GEOJSON_SPEC = "EUDR GeoJSON File Description v1.5"
REF_4084 = "Reglamento de Ejecución (UE) 2024/3084"
REF_ART9 = "Reglamento (UE) 2023/1115, Art. 9"


def canon_prop_lookup():
    return {p.lower(): p for p in CANONICAL_PROPS}


def check_coordinate_value(lon, lat, parcel_id, vertex_label=""):
    """Chequea rango (±180/±90) y precisión decimal (máx. 6) de un par de
    coordenadas crudo. Devuelve una lista de Finding."""
    findings = []
    where = f" ({vertex_label})" if vertex_label else ""

    if lon is None or lat is None:
        return findings  # otros chequeos ya cubren faltantes

    try:
        lon_f, lat_f = float(lon), float(lat)
    except (TypeError, ValueError):
        findings.append(Finding(
            ERROR, "COORD_NOT_NUMERIC",
            f"Coordenada no numérica{where}: lon={lon!r}, lat={lat!r}.",
            REF_GEOJSON_SPEC, parcel_id=parcel_id))
        return findings

    if not (-180.0 <= lon_f <= 180.0) or not (-90.0 <= lat_f <= 90.0):
        findings.append(Finding(
            ERROR, "COORD_OUT_OF_RANGE",
            f"Coordenada fuera de rango{where}: lon={lon_f}, lat={lat_f} "
            "(se esperaba lon en ±180°, lat en ±90°). Sospechá una inversión "
            "lat/lon si los valores están invertidos respecto de este rango.",
            REF_GEOJSON_SPEC, parcel_id=parcel_id))

    for val, name in ((lon_f, "longitud"), (lat_f, "latitud")):
        decimals = _count_decimals(val)
        if decimals > MAX_DECIMALS:
            findings.append(Finding(
                WARNING, "COORD_PRECISION",
                f"La {name} tiene {decimals} decimales{where} (máximo recomendado: "
                f"{MAX_DECIMALS}). Más de 6 decimales puede generar coordenadas "
                "duplicadas por redondeo al procesarse en el sistema.",
                REF_GEOJSON_SPEC, parcel_id=parcel_id))

    return findings


def _count_decimals(value):
    s = repr(float(value))
    if "e" in s or "E" in s:
        # notación científica: contamos vía formato fijo con margen amplio
        s = f"{value:.12f}".rstrip("0")
    if "." not in s:
        return 0
    return len(s.split(".")[1].rstrip("0"))


def round_coords(geom, ndigits=MAX_DECIMALS):
    """Redondea todas las coordenadas de una geometría shapely a `ndigits`
    decimales, preservando el tipo de geometría."""
    from shapely.ops import transform

    def _round(x, y, z=None):
        if z is None:
            return (round(x, ndigits), round(y, ndigits))
        return (round(x, ndigits), round(y, ndigits), round(z, ndigits))

    return transform(_round, geom)
