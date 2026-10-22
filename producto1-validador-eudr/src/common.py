"""Low-level constants and helpers shared by ingest.py and validators.py."""

from .models import Finding, ERROR, WARNING

# EXACT property names required by the Information System GeoJSON v1.5
# specification (plus CommonName/ScientificName, which we add for wood under
# Art. 4 of Implementing Regulation 2024/3084. They are not part of the base
# schema, but the system silently ignores additional syntactically valid
# properties, so they do not break conformance).
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
REF_4084 = "Implementing Regulation (EU) 2024/3084"
REF_ART9 = "Regulation (EU) 2023/1115, Art. 9"


def canon_prop_lookup():
    return {p.lower(): p for p in CANONICAL_PROPS}


def check_coordinate_value(lon, lat, parcel_id, vertex_label=""):
    """Checks range (±180/±90) and decimal precision (max. 6) of a raw
    coordinate pair. Returns a list of Findings."""
    findings = []
    where = f" ({vertex_label})" if vertex_label else ""

    if lon is None or lat is None:
        return findings  # other checks already cover missing values

    try:
        lon_f, lat_f = float(lon), float(lat)
    except (TypeError, ValueError):
        findings.append(Finding(
            ERROR, "COORD_NOT_NUMERIC",
            f"Non-numeric coordinate{where}: lon={lon!r}, lat={lat!r}.",
            REF_GEOJSON_SPEC, parcel_id=parcel_id))
        return findings

    if not (-180.0 <= lon_f <= 180.0) or not (-90.0 <= lat_f <= 90.0):
        findings.append(Finding(
            ERROR, "COORD_OUT_OF_RANGE",
            f"Coordinate out of range{where}: lon={lon_f}, lat={lat_f} "
            "(expected lon within ±180°, lat within ±90°). Suspect a lat/lon "
            "swap if the values would be valid when reversed.",
            REF_GEOJSON_SPEC, parcel_id=parcel_id))

    for val, name in ((lon_f, "longitude"), (lat_f, "latitude")):
        decimals = _count_decimals(val)
        if decimals > MAX_DECIMALS:
            findings.append(Finding(
                WARNING, "COORD_PRECISION",
                f"The {name} has {decimals} decimal places{where} (recommended maximum: "
                f"{MAX_DECIMALS}). More than 6 decimals can produce duplicate "
                "coordinates through rounding when processed by the system.",
                REF_GEOJSON_SPEC, parcel_id=parcel_id))

    return findings


def _count_decimals(value):
    s = repr(float(value))
    if "e" in s or "E" in s:
        # scientific notation: count via fixed format with a wide margin
        s = f"{value:.12f}".rstrip("0")
    if "." not in s:
        return 0
    return len(s.split(".")[1].rstrip("0"))


def round_coords(geom, ndigits=MAX_DECIMALS):
    """Rounds all coordinates of a shapely geometry to `ndigits` decimals,
    preserving the geometry type."""
    from shapely.ops import transform

    def _round(x, y, z=None):
        if z is None:
            return (round(x, ndigits), round(y, ndigits))
        return (round(x, ndigits), round(y, ndigits), round(z, ndigits))

    return transform(_round, geom)
