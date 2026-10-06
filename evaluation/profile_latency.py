# evaluation/profile_latency.py
"""
O4 — Perfil de latencia por componente del pipeline completo (sin caché).

Mide, para cada consulta del banco: enrutador (Llama 3), búsqueda densa
(FAISS), búsqueda léxica (BM25), fusión RRF, reranking (cross-encoder)
y generación (Llama 3). Produce la tabla de desglose que pide el revisor.

Requiere Ollama corriendo.
"""
import os
import sys
import json
import time
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE    = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP_DIR)

from router    import route_query
from retriever import dense_search, lexical_search, reciprocal_rank_fusion
from embeddings import rerank
from llm       import generate_response

ETAPAS = ["enrutador", "densa_faiss", "lexica_bm25", "fusion_rrf",
          "rerank_crossenc", "generacion_llm", "total"]


def main():
    with open(os.path.join(HERE, "queries.json"), encoding="utf-8") as f:
        consultas = json.load(f)["consultas"]

    tiempos = {e: [] for e in ETAPAS}

    for c in consultas:
        q  = c["query"]
        t0 = time.perf_counter()

        r = route_query(q)
        t1 = time.perf_counter()

        if not r["is_in_domain"]:
            print(f"[SKIP] Fuera de dominio: '{q[:50]}'")
            continue
        cat = r["category"]

        dense = dense_search(q, cat, top_k=10)
        t2 = time.perf_counter()

        lex = lexical_search(q, cat, top_k=10)
        t3 = time.perf_counter()

        fused = reciprocal_rank_fusion(dense, lex, top_k=20)
        t4 = time.perf_counter()

        ranked = rerank(q, fused, top_k=5)
        t5 = time.perf_counter()

        generate_response(q, ranked)
        t6 = time.perf_counter()

        vals = [t1-t0, t2-t1, t3-t2, t4-t3, t5-t4, t6-t5, t6-t0]
        for etapa, v in zip(ETAPAS, vals):
            tiempos[etapa].append(v)
        print(f"[OK] '{q[:45]}' -> total {t6-t0:.1f}s "
              f"(router {t1-t0:.1f}s, rerank {t5-t4:.1f}s, LLM {t6-t5:.1f}s)")

    total_medio = np.mean(tiempos["total"])
    print(f"\n{'='*66}")
    print("DESGLOSE DE LATENCIA POR COMPONENTE (para la Tabla del artículo)")
    print(f"{'Etapa':<20}{'Media (s)':>12}{'Desv. (s)':>12}{'% del total':>14}")
    for etapa in ETAPAS:
        m = np.mean(tiempos[etapa])
        s = np.std(tiempos[etapa])
        pct = 100 * m / total_medio if etapa != "total" else 100.0
        print(f"{etapa:<20}{m:>12.2f}{s:>12.2f}{pct:>13.1f}%")


if __name__ == "__main__":
    main()
