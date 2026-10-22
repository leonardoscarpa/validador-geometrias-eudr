"""
Validators that operate on the already-built internal GeoDataFrame (regardless
of whether it came from GeoJSON, CSV or Excel). Each function returns a list of
Findings. `run_all` runs them all and adds file-level findings (size, number of
parcels, etc.).
"""

import os

import geopandas as gpd
import pandas as pd
import pycountry
from shapely.geometry.base import BaseGeometry

from .models import Finding, ERROR, WARNING
from .common import ALLOWED_GEOM_TYPES, REF_GEOJSON_SPEC, REF_ART9, REF_4084

# Equal-area projection centered on the Southern Cone (Albers Equal Area
# Conic, parameters tuned to the region). Used ONLY to compute hectares
# consistently; nothing is exported in this projection.
AEA_SOUTHERN_CONE = (
    "+proj=aea +lat_1=-5 +lat_2=-42 +lat_0=-32 +lon_0=-60 "
    "+x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs"
)

_COUNTRY_BOUNDARY_TOLERANCE_DEG = 0.08  # margin for border simplification


def _load_country_boundaries(path):
    gdf = gpd.read_file(path)
    return gdf.set_index("iso2")


def compute_areas_ha(gdf):
    """Returns a Series with the area in hectares of each geometry
    (0 for points)."""
    proj = gdf.geometry.to_crs(AEA_SOUTHERN_CONE)
    return proj.area / 10000.0


def run_all(gdf, country_boundaries_path, commodity="wood"):
    findings = []

    if gdf.empty:
        return findings

    if gdf["ParcelID"].duplicated().any():
        dupes = gdf.loc[gdf["ParcelID"].duplicated(), "ParcelID"].unique().tolist()
        for d in dupes:
            findings.append(Finding(
                ERROR, "DUPLICATE_PARCEL_ID",
                f"ParcelID '{d}' appears on more than one parcel in the file. "
                "Each parcel needs a unique identifier.",
                "Product 1: parcel identification", parcel_id=d))

    areas_ha = compute_areas_ha(gdf)
    countries = _load_country_boundaries(country_boundaries_path)

    for idx, row in gdf.iterrows():
        pid = row["ParcelID"]
        geom = row["geometry"]
        area_calc = areas_ha.loc[idx]

        findings.extend(_check_geometry_validity(pid, geom))
        findings.extend(_check_country(pid, row, geom, countries))
        findings.extend(_check_area(pid, row, geom, area_calc))
        if commodity == "wood":
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
            f"Final geometry type '{gtype}' is not allowed.",
            REF_GEOJSON_SPEC, parcel_id=pid))
        return findings

    if gtype in ("Polygon", "MultiPolygon") and not geom.is_valid:
        findings.append(Finding(
            ERROR, "GEOM_SELF_INTERSECTION",
            "The geometry is invalid (self-intersecting or malformed, e.g. a figure-eight shape).",
            REF_GEOJSON_SPEC, parcel_id=pid))

    # Note: holes (interior rings) are already detected in ingest.load_geojson
    # from the raw coordinates (GeoJSON part). They are not repeated here to
    # avoid duplicating the same finding; this validity check covers
    # self-intersection for any data source (GeoJSON or tabular).

    return findings


def _check_country(pid, row, geom, countries):
    findings = []
    code = row.get("ProducerCountry")

    if code is None or (isinstance(code, float) and pd.isna(code)) or str(code).strip() == "":
        findings.append(Finding(
            ERROR, "COUNTRY_MISSING",
            "The ProducerCountry property is missing (required).",
            REF_GEOJSON_SPEC, parcel_id=pid))
        return findings

    code = str(code).strip().upper()

    if len(code) != 2 or pycountry.countries.get(alpha_2=code) is None:
        findings.append(Finding(
            ERROR, "COUNTRY_INVALID_ISO",
            f"'{code}' is not a valid ISO 3166-1 alpha-2 code.",
            REF_GEOJSON_SPEC, parcel_id=pid))
        return findings

    if code not in countries.index:
        findings.append(Finding(
            WARNING, "COUNTRY_OUT_OF_REFERENCE_SET",
            f"ProducerCountry='{code}' is valid but outside the loaded reference "
            "border set (Southern Cone); geographic consistency could not be "
            "verified.",
            "Product 1: reference border set", parcel_id=pid))
        return findings

    boundary = countries.loc[code, "geometry"]
    check_point = geom.centroid if geom.geom_type != "Point" else geom
    if not boundary.buffer(_COUNTRY_BOUNDARY_TOLERANCE_DEG).contains(check_point):
        findings.append(Finding(
            ERROR, "COUNTRY_MISMATCH",
            f"ProducerCountry='{code}' does not match the actual location of the "
            "geometry (the parcel centroid falls outside the declared country, "
            "even with a tolerance margin).",
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
                f"The Area value ('{declared}') is not numeric.",
                REF_GEOJSON_SPEC, parcel_id=pid))
            declared_val = None

    if is_point:
        if declared_val is None:
            findings.append(Finding(
                WARNING, "POINT_NO_AREA",
                "The parcel is a Point with no declared Area. The Information "
                "System will assume 4 ha by default, a silent risk if the "
                "real parcel is larger or smaller.",
                REF_GEOJSON_SPEC, parcel_id=pid))
        elif declared_val > 4:
            findings.append(Finding(
                ERROR, "RULE_4HA_VIOLATION",
                f"Declared Area = {declared_val} ha (> 4 ha) but the geometry "
                "is a Point. Parcels larger than 4 ha must be declared as a "
                "polygon, with enough vertices to describe the perimeter.",
                REF_ART9, parcel_id=pid))
    else:
        if area_calc_ha > 4.0 and declared_val is not None and declared_val <= 4.0:
            findings.append(Finding(
                WARNING, "AREA_MISMATCH",
                f"The computed area of the geometry ({area_calc_ha:.2f} ha) exceeds "
                f"4 ha but the declared Area ({declared_val} ha) does not. Check which "
                "of the two values is correct.",
                REF_GEOJSON_SPEC, parcel_id=pid))
        elif declared_val is not None and area_calc_ha > 1e-4:
            # 1e-4 ha threshold (~1 m^2) so floating-point noise from invalid
            # (self-intersecting) geometries is not mistaken for a real,
            # nearly zero area
            diff_pct = abs(declared_val - area_calc_ha) / area_calc_ha * 100
            if diff_pct > 15:
                findings.append(Finding(
                    WARNING, "AREA_MISMATCH",
                    f"Declared Area ({declared_val} ha) differs by {diff_pct:.0f}% from the "
                    f"computed area of the geometry ({area_calc_ha:.2f} ha).",
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
            f"Missing: {', '.join(missing)}. For wood, the due diligence statement "
            "requires the common name and full scientific name of the species.",
            f"{REF_4084}, Art. 4", parcel_id=pid))
    return findings


def _check_overlaps(gdf, areas_ha):
    findings = []
    polys = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    if len(polys) < 2:
        return findings

    proj = polys.geometry.to_crs(AEA_SOUTHERN_CONE)
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
            if not inter.is_empty and inter.area > 1.0:  # > 1 m^2, ignores edge noise
                findings.append(Finding(
                    ERROR, "PARCELS_OVERLAP",
                    f"Parcel '{pids[i]}' overlaps with '{pids[j]}' by "
                    f"{inter.area / 10000:.3f} ha.",
                    REF_GEOJSON_SPEC, parcel_id=f"{pids[i]} / {pids[j]}"))

    return findings
