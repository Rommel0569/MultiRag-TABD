"""Runs V4 (old code, frozen copy) or V4b (current app/) on a question bank. Same index/model/settings as run_heldout.py.

  --app app                                     --systems V4b   (improved three-phase pipeline)
  --app evaluation/heldout/app_v4_frozen        --systems V4    (the pipeline as it was before the improvements)
  --freeze FREEZE2.json  verifies app/*.py hashes before running (used for the sealed test).
V4b = router -> evidence check on an OOD verdict -> structured extraction in the routed category, then the others
      -> hybrid retrieval + rerank -> generator. Cache disabled.
"""
import hashlib, json, os, sys, time, argparse, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--app", default="app")
ap.add_argument("--systems", default="V4b")
ap.add_argument("--bank", default=str(HERE / "heldout_bank.json"))
ap.add_argument("--out", required=True)
ap.add_argument("--freeze", default=None)
a = ap.parse_args()
APP = (ROOT / a.app).resolve()
sys.path.insert(0, str(APP))
os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)
os.environ["CEPRUNSA_INDEX_DIR"] = str(ROOT / "data" / "index_textract_85_v9")
os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
os.environ["CEPRUNSA_GENERATOR_MODEL"] = "llama3:8b"
os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
os.environ["CEPRUNSA_ROUTER_MODEL"] = "llama3:8b"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
if a.freeze:
    fr = json.load(open(a.freeze, encoding="utf-8"))
    bad = [n for n, h in fr["app_sha256"].items() if sha(APP / n) != h]
    if bad:
        raise SystemExit(f"FROZEN FILES CHANGED: {bad}")

from router import route_query
from retriever import retrieve_with_global_fallback, documents as indexed_documents
from llm import generate_response
import pipeline as P


def run_system(name, q):
    info = {}
    if name in ("V1", "V6"):  # baselines, identical to run_heldout.py
        from retriever import CATEGORIES, dense_search, retrieve_all
        if name == "V1":
            r = []
            for c in CATEGORIES:
                r += dense_search(q, c, top_k=5)
            r.sort(key=lambda d: d["score_dense"]); chunks = r[:5]
        else:
            chunks = retrieve_all(q, top_k_per_cat=5)[:5]
        resp = generate_response(q, chunks)
        return dict(answer=resp["answer"], contexts=[c.get("text", "") for c in chunks], phase="baseline_" + name)
    route = route_query(q); info["router"] = route.get("raw_response"); info["pred_category"] = route["category"]
    cat = route["category"]
    if name == "V4b":
        ov = P.ood_evidence_override(q, route)
        if ov:
            info["ood_override"] = ov; cat = ov["category"]; route = dict(route, is_in_domain=True)
        if not route["is_in_domain"]:
            return dict(answer=P.OUT_OF_DOMAIN_RESPONSE, contexts=[], phase="router_ood", **info)
        from structured_answers import resolve_structured_answer_any
        st = resolve_structured_answer_any(q, cat, indexed_documents)
    else:  # old V4
        if not route["is_in_domain"]:
            return dict(answer=P.OUT_OF_DOMAIN_RESPONSE, contexts=[], phase="router_ood", **info)
        from structured_answers import resolve_structured_answer
        st = resolve_structured_answer(q, cat, indexed_documents)
    if st:
        return dict(answer=st["answer"], contexts=[c.get("text", "") for c in st["contexts"]],
                    phase="structured_" + str(st.get("structured_lookup")), **info)
    chunks = retrieve_with_global_fallback(q, cat, top_k=5)
    resp = generate_response(q, chunks)
    return dict(answer=resp["answer"], contexts=[c.get("text", "") for c in chunks], phase="hybrid_fallback_generation", **info)


bank = json.load(open(a.bank, encoding="utf-8"))["consultas"]
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / f"manifest_{a.systems.replace(',', '_')}.json").write_text(json.dumps({
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "bank": a.bank, "bank_sha256": sha(a.bank),
    "app": a.app, "app_sha256": {p.name: sha(p) for p in sorted(APP.glob("*.py"))}, "freeze": a.freeze,
    "model": "ollama llama3:8b T=0.1", "cache": "disabled"}, indent=1), encoding="utf-8")
for s in a.systems.split(","):
    path = out / f"{s}.jsonl"
    done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
    with open(path, "a", encoding="utf-8") as f:
        for i, it in enumerate(bank, 1):
            if it["id"] in done:
                continue
            t0 = time.perf_counter()
            try:
                r = run_system(s, it["query"]); err = None
            except Exception as e:
                r = dict(answer="", contexts=[], phase="error"); err = f"{type(e).__name__}: {e}"
            r.update(id=it["id"], query=it["query"], system=s, error=err, elapsed_s=round(time.perf_counter() - t0, 3))
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            print(f"[{s} {i}/{len(bank)}] {it['id']} {r['phase']} {r['elapsed_s']}s err={bool(err)}", flush=True)
print("[DONE]")
