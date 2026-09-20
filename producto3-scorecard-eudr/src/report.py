import datetime

TIER_ICON = {"Bajo": "🟢", "Medio": "🟡", "Alto": "🔴"}


def generate_markdown(scores, warnings, input_filename):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# Scorecard de riesgo de proveedor — EUDR (Art. 10)")
    lines.append("")
    lines.append(f"**Archivo de entrada:** `{input_filename}`  ")
    lines.append(f"**Fecha de generación:** {now}  ")
    lines.append("**Fundamento normativo:** Reglamento (UE) 2023/1115, Art. 10 (criterios de evaluación de "
                  "riesgo) — clasificación de país según Reglamento de Ejecución (UE) 2025/1093.")
    lines.append("")

    by_tier = {"Alto": [], "Medio": [], "Bajo": []}
    for s in scores:
        by_tier[s.tier].append(s)

    lines.append("## Resumen ejecutivo")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---|---|")
    lines.append(f"| Proveedores evaluados | {len(scores)} |")
    lines.append(f"| 🔴 Riesgo Alto | {len(by_tier['Alto'])} |")
    lines.append(f"| 🟡 Riesgo Medio | {len(by_tier['Medio'])} |")
    lines.append(f"| 🟢 Riesgo Bajo | {len(by_tier['Bajo'])} |")
    lines.append("")
    lines.append(
        "**Nota de terminología:** \"Bajo / Medio / Alto\" acá es el nivel de riesgo del "
        "*proveedor* que calcula esta herramienta — no confundir con \"Bajo / Estándar / Alto\", "
        "que es la clasificación *oficial del país* según el Reglamento 2025/1093. El país es un "
        "insumo del puntaje del proveedor, no lo determina por sí solo."
    )
    lines.append("")

    for tier in ("Alto", "Medio", "Bajo"):
        group = sorted(by_tier[tier], key=lambda s: -s.total_points)
        if not group:
            continue
        lines.append(f"## {TIER_ICON[tier]} Riesgo {tier} ({len(group)})")
        lines.append("")
        for s in group:
            lines.append(f"### {s.producer_name} — {s.total_points} puntos")
            lines.append(f"Parcelas: {', '.join(s.parcels)} · Superficie total: {s.total_area_ha} ha · "
                          f"País(es): {', '.join(sorted(s.countries)) or '(sin dato)'}")
            lines.append("")
            for f in s.factors:
                sign = "+" if f.points >= 0 else ""
                lines.append(f"- **{sign}{f.points}** [{f.article}] {f.label} — {f.detail}")
            lines.append("")

    if warnings:
        lines.append("## ⚠️ Advertencias de carga de datos")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines)


def generate_excel(scores, warnings, input_filename, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()

    ws_f = wb.active
    ws_f.title = "Factores"
    ws_f.append(["Proveedor", "Puntos", "Articulo", "Factor", "Detalle"])
    for s in scores:
        for f in s.factors:
            ws_f.append([s.producer_name, f.points, f.article, f.label, f.detail])

    ws_s = wb.create_sheet("Proveedores")
    ws_s.append(["Proveedor", "Parcelas", "Superficie (ha)", "Paises", "Puntaje total", "Nivel"])
    for i, s in enumerate(scores, start=2):
        ws_s.append([s.producer_name, len(s.parcels), s.total_area_ha,
                     ", ".join(sorted(s.countries)), s.total_points, s.tier])

    ws_r = wb.create_sheet("Resumen", 0)
    ws_r.append(["Scorecard de riesgo de proveedor — EUDR (Art. 10)"])
    ws_r.append(["Archivo de entrada", input_filename])
    ws_r.append(["Fecha de generación", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")])
    ws_r.append([])
    ws_r.append(["Métrica", "Valor"])
    last_s = len(scores) + 1
    ws_r.append(["Proveedores evaluados", f"=COUNTA(Proveedores!A2:A{last_s})" if scores else 0])
    ws_r.append(["Riesgo Alto", f'=COUNTIF(Proveedores!F2:F{last_s},"Alto")' if scores else 0])
    ws_r.append(["Riesgo Medio", f'=COUNTIF(Proveedores!F2:F{last_s},"Medio")' if scores else 0])
    ws_r.append(["Riesgo Bajo", f'=COUNTIF(Proveedores!F2:F{last_s},"Bajo")' if scores else 0])
    ws_r.append([])
    ws_r.append(["Nota: \"Bajo/Medio/Alto\" es el nivel de riesgo del PROVEEDOR calculado por esta "
                  "herramienta, distinto de \"Bajo/Estandar/Alto\" (clasificacion OFICIAL del pais, "
                  "Reglamento 2025/1093), que es solo uno de los insumos del puntaje."])

    header_fill = PatternFill(start_color="2F5233", end_color="2F5233", fill_type="solid")
    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    for ws in (ws_f, ws_s):
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
        for col_idx, width in enumerate([26, 10, 16, 34, 70][:ws.max_column], start=1):
            ws.column_dimensions[chr(64 + col_idx)].width = width
    ws_r["A1"].font = Font(name="Arial", bold=True, size=14)
    ws_r["A5"].font = header_font; ws_r["A5"].fill = header_fill
    ws_r["B5"].font = header_font; ws_r["B5"].fill = header_fill
    ws_r.column_dimensions["A"].width = 30
    ws_r.column_dimensions["B"].width = 70
    for ws in (ws_r, ws_s, ws_f):
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True

    wb.save(path)
