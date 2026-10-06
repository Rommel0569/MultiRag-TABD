"""Runs the improved three-phase pipeline (V4d) on a question bank. Options choose the generator model and the retrieval mode.
V4d = router (rules, zero-shot Llama 3, evidence check) -> structured extraction incl. aggregate resolvers (any category)
      -> hybrid retrieval (+ optional neighbouring chunks) -> generator with contextual answer style; extracted facts are
      verbalized with the number-checked verbalizer. Cache disabled. The router uses the same local model as the generator.
usage: python run_v4d.py --bank B.json --out DIR --label NAME [--gen-model qwen2.5:7b] [--retrieval top8_nbr] [--freeze FREEZE.json]"""
import argparse, hashlib, json, os, sys, time, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--bank", required=True); ap.add_argument("--out", required=True); ap.add_argument("--label", required=True)
ap.add_argument("--gen-model", default="llama3:8b"); ap.add_argument("--retrieval", default="top5", choices=["top5", "top8_nbr"])
ap.add_argument("--freeze"); ap.add_argument("--plain", action="store_true", help="terse answers (no contextual style / verbalizer)")
a = ap.parse_args()
sys.path.insert(0, str(ROOT / "app")); os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)
os.environ["CEPRUNSA_INDEX_DIR"] = str(ROOT / "data" / "index_textract_85_v9")
os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
os.environ["CEPRUNSA_GENERATOR_MODEL"] = a.gen_model
os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
os.environ["CEPRUNSA_ROUTER_MODEL"] = a.gen_model   # one local model for routing and generation
os.environ["CEPRUNSA_RETRIEVAL_MODE"] = a.retrieval
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
if a.freeze:
    fr = json.load(open(a.freeze, encoding="utf-8"))
    bad = [n for n, h in fr["app_sha256"].items() if sha(ROOT / "app" / n) != h]
    bad += [n for n, h in fr.get("index_sha256", {}).items() if sha(ROOT / "data/index_textract_85_v9" / n) != h]
    if bad:
        raise SystemExit(f"FROZEN FILES CHANGED: {bad}")

from router import route_query
from retriever import documents as indexed_documents
from llm import generate_response
from structured_answers import resolve_structured_answer_any
from context_expansion import retrieve_for_generation
from verbalizer import verbalize
import pipeline as P


def run(q):
    route = route_query(q); cat = route["category"]
    info = {"router": route.get("raw_response"), "pred_category": cat}
    ov = P.ood_evidence_override(q, route)
    if ov:
        cat = ov["category"]; route = dict(route, is_in_domain=True); info["ood_override"] = ov
    if not route["is_in_domain"]:
        return dict(answer=P.OUT_OF_DOMAIN_RESPONSE, contexts=[], phase="router_ood", **info)
    st = resolve_structured_answer_any(q, cat, indexed_documents)
    if st:
        ans, mode = (st["answer"], "plain") if a.plain else verbalize(q, st)
        return dict(answer=ans, contexts=[c.get("text", "") for c in st["contexts"]], phase="structured_" + str(st.get("structured_lookup")), verbalizer=mode, **info)
    ch = retrieve_for_generation(q, cat, top_k=5)
    resp = generate_response(q, ch, contextual=not a.plain)
    return dict(answer=resp["answer"], contexts=[c.get("text", "") for c in ch], phase="hybrid_fallback_generation", **info)


bank = json.load(open(a.bank, encoding="utf-8"))["consultas"]
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / f"manifest_{a.label}.json").write_text(json.dumps({
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "bank": a.bank, "bank_sha256": sha(a.bank),
    "gen_model": a.gen_model, "retrieval": a.retrieval, "plain": a.plain, "freeze": a.freeze,
    "app_sha256": {p.name: sha(p) for p in sorted((ROOT / "app").glob("*.py"))}}, indent=1), encoding="utf-8")
path = out / f"{a.label}.jsonl"
done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
with open(path, "a", encoding="utf-8") as f:
    for i, it in enumerate(bank, 1):
        if it["id"] in done:
            continue
        t0 = time.perf_counter()
        try:
            r = run(it["query"]); err = None
        except Exception as e:
            r = dict(answer="", contexts=[], phase="error"); err = f"{type(e).__name__}: {e}"
        r.update(id=it["id"], query=it["query"], system=a.label, error=err, elapsed_s=round(time.perf_counter() - t0, 3))
        f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
        print(f"[{a.label} {i}/{len(bank)}] {it['id']} {r['phase']} {r['elapsed_s']}s err={bool(err)}", flush=True)
print("[DONE]")
