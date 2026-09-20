from dataclasses import dataclass, field


@dataclass
class RiskFactor:
    points: float
    article: str          # ej. "Art. 10(c)(d)"
    label: str             # ej. "Pueblos indígenas sin consulta documentada"
    detail: str             # texto explicando el valor concreto que lo disparó


@dataclass
class SupplierScore:
    producer_name: str
    parcels: list = field(default_factory=list)   # ParcelIDs agregados
    total_area_ha: float = 0.0
    countries: set = field(default_factory=set)
    factors: list = field(default_factory=list)    # list[RiskFactor]
    total_points: float = 0.0
    tier: str = ""
    warnings: list = field(default_factory=list)   # inconsistencias detectadas al agregar
