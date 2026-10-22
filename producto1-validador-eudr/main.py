import argparse
import os

import pandas as pd

from src import ingest, validators, geojson_writer, report

DEFAULT_COUNTRIES = os.path.join(os.path.dirname(__file__), "data", "cono_sur_countries.geojson")


def run(input_path, output_dir, country_boundaries_path=DEFAULT_COUNTRIES, commodity="wood"):
    os.makedirs(output_dir, exist_ok=True)

    ingest_result = ingest.load_any(input_path)
    gdf = ingest_result.gdf
    findings = list(ingest_result.findings)

    if not gdf.empty:
        findings.extend(validators.run_all(gdf, country_boundaries_path, commodity=commodity))
        areas_ha = validators.compute_areas_ha(gdf)
    else:
        areas_ha = pd.Series(dtype=float)

    input_filename = os.path.basename(input_path)

    n_out, n_excluded = geojson_writer.write_geojson(
        gdf, findings, os.path.join(output_dir, "output.geojson"))

    md = report.generate_markdown(gdf, findings, input_filename, failed_ids=ingest_result.failed_ids)
    with open(os.path.join(output_dir, "quality_report.md"), "w", encoding="utf-8") as f:
        f.write(md)

    report.generate_pdf(gdf, findings, input_filename,
                         os.path.join(output_dir, "quality_report.pdf"),
                         failed_ids=ingest_result.failed_ids)
    report.generate_excel(gdf, findings, areas_ha, input_filename,
                           os.path.join(output_dir, "quality_report.xlsx"),
                           failed_ids=ingest_result.failed_ids)

    return {
        "gdf": gdf,
        "findings": findings,
        "n_output_features": n_out,
        "n_excluded_parcels": n_excluded,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EUDR supplier geometry validator")
    parser.add_argument("input", help="Input file (.geojson/.json/.csv/.xlsx)")
    parser.add_argument("-o", "--output-dir", default="outputs")
    parser.add_argument("--countries", default=DEFAULT_COUNTRIES)
    parser.add_argument("--commodity", default="wood")
    args = parser.parse_args()

    result = run(args.input, args.output_dir, args.countries, args.commodity)
    print(f"Parcels in the output GeoJSON: {result['n_output_features']}")
    print(f"Parcels excluded due to blocking error: {result['n_excluded_parcels']}")
    print(f"Total findings: {len(result['findings'])}")
