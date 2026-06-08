# app/cache.py
import os
import json
import numpy as np
from embeddings import embed_query
from datetime import datetime

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
CACHE_DIR  = os.path.join(os.getcwd(), "data", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "semantic_cache.json")

# 0.85 = consultas semánticamente casi idénticas.
# El valor anterior (0.4) era demasiado permisivo: cualquier par de frases
# en español supera 0.4 de similitud coseno, generando falsos cache hits.
SIMILARITY_THRESHOLD = 0.85

os.makedirs(CACHE_DIR, exist_ok=True)

# -----------------------------
# ESTRUCTURA DE CACHÉ
# {
#   "entries": [
#     {
#       "query":     "texto original de la consulta",
#       "vector":    [0.1, 0.2, ...],   <- embedding como lista
#       "response":  { answer, sources, tokens_used },
#       "category":  "CRONOGRAMA",
#       "hits":      3,                 <- veces que fue reutilizada
#       "created_at": "2025-01-01T..."
#     }
#   ]
# }
# -----------------------------

def _load_cache() -> dict:
    """Carga el archivo de caché desde disco."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}

def _save_cache(cache: dict):
    """Guarda el archivo de caché en disco."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Similitud coseno entre dos vectores normalizados."""
    return float(np.dot(vec_a, vec_b))

# -----------------------------
# FUNCIONES PRINCIPALES
# -----------------------------
def search_cache(query: str) -> dict | None:
    """
    Busca en la caché semántica una consulta similar.

    Returns:
        La respuesta cacheada si similitud >= SIMILARITY_THRESHOLD,
        None si no hay hit.
    """
    cache = _load_cache()
    if not cache["entries"]:
        return None

    query_vector = embed_query(query)

    best_score = 0.0
    best_entry = None
    best_idx   = -1

    for i, entry in enumerate(cache["entries"]):
        cached_vector = np.array(entry["vector"], dtype=np.float32)
        if cached_vector.shape != query_vector.shape:
            # Vector de dimensión distinta — entrada antigua de otro modelo, ignorar
            continue
        score = _cosine_similarity(query_vector, cached_vector)
        if score > best_score:
            best_score = score
            best_entry = entry
            best_idx   = i

    if best_score >= SIMILARITY_THRESHOLD:
        print(f"[CACHE HIT] Similitud: {best_score:.4f} — "
              f"Query original: '{best_entry['query'][:60]}...'")

        # Incrementar contador de hits
        cache["entries"][best_idx]["hits"] += 1
        _save_cache(cache)

        return {
            "answer":      best_entry["response"]["answer"],
            "sources":     best_entry["response"]["sources"],
            "tokens_used": 0,          # no se usaron tokens — cache hit
            "cache_hit":   True,
            "similarity":  best_score,
            "original_query": best_entry["query"]
        }

    print(f"[CACHE MISS] Mejor similitud: {best_score:.4f} < {SIMILARITY_THRESHOLD}")
    return None

def add_to_cache(query: str, response: dict, category: str):
    """
    Agrega una nueva entrada a la caché semántica.

    Args:
        query:    Consulta del usuario
        response: Dict con {answer, sources, tokens_used}
        category: Categoría identificada por el router
    """
    cache = _load_cache()

    query_vector = embed_query(query)

    entry = {
        "query":      query,
        "vector":     query_vector.tolist(),   # numpy → lista para JSON
        "response":   response,
        "category":   category,
        "hits":       0,
        "created_at": datetime.now().isoformat()
    }

    cache["entries"].append(entry)
    _save_cache(cache)
    print(f"[CACHE] Nueva entrada guardada. "
          f"Total en caché: {len(cache['entries'])}")

def get_cache_stats() -> dict:
    """
    Retorna estadísticas de la caché para el StatsPanel del frontend.
    """
    cache = _load_cache()
    entries = cache["entries"]

    if not entries:
        return {
            "total_entries": 0,
            "total_hits":    0,
            "hit_rate":      0.0,
            "top_queries":   []
        }

    total_hits = sum(e["hits"] for e in entries)

    # Top 5 consultas más reutilizadas
    top_queries = sorted(
        entries,
        key=lambda x: x["hits"],
        reverse=True
    )[:5]

    return {
        "total_entries": len(entries),
        "total_hits":    total_hits,
        "hit_rate":      total_hits / max(len(entries), 1),
        "top_queries": [
            {
                "query":    e["query"][:80],
                "hits":     e["hits"],
                "category": e["category"]
            }
            for e in top_queries
        ]
    }