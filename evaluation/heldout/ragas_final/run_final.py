"""Generates the answers for the final RAGAS run (Ollama llama3:8b, T=0.1, no cache), for the questions of sample_bank.json.
  V1   dense baseline, original terse prompt                         (same as before)
  V1c  dense baseline, contextual answer style                       (isolates the effect of the answer style)
  V4c  improved system (V4b) + contextual style + verbalized facts   (full system)
Refuses to run if app/*.py differ from FREEZE3.json. Resumable."""
import hashlib, json, os, sys, time, argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "app")); os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)
os.environ["CEPRUNSA_INDEX_DIR"] = str(ROOT / "data" / "index_textract_85_v9")
os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
os.environ["CEPRUNSA_GENERATOR_MODEL"] = "llama3:8b"
os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
os.environ["CEPRUNSA_ROUTER_MODEL"] = "llama3:8b"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
fr = json.load(open(HERE / "FREEZE3.json", encoding="utf-8"))
bad = [n for n, h in fr["app_sha256"].items() if sha(ROOT / "app" / n) != h]
bad += [n for n, h in fr["index_sha256"].items() if sha(ROOT / "data/index_textract_85_v9" / n) != h]
if bad or sha(HERE / "sample_bank.json") != fr["sample_bank_sha256"]:
    raise SystemExit(f"FROZEN FILES CHANGED: {bad}")

from router import route_query
from retriever import CATEGORIES, dense_search, retrieve_with_global_fallback, documents as indexed_documents
from llm import generate_response
from structured_answers import resolve_structured_answer_any
from verbalizer import verbalize
import pipeline as P

ap = argparse.ArgumentParser(); ap.add_argument("--systems", default="V1,V1c,V4c"); a = ap.parse_args()
bank = json.load(open(HERE / "sample_bank.json", encoding="utf-8"))["consultas"]


def dense(q, k=5):
    r = []
    for c in CATEGORIES:
        r += dense_search(q, c, top_k=k)
    r.sort(key=lambda d: d["score_dense"]); return r[:k]


def run(name, q):
    if name in ("V1", "V1c"):
        ch = dense(q); resp = generate_response(q, ch, contextual=(name == "V1c"))
        return dict(answer=resp["answer"], contexts=[c["text"] for c in ch], phase="dense_global_top5")
    route = route_query(q); cat = route["category"]; info = {"router": route.get("raw_response"), "pred_category": cat}
    ov = P.ood_evidence_override(q, route)
    if ov:
        cat = ov["category"]; route = dict(route, is_in_domain=True)
    if not route["is_in_domain"]:
        return dict(answer=P.OUT_OF_DOMAIN_RESPONSE, contexts=[], phase="router_ood", **info)
    st = resolve_structured_answer_any(q, cat, indexed_documents)
    if st:
        ans, mode = verbalize(q, st)
        return dict(answer=ans, contexts=[c.get("text", "") for c in st["contexts"]], phase="structured_" + str(st.get("structured_lookup")), verbalizer=mode, **info)
    ch = retrieve_with_global_fallback(q, cat, top_k=5)
    resp = generate_response(q, ch, contextual=True)
    return dict(answer=resp["answer"], contexts=[c.get("text", "") for c in ch], phase="hybrid_fallback_generation", **info)


out = HERE / "runs"; out.mkdir(exist_ok=True)
for s in a.systems.split(","):
    path = out / f"{s}.jsonl"
    done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
    with open(path, "a", encoding="utf-8") as f:
        for i, it in enumerate(bank, 1):
            if it["id"] in done:
                continue
            t0 = time.perf_counter()
            try:
                r = run(s, it["query"]); err = None
            except Exception as e:
                r = dict(answer="", contexts=[], phase="error"); err = f"{type(e).__name__}: {e}"
            r.update(id=it["id"], query=it["query"], system=s, error=err, elapsed_s=round(time.perf_counter() - t0, 3))
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            print(f"[{s} {i}/{len(bank)}] {it['id']} {r['phase']} {r.get('verbalizer','')} {r['elapsed_s']}s err={bool(err)}", flush=True)
print("[DONE]")
