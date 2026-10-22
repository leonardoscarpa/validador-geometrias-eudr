import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingest import load_supplier_rows
from src.scoring import score_all

suppliers, warnings = load_supplier_rows(os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_suppliers.xlsx"))
scores = {s.producer_name: s for s in score_all(suppliers)}

expected = {
    "Vivero Andino SRL": (0.0, "Low"),
    "Forestal Don Aparicio": (1.0, "Low"),
    "Maderera Litoral SA": (2.0, "Medium"),
    "Establecimiento Yaguarete": (3.0, "Medium"),
    "Exportadora del Norte": (6.0, "High"),
    "Pinares Certificados SA": (0.0, "Low"),
    "Cooperativa Binacional": (1.0, "Low"),
    "Yerbatera San Ignacio": (1.5, "Low"),
}

ok = True
for name, (exp_points, exp_tier) in expected.items():
    if name not in scores:
        print(f"MISSING supplier: {name}"); ok = False; continue
    s = scores[name]
    if s.total_points != exp_points or s.tier != exp_tier:
        ok = False
        print(f"❌ {name}: expected ({exp_points}, {exp_tier}) | got ({s.total_points}, {s.tier})")
    else:
        print(f"✅ {name}: {s.total_points} pts -> {s.tier}")

print("\nSuppliers excluded for missing ProducerName (expected 1, 'P-H1'):",
      any("has no ProducerName" in w for w in warnings))
print("Multi-country warning detected (expected True):",
      any("more than one country" in w for w in warnings))
print("\nAll warnings:")
for w in warnings:
    print(" -", w)

print("\n" + ("=== ALL GOOD ===" if ok else "=== FAILURES ==="))
sys.exit(0 if ok else 1)
