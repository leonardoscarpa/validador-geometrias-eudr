"""
Ingesta: toma un archivo de entrada (GeoJSON, CSV o Excel) y lo convierte a un
GeoDataFrame interno común con columnas:
    geometry, ParcelID, ProducerName, ProducerCountry, ProductionPlace,
    Area, CommonName, ScientificName

Además devuelve los hallazgos (Finding) detectados durante la conversión misma
— por ejemplo, un grupo de solo 2 vértices no puede convertirse en nada válido,
o metadatos inconsistentes entre las filas de una misma parcela.

Los chequeos de "calidad geométrica" que dependen de la geometría YA construida
(auto-intersección, superposición entre parcelas, regla de 4 ha, etc.) viven en
validators.py y se aplican por igual sin importar si el dato vino de GeoJSON,
CSV o Excel — ese es justamente el punto de tener un modelo interno común.
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

# alias case-insensitive de columnas tabulares -> nombre canónico interno
_TABULAR_ALIASES = {
    "parcelid": "ParcelID", "parcel_id": "ParcelID", "id": "ParcelID",
    "lat": "Latitude", "latitude": "Latitude", "latitud": "Latitude",
    "lon": "Longitude", "lng": "Longitude", "long": "Longitude",
    "longitude": "Longitude", "longitud": "Longitude",
    "vertexorder": "VertexOrder", "vertex_order": "VertexOrder",
    "orden": "VertexOrder", "punto": "VertexOrder",
    "producercountry": "ProducerCountry", "country": "ProducerCountry",
    "pais": "ProducerCountry", "país": "ProducerCountry",
    "producername": "ProducerName", "productor": "ProducerName",
    "productionplace": "ProductionPlace", "lugar": "ProductionPlace",
    "finca": "ProductionPlace", "predio": "ProductionPlace",
    "area": "Area", "superficie": "Area", "hectareas": "Area", "ha": "Area",
    "commonname": "CommonName", "nombre_comun": "CommonName",
    "nombrecomun": "CommonName",
    "scientificname": "ScientificName", "nombre_cientifico": "ScientificName",
    "nombrecientifico": "ScientificName",
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
            f"Extensión de archivo no soportada: '{ext}'. Se aceptan .geojson, "
            ".json, .csv, .xlsx.", "Producto 1 — formatos de entrada soportados")]
        return IngestResult(gdf=_empty_gdf(), findings=findings, source_format=ext)


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

def load_geojson(path):
    findings = []
    failed_ids = []
    file_size_mb = os.path.getsize(path) / (1024 * 1024)

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if raw.get("type") != "FeatureCollection":
        findings.append(Finding(
            ERROR, "STRUCT_ROOT",
            f"La raíz del archivo es '{raw.get('type')}', debe ser "
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

        # capitalización exacta de propiedades
        for key in props.keys():
            kl = key.lower()
            if kl in lookup and key != lookup[kl]:
                findings.append(Finding(
                    WARNING, "PROPERTY_CASE",
                    f"La propiedad '{key}' debería llamarse exactamente "
                    f"'{lookup[kl]}'. Los nombres son sensibles a mayúsculas/"
                    "minúsculas: el Information System la ignora si no coincide.",
                    REF_GEOJSON_SPEC, parcel_id=pid))

        if gtype in PROHIBITED_GEOM_TYPES:
            findings.append(Finding(
                ERROR, "GEOM_TYPE_PROHIBITED",
                f"Tipo de geometría '{gtype}' no está permitido "
                "(LineString, MultiLineString y GeometryCollection están prohibidos).",
                REF_GEOJSON_SPEC, parcel_id=pid))
            failed_ids.append(pid)
            continue

        if gtype not in ALLOWED_GEOM_TYPES:
            findings.append(Finding(
                ERROR, "GEOM_TYPE_UNKNOWN",
                f"Tipo de geometría '{gtype}' no reconocido.",
                REF_GEOJSON_SPEC, parcel_id=pid))
            failed_ids.append(pid)
            continue

        # chequeos que solo se pueden hacer sobre las coordenadas CRUDAS,
        # antes de que shapely normalice el anillo (shapely cierra polígonos
        # automáticamente al parsear, así que después de shape() ya no se
        # puede saber si el archivo original venía cerrado o no)
        if gtype == "Polygon":
            rings = geom_dict.get("coordinates", [])
            if len(rings) > 1:
                findings.append(Finding(
                    ERROR, "POLY_HAS_HOLES",
                    f"El polígono tiene {len(rings) - 1} anillo(s) interior(es) "
                    "(hueco tipo 'dona'), lo cual está prohibido.",
                    REF_GEOJSON_SPEC, parcel_id=pid))
            if rings:
                ext_ring = rings[0]
                if len(ext_ring) < 4:
                    findings.append(Finding(
                        ERROR, "POLY_TOO_FEW_VERTICES",
                        f"El polígono tiene {len(ext_ring)} pares de coordenadas; "
                        "se requieren al menos 4 (incluyendo el cierre).",
                        REF_GEOJSON_SPEC, parcel_id=pid))
                elif ext_ring[0] != ext_ring[-1]:
                    findings.append(Finding(
                        ERROR, "POLY_NOT_CLOSED",
                        "El polígono no está cerrado: el primer punto debe ser "
                        "idéntico al último.",
                        REF_GEOJSON_SPEC, parcel_id=pid))
                for vi, (lon, lat) in enumerate(ext_ring):
                    findings.extend(check_coordinate_value(lon, lat, pid, f"vértice {vi}"))
        elif gtype == "Point":
            coords = geom_dict.get("coordinates", [None, None])
            if len(coords) >= 2:
                findings.extend(check_coordinate_value(coords[0], coords[1], pid))

        try:
            geom = shape(geom_dict)
        except Exception as e:
            findings.append(Finding(
                ERROR, "GEOM_INVALID",
                f"No se pudo interpretar la geometría: {e}",
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
            f"El archivo pesa {file_size_mb:.1f} MB; el límite por presentación "
            "es 25 MB. Estrategias: reducir puntos en tramos rectos, usar puntos "
            "en vez de polígonos para parcelas ≤4 ha, o dividir en varias DDS.",
            REF_GEOJSON_SPEC))

    gdf = _rows_to_gdf(rows)
    return IngestResult(gdf=gdf, findings=findings, source_format="geojson", failed_ids=failed_ids)


# ---------------------------------------------------------------------------
# CSV / Excel (formato "largo": una fila = un vértice; 1 fila por ParcelID = punto)
# ---------------------------------------------------------------------------

def load_tabular(path, fmt="csv"):
    findings = []
    if fmt == "csv":
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.read_excel(path, dtype=str)

    # normalizar encabezados a nombres canónicos (case-insensitive)
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
            f"Faltan columnas obligatorias en el archivo: {', '.join(sorted(missing))}.",
            "Producto 1 — esquema de entrada tabular"))
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
            f"El archivo pesa {file_size_mb:.1f} MB; el límite por presentación es 25 MB.",
            REF_GEOJSON_SPEC))

    return IngestResult(gdf=gdf, findings=findings, source_format=fmt, failed_ids=failed_ids)


def _build_geometry_for_group(pid, group):
    findings = []

    # metadatos: deben ser consistentes dentro de la misma parcela
    meta = {}
    for prop in CANONICAL_PROPS:
        if prop not in group.columns:
            meta[prop] = None
            continue
        values = group[prop].dropna().unique().tolist()
        if len(values) > 1:
            findings.append(Finding(
                WARNING, "ING_METADATA_INCONSISTENT",
                f"La propiedad '{prop}' tiene valores distintos entre filas de la "
                f"misma parcela ({values}); se usó el primero.",
                "Producto 1 — consistencia de metadatos por ParcelID", parcel_id=pid))
        meta[prop] = values[0] if values else None

    n = len(group)

    if n == 1:
        r = group.iloc[0]
        lon, lat = r.get("Longitude"), r.get("Latitude")
        if pd.isna(lon) or pd.isna(lat):
            findings.append(Finding(
                ERROR, "ING_MISSING_LATLON",
                "Falta Latitude o Longitude.", "Producto 1 — esquema de entrada tabular",
                parcel_id=pid))
            return None, findings
        findings.extend(check_coordinate_value(lon, lat, pid))
        try:
            geom = Point(float(lon), float(lat))
        except ValueError:
            findings.append(Finding(
                ERROR, "COORD_NOT_NUMERIC",
                f"Coordenada no numérica: lon={lon!r}, lat={lat!r}.",
                REF_GEOJSON_SPEC, parcel_id=pid))
            return None, findings

    elif n == 2:
        findings.append(Finding(
            ERROR, "ING_TWO_VERTICES",
            "La parcela tiene exactamente 2 filas de vértices: no alcanza para "
            "un polígono (mínimo 3 vértices distintos) y no es un único punto. "
            "Revisar si falta un vértice o si se declaró de más.",
            "Producto 1 — esquema de entrada tabular", parcel_id=pid))
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
                    "VertexOrder tiene valores no numéricos; se usó el orden de "
                    "las filas en el archivo.",
                    "Producto 1 — esquema de entrada tabular", parcel_id=pid))
        coords = []
        bad = False
        for _, r in g.iterrows():
            lon, lat = r.get("Longitude"), r.get("Latitude")
            if pd.isna(lon) or pd.isna(lat):
                findings.append(Finding(
                    ERROR, "ING_MISSING_LATLON",
                    "Falta Latitude o Longitude en uno de los vértices.",
                    "Producto 1 — esquema de entrada tabular", parcel_id=pid))
                bad = True
                continue
            findings.extend(check_coordinate_value(lon, lat, pid))
            try:
                coords.append((float(lon), float(lat)))
            except ValueError:
                findings.append(Finding(
                    ERROR, "COORD_NOT_NUMERIC",
                    f"Coordenada no numérica: lon={lon!r}, lat={lat!r}.",
                    REF_GEOJSON_SPEC, parcel_id=pid))
                bad = True
        if bad or len(coords) < 3:
            return None, findings

        if coords[0] != coords[-1]:
            coords.append(coords[0])
            findings.append(Finding(
                INFO, "ING_AUTOCLOSE",
                "El polígono se cerró automáticamente repitiendo el primer "
                "vértice al final (el archivo de origen no lo traía repetido, "
                "práctica habitual en planillas).",
                "Producto 1 — conversión tabular → GeoJSON", parcel_id=pid))

        try:
            geom = Polygon(coords)
        except Exception as e:
            findings.append(Finding(
                ERROR, "GEOM_INVALID",
                f"No se pudo construir el polígono: {e}",
                "RFC 7946", parcel_id=pid))
            return None, findings

        if not geom.is_valid:
            findings.append(Finding(
                ERROR, "GEOM_SELF_INTERSECTION",
                "La secuencia de vértices produce una geometría inválida "
                "(auto-intersectada, tipo 'ocho'). Revisar el orden de los vértices.",
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
