"""Router analysis on the Dev (89) and sealed Test (138) banks, using the router decisions logged by the V4b runs
(router = rules, then zero-shot Llama 3). Supervised classifiers are trained on the 500-question bank only.
Items with gold category SIN_RESPUESTA (in-domain but unanswerable) have no routing label and are excluded.
No LLM call: reads the saved runs. Writes results/router_analysis.json."""
import json, sys, collections, time
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, recall_score, precision_score

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
EV = HERE.parent
LAB = ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO", "FUERA_DE_DOMINIO"]
sets = {"Dev": (HERE / "heldout_bank.json", HERE / "runs_dev_v4b" / "V4b.jsonl"),
        "Test": (HERE / "test2" / "test2_bank.json", HERE / "test2" / "runs" / "V4b.jsonl")}
rows = []
for name, (bp, rp) in sets.items():
    bank = {x["id"]: x for x in json.load(open(bp, encoding="utf-8"))["consultas"]}
    for l in open(rp, encoding="utf-8"):
        r = json.loads(l); b = bank[r["id"]]
        if b["category"] in LAB:
            rows.append(dict(set=name, q=r["query"], gold=b["category"], pred=r["pred_category"],
                             by_rule=r["router"] in ("explicit_intent_rule", "explicit_out_of_domain"),
                             overridden="ood_override" in r))
out = {"n": len(rows)}


def stats(sub, label):
    y = [x["gold"] for x in sub]; p = [x["pred"] for x in sub]
    d = {"n": len(sub), "accuracy": accuracy_score(y, p)}
    d["per_class"] = {c: {"n": y.count(c), "recall": recall_score(y, p, labels=[c], average=None, zero_division=0)[0],
                          "precision": precision_score(y, p, labels=[c], average=None, zero_division=0)[0]} for c in LAB if y.count(c)}
    out[label] = d
    return d


stats(rows, "router_all")
stats([x for x in rows if x["by_rule"]], "router_rule_resolved")
stats([x for x in rows if not x["by_rule"]], "router_llm_resolved")
for s in ("Dev", "Test"):
    stats([x for x in rows if x["set"] == s], f"router_{s}")
out["rule_share"] = sum(x["by_rule"] for x in rows) / len(rows)
# effect of the evidence check: in-domain/out-of-domain decision before and after
ood_before = [(x["gold"] == "FUERA_DE_DOMINIO", x["pred"] == "FUERA_DE_DOMINIO") for x in rows]
ood_after = [(x["gold"] == "FUERA_DE_DOMINIO", x["pred"] == "FUERA_DE_DOMINIO" and not x["overridden"]) for x in rows]
f = lambda L: {"false_reject_in_domain": sum(1 for g, p in L if p and not g), "missed_ood": sum(1 for g, p in L if g and not p)}
out["ood_decision_before_check"] = f(ood_before)
out["ood_decision_after_check"] = f(ood_after)
# supervised baselines trained on the 500 bank
bank500 = json.load(open(EV / "evidence/ragas_500/inputs/queries_500_pdf_verified_ai_adjudicated.json", encoding="utf-8"))["consultas"]
Xb = [c["query"] for c in bank500]; yb = [c["category"] for c in bank500]
Xt = [x["q"] for x in rows]; yt = [x["gold"] for x in rows]
models = {"Linear SVM (TF-IDF)": make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode"), LinearSVC(C=1.0)),
          "Naive Bayes (TF-IDF)": make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode"), MultinomialNB(alpha=0.1))}
sup = {}
for n, m in models.items():
    m.fit(Xb, yb); p = list(m.predict(Xt))
    t = []
    for q in Xt[:40]:
        t0 = time.perf_counter(); m.predict([q]); t.append(time.perf_counter() - t0)
    sup[n] = dict(accuracy=accuracy_score(yt, p), reglamento_recall=recall_score(yt, p, labels=["REGLAMENTO"], average=None, zero_division=0)[0], ms=float(np.mean(t) * 1000))
from sentence_transformers import SentenceTransformer
enc = SentenceTransformer("intfloat/multilingual-e5-base", local_files_only=True)
fe = lambda L: enc.encode(["query: " + q for q in L], normalize_embeddings=True, batch_size=64)
clf = LogisticRegression(max_iter=2000, C=10).fit(fe(Xb), yb); p = list(clf.predict(fe(Xt)))
sup["Logistic regression (e5)"] = dict(accuracy=accuracy_score(yt, p), reglamento_recall=recall_score(yt, p, labels=["REGLAMENTO"], average=None, zero_division=0)[0], ms=None)
out["supervised_on_dev_test"] = sup
json.dump(out, open(HERE / "results" / "router_analysis.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
