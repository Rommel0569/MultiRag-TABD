# app/embeddings.py
# Single source of truth for all embedding and reranking models.
# Import from here instead of loading SentenceTransformer in each module.
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

EMBED_MODEL_NAME   = "intfloat/multilingual-e5-base"
RERANKER_MODEL_NAME = "amberoad/bert-multilingual-passage-reranking-msmarco"

print("[INFO] Cargando multilingual-e5-base...")
_embed_model = SentenceTransformer(EMBED_MODEL_NAME)
EMBED_DIM    = _embed_model.get_sentence_embedding_dimension()
print(f"[INFO] Embeddings listos. Dimensión: {EMBED_DIM}")

print("[INFO] Cargando cross-encoder reranker (multilingual)...")
_reranker = CrossEncoder(RERANKER_MODEL_NAME)
print("[INFO] Reranker listo.")


def embed_query(text: str) -> np.ndarray:
    """
    Embed a user query.
    multilingual-e5-base requires the 'query: ' prefix for search queries.
    """
    return _embed_model.encode(
        f"query: {text}",
        normalize_embeddings=True
    ).astype(np.float32)


def embed_passage(text: str) -> np.ndarray:
    """
    Embed a document passage.
    multilingual-e5-base requires the 'passage: ' prefix for indexed content.
    """
    return _embed_model.encode(
        f"passage: {text}",
        normalize_embeddings=True
    ).astype(np.float32)


def rerank(query: str, docs: list, top_k: int = 5) -> list:
    """
    Cross-encoder reranking: scores each (query, passage) pair directly,
    bypassing the vector-similarity approximation used in bi-encoder search.
    Much more accurate for final ranking.
    """
    if not docs:
        return docs
    pairs  = [(query, doc["text"]) for doc in docs]
    scores = np.array(_reranker.predict(pairs)).flatten()
    for doc, score in zip(docs, scores):
        doc["score_rerank"] = float(score)
    ranked = sorted(docs, key=lambda x: x["score_rerank"], reverse=True)
    return ranked[:top_k]
