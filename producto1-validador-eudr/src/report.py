"""
Genera el informe de calidad en tres formatos: Markdown, PDF y Excel.
El público objetivo es un equipo de compliance que trabaja en SAP/Excel, no
especialistas en teledetección — por eso el lenguaje evita jerga geoespacial
y cada hallazgo cita su fundamento normativo/técnico.
"""

import datetime

from .models import ERROR, WARNING, INFO

SEVERITY_LABEL = {
    ERROR: "Error bloqueante",
    WARNING: "Advertencia",
    INFO: "Nota de conversión",
}
SEVERITY_ICON = {ERROR: "🔴", WARNING: "🟡", INFO: "ℹ️"}


def build_summary(gdf, findings, failed_ids=None):
    failed_ids = list(failed_ids or [])
    bad_ids = set()
    n_error = n_warning = n_info = 0
    for f in findings:
        if f.severity == ERROR:
            n_error += 1
            if f.parcel_id:
                for pid in str(f.parcel_id).split(" / "):
                    bad_ids.add(pid)
        elif f.severity == WARNING:
            n_warning += 1
        elif f.severity == INFO:
            n_info += 1

    # Se cuenta por REGISTRO: filas del GeoDataFrame (parcelas que llegaron a
    # tener geometría) MÁS los ParcelID que fallaron tan temprano en la
    # ingesta que nunca llegaron a formar una geometría (lat/lon faltante,
    # geometría prohibida, etc.) — esos también son "parcelas evaluadas con
    # error", no deben desaparecer del conteo.
    n_gdf = len(gdf) if not gdf.empty else 0
    total_parcels = n_gdf + len(failed_ids)
    bad_rows_in_gdf = int(gdf["ParcelID"].astype(str).isin(bad_ids).sum()) if n_gdf else 0
    bad_parcels = bad_rows_in_gdf + len(failed_ids)
    ok_parcels = total_parcels - bad_parcels

    return {
        "total_parcels": total_parcels,
        "ok_parcels": max(ok_parcels, 0),
        "bad_parcels": bad_parcels,
        "n_error": n_error,
        "n_warning": n_warning,
        "n_info": n_info,
    }


def _sorted_findings(findings):
    return sorted(findings, key=lambda f: f.sort_key())


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def generate_markdown(gdf, findings, input_filename, commodity="Madera (Cono Sur)", failed_ids=None):
    s = build_summary(gdf, findings, failed_ids)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# Informe de calidad — Validador de geometrías de proveedores (EUDR)")
    lines.append("")
    lines.append(f"**Archivo de entrada:** `{input_filename}`  ")
    lines.append(f"**Fecha de generación:** {now}  ")
    lines.append(f"**Commodity:** {commodity}  ")
    lines.append("**Formato de referencia:** EUDR GeoJSON File Description v1.5 "
                  "(Reglamento de Ejecución (UE) 2024/3084)")
    lines.append("")
    lines.append("## Resumen ejecutivo")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---|---|")
    lines.append(f"| Parcelas evaluadas | {s['total_parcels']} |")
    lines.append(f"| Parcelas aptas para presentar tal cual | {s['ok_parcels']} |")
    lines.append(f"| Parcelas con error bloqueante | {s['bad_parcels']} |")
    lines.append(f"| Errores bloqueantes (total) | {s['n_error']} |")
    lines.append(f"| Advertencias (no bloqueantes) | {s['n_warning']} |")
    lines.append(f"| Notas de conversión | {s['n_info']} |")
    lines.append("")
    lines.append(
        "**Qué significa \"apto\":** la parcela no tiene ningún hallazgo de "
        "severidad *Error bloqueante*. El GeoJSON de salida (`output.geojson`) "
        "incluye únicamente las parcelas aptas. Las parcelas con error bloqueante "
        "quedan fuera del archivo de salida y deben corregirse en origen antes de "
        "volver a intentar la presentación."
    )
    lines.append("")

    sorted_findings = _sorted_findings(findings)
    for sev in (ERROR, WARNING, INFO):
        subset = [f for f in sorted_findings if f.severity == sev]
        if not subset:
            continue
        lines.append(f"## {SEVERITY_ICON[sev]} {SEVERITY_LABEL[sev]}s ({len(subset)})")
        lines.append("")
        for f in subset:
            pid_txt = f" — Parcela `{f.parcel_id}`" if f.parcel_id else " — Archivo completo"
            lines.append(f"- **[{f.code}]**{pid_txt}: {f.message}")
            lines.append(f"  *Fundamento: {f.reference}*")
        lines.append("")

    if not findings:
        lines.append("No se detectaron hallazgos: todas las parcelas cumplen los "
                      "chequeos aplicados. ✅")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PDF (reportlab)
# ---------------------------------------------------------------------------

def generate_pdf(gdf, findings, input_filename, path, commodity="Madera (Cono Sur)", failed_ids=None):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    )

    s = build_summary(gdf, findings, failed_ids)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="FindingMsg", parent=styles["Normal"], fontSize=9, leading=12))

    doc = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=18 * mm, rightMargin=18 * mm,
                             topMargin=16 * mm, bottomMargin=16 * mm)
    story = []

    story.append(Paragraph("Informe de calidad — Validador de geometrías de proveedores (EUDR)",
                            styles["Title"]))
    story.append(Spacer(1, 4 * mm))
    meta_tbl = Table([
        ["Archivo de entrada", input_filename],
        ["Fecha de generación", now],
        ["Commodity", commodity],
        ["Formato de referencia", "EUDR GeoJSON File Description v1.5 (Reglamento 2024/3084)"],
    ], colWidths=[45 * mm, 120 * mm])
    meta_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Resumen ejecutivo", styles["Heading2"]))
    summary_data = [
        ["Métrica", "Valor"],
        ["Parcelas evaluadas", str(s["total_parcels"])],
        ["Parcelas aptas para presentar tal cual", str(s["ok_parcels"])],
        ["Parcelas con error bloqueante", str(s["bad_parcels"])],
        ["Errores bloqueantes (total)", str(s["n_error"])],
        ["Advertencias (no bloqueantes)", str(s["n_warning"])],
        ["Notas de conversión", str(s["n_info"])],
    ]
    sum_tbl = Table(summary_data, colWidths=[100 * mm, 40 * mm])
    sum_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f5233")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "<b>Qué significa \"apto\":</b> la parcela no tiene ningún hallazgo de "
        "severidad Error bloqueante. El GeoJSON de salida incluye únicamente las "
        "parcelas aptas.", styles["Small"]))
    story.append(PageBreak())

    sorted_findings = _sorted_findings(findings)
    sev_colors = {
        ERROR: colors.HexColor("#c0392b"),
        WARNING: colors.HexColor("#b7950b"),
        INFO: colors.HexColor("#2874a6"),
    }
    for sev in (ERROR, WARNING, INFO):
        subset = [f for f in sorted_findings if f.severity == sev]
        if not subset:
            continue
        story.append(Paragraph(f"{SEVERITY_LABEL[sev]}s ({len(subset)})",
                                ParagraphStyle(name=f"H_{sev}", parent=styles["Heading2"],
                                               textColor=sev_colors[sev])))
        story.append(Spacer(1, 2 * mm))
        rows = [["Parcela", "Código", "Detalle"]]
        for f in subset:
            pid_txt = f.parcel_id if f.parcel_id else "Archivo completo"
            pid_p = Paragraph(str(pid_txt), styles["FindingMsg"])
            code_p = Paragraph(f.code, styles["FindingMsg"])
            detail = Paragraph(f"{f.message}<br/><font size=7 color='grey'>{f.reference}</font>",
                                styles["FindingMsg"])
            rows.append([pid_p, code_p, detail])
        t = Table(rows, colWidths=[36 * mm, 36 * mm, 98 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 6 * mm))

    if not findings:
        story.append(Paragraph("No se detectaron hallazgos: todas las parcelas "
                                "cumplen los chequeos aplicados.", styles["Normal"]))

    doc.build(story)


# ---------------------------------------------------------------------------
# Excel (openpyxl, con fórmulas para que el resumen se recalcule)
# ---------------------------------------------------------------------------

def generate_excel(gdf, findings, areas_ha, input_filename, path, commodity="Madera (Cono Sur)",
                    failed_ids=None):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    failed_ids = list(failed_ids or [])
    wb = Workbook()

    # ---- Hoja Hallazgos (datos base) ----
    ws_f = wb.active
    ws_f.title = "Hallazgos"
    headers = ["Severidad", "ParcelID", "Codigo", "Mensaje", "Referencia normativa"]
    ws_f.append(headers)
    for f in _sorted_findings(findings):
        ws_f.append([f.severity, f.parcel_id or "(archivo completo)", f.code, f.message, f.reference])

    # ---- Hoja Parcelas (una fila por parcela, con formula de Estado) ----
    ws_p = wb.create_sheet("Parcelas")
    ws_p.append(["ParcelID", "Tipo de geometria", "Area calculada (ha)",
                 "Area declarada (ha)", "ProducerCountry", "Estado"])
    n_parcels = 0
    if not gdf.empty:
        for i, (idx, row) in enumerate(gdf.iterrows(), start=2):
            n_parcels += 1
            gtype = row["geometry"].geom_type if row["geometry"] is not None else ""
            area_calc = round(float(areas_ha.loc[idx]), 3) if idx in areas_ha.index else None
            declared = row.get("Area")
            try:
                declared = float(declared)
            except (TypeError, ValueError):
                declared = None
            ws_p.append([
                row["ParcelID"], gtype, area_calc, declared, row.get("ProducerCountry"),
                # COUNTIFS con comodines: soporta el caso de PARCELS_OVERLAP,
                # cuyo ParcelID en Hallazgos viene combinado ("A / B") porque
                # involucra dos parcelas a la vez.
                f'=IF(COUNTIFS(Hallazgos!A:A,"ERROR",Hallazgos!B:B,"*"&A{i}&"*")>0,"Con error","Apto")'
            ])
    # Parcelas que fallaron tan temprano en la ingesta que nunca llegaron a
    # tener geometría (lat/lon faltante, geometría prohibida, etc.) — se
    # listan igual, con los campos geométricos vacíos, para que no
    # desaparezcan silenciosamente del informe.
    for pid in failed_ids:
        n_parcels += 1
        i = n_parcels + 1
        ws_p.append([
            pid, "(sin geometría válida)", None, None, None,
            f'=IF(COUNTIFS(Hallazgos!A:A,"ERROR",Hallazgos!B:B,"*"&A{i}&"*")>0,"Con error","Apto")'
        ])

    # ---- Hoja Resumen (formulas sobre las otras dos hojas) ----
    ws_r = wb.create_sheet("Resumen", 0)
    ws_r.append(["Informe de calidad — Validador de geometrías de proveedores (EUDR)"])
    ws_r.append(["Archivo de entrada", input_filename])
    ws_r.append(["Fecha de generación", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")])
    ws_r.append(["Commodity", commodity])
    ws_r.append(["Formato de referencia", "EUDR GeoJSON File Description v1.5 (Reglamento 2024/3084)"])
    ws_r.append([])
    ws_r.append(["Métrica", "Valor"])
    last_p = n_parcels + 1
    last_f = len(findings) + 1
    ws_r.append(["Parcelas evaluadas", f"=COUNTA(Parcelas!A2:A{last_p})" if n_parcels else 0])
    ws_r.append(["Parcelas aptas para presentar tal cual",
                  f'=COUNTIF(Parcelas!F2:F{last_p},"Apto")' if n_parcels else 0])
    ws_r.append(["Parcelas con error bloqueante",
                  f'=COUNTIF(Parcelas!F2:F{last_p},"Con error")' if n_parcels else 0])
    ws_r.append(["Errores bloqueantes (total)",
                  f'=COUNTIF(Hallazgos!A2:A{last_f},"ERROR")' if findings else 0])
    ws_r.append(["Advertencias (no bloqueantes)",
                  f'=COUNTIF(Hallazgos!A2:A{last_f},"WARNING")' if findings else 0])
    ws_r.append(["Notas de conversión",
                  f'=COUNTIF(Hallazgos!A2:A{last_f},"INFO")' if findings else 0])
    ws_r.append([])
    ws_r.append(["Qué significa \"apto\": la parcela no tiene ningún hallazgo de "
                  "severidad Error bloqueante. El GeoJSON de salida incluye "
                  "únicamente las parcelas aptas."])

    # ---- estilo ----
    header_fill = PatternFill(start_color="2F5233", end_color="2F5233", fill_type="solid")
    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    title_font = Font(name="Arial", bold=True, size=14)
    normal_font = Font(name="Arial", size=10)

    for ws in (ws_f, ws_p):
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font = normal_font
                cell.alignment = Alignment(vertical="top", wrap_text=(ws is ws_f and cell.column == 4))
        for col_idx in range(1, ws.max_column + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 22
        if ws is ws_f:
            ws.column_dimensions["D"].width = 70
            ws.column_dimensions["E"].width = 55

    ws_r["A1"].font = title_font
    for r in range(2, 6):
        ws_r.cell(row=r, column=1).font = Font(name="Arial", bold=True, size=10)
        ws_r.cell(row=r, column=2).font = normal_font
    ws_r["A7"].font = header_font
    ws_r["B7"].font = header_font
    ws_r["A7"].fill = header_fill
    ws_r["B7"].fill = header_fill
    for r in range(8, 14):
        ws_r.cell(row=r, column=1).font = normal_font
        ws_r.cell(row=r, column=2).font = Font(name="Arial", size=10, bold=True)
    ws_r.column_dimensions["A"].width = 42
    ws_r.column_dimensions["B"].width = 70

    # configuración de impresión: horizontal, ajustada a 1 página de ancho
    # (por si alguien lo imprime o lo exporta a PDF, además de abrirlo en Excel)
    for ws in (ws_r, ws_p, ws_f):
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = False

    wb.save(path)
