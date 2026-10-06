"""Runs every system on the held-out bank with the SAME index/model/settings. Resumable, per-row logs.

Refuses to run if app/*.py or the index differ from FREEZE.json (so no tuning after seeing the bank).
Systems (all cache disabled; Ollama llama3:8b, temperature 0.1):
  V1  dense global top-5 + LLM                        (the paper's baseline)
  V2  dense global top-20 -> cross-encoder top-5 + LLM
  V3  router + hybrid (dense+BM25, RRF) top-5 + LLM
  V5  router + hybrid + rerank (+global fallback) + LLM, NO structured extraction
  V6  NO router: hybrid + rerank over all categories + LLM   (stronger baseline)
  V4  complete system: router -> structured extraction -> hybrid fallback + LLM; fixed out-of-domain reply
"""
import hashlib, json, os, sys, time, glob, argparse, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "app"))
os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)
os.environ["CEPRUNSA_INDEX_DIR"] = "data/index_textract_85_v9"
os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
os.environ["CEPRUNSA_GENERATOR_MODEL"] = "llama3:8b"
os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
os.environ["CEPRUNSA_ROUTER_MODEL"] = "llama3:8b"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


freeze = json.load(open(HERE / "FREEZE.json", encoding="utf-8"))
bad = [n for n, h in freeze["app_sha256"].items() if sha(ROOT / "app" / n) != h]
bad += [n for n, h in freeze["index_sha256"].items() if sha(ROOT / "data/index_textract_85_v9" / n) != h]
if bad:
    raise SystemExit(f"FROZEN FILES CHANGED: {bad}. Re-freeze explicitly and report it; refusing to run.")

from router import route_query
from retriever import (CATEGORIES, dense_search, lexical_search, reciprocal_rank_fusion, retrieve,
                       retrieve_all, retrieve_with_global_fallback, documents as indexed_documents)
from embeddings import rerank
from llm import generate_response
from structured_answers import resolve_structured_answer
from pipeline import OUT_OF_DOMAIN_RESPONSE


def dense_global(q, k):
    r = []
    for c in CATEGORIES:
        r += dense_search(q, c, top_k=k)
    r.sort(key=lambda d: d["score_dense"])
    return r[:k]


def run_system(name, q):
    info = {}
    if name == "V1":
        chunks = dense_global(q, 5); resp = generate_response(q, chunks); phase = "dense_global_top5"
    elif name == "V2":
        chunks = rerank(q, dense_global(q, 20), top_k=5); resp = generate_response(q, chunks); phase = "dense20_rerank5"
    elif name == "V6":
        chunks = retrieve_all(q, top_k_per_cat=5)[:5]; resp = generate_response(q, chunks); phase = "global_hybrid_rerank"
    elif name in ("V3", "V5"):
        route = route_query(q); info["router"] = route.get("raw_response"); info["pred_category"] = route["category"]
        if not route["is_in_domain"]:
            chunks, resp, phase = [], generate_response(q, []), "router_ood_generic"
        elif name == "V3":
            cat = route["category"]
            chunks = reciprocal_rank_fusion(dense_search(q, cat, top_k=10), lexical_search(q, cat, top_k=10), top_k=5)
            resp = generate_response(q, chunks); phase = "router_hybrid_rrf"
        else:
            chunks = retrieve_with_global_fallback(q, route["category"], top_k=5)
            resp = generate_response(q, chunks); phase = "router_hybrid_rerank"
    elif name == "V4":
        route = route_query(q); info["router"] = route.get("raw_response"); info["pred_category"] = route["category"]
        if not route["is_in_domain"]:
            return dict(answer=OUT_OF_DOMAIN_RESPONSE, contexts=[], phase="router_ood", **info)
        st = resolve_structured_answer(q, route["category"], indexed_documents)
        if st:
            return dict(answer=st["answer"], contexts=[c.get("text", "") for c in st["contexts"]],
                        phase="structured_" + str(st.get("structured_lookup")), **info)
        chunks = retrieve_with_global_fallback(q, route["category"], top_k=5)
        resp = generate_response(q, chunks); phase = "hybrid_fallback_generation"
    else:
        raise ValueError(name)
    return dict(answer=resp["answer"], contexts=[c.get("text", "") for c in chunks], phase=phase, **info)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="V4,V6,V1,V2,V3,V5")
    ap.add_argument("--out", default=str(HERE / "runs"))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    bank = json.load(open(HERE / "heldout_bank.json", encoding="utf-8"))
    qs = bank["consultas"][: a.limit] if a.limit else bank["consultas"]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    manifest = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "bank_sha256": sha(HERE / "heldout_bank.json"), "freeze": freeze["frozen_utc"],
                "n_queries": len(qs), "systems": a.systems.split(","),
                "model": "ollama llama3:8b T=0.1", "index": "data/index_textract_85_v9", "cache": "disabled"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    for s in a.systems.split(","):
        path = out / f"{s}.jsonl"
        done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
        with open(path, "a", encoding="utf-8") as f:
            for i, it in enumerate(qs, 1):
                if it["id"] in done:
                    continue
                t0 = time.perf_counter()
                try:
                    r = run_system(s, it["query"]); err = None
                except Exception as e:
                    r = dict(answer="", contexts=[], phase="error"); err = f"{type(e).__name__}: {e}"
                r.update(id=it["id"], query=it["query"], system=s, error=err, elapsed_s=round(time.perf_counter() - t0, 3))
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
                print(f"[{s} {i}/{len(qs)}] {it['id']} {r['phase']} {r['elapsed_s']}s err={bool(err)}", flush=True)
    manifest["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print("[DONE]")


if __name__ == "__main__":
    main()
