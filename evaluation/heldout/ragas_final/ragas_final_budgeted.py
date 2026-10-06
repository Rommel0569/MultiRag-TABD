"""RAGAS (Gemini judge) for the final run, with a HARD spending cap (PEN, measured from token usage metadata).

Rows are (question, variant). Questions are scored in batches that contain ALL variants of the same questions, so that if the cap
stops the run every scored question has every variant (paired analysis stays valid). Before each batch the worst-case cost of the
batch (rows x PEN_PER_ROW_WORST) must fit under the cap; the measured spend is checkpointed after each batch.
usage: python ragas_final_budgeted.py --cap-pen 2.55"""
import argparse, importlib.util, json, os, sys, time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCH = ROOT / "evaluation/archive/historical/revision_20260930/manual_validation/run_ragas_500_gemini_budgeted.py"
spec = importlib.util.spec_from_file_location("budgeted", ARCH)
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
METRICS = B.METRICS
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PEN_PER_ROW_WORST = 0.016          # the most expensive row of the 500-query run cost 0.0132 PEN
VARIANTS = ["V1", "V1c", "V4c"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap-pen", type=float, default=2.55)
    ap.add_argument("--questions-per-batch", type=int, default=4)
    args = ap.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    model = os.environ["CEPRUNSA_GEMINI_JUDGE_MODEL"]
    bank = json.load(open(HERE / "sample_bank.json", encoding="utf-8"))["consultas"]
    runs = {v: {json.loads(l)["id"]: json.loads(l) for l in open(HERE / "runs" / f"{v}.jsonl", encoding="utf-8")} for v in VARIANTS}
    for v in VARIANTS:
        assert len(runs[v]) == len(bank), f"{v} incomplete: {len(runs[v])}/{len(bank)}"
    out = HERE / "ragas_scores.csv"
    prev = pd.read_csv(out) if out.exists() else pd.DataFrame(columns=["id", "variant"])
    done_q = {i for i, g in prev.groupby("id") if set(g["variant"]) == set(VARIANTS)}
    spent_file = HERE / "spend.json"
    spent_before = json.load(open(spent_file))["pen"] if spent_file.exists() else 0.0
    pending = [b for b in bank if b["id"] not in done_q]
    print(f"pending questions: {len(pending)}; already spent S/{spent_before:.3f}; cap S/{args.cap_pen}")

    from datasets import Dataset
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas import RunConfig, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

    llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(model=model, temperature=0, max_retries=0))
    emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base", model_kwargs={"local_files_only": True}))
    meter = B.TokenMeter()
    for i in range(0, len(pending), args.questions_per_batch):
        batch = pending[i:i + args.questions_per_batch]
        rows = len(batch) * len(VARIANTS)
        spent = spent_before + B.money_usd(*meter.snapshot()) * B.PEN_PER_USD
        if spent + rows * PEN_PER_ROW_WORST > args.cap_pen:
            print(f"[STOP] next batch could exceed the cap (spent S/{spent:.3f}, worst-case batch S/{rows * PEN_PER_ROW_WORST:.3f})"); break
        recs = [(b, v) for b in batch for v in VARIANTS]
        ds = Dataset.from_dict({"question": [b["query"] for b, v in recs], "contexts": [runs[v][b["id"]]["contexts"] or [""] for b, v in recs],
                                "answer": [runs[v][b["id"]]["answer"] for b, v in recs], "ground_truth": [b["ground_truth"] for b, v in recs]})
        res = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision, context_recall], llm=llm, embeddings=emb,
                       callbacks=[meter.handler], run_config=RunConfig(max_workers=8, max_retries=2, max_wait=30, timeout=180, seed=42),
                       raise_exceptions=True, show_progress=False).to_pandas()
        res.insert(0, "id", [b["id"] for b, v in recs]); res.insert(1, "variant", [v for b, v in recs])
        res.insert(2, "category", [b["category"] for b, v in recs])
        res[["id", "variant", "category", *METRICS]].to_csv(out, mode="a", header=not out.exists(), index=False, encoding="utf-8")
        spent = spent_before + B.money_usd(*meter.snapshot()) * B.PEN_PER_USD
        json.dump({"pen": spent, "input_tokens": meter.snapshot()[0], "output_tokens": meter.snapshot()[1], "model": model}, open(spent_file, "w"))
        print(f"[{min(i + len(batch), len(pending))}/{len(pending)}] measured spend S/{spent:.3f}", flush=True)
        time.sleep(0.5)
    print("[DONE]")


if __name__ == "__main__":
    main()
