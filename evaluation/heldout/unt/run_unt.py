"""Ingests the UNT regulation (native text, NO OCR) into a fresh workspace with the UNMODIFIED application code,
then answers the UNT bank with four systems that share the same chunks, embeddings, generator and prompt:
  D  dense top-8 (FAISS only)
  H  hybrid dense+BM25 (RRF) top-8, no reranking
  F  hybrid + cross-encoder reranking top-8            (the retrieval used by the shipped workspace pipeline)
  G  the shipped end-to-end workspace pipeline (scope classifier -> F -> generation); cache disabled
Refuses to run if app/*.py differ from FREEZE.json.
"""
import hashlib, json, os, sys, time, datetime, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "app"))
WS = ROOT / "tmp" / "unt_workspaces"
shutil.rmtree(WS, ignore_errors=True)
os.environ["CEPRUNSA_WORKSPACES_DIR"] = str(WS)
os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
os.environ["CEPRUNSA_GENERATOR_MODEL"] = "llama3:8b"
os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
os.environ["CEPRUNSA_ROUTER_MODEL"] = "llama3:8b"
os.environ["CEPRUNSA_INDEX_DIR"] = "data/index_textract_85_v9"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
fr = json.load(open(HERE.parent / "FREEZE.json", encoding="utf-8"))
bad = [n for n, h in fr["app_sha256"].items() if sha(ROOT / "app" / n) != h]
if bad:
    raise SystemExit(f"FROZEN FILES CHANGED: {bad}")

import numpy as np
import workspace_manager as wm
from embeddings import embed_query, rerank
from retriever import reciprocal_rank_fusion
from llm import generator_config

PDF = ROOT.parent / "otra_inst" / "c4.pdf"
bank = json.load(open(HERE / "unt_bank.json", encoding="utf-8"))["consultas"]

ws = wm.create_workspace("Universidad Nacional de Trujillo - Reglamento de Admisión 2027",
                         "Reglamento de admisión a los programas de pregrado de la Universidad Nacional de Trujillo: modalidades, requisitos, vacantes, evaluación, sanciones.")
doc = wm.add_pdf(ws["id"], "UNT_Reglamento_Admision_2027.pdf", PDF.read_bytes(), context_confirmed=True)
manifest = wm._read_manifest(ws["id"])
print("INGEST:", {k: doc[k] for k in ("pages", "native_pages", "ocr_pages", "status")}, "segments:", manifest.get("segment_count"))
# Two pages are flagged "needs OCR" by the app's conservative heuristic (p.1: a 31-character approval stamp;
# p.16: a table with a math formula that yields a few odd glyphs). No OCR credit is available, so their NATIVE text is
# indexed as-is using the app's own functions (no app code is modified). Recorded as a deviation in the manifest.
FORCED_NATIVE = doc["status"] == "awaiting_ocr_consent"
if FORCED_NATIVE:
    pdf_path = wm._workspace_dir(ws["id"]) / "documents" / doc["id"] / "original.pdf"
    native_pages, _ = wm._native_pages(pdf_path)
    clean = [{k: v for k, v in pg.items() if k != "text_layer_quality"} for pg in native_pages]
    wm._process_native(ws["id"], doc["id"], clean)
    manifest = wm._read_manifest(ws["id"])
    print("FORCED NATIVE INDEXING of all pages (no OCR); segments:", manifest.get("segment_count"))
# cache off, so each query is answered from scratch
wm._cache_get = lambda *a, **k: None
wm._cache_put = lambda *a, **k: None


def retrieve(kind, q, k=8):
    manifest = wm._read_manifest(ws["id"])
    index, docs, bm25 = wm._load_workspace_retriever(ws["id"], int(manifest.get("index_version", 0)))
    vec = embed_query(q).reshape(1, -1)
    ds, di = index.search(vec, min(20, len(docs)))
    dense = []
    for s, i in zip(ds[0], di[0]):
        if i >= 0:
            it = docs[int(i)].copy(); it["score_dense"] = float(s); dense.append(it)
    if kind == "D":
        return dense[:k]
    toks = wm._tokenize(q)
    sc = bm25.get_scores(toks) if toks else np.zeros(len(docs))
    lex = []
    for i in np.argsort(sc)[::-1][:20]:
        if sc[i] > 0:
            it = docs[int(i)].copy(); it["score_bm25"] = float(sc[i]); lex.append(it)
    cands = reciprocal_rank_fusion(dense, lex, top_k=min(40, len(docs)))
    return cands[:k] if kind == "H" else rerank(q, cands, top_k=k)


def generate(q, chunks):
    cfg = generator_config()
    context = "\n\n".join(f"[Fuente: {c.get('source','?')}, página {c.get('page','?')}; tipo: {c.get('extraction','texto')}]\n{c['text']}" for c in chunks)
    system_prompt = (
        f"Respondes preguntas usando exclusivamente los documentos del contexto activo {manifest['name']}. "
        f"Alcance declarado: {manifest['description']} Responde en español y con brevedad. "
        "No mezcles datos de otras universidades, documentos, contextos ni conocimiento externo. "
        "Para tablas, relaciona explícitamente encabezado, fila y valor; no unas columnas diferentes. "
        "Si los fragmentos no bastan o no permiten confirmar el dato, responde que no aparece en los documentos del contexto.")
    r = wm._client(cfg["base_url"], cfg["api_key"]).chat.completions.create(
        model=cfg["model"], messages=[{"role": "system", "content": system_prompt},
                                      {"role": "user", "content": f"EVIDENCIA:\n{context}\n\nPREGUNTA: {q}"}],
        temperature=0.1)
    return (r.choices[0].message.content or "").strip()


out = HERE / "runs"; out.mkdir(exist_ok=True)
json.dump({"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "pdf": str(PDF), "pdf_sha256": sha(PDF),
           "bank_sha256": sha(HERE / "unt_bank.json"), "ingest": doc, "segments": manifest.get("segment_count"),
           "model": "ollama llama3:8b T=0.1", "ocr": "none (native text layer)", "forced_native_pages_flagged_needs_ocr": FORCED_NATIVE}, open(out / "manifest.json", "w"), indent=1)
for s in ["D", "H", "F", "G"]:
    path = out / f"{s}.jsonl"
    done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
    with open(path, "a", encoding="utf-8") as f:
        for i, it in enumerate(bank, 1):
            if it["id"] in done:
                continue
            t0 = time.perf_counter(); err = None
            try:
                if s == "G":
                    r = wm.query_workspace(ws["id"], it["query"]); ans = r["answer"]; phase = r["phase"]
                    ctx = []
                else:
                    ch = retrieve(s, it["query"]); ans = generate(it["query"], ch); phase = s
                    ctx = [c["text"] for c in ch]
            except Exception as e:
                ans, phase, ctx, err = "", "error", [], f"{type(e).__name__}: {e}"
            f.write(json.dumps(dict(id=it["id"], query=it["query"], system=s, answer=ans, phase=phase, contexts=ctx, error=err,
                                    elapsed_s=round(time.perf_counter() - t0, 3)), ensure_ascii=False) + "\n"); f.flush()
            print(f"[{s} {i}/{len(bank)}] {it['id']} {phase} {round(time.perf_counter()-t0,1)}s err={bool(err)}", flush=True)
print("[DONE]")
