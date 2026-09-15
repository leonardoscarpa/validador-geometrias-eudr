import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import run  # noqa: E402

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "data")

with open(os.path.join(HERE, "expected_codes.json"), encoding="utf-8") as f:
    expected = json.load(f)


def check(label, input_path, expected_map, output_dir):
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}")
    result = run(input_path, output_dir)
    findings = result["findings"]

    detected_by_pid = {}
    for f in findings:
        pids = str(f.parcel_id).split(" / ") if f.parcel_id else [None]
        for pid in pids:
            detected_by_pid.setdefault(pid, set()).add(f.code)

    all_ok = True
    for pid, exp_codes in expected_map.items():
        detected = detected_by_pid.get(pid, set())
        missing = set(exp_codes) - detected
        unexpected = detected - set(exp_codes)
        if missing:
            all_ok = False
            print(f"  ❌ {pid}: FALTAN {missing}  (detectados: {sorted(detected)})")
        elif not exp_codes and detected:
            # parcela control: se esperaba CERO hallazgos y hubo alguno
            all_ok = False
            print(f"  ❌ {pid}: se esperaban 0 hallazgos (control) pero hubo {sorted(detected)}")
        else:
            tag = "sin hallazgos (control válido)" if not exp_codes else f"OK {sorted(exp_codes)}"
            extra_note = f"  [+ extra no evaluados: {sorted(unexpected)}]" if unexpected else ""
            print(f"  ✅ {pid}: {tag}{extra_note}")

    print(f"\n  Total hallazgos: {len(findings)}")
    print(f"  Parcelas en GeoJSON de salida: {result['n_output_features']}")
    print(f"  Parcelas excluidas por error bloqueante: {result['n_excluded_parcels']}")
    return all_ok


ok1 = check("TEST 1 — GeoJSON crudo (synthetic_geojson_input.geojson)",
            os.path.join(DATA_DIR, "synthetic_geojson_input.geojson"),
            expected["geojson"],
            os.path.join(HERE, "..", "outputs", "test_geojson"))

ok2 = check("TEST 2 — Planilla Excel (synthetic_planilla_proveedores.xlsx)",
            os.path.join(DATA_DIR, "synthetic_planilla_proveedores.xlsx"),
            expected["tabular"],
            os.path.join(HERE, "..", "outputs", "test_excel"))

print("\n" + "=" * 70)
if ok1 and ok2:
    print("RESULTADO FINAL: ✅ el validador detectó TODOS los errores sembrados.")
    sys.exit(0)
else:
    print("RESULTADO FINAL: ❌ hay errores sembrados que no se detectaron. Revisar arriba.")
    sys.exit(1)
