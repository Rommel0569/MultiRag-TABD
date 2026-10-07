"""Component ablation of the final system (V4d) on a sealed bank, WITHOUT changing the frozen application code.
Each variant removes one component of V4d; everything else (model, index, temperature, bank) is identical to the V4d run.
Variants declared before running:
  no_structured   Phase 3a off: every in-domain question goes to retrieval + generation
  no_evidence     evidence check off: an LLM out-of-domain verdict is final
  top5            retrieval depth 5 without same-page neighbours (instead of top-8 + neighbours)
  no_verbalizer   extracted facts are returned as the extracted sentence (no verbalizer)
  terse_style     generation with the terse prompt (no contextual style); verbalizer kept
usage: python run_ablation.py --variant NAME --bank B.json --out DIR --gen-model qwen2.5:7b --freeze FREEZE4.json"""
import argparse, hashlib, json, os, sys, time, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VARIANTS = ["no_structured", "no_evidence", "top5", "no_verbalizer", "terse_style"]
ap = argparse.ArgumentParser()
ap.add_argument("--variant", required=True, choices=VARIANTS)
ap.add_argument("--bank", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--gen-model", default="qwen2.5:7b"); ap.add_argument("--freeze")
a = ap.parse_args()
sys.path.insert(0, str(ROOT / "app")); os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)
os.environ["CEPRUNSA_INDEX_DIR"] = str(ROOT / "data" / "index_textract_85_v9")
os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
os.environ["CEPRUNSA_GENERATOR_MODEL"] = a.gen_model
os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
os.environ["CEPRUNSA_ROUTER_MODEL"] = a.gen_model
os.environ["CEPRUNSA_RETRIEVAL_MODE"] = "top5" if a.variant == "top5" else "top8_nbr"
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
    ov = None if a.variant == "no_evidence" else P.ood_evidence_override(q, route)
    if ov:
        cat = ov["category"]; route = dict(route, is_in_domain=True); info["ood_override"] = ov
    if not route["is_in_domain"]:
        return dict(answer=P.OUT_OF_DOMAIN_RESPONSE, contexts=[], phase="router_ood", **info)
    st = None if a.variant == "no_structured" else resolve_structured_answer_any(q, cat, indexed_documents)
    if st:
        ans, mode = (st["answer"], "plain") if a.variant == "no_verbalizer" else verbalize(q, st)
        return dict(answer=ans, contexts=[c.get("text", "") for c in st["contexts"]], phase="structured_" + str(st.get("structured_lookup")), verbalizer=mode, **info)
    ch = retrieve_for_generation(q, cat, top_k=5)
    resp = generate_response(q, ch, contextual=(a.variant != "terse_style"))
    return dict(answer=resp["answer"], contexts=[c.get("text", "") for c in ch], phase="hybrid_fallback_generation", **info)


bank = json.load(open(a.bank, encoding="utf-8"))["consultas"]
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
label = "A_" + a.variant
(out / f"manifest_{label}.json").write_text(json.dumps({
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "bank": a.bank, "bank_sha256": sha(a.bank),
    "variant": a.variant, "gen_model": a.gen_model, "retrieval": os.environ["CEPRUNSA_RETRIEVAL_MODE"], "freeze": a.freeze,
    "app_sha256": {p.name: sha(p) for p in sorted((ROOT / "app").glob("*.py"))}}, indent=1), encoding="utf-8")
path = out / f"{label}.jsonl"
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
        r.update(id=it["id"], query=it["query"], system=label, error=err, elapsed_s=round(time.perf_counter() - t0, 3))
        f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
        print(f"[{label} {i}/{len(bank)}] {it['id']} {r['phase']} {r['elapsed_s']}s err={bool(err)}", flush=True)
print("[DONE]")
