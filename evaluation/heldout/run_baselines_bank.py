"""Dense baselines on any bank (Ollama llama3:8b, T=0.1, no cache), same index as the rest of the experiments.
  V1   dense global top-5, original terse prompt
  V1c  dense global top-5, contextual answer style (isolates the effect of the answer style from the architecture)
usage: python run_baselines_bank.py --bank B.json --out DIR --label V1|V1c [--freeze FREEZE.json]"""
import argparse, hashlib, json, os, sys, time, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--bank", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--label", required=True, choices=["V1", "V1c"]); ap.add_argument("--freeze"); ap.add_argument("--gen-model", default="llama3:8b")
a = ap.parse_args()
sys.path.insert(0, str(ROOT / "app")); os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)
os.environ["CEPRUNSA_INDEX_DIR"] = str(ROOT / "data" / "index_textract_85_v9")
os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
os.environ["CEPRUNSA_GENERATOR_MODEL"] = a.gen_model
os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
if a.freeze:
    fr = json.load(open(a.freeze, encoding="utf-8"))
    bad = [n for n, h in fr["app_sha256"].items() if sha(ROOT / "app" / n) != h]
    if bad:
        raise SystemExit(f"FROZEN FILES CHANGED: {bad}")
from retriever import CATEGORIES, dense_search
from llm import generate_response

bank = json.load(open(a.bank, encoding="utf-8"))["consultas"]
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / f"manifest_{a.label}.json").write_text(json.dumps({"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "bank_sha256": sha(a.bank), "label": a.label, "freeze": a.freeze, "model": f"ollama {a.gen_model} T=0.1"}, indent=1), encoding="utf-8")
path = out / f"{a.label}.jsonl"
done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
with open(path, "a", encoding="utf-8") as f:
    for i, it in enumerate(bank, 1):
        if it["id"] in done:
            continue
        t0 = time.perf_counter(); err = None
        try:
            r = []
            for c in CATEGORIES:
                r += dense_search(it["query"], c, top_k=5)
            r.sort(key=lambda d: d["score_dense"]); ch = r[:5]
            resp = generate_response(it["query"], ch, contextual=(a.label == "V1c"))
            rec = dict(answer=resp["answer"], contexts=[c["text"] for c in ch], phase="dense_global_top5")
        except Exception as e:
            rec = dict(answer="", contexts=[], phase="error"); err = f"{type(e).__name__}: {e}"
        rec.update(id=it["id"], query=it["query"], system=a.label, error=err, elapsed_s=round(time.perf_counter() - t0, 3))
        f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
        print(f"[{a.label} {i}/{len(bank)}] {it['id']} {rec['elapsed_s']}s err={bool(err)}", flush=True)
print("[DONE]")
