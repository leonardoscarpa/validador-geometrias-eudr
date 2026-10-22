"""
Shared data model for the whole validator.

A Finding is a validation finding: it can come from the ingestion stage
(Excel/CSV to geometry conversion) or from the validation stage proper
(checks against the GeoJSON v1.5 / EUDR specification).
"""

from dataclasses import dataclass, field
from typing import Optional


# Severities. ERROR = the file cannot be submitted as-is to the Information
# System. WARNING = real but non-blocking risk (e.g. the silent 4 ha default).
# INFO = a decision the converter made that the user should know about, but
# not a data quality problem.
ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"

_SEVERITY_ORDER = {ERROR: 0, WARNING: 1, INFO: 2}


@dataclass
class Finding:
    severity: str                  # ERROR | WARNING | INFO
    code: str                      # short identifier, e.g. "RULE_4HA_VIOLATION"
    message: str                   # human-readable text for the report
    reference: str                 # citable regulatory/technical basis
    parcel_id: Optional[str] = None  # None = file-level finding

    def sort_key(self):
        return (_SEVERITY_ORDER.get(self.severity, 9), self.code, str(self.parcel_id))


@dataclass
class IngestResult:
    """Result of the ingestion stage: built geometries plus findings."""
    gdf: "object"                      # geopandas.GeoDataFrame (avoids a circular import in the type)
    findings: list = field(default_factory=list)
    source_format: str = ""            # "geojson" | "csv" | "xlsx"
    failed_ids: list = field(default_factory=list)  # ParcelIDs that NEVER became
    # a valid geometry (missing lat/lon, prohibited geometry, etc.).
    # They are not in gdf, but MUST be counted as "parcel evaluated with error".
