# app/retriever.py
import os
import json
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from embeddings import embed_query, rerank

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
INDEX_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "data", "index")
CATEGORIES = ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO"]

# Stopwords en español — evitan que palabras vacías inflen el score BM25
# y diluyan términos realmente relevantes como "vacantes", "ingeniería", etc.
SPANISH_STOPWORDS = {
    'a', 'al', 'algo', 'algunas', 'algunos', 'ante', 'antes', 'como', 'con',
    'contra', 'cual', 'cuando', 'de', 'del', 'desde', 'donde', 'durante',
    'e', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 'erais',
    'eran', 'eras', 'eres', 'es', 'esa', 'esas', 'ese', 'eso', 'esos',
    'esta', 'estaba', 'estaban', 'estado', 'estamos', 'estar', 'estas',
    'este', 'esto', 'estos', 'fue', 'fueron', 'fui', 'fuimos', 'ha', 'han',
    'has', 'hasta', 'hay', 'he', 'hemos', 'hubo', 'la', 'las', 'le', 'les',
    'lo', 'los', 'me', 'mi', 'mis', 'mucho', 'muchos', 'muy', 'más', 'ni',
    'no', 'nos', 'nosotras', 'nosotros', 'o', 'os', 'otra', 'otras', 'otro',
    'otros', 'para', 'pero', 'poco', 'por', 'porque', 'que', 'quien',
    'quienes', 'se', 'ser', 'si', 'sin', 'sobre', 'son', 'su', 'sus',
    'también', 'tanto', 'te', 'tengo', 'ti', 'tiene', 'tienen', 'todo',
    'todos', 'tu', 'tus', 'un', 'una', 'unas', 'uno', 'unos', 'vos',
    'vosotras', 'vosotros', 'vuestra', 'vuestras', 'vuestro', 'vuestros',
    'y', 'ya', 'yo', 'él', 'ésta', 'éstas', 'éste', 'éstos', 'ó',
    'del', 'al', 'ese', 'esa', 'eso', 'este', 'esta', 'esto',
}


def _tokenize(text: str) -> list[str]:
    """Tokenización BM25: minúsculas, sin stopwords, sin puntuación básica."""
    tokens = text.lower().split()
    return [
        t.strip('.,;:¿?¡!"()[]{}') for t in tokens
        if t.strip('.,;:¿?¡!"()[]{}') not in SPANISH_STOPWORDS
        and len(t.strip('.,;:¿?¡!"()[]{}')) > 1
    ]


# -----------------------------
# CARGAR ÍNDICES AL INICIO
# -----------------------------
indexes      = {}   # { categoria: faiss.Index }
documents    = {}   # { categoria: [ {id, text, source, page, category} ] }
bm25_indexes = {}   # { categoria: BM25Okapi }

def load_indexes():
    for cat in CATEGORIES:
        index_path = os.path.join(INDEX_DIR, f"{cat}.index")
        json_path  = os.path.join(INDEX_DIR, f"{cat}.json")

        if not os.path.exists(index_path) or not os.path.exists(json_path):
            print(f"[WARN] Índice no encontrado para {cat} — ejecuta ingest.py primero")
            continue

        indexes[cat]   = faiss.read_index(index_path)
        with open(json_path, "r", encoding="utf-8") as f:
            documents[cat] = json.load(f)

        tokenized = [_tokenize(doc["text"]) for doc in documents[cat]]
        bm25_indexes[cat] = BM25Okapi(tokenized)

        print(f"[OK] {cat}: {indexes[cat].ntotal} vectores, "
              f"{len(documents[cat])} documentos cargados")

load_indexes()


# -----------------------------
# BÚSQUEDA DENSA (FAISS)
# -----------------------------
def dense_search(query: str, category: str, top_k: int = 10):
    """Recuperación semántica. Pide top_k=10 para dar más candidatos al reranker."""
    if category not in indexes:
        return []

    query_vector = embed_query(query).reshape(1, -1)
    distances, indices = indexes[category].search(query_vector, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        doc = documents[category][idx].copy()
        doc["score_dense"] = float(dist)
        results.append(doc)
    return results


# -----------------------------
# BÚSQUEDA LÉXICA (BM25)
# -----------------------------
def lexical_search(query: str, category: str, top_k: int = 10):
    """Recuperación léxica con BM25, usando stopwords en español."""
    if category not in bm25_indexes:
        return []

    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    scores      = bm25_indexes[category].get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] == 0.0:
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
    top_k: int = 20   # devuelve más candidatos para el reranker
):
    """
    Combina FAISS y BM25 con RRF. Retorna top_k=20 candidatos para
    que el cross-encoder reranker pueda elegir los mejores 5.
    """
    rrf_scores = {}
    doc_map    = {}

    for rank, doc in enumerate(dense_results):
        doc_id = doc["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        doc_map[doc_id]    = doc

    for rank, doc in enumerate(lexical_results):
        doc_id = doc["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        doc_map[doc_id]    = doc

    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
    results = []
    for doc_id in sorted_ids[:top_k]:
        doc              = doc_map[doc_id].copy()
        doc["score_rrf"] = rrf_scores[doc_id]
        results.append(doc)
    return results


# -----------------------------
# FUNCIÓN PRINCIPAL DE RECUPERACIÓN
# -----------------------------
def retrieve(query: str, category: str, top_k: int = 5):
    """
    Pipeline completo:
      1. FAISS dense (top-10) + BM25 (top-10)
      2. RRF fusion → top-20 candidatos
      3. Cross-encoder reranker → top-5 finales

    El reranker es la capa de precisión: evalúa cada par (query, chunk)
    directamente en lugar de solo comparar vectores.
    """
    dense   = dense_search(query, category, top_k=10)
    lexical = lexical_search(query, category, top_k=10)
    fused   = reciprocal_rank_fusion(dense, lexical, top_k=20)
    ranked  = rerank(query, fused, top_k=top_k)
    return ranked


# -----------------------------
# RECUPERACIÓN MULTI-CATEGORÍA
# -----------------------------
def retrieve_all(query: str, top_k_per_cat: int = 3):
    """
    Busca en todas las categorías y retorna los mejores fragmentos globales.
    Útil cuando el enrutador no identifica una categoría específica.
    """
    all_results = []
    for cat in CATEGORIES:
        if cat in indexes:
            results = retrieve(query, cat, top_k=top_k_per_cat)
            all_results.extend(results)

    all_results.sort(key=lambda x: x.get("score_rerank", x.get("score_rrf", 0)), reverse=True)
    return all_results[:top_k_per_cat * 2]
