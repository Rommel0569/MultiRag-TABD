# app/pipeline.py
from dotenv import load_dotenv
load_dotenv()

from cache    import search_cache, add_to_cache
from router   import route_query
from retriever import retrieve, retrieve_all
from llm      import generate_response

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
TOP_K = 5

OUT_OF_DOMAIN_RESPONSE = (
    "Lo sentimos, tu consulta está fuera del alcance del sistema. "
    "Solo puedo responder preguntas sobre el proceso de admisión de "
    "CEPRUNSA: cronogramas, vacantes, temario y reglamento."
)

# -----------------------------
# PIPELINE PRINCIPAL
# -----------------------------
def pipeline(query: str) -> dict:
    """
    Pipeline Multi-RAG de 3 Fases con lógica fail-fast.

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
            "category":    "CACHE",
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
    chunks = retrieve(query, category, top_k=TOP_K)

    # Si la categoría específica no retorna resultados,
    # buscar en todas las categorías
    if not chunks:
        print(f"[WARN] Sin resultados en {category}, buscando globalmente...")
        chunks = retrieve_all(query, top_k_per_cat=3)

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