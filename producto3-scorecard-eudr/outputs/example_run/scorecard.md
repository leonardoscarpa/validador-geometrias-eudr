# Supplier risk scorecard: EUDR (Art. 10)

**Input file:** `synthetic_suppliers.xlsx`  
**Generated:** 2026-10-22 11:16  
**Regulatory basis:** Regulation (EU) 2023/1115, Art. 10 (risk assessment criteria). Country classification per Implementing Regulation (EU) 2025/1093.

## Executive summary

| Metric | Value |
|---|---|
| Suppliers evaluated | 8 |
| 🔴 High risk | 1 |
| 🟡 Medium risk | 2 |
| 🟢 Low risk | 5 |

**Terminology note:** "Low / Medium / High" here is the risk level of the *supplier* computed by this tool. Do not confuse it with "Low / Standard / High", which is the *official country classification* under Regulation 2025/1093. The country is one input to the supplier score and does not determine it on its own.

## 🔴 High risk (1)

### Exportadora del Norte: 6.0 points
Parcels: P-E1 · Total area: 12.0 ha · Country(ies): BR

- **+1.0** [Art. 10(a)] Country classification: Standard: Declared country(ies): BR per Implementing Regulation (EU) 2025/1093.
- **+2.0** [Art. 10(i)] Long supply chain (3 intermediaries): 3 or more intermediaries declared between the producer and the operator.
- **+2.0** [Art. 10(j) / Art. 13] Mixing or circumvention risk declared: A risk of mixing with product of unknown origin or from higher-risk countries was declared.
- **+1.0** [Art. 10(l)] Non-compliance history (2 prior incident(s)): 1-2 non-compliance incidents declared.

## 🟡 Medium risk (2)

### Establecimiento Yaguarete: 3.0 points
Parcels: P-D1 · Total area: 8.0 ha · Country(ies): AR

- **+1.0** [Art. 10(a)] Country classification: Standard: Declared country(ies): AR per Implementing Regulation (EU) 2025/1093.
- **+2.0** [Art. 10(c)(d)(e)] Indigenous peoples present, WITHOUT documented consultation: At least one parcel reports the presence of indigenous peoples with no documented consultation. Unmitigated risk.

### Maderera Litoral SA: 2.0 points
Parcels: P-C1 · Total area: 6.0 ha · Country(ies): AR

- **+1.0** [Art. 10(a)] Country classification: Standard: Declared country(ies): AR per Implementing Regulation (EU) 2025/1093.
- **+1.0** [Art. 10(i)] Supply chain with intermediaries (2): 1-2 intermediaries declared.

## 🟢 Low risk (5)

### Yerbatera San Ignacio: 1.5 points
Parcels: P-I1 · Total area: 7.0 ha · Country(ies): AR

- **+1.0** [Art. 10(a)] Country classification: Standard: Declared country(ies): AR per Implementing Regulation (EU) 2025/1093.
- **+0.5** [Art. 10(c)(d)] Indigenous peoples present, with documented consultation: At least one parcel reports the presence of indigenous peoples; consultation is documented for all of them.

### Forestal Don Aparicio: 1.0 points
Parcels: P-B1 · Total area: 4.2 ha · Country(ies): AR

- **+1.0** [Art. 10(a)] Country classification: Standard: Declared country(ies): AR per Implementing Regulation (EU) 2025/1093.

### Cooperativa Binacional: 1.0 points
Parcels: P-G1, P-G2 · Total area: 6.0 ha · Country(ies): AR, CL

- **+1.0** [Art. 10(a)] Country classification: Standard: Declared country(ies): AR, CL per Implementing Regulation (EU) 2025/1093.

### Vivero Andino SRL: 0.0 points
Parcels: P-A1 · Total area: 5.0 ha · Country(ies): CL

- **+0.0** [Art. 10(a)] Country classification: Low: Declared country(ies): CL per Implementing Regulation (EU) 2025/1093.

### Pinares Certificados SA: 0.0 points
Parcels: P-F1 · Total area: 10.0 ha · Country(ies): AR

- **+1.0** [Art. 10(a)] Country classification: Standard: Declared country(ies): AR per Implementing Regulation (EU) 2025/1093.
- **-1.5** [Art. 10(n)] Voluntary certification: FSC: Third-party verification scheme or voluntary certification declared. It mitigates the risk but does not remove it; the rest of the due diligence is still required.

## ⚠️ Data loading warnings

- Parcel 'P-H1' has no ProducerName and was excluded from the scorecard.
- Supplier 'Cooperativa Binacional' has parcels in more than one country (AR, CL); the highest-risk one was used for scoring.
