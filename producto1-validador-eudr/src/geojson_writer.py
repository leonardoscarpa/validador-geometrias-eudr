"""
Writes the output GeoJSON conforming to specification v1.5: FeatureCollection,
coordinates rounded to 6 decimals, exact property capitalization, and ONLY
the parcels with no ERROR-severity finding (those with an ERROR cannot be
submitted as-is and are documented in the quality report, not in the output
file).
"""

import json

from .common import CANONICAL_PROPS, round_coords, MAX_DECIMALS
from .models import ERROR


def parcels_with_errors(findings):
    ids = set()
    for f in findings:
        if f.severity == ERROR and f.parcel_id is not None:
            for pid in str(f.parcel_id).split(" / "):
                ids.add(pid)
    return ids


def write_geojson(gdf, findings, path):
    bad_ids = parcels_with_errors(findings)
    clean = gdf[~gdf["ParcelID"].astype(str).isin(bad_ids)]

    features = []
    for _, row in clean.iterrows():
        geom = round_coords(row["geometry"], MAX_DECIMALS)
        props = {}
        for p in CANONICAL_PROPS:
            val = row.get(p)
            if val is None:
                continue
            try:
                import pandas as pd
                if isinstance(val, float) and pd.isna(val):
                    continue
            except ImportError:
                pass
            if p == "Area":
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    pass
            props[p] = val

        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": json.loads(json.dumps(geom.__geo_interface__)),
        })

    fc = {"type": "FeatureCollection", "features": features}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)

    return len(features), len(bad_ids)
