# app/retriever.py
import os
import json
import re
import time
from pathlib import Path
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from embeddings import embed_query, rerank
from structured_answers import is_article_heading

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
_INDEX_DIR = Path(os.environ.get("CEPRUNSA_INDEX_DIR", str(PROJECT_ROOT / "data" / "index"))).expanduser()
INDEX_DIR = str((_INDEX_DIR if _INDEX_DIR.is_absolute() else PROJECT_ROOT / _INDEX_DIR).resolve())
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


def _record_timing(timings: dict | None, name: str, started_ns: int) -> None:
    """Accumulate a component duration in milliseconds when profiling is enabled."""
    if timings is not None:
        timings[name] = timings.get(name, 0.0) + (time.perf_counter_ns() - started_ns) / 1_000_000


def _timed_call(timings: dict | None, name: str, function, *args, **kwargs):
    started_ns = time.perf_counter_ns()
    try:
        return function(*args, **kwargs)
    finally:
        _record_timing(timings, name, started_ns)

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
def retrieve(query: str, category: str, top_k: int = 5, *, timings: dict | None = None):
    """
    Pipeline completo:
      1. FAISS dense (top-10) + BM25 (top-10)
      2. RRF fusion → top-20 candidatos
      3. Cross-encoder reranker → top-5 finales

    El reranker es la capa de precisión: evalúa cada par (query, chunk)
    directamente en lugar de solo comparar vectores.
    """
    # For legal/article questions, prefer the indexed passage whose heading
    # exactly matches the requested article number. This prevents a nearby
    # article or an in-body cross-reference from displacing the requested one.
    article_lookup_started = time.perf_counter_ns()
    article_match = re.search(r"\bart[ií]culo\s+(\d+)\b", query, flags=re.IGNORECASE)
    if article_match and category in documents:
        target = article_match.group(1)
        exact = [doc for doc in documents[category] if is_article_heading(doc, target)]
        if exact:
            selected = [exact[0]]
            anchor = exact[0]
            # Some legal provisions introduce a table immediately after the
            # article heading. Attach that page's table rows so the table is
            # available to generation alongside the exact article passage.
            if re.search(r"\b(tabla|siguiente forma|distribuci[oó]n|se distribuyen)\b",
                         anchor.get("text", ""), flags=re.IGNORECASE):
                selected.extend(
                    doc for doc in documents[category]
                    if doc.get("source") == anchor.get("source")
                    and doc.get("page") == anchor.get("page")
                    and doc.get("extraction") == "textract_table_row"
                )
            # A provision can continue at the top of the next scanned page.
            # If the OCR passage ends mid-sentence, add the first substantial
            # prose chunk from the next page when it does not start a new
            # article. This uses source order and extracted text only.
            if not re.search(r"[.!?;:]\s*[\"'»)]*$", anchor.get("text", "")):
                continuation = next((doc for doc in documents[category]
                                     if doc.get("source") == anchor.get("source")
                                     and doc.get("page") == (anchor.get("page") or 0) + 1
                                     and doc.get("extraction") == "textract_prose_chunk"
                                     and len(doc.get("text", "")) > 180
                                     and not re.match(r"\s*Art[ií]culo\s+\d+\b",
                                                      doc.get("text", ""), flags=re.IGNORECASE)), None)
                if continuation:
                    selected.append(continuation)
            _record_timing(timings, "retriever_article_anchor_lookup", article_lookup_started)
            return selected

    _record_timing(timings, "retriever_article_anchor_lookup", article_lookup_started)

    dense = _timed_call(timings, "faiss_dense_search", dense_search, query, category, top_k=10)
    lexical = _timed_call(timings, "bm25_lexical_search", lexical_search, query, category, top_k=10)
    fused = _timed_call(timings, "rrf_fusion", reciprocal_rank_fusion, dense, lexical, top_k=20)
    ranked = _timed_call(timings, "cross_encoder_rerank", rerank, query, fused, top_k=top_k)
    return ranked


# -----------------------------
# RECUPERACIÓN MULTI-CATEGORÍA
# -----------------------------
def retrieve_all(query: str, top_k_per_cat: int = 3, *, timings: dict | None = None):
    """
    Busca en todas las categorías y retorna los mejores fragmentos globales.
    Útil cuando el enrutador no identifica una categoría específica.
    """
    all_results = []
    for cat in CATEGORIES:
        if cat in indexes:
            results = retrieve(query, cat, top_k=top_k_per_cat, timings=timings)
            all_results.extend(results)

    all_results.sort(key=lambda x: x.get("score_rerank", x.get("score_rrf", 0)), reverse=True)
    return all_results[:top_k_per_cat * 2]


_GENERIC_QUERY_TERMS = {
    "admision", "ceprunsa", "proceso", "examen", "postulante", "postular",
    "pregunta", "informacion", "documento", "documentos", "dice", "saber",
    "quiero", "puedo", "debo", "seria", "serian", "cual", "cuales",
}


def _retrieval_has_query_anchors(query: str, chunks: list[dict]) -> bool:
    """Check whether the routed context contains the query's specific terms."""
    terms = [token for token in _tokenize(query)
             if len(token) >= 4 and token not in _GENERIC_QUERY_TERMS]
    if not terms:
        return True
    context_terms = set()
    for chunk in chunks:
        context_terms.update(_tokenize(chunk.get("text", "")))
    matched = sum(term in context_terms for term in set(terms))
    required = max(1, min(2, int(np.ceil(len(set(terms)) * 0.35))))
    return matched >= required


def retrieve_with_global_fallback(query: str, category: str, top_k: int = 5, *, timings: dict | None = None):
    """Use routed hybrid retrieval first, then global hybrid retrieval if weak.

    Routing narrows the normal search for precision. When its top passages do
    not contain even the query's distinctive lexical anchors, a global hybrid
    pass can recover evidence from another collection; the combined candidates
    are reranked together so the backup does not automatically flood context.
    """
    primary = retrieve(query, category, top_k=top_k, timings=timings)
    has_anchors = bool(primary and _timed_call(timings, "retrieval_anchor_check",
                                               _retrieval_has_query_anchors, query, primary))
    if has_anchors:
        for chunk in primary:
            chunk.setdefault("retrieval_scope", "routed")
        return primary

    backup = retrieve_all(query, top_k_per_cat=max(2, top_k // 2), timings=timings)
    if not backup:
        return primary
    candidates = []
    seen = set()
    for chunk in [*primary, *backup]:
        key = (chunk.get("category"), chunk.get("id"), chunk.get("source"), chunk.get("page"), chunk.get("text"))
        if key not in seen:
            seen.add(key)
            copied = chunk.copy()
            copied["retrieval_scope"] = "routed" if chunk in primary else "global_fallback"
            candidates.append(copied)
    return _timed_call(timings, "cross_encoder_rerank", rerank, query, candidates, top_k=top_k)
