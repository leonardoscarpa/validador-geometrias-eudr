"""
Validadores que operan sobre el GeoDataFrame interno ya construido (sin
importar si vino de GeoJSON, CSV o Excel). Cada función devuelve una lista de
Finding. `run_all` las corre todas y agrega los hallazgos de nivel de archivo
(tamaño, cantidad de parcelas, etc.).
"""

import os

import geopandas as gpd
import pandas as pd
import pycountry
from shapely.geometry.base import BaseGeometry

from .models import Finding, ERROR, WARNING
from .common import ALLOWED_GEOM_TYPES, REF_GEOJSON_SPEC, REF_ART9, REF_4084

# Proyección de área equivalente centrada en el Cono Sur (Albers Equal Area
# Conic, parámetros ajustados a la región). Se usa SOLO para calcular
# hectáreas de forma consistente; no se exporta nada en esta proyección.
AEA_CONO_SUR = (
    "+proj=aea +lat_1=-5 +lat_2=-42 +lat_0=-32 +lon_0=-60 "
    "+x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs"
)

_COUNTRY_BOUNDARY_TOLERANCE_DEG = 0.08  # margen por simplificación de fronteras


def _load_country_boundaries(path):
    gdf = gpd.read_file(path)
    return gdf.set_index("iso2")


def compute_areas_ha(gdf):
    """Devuelve una Series con el área geodésica en hectáreas de cada geometría
    (0 para puntos)."""
    proj = gdf.geometry.to_crs(AEA_CONO_SUR)
    return proj.area / 10000.0


def run_all(gdf, country_boundaries_path, commodity="madera"):
    findings = []

    if gdf.empty:
        return findings

    if gdf["ParcelID"].duplicated().any():
        dupes = gdf.loc[gdf["ParcelID"].duplicated(), "ParcelID"].unique().tolist()
        for d in dupes:
            findings.append(Finding(
                ERROR, "DUPLICATE_PARCEL_ID",
                f"El ParcelID '{d}' aparece en más de una parcela del archivo. "
                "Cada parcela necesita un identificador único.",
                "Producto 1 — identificación de parcelas", parcel_id=d))

    areas_ha = compute_areas_ha(gdf)
    countries = _load_country_boundaries(country_boundaries_path)

    for idx, row in gdf.iterrows():
        pid = row["ParcelID"]
        geom = row["geometry"]
        area_calc = areas_ha.loc[idx]

        findings.extend(_check_geometry_validity(pid, geom))
        findings.extend(_check_country(pid, row, geom, countries))
        findings.extend(_check_area(pid, row, geom, area_calc))
        if commodity == "madera":
            findings.extend(_check_species(pid, row))

    findings.extend(_check_overlaps(gdf, areas_ha))

    return findings


def _check_geometry_validity(pid, geom):
    findings = []
    if geom is None or not isinstance(geom, BaseGeometry):
        return findings

    gtype = geom.geom_type
    if gtype not in ALLOWED_GEOM_TYPES:
        findings.append(Finding(
            ERROR, "GEOM_TYPE_UNKNOWN",
            f"Tipo de geometría final '{gtype}' no admitido.",
            REF_GEOJSON_SPEC, parcel_id=pid))
        return findings

    if gtype in ("Polygon", "MultiPolygon") and not geom.is_valid:
        findings.append(Finding(
            ERROR, "GEOM_SELF_INTERSECTION",
            "La geometría es inválida (auto-intersectada o mal formada, tipo 'ocho').",
            REF_GEOJSON_SPEC, parcel_id=pid))

    # Nota: los huecos (anillos interiores) ya se detectan en ingest.load_geojson
    # a partir de las coordenadas crudas (Parte GeoJSON). No se repite acá para
    # no duplicar el mismo hallazgo; este chequeo de validez cubre self-intersection
    # para cualquier origen de datos (GeoJSON o tabular).

    return findings


def _check_country(pid, row, geom, countries):
    findings = []
    code = row.get("ProducerCountry")

    if code is None or (isinstance(code, float) and pd.isna(code)) or str(code).strip() == "":
        findings.append(Finding(
            ERROR, "COUNTRY_MISSING",
            "Falta la propiedad ProducerCountry (obligatoria).",
            REF_GEOJSON_SPEC, parcel_id=pid))
        return findings

    code = str(code).strip().upper()

    if len(code) != 2 or pycountry.countries.get(alpha_2=code) is None:
        findings.append(Finding(
            ERROR, "COUNTRY_INVALID_ISO",
            f"'{code}' no es un código ISO 3166-1 alpha-2 válido.",
            REF_GEOJSON_SPEC, parcel_id=pid))
        return findings

    if code not in countries.index:
        findings.append(Finding(
            WARNING, "COUNTRY_OUT_OF_REFERENCE_SET",
            f"ProducerCountry='{code}' es válido pero está fuera del set de "
            "fronteras de referencia cargado (Cono Sur); no se pudo verificar "
            "coherencia geográfica.",
            "Producto 1 — set de fronteras de referencia", parcel_id=pid))
        return findings

    boundary = countries.loc[code, "geometry"]
    check_point = geom.centroid if geom.geom_type != "Point" else geom
    if not boundary.buffer(_COUNTRY_BOUNDARY_TOLERANCE_DEG).contains(check_point):
        findings.append(Finding(
            ERROR, "COUNTRY_MISMATCH",
            f"ProducerCountry='{code}' no coincide con la ubicación real de la "
            "geometría (el centroide de la parcela cae fuera del país declarado, "
            "incluso con margen de tolerancia).",
            REF_GEOJSON_SPEC, parcel_id=pid))

    return findings


def _check_area(pid, row, geom, area_calc_ha):
    findings = []
    declared = row.get("Area")
    is_point = geom is not None and geom.geom_type == "Point"

    declared_val = None
    if declared is not None and not (isinstance(declared, float) and pd.isna(declared)):
        try:
            declared_val = float(declared)
        except (TypeError, ValueError):
            findings.append(Finding(
                ERROR, "AREA_NOT_NUMERIC",
                f"El valor de Area ('{declared}') no es numérico.",
                REF_GEOJSON_SPEC, parcel_id=pid))
            declared_val = None

    if is_point:
        if declared_val is None:
            findings.append(Finding(
                WARNING, "POINT_NO_AREA",
                "La parcela es un Point sin Area declarada. El Information "
                "System asumirá 4 ha por defecto — riesgo silencioso si la "
                "parcela real es más grande o más chica.",
                REF_GEOJSON_SPEC, parcel_id=pid))
        elif declared_val > 4:
            findings.append(Finding(
                ERROR, "RULE_4HA_VIOLATION",
                f"Area declarada = {declared_val} ha (> 4 ha) pero la geometría "
                "es un Point. Parcelas de más de 4 ha deben declararse como "
                "polígono, con vértices suficientes para describir el perímetro.",
                REF_ART9, parcel_id=pid))
    else:
        if area_calc_ha > 4.0 and declared_val is not None and declared_val <= 4.0:
            findings.append(Finding(
                WARNING, "AREA_MISMATCH",
                f"El área calculada de la geometría ({area_calc_ha:.2f} ha) supera "
                f"4 ha pero el Area declarada ({declared_val} ha) no. Revisar cuál "
                "de los dos valores es correcto.",
                REF_GEOJSON_SPEC, parcel_id=pid))
        elif declared_val is not None and area_calc_ha > 1e-4:
            # umbral de 1e-4 ha (~1 m^2) para no confundir ruido de punto
            # flotante de geometrías inválidas (auto-intersectadas) con un
            # área real casi nula
            diff_pct = abs(declared_val - area_calc_ha) / area_calc_ha * 100
            if diff_pct > 15:
                findings.append(Finding(
                    WARNING, "AREA_MISMATCH",
                    f"Area declarada ({declared_val} ha) difiere {diff_pct:.0f}% del "
                    f"área calculada de la geometría ({area_calc_ha:.2f} ha).",
                    REF_GEOJSON_SPEC, parcel_id=pid))

    return findings


def _check_species(pid, row):
    findings = []
    common = row.get("CommonName")
    sci = row.get("ScientificName")
    missing = []
    if common is None or (isinstance(common, float) and pd.isna(common)) or str(common).strip() == "":
        missing.append("CommonName")
    if sci is None or (isinstance(sci, float) and pd.isna(sci)) or str(sci).strip() == "":
        missing.append("ScientificName")
    if missing:
        findings.append(Finding(
            WARNING, "SPECIES_MISSING",
            f"Falta(n) {', '.join(missing)}. Para madera, la DDS exige nombre "
            "común y nombre científico completo de la especie.",
            f"{REF_4084}, Art. 4", parcel_id=pid))
    return findings


def _check_overlaps(gdf, areas_ha):
    findings = []
    polys = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    if len(polys) < 2:
        return findings

    proj = polys.geometry.to_crs(AEA_CONO_SUR)
    proj = proj.reset_index(drop=True)
    pids = polys["ParcelID"].reset_index(drop=True)

    sindex = proj.sindex
    seen = set()
    for i, geom_i in enumerate(proj):
        candidates = list(sindex.intersection(geom_i.bounds))
        for j in candidates:
            if j <= i:
                continue
            key = (i, j)
            if key in seen:
                continue
            seen.add(key)
            geom_j = proj.iloc[j]
            inter = geom_i.intersection(geom_j)
            if not inter.is_empty and inter.area > 1.0:  # > 1 m^2, ignora ruido de borde
                findings.append(Finding(
                    ERROR, "PARCELS_OVERLAP",
                    f"La parcela '{pids[i]}' se superpone con '{pids[j]}' en "
                    f"{inter.area / 10000:.3f} ha.",
                    REF_GEOJSON_SPEC, parcel_id=f"{pids[i]} / {pids[j]}"))

    return findings
