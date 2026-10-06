"""Optional context expansion for the generator: top-8 passages plus the neighbouring chunks of the same page.

Retrieval-only study on the development bank (evaluation/heldout/results/retrieval_variants_dev.json): the needed fact was in
the context for 36/44 questions with the top-5 passages and for 38/44 with top-8 plus neighbours. The mode is selected with
CEPRUNSA_RETRIEVAL_MODE ('top5' = previous behaviour, 'top8_nbr')."""
import os

from retriever import retrieve_with_global_fallback, documents as D

_IDX = {cat: {d.get("id"): i for i, d in enumerate(docs)} for cat, docs in D.items()}


def with_neighbours(chunks: list) -> list:
    out, seen = [], set()
    for ch in chunks:
        cat = ch.get("category")
        i = _IDX.get(cat, {}).get(ch.get("id"))
        if i is None:
            if (cat, ch.get("id")) not in seen:
                seen.add((cat, ch.get("id"))); out.append(ch)
            continue
        for j in (i - 1, i, i + 1):
            if j < 0 or j >= len(D[cat]):
                continue
            d = D[cat][j]
            if j != i and d.get("page") != ch.get("page"):
                continue
            key = (cat, d.get("id"))
            if key not in seen:
                seen.add(key); out.append(d)
    return out


def retrieve_for_generation(query: str, category: str, top_k: int = 5, mode: str | None = None) -> list:
    mode = mode or os.environ.get("CEPRUNSA_RETRIEVAL_MODE", "top5")
    if mode == "top8_nbr":
        return with_neighbours(retrieve_with_global_fallback(query, category, top_k=max(8, top_k)))
    return retrieve_with_global_fallback(query, category, top_k=top_k)
