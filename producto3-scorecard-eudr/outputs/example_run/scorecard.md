# Scorecard de riesgo de proveedor — EUDR (Art. 10)

**Archivo de entrada:** `proveedores_sinteticos.xlsx`  
**Fecha de generación:** 2026-09-18 09:14  
**Fundamento normativo:** Reglamento (UE) 2023/1115, Art. 10 (criterios de evaluación de riesgo) — clasificación de país según Reglamento de Ejecución (UE) 2025/1093.

## Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Proveedores evaluados | 8 |
| 🔴 Riesgo Alto | 1 |
| 🟡 Riesgo Medio | 2 |
| 🟢 Riesgo Bajo | 5 |

**Nota de terminología:** "Bajo / Medio / Alto" acá es el nivel de riesgo del *proveedor* que calcula esta herramienta — no confundir con "Bajo / Estándar / Alto", que es la clasificación *oficial del país* según el Reglamento 2025/1093. El país es un insumo del puntaje del proveedor, no lo determina por sí solo.

## 🔴 Riesgo Alto (1)

### Exportadora del Norte — 6.0 puntos
Parcelas: P-E1 · Superficie total: 12.0 ha · País(es): BR

- **+1.0** [Art. 10(a)] Clasificación de país: Estándar — País(es) declarado(s): BR — Reglamento de Ejecución (UE) 2025/1093.
- **+2.0** [Art. 10(i)] Cadena de suministro larga (3 intermediarios) — 3 o más intermediarios declarados entre el productor y el operador.
- **+2.0** [Art. 10(j) / Art. 13] Riesgo de mezcla o elusión declarado — Se declaró riesgo de mezcla con producto de origen desconocido o de países de mayor riesgo.
- **+1.0** [Art. 10(l)] Historial de incumplimiento (2 incidente(s) previo(s)) — 1-2 incidentes de incumplimiento declarados.

## 🟡 Riesgo Medio (2)

### Establecimiento Yaguarete — 3.0 puntos
Parcelas: P-D1 · Superficie total: 8.0 ha · País(es): AR

- **+1.0** [Art. 10(a)] Clasificación de país: Estándar — País(es) declarado(s): AR — Reglamento de Ejecución (UE) 2025/1093.
- **+2.0** [Art. 10(c)(d)(e)] Pueblos indígenas presentes, SIN consulta documentada — Al menos una parcela reporta presencia de pueblos indígenas sin que conste consulta documentada — riesgo no mitigado.

### Maderera Litoral SA — 2.0 puntos
Parcelas: P-C1 · Superficie total: 6.0 ha · País(es): AR

- **+1.0** [Art. 10(a)] Clasificación de país: Estándar — País(es) declarado(s): AR — Reglamento de Ejecución (UE) 2025/1093.
- **+1.0** [Art. 10(i)] Cadena de suministro con intermediarios (2) — 1-2 intermediarios declarados.

## 🟢 Riesgo Bajo (5)

### Yerbatera San Ignacio — 1.5 puntos
Parcelas: P-I1 · Superficie total: 7.0 ha · País(es): AR

- **+1.0** [Art. 10(a)] Clasificación de país: Estándar — País(es) declarado(s): AR — Reglamento de Ejecución (UE) 2025/1093.
- **+0.5** [Art. 10(c)(d)] Pueblos indígenas presentes, con consulta documentada — Al menos una parcela reporta presencia de pueblos indígenas; la consulta figura como documentada en todas ellas.

### Forestal Don Aparicio — 1.0 puntos
Parcelas: P-B1 · Superficie total: 4.2 ha · País(es): AR

- **+1.0** [Art. 10(a)] Clasificación de país: Estándar — País(es) declarado(s): AR — Reglamento de Ejecución (UE) 2025/1093.

### Cooperativa Binacional — 1.0 puntos
Parcelas: P-G1, P-G2 · Superficie total: 6.0 ha · País(es): AR, CL

- **+1.0** [Art. 10(a)] Clasificación de país: Estándar — País(es) declarado(s): AR, CL — Reglamento de Ejecución (UE) 2025/1093.

### Vivero Andino SRL — 0.0 puntos
Parcelas: P-A1 · Superficie total: 5.0 ha · País(es): CL

- **+0.0** [Art. 10(a)] Clasificación de país: Bajo — País(es) declarado(s): CL — Reglamento de Ejecución (UE) 2025/1093.

### Pinares Certificados SA — 0.0 puntos
Parcelas: P-F1 · Superficie total: 10.0 ha · País(es): AR

- **+1.0** [Art. 10(a)] Clasificación de país: Estándar — País(es) declarado(s): AR — Reglamento de Ejecución (UE) 2025/1093.
- **-1.5** [Art. 10(n)] Certificación voluntaria: FSC — Esquema de verificación por terceros o certificación voluntaria declarada — atenúa el riesgo, no lo elimina; sigue exigiendo el resto de la debida diligencia.

## ⚠️ Advertencias de carga de datos

- Parcela 'P-H1' sin ProducerName — excluida del scorecard.
- Proveedor 'Cooperativa Binacional' tiene parcelas en más de un país (AR, CL); se usó el de mayor riesgo para el puntaje.
