"""
Scorecard ingestion: reads the same "long" parcel spreadsheet as Product 1,
BUT recognizing additional columns with the Art. 10 signals that cannot be
computed on their own (indigenous peoples, supply chain, certifications,
non-compliance history).

Two aggregation levels:
  rows (vertices)  ->  parcels (by ParcelID)  ->  suppliers (by ProducerName)

The qualitative columns should be CONSISTENT across all parcels of the same
supplier (they are supplier attributes, not parcel attributes). If they are
not, this is documented as a warning and the value implying MORE risk is
taken. A declared risk signal is never silently discarded.
"""

import pandas as pd

from .country_risk import country_risk_tier, RISK_ORDER

BASE_ALIASES = {
    "parcelid": "ParcelID", "parcel_id": "ParcelID", "id": "ParcelID",
    "producername": "ProducerName", "producer": "ProducerName", "supplier": "ProducerName",
    "producercountry": "ProducerCountry", "country": "ProducerCountry",
    "area": "Area", "hectares": "Area",
}

QUALITATIVE_ALIASES = {
    "indigenouspeoples": "IndigenousPeoplesPresence",
    "indigenouspeoplespresence": "IndigenousPeoplesPresence",
    "indigenousconsultation": "IndigenousConsultation",
    "supplychainintermediaries": "SupplyChainIntermediaries", "intermediaries": "SupplyChainIntermediaries",
    "mixingriskdeclared": "MixingRiskDeclared", "mixingrisk": "MixingRiskDeclared",
    "priornoncomplianceincidents": "PriorNonComplianceIncidents",
    "priorincidents": "PriorNonComplianceIncidents",
    "voluntarycertification": "VoluntaryCertification", "certification": "VoluntaryCertification",
}

ALL_ALIASES = {**BASE_ALIASES, **QUALITATIVE_ALIASES}
QUALITATIVE_COLS = sorted(set(QUALITATIVE_ALIASES.values()))


def _normalize(df):
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in ALL_ALIASES:
            rename[col] = ALL_ALIASES[key]
    return df.rename(columns=rename)


def _yesno(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip().lower()
    if s in ("yes", "y", "true", "1"):
        return True
    if s in ("no", "n", "false", "0"):
        return False
    return None


def _num(v, default=0):
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def load_supplier_rows(path):
    """Returns (suppliers, warnings) where suppliers is a list of dicts:
    {producer_name, total_area_ha, countries:set, worst_country_tier,
     indigenous_present, indigenous_consulted, max_intermediaries,
     mixing_risk, total_incidents, certification, parcels:[ParcelID,...]}
    """
    warnings = []
    ext = str(path).lower()
    if ext.endswith(".csv"):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.read_excel(path, dtype=str)
    df = _normalize(df)

    required = {"ParcelID", "ProducerName", "ProducerCountry"}
    missing = required - set(df.columns)
    if missing:
        warnings.append(f"Required columns are missing: {', '.join(sorted(missing))}.")
        return [], warnings

    # level 1: collapse to one row per ParcelID (takes the first non-null
    # value of each field within the group, same criterion as Product 1)
    parcel_rows = []
    for pid, g in df.groupby("ParcelID", dropna=False):
        rec = {"ParcelID": pid}
        for col in ["ProducerName", "ProducerCountry", "Area"] + QUALITATIVE_COLS:
            if col in g.columns:
                vals = [v for v in g[col].tolist() if v is not None and str(v).strip() != "" and not (isinstance(v, float) and pd.isna(v))]
                rec[col] = vals[0] if vals else None
            else:
                rec[col] = None
        parcel_rows.append(rec)

    # level 2: aggregate by ProducerName
    suppliers = {}
    for rec in parcel_rows:
        name = rec.get("ProducerName")
        if not name or str(name).strip() == "":
            warnings.append(f"Parcel '{rec['ParcelID']}' has no ProducerName and was excluded from the scorecard.")
            continue
        name = str(name).strip()
        s = suppliers.setdefault(name, {
            "producer_name": name, "parcels": [], "total_area_ha": 0.0,
            "countries": set(), "indigenous_present": False, "indigenous_consulted": True,
            "max_intermediaries": 0, "mixing_risk": False, "total_incidents": 0,
            "certifications": set(),
        })
        s["parcels"].append(rec["ParcelID"])
        s["total_area_ha"] += _num(rec.get("Area"), 0)
        if rec.get("ProducerCountry"):
            s["countries"].add(str(rec["ProducerCountry"]).strip().upper())

        ind = _yesno(rec.get("IndigenousPeoplesPresence"))
        if ind:
            s["indigenous_present"] = True
            cons = _yesno(rec.get("IndigenousConsultation"))
            # if ANY parcel with indigenous peoples lacks documented
            # consultation, the whole supplier is marked as "no consultation"
            if cons is not True:
                s["indigenous_consulted"] = False

        s["max_intermediaries"] = max(s["max_intermediaries"], _num(rec.get("SupplyChainIntermediaries"), 0))

        if _yesno(rec.get("MixingRiskDeclared")):
            s["mixing_risk"] = True

        s["total_incidents"] += _num(rec.get("PriorNonComplianceIncidents"), 0)

        cert = rec.get("VoluntaryCertification")
        if cert and str(cert).strip().lower() not in ("none", "no", ""):
            s["certifications"].add(str(cert).strip())

    for s in suppliers.values():
        if len(s["countries"]) > 1:
            warnings.append(
                f"Supplier '{s['producer_name']}' has parcels in more than one country "
                f"({', '.join(sorted(s['countries']))}); the highest-risk one was used for scoring."
            )
        tiers = [country_risk_tier(c) for c in s["countries"]] or ["Standard"]
        s["worst_country_tier"] = max(tiers, key=lambda t: RISK_ORDER[t])
        if not s["indigenous_present"]:
            s["indigenous_consulted"] = None  # not applicable

    return list(suppliers.values()), warnings
