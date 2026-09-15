"""
Modelo de datos compartido por todo el validador.

Un Finding es un hallazgo de validación: puede venir de la etapa de ingesta
(conversión de Excel/CSV a geometría) o de la etapa de validación propiamente
dicha (chequeos contra la especificación GeoJSON v1.5 / EUDR).
"""

from dataclasses import dataclass, field
from typing import Optional


# Severidades. ERROR = el archivo no puede presentarse tal cual al Information
# System. WARNING = riesgo real pero no bloqueante (ej. default silencioso de
# 4 ha). INFO = decisión que tomó el conversor y que el usuario debería conocer,
# pero no es un problema de calidad del dato.
ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"

_SEVERITY_ORDER = {ERROR: 0, WARNING: 1, INFO: 2}


@dataclass
class Finding:
    severity: str                  # ERROR | WARNING | INFO
    code: str                      # identificador corto, ej. "RULE_4HA_VIOLATION"
    message: str                   # texto legible, en español, para el informe
    reference: str                 # fundamento normativo/técnico citable
    parcel_id: Optional[str] = None  # None = hallazgo a nivel de archivo completo

    def sort_key(self):
        return (_SEVERITY_ORDER.get(self.severity, 9), self.code, str(self.parcel_id))


@dataclass
class IngestResult:
    """Resultado de la etapa de ingesta: geometrías construidas + hallazgos."""
    gdf: "object"                      # geopandas.GeoDataFrame (evitamos import circular en el tipo)
    findings: list = field(default_factory=list)
    source_format: str = ""            # "geojson" | "csv" | "xlsx"
    failed_ids: list = field(default_factory=list)  # ParcelIDs que NUNCA llegaron
    # a formar una geometría válida (lat/lon faltante, geometría prohibida, etc.)
    # — no están en gdf, pero SÍ deben contarse como "parcela evaluada con error".
