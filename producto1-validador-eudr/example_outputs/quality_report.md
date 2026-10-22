# Quality report: EUDR supplier geometry validator

**Input file:** `synthetic_supplier_spreadsheet.xlsx`  
**Generated:** 2026-10-22 11:14  
**Commodity:** Wood (Southern Cone)  
**Reference format:** EUDR GeoJSON File Description v1.5 (Implementing Regulation (EU) 2024/3084)

## Executive summary

| Metric | Value |
|---|---|
| Parcels evaluated | 15 |
| Parcels ready to submit as-is | 7 |
| Parcels with blocking error | 8 |
| Blocking errors (total) | 7 |
| Warnings (non-blocking) | 6 |
| Conversion notes | 6 |

**What "ready" means:** the parcel has no finding of severity *Blocking error*. The output GeoJSON (`output.geojson`) contains only ready parcels. Parcels with a blocking error are left out of the output file and must be corrected at the source before attempting submission again.

## 🔴 Blocking errors (7)

- **[COUNTRY_INVALID_ISO]** Parcel `MSNS-011-INVALIDISO`: 'ZZ' is not a valid ISO 3166-1 alpha-2 code.
  *Basis: EUDR GeoJSON File Description v1.5*
- **[COUNTRY_MISMATCH]** Parcel `MSNS-006-LATLONSWAP`: ProducerCountry='AR' does not match the actual location of the geometry (the parcel centroid falls outside the declared country, even with a tolerance margin).
  *Basis: EUDR GeoJSON File Description v1.5*
- **[GEOM_SELF_INTERSECTION]** Parcel `MSNS-014-SELFINTERSECT`: The vertex sequence produces an invalid geometry (self-intersecting, figure-eight shape). Check the vertex order.
  *Basis: EUDR GeoJSON File Description v1.5*
- **[ING_MISSING_LATLON]** Parcel `MSNS-003-MISSINGLATLON`: Latitude or Longitude is missing.
  *Basis: Product 1: tabular input schema*
- **[ING_TWO_VERTICES]** Parcel `MSNS-004-TWOVERTICES`: The parcel has exactly 2 vertex rows: not enough for a polygon (minimum 3 distinct vertices) and not a single point. Check whether a vertex is missing or one was declared too many.
  *Basis: Product 1: tabular input schema*
- **[PARCELS_OVERLAP]** Parcel `MSNS-010-OVERLAP-A / MSNS-010-OVERLAP-B`: Parcel 'MSNS-010-OVERLAP-A' overlaps with 'MSNS-010-OVERLAP-B' by 7.170 ha.
  *Basis: EUDR GeoJSON File Description v1.5*
- **[RULE_4HA_VIOLATION]** Parcel `MSNS-008-4HAVIOLATION`: Declared Area = 8.0 ha (> 4 ha) but the geometry is a Point. Parcels larger than 4 ha must be declared as a polygon, with enough vertices to describe the perimeter.
  *Basis: Regulation (EU) 2023/1115, Art. 9*

## 🟡 Warnings (6)

- **[AREA_MISMATCH]** Parcel `MSNS-013-AREAMISMATCH`: The computed area of the geometry (14.94 ha) exceeds 4 ha but the declared Area (1.5 ha) does not. Check which of the two values is correct.
  *Basis: EUDR GeoJSON File Description v1.5*
- **[COORD_PRECISION]** Parcel `MSNS-007-PRECISION`: The longitude has 14 decimal places (recommended maximum: 6). More than 6 decimals can produce duplicate coordinates through rounding when processed by the system.
  *Basis: EUDR GeoJSON File Description v1.5*
- **[COORD_PRECISION]** Parcel `MSNS-007-PRECISION`: The latitude has 14 decimal places (recommended maximum: 6). More than 6 decimals can produce duplicate coordinates through rounding when processed by the system.
  *Basis: EUDR GeoJSON File Description v1.5*
- **[ING_METADATA_INCONSISTENT]** Parcel `MSNS-005-INCONSISTENT`: The property 'ProducerCountry' has different values across rows of the same parcel (['AR', 'BR']); the first one was used.
  *Basis: Product 1: metadata consistency per ParcelID*
- **[POINT_NO_AREA]** Parcel `MSNS-009-NOAREA`: The parcel is a Point with no declared Area. The Information System will assume 4 ha by default, a silent risk if the real parcel is larger or smaller.
  *Basis: EUDR GeoJSON File Description v1.5*
- **[SPECIES_MISSING]** Parcel `MSNS-012-NOSPECIES`: Missing: CommonName, ScientificName. For wood, the due diligence statement requires the common name and full scientific name of the species.
  *Basis: Implementing Regulation (EU) 2024/3084, Art. 4*

## ℹ️ Conversion notes (6)

- **[ING_AUTOCLOSE]** Parcel `MSNS-002`: The polygon was closed automatically by repeating the first vertex at the end (the source file did not repeat it, which is common practice in spreadsheets).
  *Basis: Product 1: tabular to GeoJSON conversion*
- **[ING_AUTOCLOSE]** Parcel `MSNS-005-INCONSISTENT`: The polygon was closed automatically by repeating the first vertex at the end (the source file did not repeat it, which is common practice in spreadsheets).
  *Basis: Product 1: tabular to GeoJSON conversion*
- **[ING_AUTOCLOSE]** Parcel `MSNS-010-OVERLAP-A`: The polygon was closed automatically by repeating the first vertex at the end (the source file did not repeat it, which is common practice in spreadsheets).
  *Basis: Product 1: tabular to GeoJSON conversion*
- **[ING_AUTOCLOSE]** Parcel `MSNS-010-OVERLAP-B`: The polygon was closed automatically by repeating the first vertex at the end (the source file did not repeat it, which is common practice in spreadsheets).
  *Basis: Product 1: tabular to GeoJSON conversion*
- **[ING_AUTOCLOSE]** Parcel `MSNS-013-AREAMISMATCH`: The polygon was closed automatically by repeating the first vertex at the end (the source file did not repeat it, which is common practice in spreadsheets).
  *Basis: Product 1: tabular to GeoJSON conversion*
- **[ING_AUTOCLOSE]** Parcel `MSNS-014-SELFINTERSECT`: The polygon was closed automatically by repeating the first vertex at the end (the source file did not repeat it, which is common practice in spreadsheets).
  *Basis: Product 1: tabular to GeoJSON conversion*
