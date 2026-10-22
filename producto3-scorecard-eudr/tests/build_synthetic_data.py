import pandas as pd

rows = []

def add(pid, producer, country, area, **extra):
    r = dict(ParcelID=pid, ProducerName=producer, ProducerCountry=country, Area=area,
              Latitude=-27.5, Longitude=-55.9)
    r.update(extra)
    rows.append(r)

# A: Low, clean (Chile, nothing else) -> expected: 0 points, Low
add("P-A1", "Vivero Andino SRL", "CL", 5)

# B: Standard only (Argentina, nothing else) -> expected: 1 point, Low
add("P-B1", "Forestal Don Aparicio", "AR", 4.2)

# C: Standard + 2 intermediaries -> expected: 1+1=2, Medium (exact boundary)
add("P-C1", "Maderera Litoral SA", "AR", 6, SupplyChainIntermediaries=2)

# D: Standard + indigenous peoples WITHOUT consultation -> expected: 1+2=3, Medium
add("P-D1", "Establecimiento Yaguarete", "AR", 8, IndigenousPeoplesPresence="Yes",
    IndigenousConsultation="No")

# E: compound high: standard + 3 intermediaries + mixing + 2 incidents -> 1+2+2+1=6, High
add("P-E1", "Exportadora del Norte", "BR", 12, SupplyChainIntermediaries=3,
    MixingRiskDeclared="Yes", PriorNonComplianceIncidents=2)

# F: standard + FSC certification -> 1 - 1.5 = -0.5 -> clamped to 0, Low
add("P-F1", "Pinares Certificados SA", "AR", 10, VoluntaryCertification="FSC")

# G: multi-country (AR standard + CL low) -> must raise a warning and use the worst (standard) = 1, Low
add("P-G1", "Cooperativa Binacional", "AR", 3)
add("P-G2", "Cooperativa Binacional", "CL", 3)

# H: no ProducerName -> must be excluded with a warning
add("P-H1", "", "AR", 2)

# I: indigenous peoples WITH documented consultation -> 1 + 0.5 = 1.5, Low
add("P-I1", "Yerbatera San Ignacio", "AR", 7, IndigenousPeoplesPresence="Yes",
    IndigenousConsultation="Yes")

df = pd.DataFrame(rows)
df.to_excel("data/synthetic_suppliers.xlsx", index=False)
print("rows:", len(df), "| unique suppliers:", df["ProducerName"].nunique())
