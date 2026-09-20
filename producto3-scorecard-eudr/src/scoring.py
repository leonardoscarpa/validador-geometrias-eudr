from .models import RiskFactor, SupplierScore

COUNTRY_BASE_POINTS = {"Bajo": 0.0, "Estándar": 1.0, "Alto": 4.0}


def score_supplier(s):
    factors = []

    tier = s["worst_country_tier"]
    factors.append(RiskFactor(
        COUNTRY_BASE_POINTS[tier], "Art. 10(a)",
        f"Clasificación de país: {tier}",
        f"País(es) declarado(s): {', '.join(sorted(s['countries'])) or '(sin dato)'} "
        f"— Reglamento de Ejecución (UE) 2025/1093."
    ))

    if s["indigenous_present"]:
        if s["indigenous_consulted"]:
            factors.append(RiskFactor(0.5, "Art. 10(c)(d)",
                "Pueblos indígenas presentes, con consulta documentada",
                "Al menos una parcela reporta presencia de pueblos indígenas; "
                "la consulta figura como documentada en todas ellas."))
        else:
            factors.append(RiskFactor(2.0, "Art. 10(c)(d)(e)",
                "Pueblos indígenas presentes, SIN consulta documentada",
                "Al menos una parcela reporta presencia de pueblos indígenas "
                "sin que conste consulta documentada — riesgo no mitigado."))

    inter = s["max_intermediaries"]
    if inter >= 3:
        factors.append(RiskFactor(2.0, "Art. 10(i)",
            f"Cadena de suministro larga ({int(inter)} intermediarios)",
            "3 o más intermediarios declarados entre el productor y el operador."))
    elif inter >= 1:
        factors.append(RiskFactor(1.0, "Art. 10(i)",
            f"Cadena de suministro con intermediarios ({int(inter)})",
            "1-2 intermediarios declarados."))

    if s["mixing_risk"]:
        factors.append(RiskFactor(2.0, "Art. 10(j) / Art. 13",
            "Riesgo de mezcla o elusión declarado",
            "Se declaró riesgo de mezcla con producto de origen desconocido "
            "o de países de mayor riesgo."))

    inc = s["total_incidents"]
    if inc >= 3:
        factors.append(RiskFactor(3.0, "Art. 10(l)",
            f"Historial de incumplimiento ({int(inc)} incidentes previos)",
            "3 o más incidentes de incumplimiento declarados para este proveedor."))
    elif inc >= 1:
        factors.append(RiskFactor(1.0, "Art. 10(l)",
            f"Historial de incumplimiento ({int(inc)} incidente(s) previo(s))",
            "1-2 incidentes de incumplimiento declarados."))

    if s["certifications"]:
        factors.append(RiskFactor(-1.5, "Art. 10(n)",
            f"Certificación voluntaria: {', '.join(sorted(s['certifications']))}",
            "Esquema de verificación por terceros o certificación voluntaria declarada — "
            "atenúa el riesgo, no lo elimina; sigue exigiendo el resto de la debida diligencia."))

    total = max(sum(f.points for f in factors), 0.0)
    if total < 2:
        level = "Bajo"
    elif total < 5:
        level = "Medio"
    else:
        level = "Alto"

    return SupplierScore(
        producer_name=s["producer_name"], parcels=s["parcels"],
        total_area_ha=round(s["total_area_ha"], 2), countries=s["countries"],
        factors=factors, total_points=round(total, 2), tier=level,
    )


def score_all(suppliers):
    return [score_supplier(s) for s in suppliers]
