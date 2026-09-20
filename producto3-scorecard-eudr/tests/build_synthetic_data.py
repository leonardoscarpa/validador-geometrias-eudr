import pandas as pd

rows = []

def add(pid, producer, country, area, **extra):
    r = dict(ParcelID=pid, ProducerName=producer, ProducerCountry=country, Area=area,
              Latitude=-27.5, Longitude=-55.9)
    r.update(extra)
    rows.append(r)

# A — Bajo, limpio (Chile, sin nada mas) -> esperado: 0 puntos, Bajo
add("P-A1", "Vivero Andino SRL", "CL", 5)

# B — Estandar solo (Argentina, sin nada mas) -> esperado: 1 punto, Bajo
add("P-B1", "Forestal Don Aparicio", "AR", 4.2)

# C — Estandar + 2 intermediarios -> esperado: 1+1=2, Medio (limite exacto)
add("P-C1", "Maderera Litoral SA", "AR", 6, SupplyChainIntermediaries=2)

# D — Estandar + pueblos indigenas SIN consulta -> esperado: 1+2=3, Medio
add("P-D1", "Establecimiento Yaguarete", "AR", 8, IndigenousPeoplesPresence="Si",
    IndigenousConsultation="No")

# E — compuesto alto: estandar + 3 intermediarios + mezcla + 2 incidentes -> 1+2+2+1=6, Alto
add("P-E1", "Exportadora del Norte", "BR", 12, SupplyChainIntermediaries=3,
    MixingRiskDeclared="Si", PriorNonComplianceIncidents=2)

# F — estandar + certificacion FSC -> 1 - 1.5 = -0.5 -> clamp a 0, Bajo
add("P-F1", "Pinares Certificados SA", "AR", 10, VoluntaryCertification="FSC")

# G — multi-pais (AR estandar + CL bajo) -> debe generar warning y usar el peor (estandar) = 1, Bajo
add("P-G1", "Cooperativa Binacional", "AR", 3)
add("P-G2", "Cooperativa Binacional", "CL", 3)

# H — sin ProducerName -> debe excluirse con warning
add("P-H1", "", "AR", 2)

# I — pueblos indigenas CON consulta documentada -> 1 + 0.5 = 1.5, Bajo
add("P-I1", "Yerbatera San Ignacio", "AR", 7, IndigenousPeoplesPresence="Si",
    IndigenousConsultation="Si")

df = pd.DataFrame(rows)
df.to_excel("data/proveedores_sinteticos.xlsx", index=False)
print("filas:", len(df), "| proveedores unicos:", df["ProducerName"].nunique())
