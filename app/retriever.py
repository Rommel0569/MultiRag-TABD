# app/retriever.py
import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "data", "index")

CATEGORIES = ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO"]

# Modelo de embeddings (mismo que ingest.py)
print("[INFO] Cargando modelo de embeddings para retriever...")
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("[INFO] Modelo listo.")

# -----------------------------
# CARGAR ÍNDICES AL INICIO
# -----------------------------
indexes   = {}   # { categoria: faiss.Index }
documents = {}   # { categoria: [ {id, text, source, page, category} ] }
bm25_indexes = {}  # { categoria: BM25Okapi }

def load_indexes():
    """Carga todos los índices FAISS y JSONs al arrancar."""
    for cat in CATEGORIES:
        index_path = os.path.join(INDEX_DIR, f"{cat}.index")
        json_path  = os.path.join(INDEX_DIR, f"{cat}.json")

        if not os.path.exists(index_path) or not os.path.exists(json_path):
            print(f"[WARN] Índice no encontrado para {cat} — ejecuta ingest.py primero")
            continue

        indexes[cat]   = faiss.read_index(index_path)
        with open(json_path, "r", encoding="utf-8") as f:
            documents[cat] = json.load(f)

        # Construir índice BM25 para esta categoría
        tokenized = [doc["text"].lower().split() for doc in documents[cat]]
        bm25_indexes[cat] = BM25Okapi(tokenized)

        print(f"[OK] {cat}: {indexes[cat].ntotal} vectores, "
              f"{len(documents[cat])} documentos cargados")

load_indexes()

# -----------------------------
# BÚSQUEDA DENSA (FAISS)
# -----------------------------
def dense_search(query: str, category: str, top_k: int = 5):
    """Recuperación semántica por similitud coseno con FAISS."""
    if category not in indexes:
        return []

    query_vector = embed_model.encode(
        query,
        normalize_embeddings=True
    ).astype(np.float32).reshape(1, -1)

    distances, indices = indexes[category].search(query_vector, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:   # FAISS retorna -1 cuando no hay suficientes resultados
            continue
        doc = documents[category][idx].copy()
        doc["score_dense"] = float(dist)   # coseno normalizado: 1.0 = idéntico
        results.append(doc)

    return results

# -----------------------------
# BÚSQUEDA LÉXICA (BM25)
# -----------------------------
def lexical_search(query: str, category: str, top_k: int = 5):
    """Recuperación léxica con BM25Okapi."""
    if category not in bm25_indexes:
        return []

    tokenized_query = query.lower().split()
    scores          = bm25_indexes[category].get_scores(tokenized_query)
    top_indices     = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] == 0.0:   # sin coincidencia léxica
            continue
        doc = documents[category][idx].copy()
        doc["score_bm25"] = float(scores[idx])
        results.append(doc)

    return results

# -----------------------------
# FUSIÓN RRF
# -----------------------------
def reciprocal_rank_fusion(
    dense_results: list,
    lexical_results: list,
    k: int = 60,
    top_k: int = 5
):
    """
    Combina resultados de FAISS y BM25 usando Reciprocal Rank Fusion.
    RRF score = sum( 1 / (k + rank) ) para cada documento en cada lista.
    k=60 es el valor estándar de la literatura.
    """
    rrf_scores = {}   # { doc_id: score_rrf }
    doc_map    = {}   # { doc_id: doc }

    # Puntaje por ranking en resultados densos
    for rank, doc in enumerate(dense_results):
        doc_id = doc["id"]
        rrf_scores[doc_id]  = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        doc_map[doc_id]     = doc

    # Puntaje por ranking en resultados léxicos
    for rank, doc in enumerate(lexical_results):
        doc_id = doc["id"]
        rrf_scores[doc_id]  = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        doc_map[doc_id]     = doc

    # Ordenar por score RRF descendente
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

    results = []
    for doc_id in sorted_ids[:top_k]:
        doc               = doc_map[doc_id].copy()
        doc["score_rrf"]  = rrf_scores[doc_id]
        results.append(doc)

    return results

# -----------------------------
# FUNCIÓN PRINCIPAL DE RECUPERACIÓN
# -----------------------------
def retrieve(query: str, category: str, top_k: int = 5):
    """
    Recuperación híbrida completa:
    FAISS (denso) + BM25 (léxico) → RRF → top_k fragmentos
    """
    dense   = dense_search(query, category, top_k=top_k)
    lexical = lexical_search(query, category, top_k=top_k)
    fused   = reciprocal_rank_fusion(dense, lexical, top_k=top_k)
    return fused

# -----------------------------
# RECUPERACIÓN MULTI-CATEGORÍA
# -----------------------------
def retrieve_all(query: str, top_k_per_cat: int = 3):
    """
    Busca en todas las categorías y retorna los mejores
    fragmentos globales ordenados por score RRF.
    Útil cuando el enrutador no identifica una categoría específica.
    """
    all_results = []
    for cat in CATEGORIES:
        if cat in indexes:
            results = retrieve(query, cat, top_k=top_k_per_cat)
            all_results.extend(results)

    # Reordenar globalmente por score RRF
    all_results.sort(key=lambda x: x.get("score_rrf", 0), reverse=True)
    return all_results[:top_k_per_cat * 2]