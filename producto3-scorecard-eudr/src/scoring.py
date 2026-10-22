from .models import RiskFactor, SupplierScore

COUNTRY_BASE_POINTS = {"Low": 0.0, "Standard": 1.0, "High": 4.0}


def score_supplier(s):
    factors = []

    tier = s["worst_country_tier"]
    factors.append(RiskFactor(
        COUNTRY_BASE_POINTS[tier], "Art. 10(a)",
        f"Country classification: {tier}",
        f"Declared country(ies): {', '.join(sorted(s['countries'])) or '(no data)'} "
        f"per Implementing Regulation (EU) 2025/1093."
    ))

    if s["indigenous_present"]:
        if s["indigenous_consulted"]:
            factors.append(RiskFactor(0.5, "Art. 10(c)(d)",
                "Indigenous peoples present, with documented consultation",
                "At least one parcel reports the presence of indigenous peoples; "
                "consultation is documented for all of them."))
        else:
            factors.append(RiskFactor(2.0, "Art. 10(c)(d)(e)",
                "Indigenous peoples present, WITHOUT documented consultation",
                "At least one parcel reports the presence of indigenous peoples "
                "with no documented consultation. Unmitigated risk."))

    inter = s["max_intermediaries"]
    if inter >= 3:
        factors.append(RiskFactor(2.0, "Art. 10(i)",
            f"Long supply chain ({int(inter)} intermediaries)",
            "3 or more intermediaries declared between the producer and the operator."))
    elif inter >= 1:
        factors.append(RiskFactor(1.0, "Art. 10(i)",
            f"Supply chain with intermediaries ({int(inter)})",
            "1-2 intermediaries declared."))

    if s["mixing_risk"]:
        factors.append(RiskFactor(2.0, "Art. 10(j) / Art. 13",
            "Mixing or circumvention risk declared",
            "A risk of mixing with product of unknown origin "
            "or from higher-risk countries was declared."))

    inc = s["total_incidents"]
    if inc >= 3:
        factors.append(RiskFactor(3.0, "Art. 10(l)",
            f"Non-compliance history ({int(inc)} prior incidents)",
            "3 or more non-compliance incidents declared for this supplier."))
    elif inc >= 1:
        factors.append(RiskFactor(1.0, "Art. 10(l)",
            f"Non-compliance history ({int(inc)} prior incident(s))",
            "1-2 non-compliance incidents declared."))

    if s["certifications"]:
        factors.append(RiskFactor(-1.5, "Art. 10(n)",
            f"Voluntary certification: {', '.join(sorted(s['certifications']))}",
            "Third-party verification scheme or voluntary certification declared. "
            "It mitigates the risk but does not remove it; the rest of the due diligence is still required."))

    total = max(sum(f.points for f in factors), 0.0)
    if total < 2:
        level = "Low"
    elif total < 5:
        level = "Medium"
    else:
        level = "High"

    return SupplierScore(
        producer_name=s["producer_name"], parcels=s["parcels"],
        total_area_ha=round(s["total_area_ha"], 2), countries=s["countries"],
        factors=factors, total_points=round(total, 2), tier=level,
    )


def score_all(suppliers):
    return [score_supplier(s) for s in suppliers]
