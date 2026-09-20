import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingest import load_supplier_rows
from src.scoring import score_all

suppliers, warnings = load_supplier_rows(os.path.join(os.path.dirname(__file__), "..", "data", "proveedores_sinteticos.xlsx"))
scores = {s.producer_name: s for s in score_all(suppliers)}

expected = {
    "Vivero Andino SRL": (0.0, "Bajo"),
    "Forestal Don Aparicio": (1.0, "Bajo"),
    "Maderera Litoral SA": (2.0, "Medio"),
    "Establecimiento Yaguarete": (3.0, "Medio"),
    "Exportadora del Norte": (6.0, "Alto"),
    "Pinares Certificados SA": (0.0, "Bajo"),
    "Cooperativa Binacional": (1.0, "Bajo"),
    "Yerbatera San Ignacio": (1.5, "Bajo"),
}

ok = True
for name, (exp_points, exp_tier) in expected.items():
    if name not in scores:
        print(f"FALTA proveedor: {name}"); ok = False; continue
    s = scores[name]
    if s.total_points != exp_points or s.tier != exp_tier:
        ok = False
        print(f"❌ {name}: esperado ({exp_points}, {exp_tier}) | obtenido ({s.total_points}, {s.tier})")
    else:
        print(f"✅ {name}: {s.total_points} pts -> {s.tier}")

print("\nProveedores excluidos por falta de ProducerName (esperado 1, 'P-H1'):",
      any("sin ProducerName" in w for w in warnings))
print("Warning de multi-país detectado (esperado True):",
      any("más de un país" in w for w in warnings))
print("\nWarnings completos:")
for w in warnings:
    print(" -", w)

print("\n" + ("=== TODO BIEN ===" if ok else "=== HAY FALLAS ==="))
sys.exit(0 if ok else 1)
