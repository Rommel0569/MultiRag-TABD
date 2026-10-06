# evaluation/eval_router.py
"""
O3 — Evaluación independiente del enrutador Zero-Shot.

Requiere:
  1. evaluation/queries.json con 'categoria_correcta' anotada manualmente
     para cada una de las 30 consultas.
  2. Ollama corriendo con llama3 (el enrutador lo usa).

Reporta: accuracy global, precisión/recall/F1 por categoría y matriz
de confusión — exactamente lo que pide el revisor en O3.
"""
import os
import sys
import json

# La consola de Windows usa cp1252 y falla con caracteres Unicode
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE    = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP_DIR)

from router import route_query

CATEGORIES = ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO", "FUERA_DE_DOMINIO"]


def main():
    with open(os.path.join(HERE, "queries.json"), encoding="utf-8") as f:
        consultas = json.load(f)["consultas"]

    y_true, y_pred = [], []
    for c in consultas:
        result = route_query(c["query"])
        y_true.append(c["categoria_correcta"])
        y_pred.append(result["category"])
        estado = "OK  " if y_true[-1] == y_pred[-1] else "FAIL"
        print(f"[{estado}] '{c['query'][:55]}' -> esperado={y_true[-1]}, obtenido={y_pred[-1]}")

    n_ok = sum(t == p for t, p in zip(y_true, y_pred))
    print(f"\n{'='*60}")
    print(f"Accuracy global: {n_ok / len(y_true):.4f} ({n_ok}/{len(y_true)})")

    print("\nMatriz de confusión (filas = real, columnas = predicho):")
    print(f"{'':>12}" + "".join(f"{c[:6]:>8}" for c in CATEGORIES))
    for t in CATEGORIES:
        fila = [sum(1 for yt, yp in zip(y_true, y_pred) if yt == t and yp == p)
                for p in CATEGORIES]
        print(f"{t[:10]:>12}" + "".join(f"{v:>8}" for v in fila))

    print("\nMétricas por categoría:")
    for cat in CATEGORIES:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cat and p == cat)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cat and p == cat)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cat and p != cat)
        if tp + fp + fn == 0:
            continue
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec  = tp / (tp + fn) if tp + fn else 0.0
        f1   = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        print(f"  {cat:<18} precision={prec:.3f}  recall={rec:.3f}  F1={f1:.3f}")


if __name__ == "__main__":
    main()
