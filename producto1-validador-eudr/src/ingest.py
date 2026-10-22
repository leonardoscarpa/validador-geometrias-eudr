"""
Ingestion: takes an input file (GeoJSON, CSV or Excel) and converts it to a
common internal GeoDataFrame with columns:
    geometry, ParcelID, ProducerName, ProducerCountry, ProductionPlace,
    Area, CommonName, ScientificName

It also returns the findings detected during the conversion itself, for
example a group of only 2 vertices cannot become anything valid, or metadata
that is inconsistent across the rows of one parcel.

The "geometric quality" checks that depend on the ALREADY built geometry
(self-intersection, overlap between parcels, the 4 ha rule, etc.) live in
validators.py and apply equally whether the data came from GeoJSON, CSV or
Excel. That is precisely the point of having a common internal model.
"""

import json
import os

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Point, Polygon

from .models import Finding, IngestResult, ERROR, WARNING, INFO
from .common import (
    CANONICAL_PROPS, PROHIBITED_GEOM_TYPES, ALLOWED_GEOM_TYPES,
    canon_prop_lookup, check_coordinate_value, REF_GEOJSON_SPEC, REF_ART9,
)

OUTPUT_COLUMNS = ["geometry", "ParcelID"] + CANONICAL_PROPS

# case-insensitive aliases of tabular columns -> internal canonical name
_TABULAR_ALIASES = {
    "parcelid": "ParcelID", "parcel_id": "ParcelID", "id": "ParcelID",
    "lat": "Latitude", "latitude": "Latitude",
    "lon": "Longitude", "lng": "Longitude", "long": "Longitude",
    "longitude": "Longitude",
    "vertexorder": "VertexOrder", "vertex_order": "VertexOrder",
    "order": "VertexOrder", "point": "VertexOrder",
    "producercountry": "ProducerCountry", "country": "ProducerCountry",
    "producername": "ProducerName", "producer": "ProducerName",
    "productionplace": "ProductionPlace", "place": "ProductionPlace",
    "farm": "ProductionPlace",
    "area": "Area", "hectares": "Area", "ha": "Area",
    "commonname": "CommonName", "common_name": "CommonName",
    "scientificname": "ScientificName", "scientific_name": "ScientificName",
}


def _empty_gdf():
    return gpd.GeoDataFrame(
        {c: [] for c in OUTPUT_COLUMNS}, geometry="geometry", crs="EPSG:4326"
    )


def load_any(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".geojson", ".json"):
        return load_geojson(path)
    elif ext == ".csv":
        return load_tabular(path, fmt="csv")
    elif ext in (".xlsx", ".xls"):
        return load_tabular(path, fmt="xlsx")
    else:
        findings = [Finding(
            ERROR, "UNSUPPORTED_FORMAT",
            f"Unsupported file extension: '{ext}'. Accepted: .geojson, "
            ".json, .csv, .xlsx.", "Product 1: supported input formats")]
        return IngestResult(gdf=_empty_gdf(), findings=findings, source_format=ext)


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

def _check_polygon_coordinates(rings, pid, label=""):
    """Applies the hole / minimum vertices / closure / coordinate range and
    precision checks to ONE polygon already extracted from the raw
    coordinates (coordinates[0] of a Polygon, or each sub-polygon inside a
    MultiPolygon). `label` is a suffix like " (part 2/3)" so findings from a
    MultiPolygon say which part they refer to."""
    findings = []
    if len(rings) > 1:
        findings.append(Finding(
            ERROR, "POLY_HAS_HOLES",
            f"The polygon{label} has {len(rings) - 1} interior ring(s) "
            "(a 'donut' hole), which is prohibited.",
            REF_GEOJSON_SPEC, parcel_id=pid))
    if rings:
        ext_ring = rings[0]
        if len(ext_ring) < 4:
            findings.append(Finding(
                ERROR, "POLY_TOO_FEW_VERTICES",
                f"The polygon{label} has {len(ext_ring)} coordinate pairs; "
                "at least 4 are required (including the closing point).",
                REF_GEOJSON_SPEC, parcel_id=pid))
        elif ext_ring[0] != ext_ring[-1]:
            findings.append(Finding(
                ERROR, "POLY_NOT_CLOSED",
                f"The polygon{label} is not closed: the first point must be "
                "identical to the last.",
                REF_GEOJSON_SPEC, parcel_id=pid))
        for vi, (lon, lat) in enumerate(ext_ring):
            findings.extend(check_coordinate_value(lon, lat, pid, f"vertex {vi}{label}"))
    return findings


def load_geojson(path):
    findings = []
    failed_ids = []
    file_size_mb = os.path.getsize(path) / (1024 * 1024)

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if raw.get("type") != "FeatureCollection":
        findings.append(Finding(
            ERROR, "STRUCT_ROOT",
            f"The file root is '{raw.get('type')}', it must be "
            "'FeatureCollection' (RFC 7946).",
            REF_GEOJSON_SPEC))
        return IngestResult(gdf=_empty_gdf(), findings=findings, source_format="geojson")

    lookup = canon_prop_lookup()
    rows = []

    for i, feat in enumerate(raw.get("features", [])):
        props = feat.get("properties", {}) or {}
        geom_dict = feat.get("geometry", {}) or {}
        gtype = geom_dict.get("type")
        pid = str(props.get("ParcelID") or props.get("ProductionPlace") or f"feature_{i}")

        # exact property capitalization
        for key in props.keys():
            kl = key.lower()
            if kl in lookup and key != lookup[kl]:
                findings.append(Finding(
                    WARNING, "PROPERTY_CASE",
                    f"The property '{key}' should be named exactly "
                    f"'{lookup[kl]}'. Names are case-sensitive: "
                    "the Information System ignores it if it does not match.",
                    REF_GEOJSON_SPEC, parcel_id=pid))

        if gtype in PROHIBITED_GEOM_TYPES:
            findings.append(Finding(
                ERROR, "GEOM_TYPE_PROHIBITED",
                f"Geometry type '{gtype}' is not allowed "
                "(LineString, MultiLineString and GeometryCollection are prohibited).",
                REF_GEOJSON_SPEC, parcel_id=pid))
            failed_ids.append(pid)
            continue

        if gtype not in ALLOWED_GEOM_TYPES:
            findings.append(Finding(
                ERROR, "GEOM_TYPE_UNKNOWN",
                f"Geometry type '{gtype}' not recognized.",
                REF_GEOJSON_SPEC, parcel_id=pid))
            failed_ids.append(pid)
            continue

        # checks that can only be done on the RAW coordinates, before shapely
        # normalizes the ring (shapely closes polygons automatically when
        # parsing, so after shape() it is no longer possible to know whether
        # the original file was closed or not).
        # They apply equally to simple types (Polygon/Point) and to their
        # multipart versions (MultiPolygon/MultiPoint), part by part.
        if gtype == "Polygon":
            findings.extend(_check_polygon_coordinates(geom_dict.get("coordinates", []), pid))
        elif gtype == "MultiPolygon":
            parts = geom_dict.get("coordinates", [])
            for pi, part_rings in enumerate(parts):
                label = f" (part {pi + 1}/{len(parts)})"
                findings.extend(_check_polygon_coordinates(part_rings, pid, label))
        elif gtype == "Point":
            coords = geom_dict.get("coordinates", [None, None])
            if len(coords) >= 2:
                findings.extend(check_coordinate_value(coords[0], coords[1], pid))
        elif gtype == "MultiPoint":
            coords_list = geom_dict.get("coordinates", [])
            for vi, coords in enumerate(coords_list):
                if len(coords) >= 2:
                    findings.extend(check_coordinate_value(
                        coords[0], coords[1], pid, f"point {vi + 1}/{len(coords_list)}"))

        try:
            geom = shape(geom_dict)
        except Exception as e:
            findings.append(Finding(
                ERROR, "GEOM_INVALID",
                f"Could not interpret the geometry: {e}",
                "RFC 7946", parcel_id=pid))
            failed_ids.append(pid)
            continue

        row = {lookup.get(k.lower(), k): v for k, v in props.items()}
        row["ParcelID"] = pid
        row["geometry"] = geom
        rows.append(row)

    if file_size_mb > 25:
        findings.append(Finding(
            ERROR, "FILE_TOO_LARGE",
            f"The file is {file_size_mb:.1f} MB; the per-submission limit "
            "is 25 MB. Strategies: reduce points on straight stretches, use points "
            "instead of polygons for parcels ≤4 ha, or split into several DDS.",
            REF_GEOJSON_SPEC))

    gdf = _rows_to_gdf(rows)
    return IngestResult(gdf=gdf, findings=findings, source_format="geojson", failed_ids=failed_ids)


# ---------------------------------------------------------------------------
# CSV / Excel ("long" format: one row = one vertex; 1 row per ParcelID = point)
# ---------------------------------------------------------------------------

def load_tabular(path, fmt="csv"):
    findings = []
    if fmt == "csv":
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.read_excel(path, dtype=str)

    # normalize headers to canonical names (case-insensitive)
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in _TABULAR_ALIASES:
            rename[col] = _TABULAR_ALIASES[key]
    df = df.rename(columns=rename)

    required = {"ParcelID", "Latitude", "Longitude"}
    missing = required - set(df.columns)
    if missing:
        findings.append(Finding(
            ERROR, "ING_MISSING_COLUMNS",
            f"Required columns are missing from the file: {', '.join(sorted(missing))}.",
            "Product 1: tabular input schema"))
        return IngestResult(gdf=_empty_gdf(), findings=findings, source_format=fmt)

    if "VertexOrder" not in df.columns:
        df["VertexOrder"] = None

    rows = []
    failed_ids = []
    for pid, group in df.groupby("ParcelID", sort=False, dropna=False):
        pid_str = str(pid)
        rows_g, findings_g = _build_geometry_for_group(pid_str, group)
        findings.extend(findings_g)
        if rows_g is not None:
            rows.append(rows_g)
        else:
            failed_ids.append(pid_str)

    gdf = _rows_to_gdf(rows)

    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb > 25:
        findings.append(Finding(
            ERROR, "FILE_TOO_LARGE",
            f"The file is {file_size_mb:.1f} MB; the per-submission limit is 25 MB.",
            REF_GEOJSON_SPEC))

    return IngestResult(gdf=gdf, findings=findings, source_format=fmt, failed_ids=failed_ids)


def _build_geometry_for_group(pid, group):
    findings = []

    # metadata: must be consistent within the same parcel
    meta = {}
    for prop in CANONICAL_PROPS:
        if prop not in group.columns:
            meta[prop] = None
            continue
        values = group[prop].dropna().unique().tolist()
        if len(values) > 1:
            findings.append(Finding(
                WARNING, "ING_METADATA_INCONSISTENT",
                f"The property '{prop}' has different values across rows of the "
                f"same parcel ({values}); the first one was used.",
                "Product 1: metadata consistency per ParcelID", parcel_id=pid))
        meta[prop] = values[0] if values else None

    n = len(group)

    if n == 1:
        r = group.iloc[0]
        lon, lat = r.get("Longitude"), r.get("Latitude")
        if pd.isna(lon) or pd.isna(lat):
            findings.append(Finding(
                ERROR, "ING_MISSING_LATLON",
                "Latitude or Longitude is missing.", "Product 1: tabular input schema",
                parcel_id=pid))
            return None, findings
        findings.extend(check_coordinate_value(lon, lat, pid))
        try:
            geom = Point(float(lon), float(lat))
        except ValueError:
            findings.append(Finding(
                ERROR, "COORD_NOT_NUMERIC",
                f"Non-numeric coordinate: lon={lon!r}, lat={lat!r}.",
                REF_GEOJSON_SPEC, parcel_id=pid))
            return None, findings

    elif n == 2:
        findings.append(Finding(
            ERROR, "ING_TWO_VERTICES",
            "The parcel has exactly 2 vertex rows: not enough for "
            "a polygon (minimum 3 distinct vertices) and not a single point. "
            "Check whether a vertex is missing or one was declared too many.",
            "Product 1: tabular input schema", parcel_id=pid))
        return None, findings

    else:
        g = group.copy()
        if g["VertexOrder"].notna().any():
            try:
                g["_ord"] = g["VertexOrder"].astype(float)
                g = g.sort_values("_ord")
            except ValueError:
                findings.append(Finding(
                    WARNING, "ING_VERTEXORDER_NOT_NUMERIC",
                    "VertexOrder has non-numeric values; the row order in the "
                    "file was used.",
                    "Product 1: tabular input schema", parcel_id=pid))
        coords = []
        bad = False
        for _, r in g.iterrows():
            lon, lat = r.get("Longitude"), r.get("Latitude")
            if pd.isna(lon) or pd.isna(lat):
                findings.append(Finding(
                    ERROR, "ING_MISSING_LATLON",
                    "Latitude or Longitude is missing on one of the vertices.",
                    "Product 1: tabular input schema", parcel_id=pid))
                bad = True
                continue
            findings.extend(check_coordinate_value(lon, lat, pid))
            try:
                coords.append((float(lon), float(lat)))
            except ValueError:
                findings.append(Finding(
                    ERROR, "COORD_NOT_NUMERIC",
                    f"Non-numeric coordinate: lon={lon!r}, lat={lat!r}.",
                    REF_GEOJSON_SPEC, parcel_id=pid))
                bad = True
        if bad or len(coords) < 3:
            return None, findings

        if coords[0] != coords[-1]:
            coords.append(coords[0])
            findings.append(Finding(
                INFO, "ING_AUTOCLOSE",
                "The polygon was closed automatically by repeating the first "
                "vertex at the end (the source file did not repeat it, "
                "which is common practice in spreadsheets).",
                "Product 1: tabular to GeoJSON conversion", parcel_id=pid))

        try:
            geom = Polygon(coords)
        except Exception as e:
            findings.append(Finding(
                ERROR, "GEOM_INVALID",
                f"Could not build the polygon: {e}",
                "RFC 7946", parcel_id=pid))
            return None, findings

        if not geom.is_valid:
            findings.append(Finding(
                ERROR, "GEOM_SELF_INTERSECTION",
                "The vertex sequence produces an invalid geometry "
                "(self-intersecting, figure-eight shape). Check the vertex order.",
                REF_GEOJSON_SPEC, parcel_id=pid))
            return None, findings

    row = dict(meta)
    row["ParcelID"] = pid
    row["geometry"] = geom
    return row, findings


def _rows_to_gdf(rows):
    if not rows:
        return _empty_gdf()
    for r in rows:
        for c in OUTPUT_COLUMNS:
            r.setdefault(c, None)
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    return gdf[OUTPUT_COLUMNS]
