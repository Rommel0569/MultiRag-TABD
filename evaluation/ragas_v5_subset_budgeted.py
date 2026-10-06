"""RAGAS (juez Gemini) solo para V5_hibrido_sin_extractores sobre el subconjunto de 200.

Reutiliza TokenMeter/precios del script archivado y corta al llegar al tope en PEN.
V1 y V4 NO se vuelven a evaluar: se toman de ragas_scores_checkpoint.csv (mismo juez).
"""
import argparse, csv, importlib.util, json, os, sys, time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "evaluation/archive/historical/revision_20260930/manual_validation/run_ragas_500_gemini_budgeted.py"
spec = importlib.util.spec_from_file_location("budgeted", ARCH)
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
METRICS = B.METRICS
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--references", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--stop-pen", type=float, default=4.5)
    ap.add_argument("--batch", type=int, default=10)
    args = ap.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    model = os.environ["CEPRUNSA_GEMINI_JUDGE_MODEL"]
    refs = {r["query"].strip(): r for r in json.loads(args.references.read_text(encoding="utf-8"))["consultas"]}
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "ragas_v5_scores.csv"
    done = set(pd.read_csv(out)["query"]) if out.exists() else set()

    from datasets import Dataset
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas import RunConfig, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

    llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(model=model, temperature=0, max_retries=0))
    emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base", model_kwargs={"local_files_only": True}))
    meter = B.TokenMeter()
    pending = [r for r in rows if r["query"].strip() not in done]
    spent_pen = 0.0
    for i in range(0, len(pending), args.batch):
        if spent_pen >= args.stop_pen:
            print(f"[STOP] tope S/{args.stop_pen} alcanzado ({spent_pen:.2f})"); break
        b = pending[i:i + args.batch]
        ds = Dataset.from_dict({
            "question": [r["query"] for r in b], "contexts": [r["contexts"] for r in b],
            "answer": [r["answer"] for r in b],
            "ground_truth": [refs[r["query"].strip()]["ground_truth"] for r in b]})
        res = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                       llm=llm, embeddings=emb, callbacks=[meter.handler],
                       run_config=RunConfig(max_workers=16, max_retries=2, max_wait=30, timeout=180, seed=42),
                       raise_exceptions=True, show_progress=False).to_pandas()
        t_in, t_out = meter.snapshot()
        spent_pen = B.money_usd(t_in, t_out) * B.PEN_PER_USD
        res.insert(0, "query", [r["query"] for r in b])
        res.insert(1, "category", [refs[r["query"].strip()]["category"] for r in b])
        res[["query", "category", *METRICS]].to_csv(out, mode="a", header=not out.exists(), index=False, encoding="utf-8")
        print(f"[{i + len(b)}/{len(pending)}] gasto estimado S/{spent_pen:.2f}", flush=True)
        time.sleep(0.5)
    print(f"[DONE] gasto total estimado S/{spent_pen:.2f}")


if __name__ == "__main__":
    main()
