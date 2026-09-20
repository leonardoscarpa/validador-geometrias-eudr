import argparse
import os

from src.ingest import load_supplier_rows
from src.scoring import score_all
from src.report import generate_markdown, generate_excel


def run(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    suppliers, warnings = load_supplier_rows(input_path)
    scores = score_all(suppliers)
    scores.sort(key=lambda s: -s.total_points)

    input_filename = os.path.basename(input_path)
    md = generate_markdown(scores, warnings, input_filename)
    with open(os.path.join(output_dir, "scorecard.md"), "w", encoding="utf-8") as f:
        f.write(md)
    generate_excel(scores, warnings, input_filename, os.path.join(output_dir, "scorecard.xlsx"))

    return {"scores": scores, "warnings": warnings}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scorecard de riesgo de proveedor EUDR (Art. 10)")
    parser.add_argument("input")
    parser.add_argument("-o", "--output-dir", default="outputs")
    args = parser.parse_args()
    result = run(args.input, args.output_dir)
    print(f"Proveedores evaluados: {len(result['scores'])}")
    for s in result["scores"]:
        print(f"  {s.tier:6s} {s.total_points:5.1f} pts  {s.producer_name}")
    if result["warnings"]:
        print(f"Advertencias: {len(result['warnings'])}")
