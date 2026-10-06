# app/embeddings.py
# Single source of truth for all embedding and reranking models.
# Import from here instead of loading SentenceTransformer in each module.
import os
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder

EMBED_MODEL_NAME = os.environ.get('CEPRUNSA_EMBED_MODEL', 'intfloat/multilingual-e5-base')
RERANKER_MODEL_NAME = os.environ.get('CEPRUNSA_RERANK_MODEL', 'amberoad/bert-multilingual-passage-reranking-msmarco')
LOCAL_ONLY = os.environ.get('CEPRUNSA_LOCAL_MODELS_ONLY', '1') == '1'
torch.set_num_threads(int(os.environ.get('CEPRUNSA_TORCH_THREADS', '4')))

print("[INFO] Cargando multilingual-e5-base...")
_embed_model = SentenceTransformer(EMBED_MODEL_NAME, local_files_only=LOCAL_ONLY)
EMBED_DIM    = _embed_model.get_sentence_embedding_dimension()
print(f"[INFO] Embeddings listos. Dimensión: {EMBED_DIM}")

_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL_NAME, local_files_only=LOCAL_ONLY)
    return _reranker


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


def embed_passages(texts: list[str]) -> np.ndarray:
    """Encode an ingestion batch in one model call instead of one call per chunk."""
    if not texts:
        return np.empty((0, EMBED_DIM), dtype=np.float32)
    return _embed_model.encode(
        [f"passage: {text}" for text in texts],
        normalize_embeddings=True,
        batch_size=int(os.environ.get("CEPRUNSA_EMBED_BATCH_SIZE", "32")),
        show_progress_bar=False,
    ).astype(np.float32)


def relevance_probs(pairs: list) -> np.ndarray:
    """
    Probabilidad de relevancia [0,1] para cada par (texto_a, texto_b).
    El modelo amberoad emite 2 logits [no_relevante, relevante]:
    se aplica softmax y se toma la probabilidad de 'relevante'.
    """
    if not pairs:
        return np.asarray([], dtype=np.float32)
    scores = np.array(_get_reranker().predict(pairs))
    if scores.ndim == 2 and scores.shape[1] == 2:
        e = np.exp(scores - scores.max(axis=1, keepdims=True))
        return (e / e.sum(axis=1, keepdims=True))[:, 1]
    return scores.flatten()


def rerank(query: str, docs: list, top_k: int = 5) -> list:
    """
    Cross-encoder reranking: scores each (query, passage) pair directly,
    bypassing the vector-similarity approximation used in bi-encoder search.
    Much more accurate for final ranking.
    """
    if not docs:
        return docs
    pairs  = [(query, doc["text"]) for doc in docs]
    scores = relevance_probs(pairs)
    for doc, score in zip(docs, scores):
        doc["score_rerank"] = float(score)
    ranked = sorted(docs, key=lambda x: x["score_rerank"], reverse=True)
    return ranked[:top_k]
