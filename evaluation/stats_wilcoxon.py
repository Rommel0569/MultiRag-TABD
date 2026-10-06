# evaluation/stats_wilcoxon.py
"""
O5 — Prueba de Wilcoxon de rangos con signo sobre las métricas RAGAS
por consulta (Multi-RAG vs. baseline), con tamaño de efecto r.

Entrada: evaluation/ragas_por_consulta.csv con estas columnas:
  query,
  faithfulness_multirag,     faithfulness_baseline,
  answer_relevancy_multirag, answer_relevancy_baseline,
  context_recall_multirag,   context_recall_baseline

(Exporta estos valores del dataframe que retorna RAGAS al evaluar
cada sistema: result.to_pandas() por consulta, no el promedio.)
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE     = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "ragas_por_consulta.csv")
METRICAS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def efecto_r(a: np.ndarray, b: np.ndarray) -> float:
    """Tamaño de efecto r = |Z| / sqrt(N), con Z por aproximación normal."""
    diff = a - b
    diff = diff[diff != 0]
    n = len(diff)
    if n == 0:
        return 0.0
    W  = wilcoxon(a, b, zero_method="wilcox").statistic
    mu = n * (n + 1) / 4
    sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (W - mu) / sigma
    return abs(z) / np.sqrt(n)


def main():
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] No existe {CSV_PATH}.")
        print("Exporta los scores RAGAS por consulta de ambos sistemas a ese CSV.")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"[INFO] {len(df)} consultas cargadas.\n")
    print(f"{'Métrica':<20}{'Δ media':>10}{'W':>10}{'p-valor':>12}{'r':>8}  Significativo (α=0.05)")

    for m in METRICAS:
        a = df[f"{m}_multirag"].to_numpy(dtype=float)
        b = df[f"{m}_baseline"].to_numpy(dtype=float)
        # Descartar pares donde alguna de las dos mediciones falló (NaN)
        ok = ~(np.isnan(a) | np.isnan(b))
        a, b = a[ok], b[ok]
        if len(a) == 0:
            print(f"{m:<20} sin pares válidos (todo NaN)")
            continue
        print(f"  [{m}: {len(a)} pares válidos de {len(df)}]")
        delta = float(np.mean(a - b))
        if np.all(a == b):
            print(f"{m:<20}{delta:>10.4f}{'—':>10}{'—':>12}{'—':>8}  (sin diferencias)")
            continue
        res = wilcoxon(a, b, zero_method="wilcox")
        r   = efecto_r(a, b)
        sig = "SÍ" if res.pvalue < 0.05 else "NO"
        print(f"{m:<20}{delta:>10.4f}{res.statistic:>10.1f}{res.pvalue:>12.4f}{r:>8.3f}  {sig}")

    print("\nInterpretación de r: ~0.1 pequeño, ~0.3 mediano, ~0.5 grande.")
    print("Si p ≥ 0.05, reformular la conclusión: 'mejora observable pero")
    print("no confirmada estadísticamente' (como pide el revisor).")


if __name__ == "__main__":
    main()
