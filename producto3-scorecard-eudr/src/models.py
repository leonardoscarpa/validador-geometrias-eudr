from dataclasses import dataclass, field


@dataclass
class RiskFactor:
    points: float
    article: str          # e.g. "Art. 10(c)(d)"
    label: str             # e.g. "Indigenous peoples without documented consultation"
    detail: str             # text explaining the concrete value that triggered it


@dataclass
class SupplierScore:
    producer_name: str
    parcels: list = field(default_factory=list)   # aggregated ParcelIDs
    total_area_ha: float = 0.0
    countries: set = field(default_factory=set)
    factors: list = field(default_factory=list)    # list[RiskFactor]
    total_points: float = 0.0
    tier: str = ""
    warnings: list = field(default_factory=list)   # inconsistencies detected while aggregating
