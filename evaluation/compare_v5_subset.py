import pandas as pd, json
from scipy.stats import wilcoxon
M=["faithfulness","answer_relevancy","context_precision","context_recall"]
ck=pd.read_csv("evaluation/evidence/ragas_500/run/ragas_scores_checkpoint.csv")
v5=pd.read_csv("evaluation/runs/v5_subset200_ragas/ragas_v5_scores.csv")
q=set(v5["query"]); v5["variant"]="V5_sin_extractores"
sub=pd.concat([ck[(ck.variant.isin(["V1_baseline","V4_completo"]))&ck["query"].isin(q)],v5])
print("n por variante:",sub.groupby("variant").size().to_dict())
print(sub.groupby("variant")[M].mean().round(4).to_string())
print("\nPor categoria:"); print(sub.groupby(["category","variant"])[M].mean().round(3).to_string())
p=sub.pivot_table(index="query",columns="variant",values=M)
print("\nWilcoxon pareado (sin Holm):")
for a,b in [("V5_sin_extractores","V1_baseline"),("V4_completo","V5_sin_extractores")]:
    for m in M:
        d=(p[(m,a)]-p[(m,b)]).dropna()
        try: pv=wilcoxon(d).pvalue
        except Exception: pv=float("nan")
        print(f"{a} - {b} | {m:18s} delta={d.mean():+.4f} p={pv:.3g} n={len(d)}")
