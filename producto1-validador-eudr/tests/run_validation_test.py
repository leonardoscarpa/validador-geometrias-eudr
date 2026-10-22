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
            print(f"  ❌ {pid}: MISSING {missing}  (detected: {sorted(detected)})")
        elif not exp_codes and detected:
            # control parcel: ZERO findings expected but there were some
            all_ok = False
            print(f"  ❌ {pid}: expected 0 findings (control) but got {sorted(detected)}")
        else:
            tag = "no findings (valid control)" if not exp_codes else f"OK {sorted(exp_codes)}"
            extra_note = f"  [+ extra, not evaluated: {sorted(unexpected)}]" if unexpected else ""
            print(f"  ✅ {pid}: {tag}{extra_note}")

    print(f"\n  Total findings: {len(findings)}")
    print(f"  Parcels in output GeoJSON: {result['n_output_features']}")
    print(f"  Parcels excluded due to blocking error: {result['n_excluded_parcels']}")
    return all_ok


ok1 = check("TEST 1: raw GeoJSON (synthetic_geojson_input.geojson)",
            os.path.join(DATA_DIR, "synthetic_geojson_input.geojson"),
            expected["geojson"],
            os.path.join(HERE, "..", "outputs", "test_geojson"))

ok2 = check("TEST 2: Excel spreadsheet (synthetic_supplier_spreadsheet.xlsx)",
            os.path.join(DATA_DIR, "synthetic_supplier_spreadsheet.xlsx"),
            expected["tabular"],
            os.path.join(HERE, "..", "outputs", "test_excel"))

print("\n" + "=" * 70)
if ok1 and ok2:
    print("FINAL RESULT: ✅ the validator detected ALL seeded errors.")
    sys.exit(0)
else:
    print("FINAL RESULT: ❌ some seeded errors were not detected. See above.")
    sys.exit(1)
