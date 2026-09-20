"""
Ingesta del Scorecard: lee la misma planilla "larga" de parcelas del
Producto 1, PERO reconociendo columnas adicionales con las señales del
Art. 10 que no se pueden calcular solas (pueblos indígenas, cadena de
suministro, certificaciones, historial de incumplimiento).

Dos niveles de agregación:
  filas (vértices)  ->  parcelas (por ParcelID)  ->  proveedores (por ProducerName)

Las columnas cualitativas deberían ser CONSISTENTES entre todas las parcelas
de un mismo proveedor (son atributos del proveedor, no de la parcela). Si no
lo son, se documenta como advertencia y se toma el valor que implica MÁS
riesgo — nunca se descarta en silencio una señal de riesgo declarada.
"""

import pandas as pd

from .country_risk import country_risk_tier, RISK_ORDER

BASE_ALIASES = {
    "parcelid": "ParcelID", "parcel_id": "ParcelID", "id": "ParcelID",
    "producername": "ProducerName", "productor": "ProducerName", "proveedor": "ProducerName",
    "producercountry": "ProducerCountry", "country": "ProducerCountry", "pais": "ProducerCountry",
    "area": "Area", "superficie": "Area", "hectareas": "Area",
}

QUALITATIVE_ALIASES = {
    "indigenouspeoples": "IndigenousPeoplesPresence", "pueblosindigenas": "IndigenousPeoplesPresence",
    "indigenouspeoplespresence": "IndigenousPeoplesPresence",
    "indigenousconsultation": "IndigenousConsultation", "consultaindigena": "IndigenousConsultation",
    "supplychainintermediaries": "SupplyChainIntermediaries", "intermediarios": "SupplyChainIntermediaries",
    "mixingriskdeclared": "MixingRiskDeclared", "riesgomezcla": "MixingRiskDeclared",
    "priornoncomplianceincidents": "PriorNonComplianceIncidents",
    "incumplimientosprevios": "PriorNonComplianceIncidents",
    "voluntarycertification": "VoluntaryCertification", "certificacion": "VoluntaryCertification",
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
    if s in ("yes", "si", "sí", "y", "true", "1"):
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
    """Devuelve (suppliers, warnings) donde suppliers es una lista de dicts:
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
        warnings.append(f"Faltan columnas obligatorias: {', '.join(sorted(missing))}.")
        return [], warnings

    # nivel 1: colapsar a una fila por ParcelID (toma el primer valor no nulo
    # de cada campo dentro del grupo — mismo criterio que el Producto 1)
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

    # nivel 2: agregar por ProducerName
    suppliers = {}
    for rec in parcel_rows:
        name = rec.get("ProducerName")
        if not name or str(name).strip() == "":
            warnings.append(f"Parcela '{rec['ParcelID']}' sin ProducerName — excluida del scorecard.")
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
            # si CUALQUIER parcela con pueblos indígenas no tiene consulta
            # documentada, el proveedor completo queda marcado como "sin consulta"
            if cons is not True:
                s["indigenous_consulted"] = False

        s["max_intermediaries"] = max(s["max_intermediaries"], _num(rec.get("SupplyChainIntermediaries"), 0))

        if _yesno(rec.get("MixingRiskDeclared")):
            s["mixing_risk"] = True

        s["total_incidents"] += _num(rec.get("PriorNonComplianceIncidents"), 0)

        cert = rec.get("VoluntaryCertification")
        if cert and str(cert).strip().lower() not in ("none", "ninguna", "no", ""):
            s["certifications"].add(str(cert).strip())

    for s in suppliers.values():
        if len(s["countries"]) > 1:
            warnings.append(
                f"Proveedor '{s['producer_name']}' tiene parcelas en más de un país "
                f"({', '.join(sorted(s['countries']))}); se usó el de mayor riesgo para el puntaje."
            )
        tiers = [country_risk_tier(c) for c in s["countries"]] or ["Estándar"]
        s["worst_country_tier"] = max(tiers, key=lambda t: RISK_ORDER[t])
        if not s["indigenous_present"]:
            s["indigenous_consulted"] = None  # no aplica

    return list(suppliers.values()), warnings
