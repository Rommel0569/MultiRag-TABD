# app/pipeline.py
from pathlib import Path
import re
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from cache    import search_cache, add_to_cache
from router   import route_query
from retriever import retrieve_with_global_fallback, retrieve_all, documents as indexed_documents
from llm      import generate_response
from structured_answers import resolve_structured_answer_any

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
TOP_K = 5
LIST_QUERY = re.compile(
    r"\b(?:qu[eé]\s+(?:temas|contenidos|requisitos|documentos|etapas)|"
    r"cu[aá]les\s+son|lista\s+(?:todos|todas)|enumera\s+(?:todos|todas))\b",
    flags=re.IGNORECASE,
)

OUT_OF_DOMAIN_RESPONSE = (
    "Lo sentimos, tu consulta está fuera del alcance del sistema. "
    "Solo puedo responder preguntas sobre el proceso de admisión de "
    "CEPRUNSA: cronogramas, vacantes, temario y reglamento."
)

# A zero-shot "out of domain" verdict is double-checked against the indexed evidence:
# if the best cross-encoder match over all documents is a confident hit (probability
# >= EVIDENCE_GATE), the query is treated as in-domain. 0.5 is the cross-encoder's
# natural decision point, not a tuned value (on the 89-question development set the
# off-topic queries peak at 0.003).
EVIDENCE_GATE = 0.5


def ood_evidence_override(query: str, route_result: dict) -> dict | None:
    """Return the best-matching category when the evidence contradicts an OOD verdict."""
    if route_result.get("is_in_domain") or route_result.get("raw_response") == "explicit_out_of_domain":
        return None
    chunks = retrieve_all(query, top_k_per_cat=3)
    best = max(chunks, key=lambda c: c.get("score_rerank", 0), default=None)
    if best and best.get("score_rerank", 0) >= EVIDENCE_GATE:
        return {"category": best.get("category"), "score": best["score_rerank"]}
    return None


# -----------------------------
# PIPELINE PRINCIPAL
# -----------------------------
def pipeline(query: str) -> dict:
    """
    Pipeline Multi-RAG de 3 fases con resolución temprana (early exit).

    Fase 1 — Caché semántica
    Fase 2 — Enrutador Zero-Shot
    Fase 3 — Recuperación híbrida FAISS + BM25 → LLM

    Args:
        query: Consulta del usuario en lenguaje natural

    Returns:
        dict con {answer, sources, category, phase, cache_hit,
                  tokens_used, similarity}
    """

    # -------------------------
    # FASE 1 — CACHÉ SEMÁNTICA
    # -------------------------
    cache_result = search_cache(query)
    if cache_result:
        return {
            "answer":      cache_result["answer"],
            "sources":     cache_result["sources"],
            "category":    cache_result.get('category', 'CACHE'),
            "phase":       "FASE 1 — CACHÉ SEMÁNTICA",
            "cache_hit":   True,
            "tokens_used": 0,
            "similarity":  cache_result["similarity"]
        }

    # -------------------------
    # FASE 2 — ENRUTADOR ZERO-SHOT
    # -------------------------
    route_result = route_query(query)
    category     = route_result["category"]
    is_in_domain = route_result["is_in_domain"]

    override = ood_evidence_override(query, route_result)
    if override:
        category, is_in_domain = override["category"], True

    # Consulta fuera de dominio — respuesta directa sin LLM
    if not is_in_domain:
        return {
            "answer":      OUT_OF_DOMAIN_RESPONSE,
            "sources":     [],
            "category":    "FUERA_DE_DOMINIO",
            "phase":       "FASE 2 — ENRUTADOR",
            "cache_hit":   False,
            "tokens_used": 0,
            "similarity":  None
        }

    # -------------------------
    # FASE 3 — RECUPERACIÓN HÍBRIDA + LLM
    # -------------------------
    # Prefer exact source-linked extraction for queries that target a table
    # cell, a named syllabus section, or a numbered regulation article. This
    # avoids asking a generative model to reassemble structured facts.
    structured = resolve_structured_answer_any(query, category, indexed_documents)
    if structured:
        # Structured answers are source-backed too. Cache them so a repeated
        # table/article/topic query can genuinely exit through phase 1.
        add_to_cache(query, structured, category)
        return {
            "answer": structured["answer"],
            "sources": structured["sources"],
            "category": category,
            "phase": "FASE 3 — EXTRACCIÓN ESTRUCTURADA",
            "cache_hit": False,
            "tokens_used": 0,
            "similarity": None,
            "structured_lookup": structured["structured_lookup"],
        }

    # Broad list requests need more evidence than a short factual lookup.
    # Preserve the default context size for ordinary queries.
    retrieval_k = TOP_K * 2 if LIST_QUERY.search(query) else TOP_K
    chunks = retrieve_with_global_fallback(query, category, top_k=retrieval_k)

    # Generar respuesta con LLM
    llm_result = generate_response(query, chunks)

    # Guardar en caché para consultas futuras similares
    add_to_cache(query, llm_result, category)

    return {
        "answer":      llm_result["answer"],
        "sources":     llm_result["sources"],
        "category":    category,
        "phase":       "FASE 3 — RECUPERACIÓN HÍBRIDA",
        "cache_hit":   False,
        "tokens_used": llm_result["tokens_used"],
        "similarity":  None
    }
