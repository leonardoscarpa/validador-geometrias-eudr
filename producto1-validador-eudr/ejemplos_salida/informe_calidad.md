# Informe de calidad — Validador de geometrías de proveedores (EUDR)

**Archivo de entrada:** `synthetic_planilla_proveedores.xlsx`  
**Fecha de generación:** 2026-09-10 16:40  
**Commodity:** Madera (Cono Sur)  
**Formato de referencia:** EUDR GeoJSON File Description v1.5 (Reglamento de Ejecución (UE) 2024/3084)

## Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Parcelas evaluadas | 15 |
| Parcelas aptas para presentar tal cual | 7 |
| Parcelas con error bloqueante | 8 |
| Errores bloqueantes (total) | 7 |
| Advertencias (no bloqueantes) | 6 |
| Notas de conversión | 6 |

**Qué significa "apto":** la parcela no tiene ningún hallazgo de severidad *Error bloqueante*. El GeoJSON de salida (`output.geojson`) incluye únicamente las parcelas aptas. Las parcelas con error bloqueante quedan fuera del archivo de salida y deben corregirse en origen antes de volver a intentar la presentación.

## 🔴 Error bloqueantes (7)

- **[COUNTRY_INVALID_ISO]** — Parcela `MSNS-011-INVALIDISO`: 'ZZ' no es un código ISO 3166-1 alpha-2 válido.
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[COUNTRY_MISMATCH]** — Parcela `MSNS-006-LATLONSWAP`: ProducerCountry='AR' no coincide con la ubicación real de la geometría (el centroide de la parcela cae fuera del país declarado, incluso con margen de tolerancia).
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[GEOM_SELF_INTERSECTION]** — Parcela `MSNS-014-SELFINTERSECT`: La secuencia de vértices produce una geometría inválida (auto-intersectada, tipo 'ocho'). Revisar el orden de los vértices.
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[ING_MISSING_LATLON]** — Parcela `MSNS-003-MISSINGLATLON`: Falta Latitude o Longitude.
  *Fundamento: Producto 1 — esquema de entrada tabular*
- **[ING_TWO_VERTICES]** — Parcela `MSNS-004-TWOVERTICES`: La parcela tiene exactamente 2 filas de vértices: no alcanza para un polígono (mínimo 3 vértices distintos) y no es un único punto. Revisar si falta un vértice o si se declaró de más.
  *Fundamento: Producto 1 — esquema de entrada tabular*
- **[PARCELS_OVERLAP]** — Parcela `MSNS-010-OVERLAP-A / MSNS-010-OVERLAP-B`: La parcela 'MSNS-010-OVERLAP-A' se superpone con 'MSNS-010-OVERLAP-B' en 7.170 ha.
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[RULE_4HA_VIOLATION]** — Parcela `MSNS-008-4HAVIOLATION`: Area declarada = 8.0 ha (> 4 ha) pero la geometría es un Point. Parcelas de más de 4 ha deben declararse como polígono, con vértices suficientes para describir el perímetro.
  *Fundamento: Reglamento (UE) 2023/1115, Art. 9*

## 🟡 Advertencias (6)

- **[AREA_MISMATCH]** — Parcela `MSNS-013-AREAMISMATCH`: El área calculada de la geometría (14.94 ha) supera 4 ha pero el Area declarada (1.5 ha) no. Revisar cuál de los dos valores es correcto.
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[COORD_PRECISION]** — Parcela `MSNS-007-PRECISION`: La longitud tiene 14 decimales (máximo recomendado: 6). Más de 6 decimales puede generar coordenadas duplicadas por redondeo al procesarse en el sistema.
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[COORD_PRECISION]** — Parcela `MSNS-007-PRECISION`: La latitud tiene 14 decimales (máximo recomendado: 6). Más de 6 decimales puede generar coordenadas duplicadas por redondeo al procesarse en el sistema.
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[ING_METADATA_INCONSISTENT]** — Parcela `MSNS-005-INCONSISTENT`: La propiedad 'ProducerCountry' tiene valores distintos entre filas de la misma parcela (['AR', 'BR']); se usó el primero.
  *Fundamento: Producto 1 — consistencia de metadatos por ParcelID*
- **[POINT_NO_AREA]** — Parcela `MSNS-009-NOAREA`: La parcela es un Point sin Area declarada. El Information System asumirá 4 ha por defecto — riesgo silencioso si la parcela real es más grande o más chica.
  *Fundamento: EUDR GeoJSON File Description v1.5*
- **[SPECIES_MISSING]** — Parcela `MSNS-012-NOSPECIES`: Falta(n) CommonName, ScientificName. Para madera, la DDS exige nombre común y nombre científico completo de la especie.
  *Fundamento: Reglamento de Ejecución (UE) 2024/3084, Art. 4*

## ℹ️ Nota de conversións (6)

- **[ING_AUTOCLOSE]** — Parcela `MSNS-002`: El polígono se cerró automáticamente repitiendo el primer vértice al final (el archivo de origen no lo traía repetido, práctica habitual en planillas).
  *Fundamento: Producto 1 — conversión tabular → GeoJSON*
- **[ING_AUTOCLOSE]** — Parcela `MSNS-005-INCONSISTENT`: El polígono se cerró automáticamente repitiendo el primer vértice al final (el archivo de origen no lo traía repetido, práctica habitual en planillas).
  *Fundamento: Producto 1 — conversión tabular → GeoJSON*
- **[ING_AUTOCLOSE]** — Parcela `MSNS-010-OVERLAP-A`: El polígono se cerró automáticamente repitiendo el primer vértice al final (el archivo de origen no lo traía repetido, práctica habitual en planillas).
  *Fundamento: Producto 1 — conversión tabular → GeoJSON*
- **[ING_AUTOCLOSE]** — Parcela `MSNS-010-OVERLAP-B`: El polígono se cerró automáticamente repitiendo el primer vértice al final (el archivo de origen no lo traía repetido, práctica habitual en planillas).
  *Fundamento: Producto 1 — conversión tabular → GeoJSON*
- **[ING_AUTOCLOSE]** — Parcela `MSNS-013-AREAMISMATCH`: El polígono se cerró automáticamente repitiendo el primer vértice al final (el archivo de origen no lo traía repetido, práctica habitual en planillas).
  *Fundamento: Producto 1 — conversión tabular → GeoJSON*
- **[ING_AUTOCLOSE]** — Parcela `MSNS-014-SELFINTERSECT`: El polígono se cerró automáticamente repitiendo el primer vértice al final (el archivo de origen no lo traía repetido, práctica habitual en planillas).
  *Fundamento: Producto 1 — conversión tabular → GeoJSON*
