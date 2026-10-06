"""Retrieval-only study on the DEV bank (no LLM, no cost): does the needed fact reach the generator?
For each answerable Dev question that is not solved by a structured resolver, one retrieval with top_k=8 yields the variants:
  A top-5 (current)   B top-8   C top-5 + neighbouring chunks   D top-8 + neighbouring chunks
Recall = all gold-key `must` patterns occur in the concatenated contexts (accent/case-insensitive).
Never touches the sealed Test or bank #3."""
import json, os, re, sys, unicodedata, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "app")); os.chdir(ROOT)
os.environ["CEPRUNSA_INDEX_DIR"] = str(ROOT / "data" / "index_textract_85_v9")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from router import route_query
from retriever import retrieve_with_global_fallback, documents as D
from structured_answers import resolve_structured_answer_any

norm = lambda s: re.sub(r"\s+", " ", "".join(c for c in unicodedata.normalize("NFKD", s.casefold()) if not unicodedata.combining(c)))
bank = [b for b in json.load(open(HERE / "heldout_bank.json", encoding="utf-8"))["consultas"] if not b["abstain"]]
idx = {c: {d.get("id"): i for i, d in enumerate(docs)} for c, docs in D.items()}


def neighbours(chunks):
    out, seen = [], set()
    for ch in chunks:
        cat = ch.get("category"); i = idx.get(cat, {}).get(ch.get("id"))
        for j in ([i] if i is None else [i - 1, i, i + 1]):
            if j is None or j < 0 or j >= len(D[cat]):
                continue
            d = D[cat][j]
            if d.get("page") != ch.get("page") and j != i:
                continue
            key = (cat, d.get("id"))
            if key not in seen:
                seen.add(key); out.append(d)
    return out


res = collections.defaultdict(lambda: collections.Counter()); n_cat = collections.Counter()
for k, b in enumerate(bank, 1):
    cat = b["category"]
    if cat in ("SIN_RESPUESTA", "FUERA_DE_DOMINIO"):
        continue
    if resolve_structured_answer_any(b["query"], cat, D):
        continue
    ch8 = retrieve_with_global_fallback(b["query"], cat, top_k=8)
    variants = {"A top5": ch8[:5], "B top8": ch8, "C top5+nbr": neighbours(ch8[:5]), "D top8+nbr": neighbours(ch8)}
    n_cat[cat] += 1
    for name, ch in variants.items():
        txt = norm(" ".join(c["text"] for c in ch))
        res[cat][name] += all(re.search(p, txt) for p in b["must"])
        res["ALL"][name] += all(re.search(p, txt) for p in b["must"])
        res["chars_" + name][cat] += len(txt)
    print(k, b["id"], flush=True)
n_cat["ALL"] = sum(n_cat.values())
out = {c: {v: res[c][v] for v in ("A top5", "B top8", "C top5+nbr", "D top8+nbr")} | {"n": n_cat[c]} for c in list(n_cat)}
json.dump(out, open(HERE / "results" / "retrieval_variants_dev.json", "w"), indent=1)
print(json.dumps(out, indent=1))
