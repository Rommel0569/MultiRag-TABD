"""Scores the blind human ratings: accuracy per system (95% bootstrap CI), Cohen's kappa between monitors, paired McNemar.
usage: python score_human.py --bank real_bank.json [--resolved resolved.csv]
If the monitors disagree on some answers, the script writes disagreements_ratings.csv; fill `final` there (C/P/I/A) and pass it with --resolved.
Rule: for SIN_RESPUESTA / FUERA_DE_DOMINIO items an answer is correct only if rated A; otherwise only if rated C (P counts as incorrect;
a lenient column with P counted as correct is also reported)."""
import argparse, csv, json, random, collections
from scipy.stats import binomtest
ap = argparse.ArgumentParser()
ap.add_argument("--bank", required=True); ap.add_argument("--resolved")
a = ap.parse_args()
bank = {b["id"]: b for b in json.load(open(a.bank, encoding="utf-8"))["consultas"]}
key = json.load(open("blind_key.json"))
rate = {}
for tag in ("A", "B"):
    for r in csv.DictReader(open(f"rater_{tag}.csv", encoding="utf-8-sig")):
        k = key[f"{tag}:{r['row']}"]; rate.setdefault((k["id"], k["system"]), {})[tag] = r["rating"].strip().upper()
res = {}
if a.resolved:
    for r in csv.DictReader(open(a.resolved, encoding="utf-8-sig")):
        res[(r["id"], r["system"])] = r["final"].strip().upper()
missing = [k for k, v in rate.items() if not v.get("A") or not v.get("B")]
assert not missing, f"{len(missing)} answers without a rating from both monitors"
dis = [(k, v) for k, v in rate.items() if v["A"] != v["B"] and k not in res]
if dis:
    with open("disagreements_ratings.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "system", "question", "answer_gold", "rating_A", "rating_B", "final"])
        for (i, s), v in dis:
            w.writerow([i, s, bank[i]["query"], bank[i]["gold"], v["A"], v["B"], ""])
    raise SystemExit(f"{len(dis)} rating disagreements -> disagreements_ratings.csv; resolve them (column final) and rerun with --resolved")
final = {k: res.get(k, v["A"]) for k, v in rate.items()}


def ok(i, rating, lenient=False):
    if bank[i]["abstain"]:
        return rating == "A"
    return rating == "C" or (lenient and rating == "P")


def kappa(x, y):
    n = len(x); po = sum(p == q for p, q in zip(x, y)) / n
    cx, cy = collections.Counter(x), collections.Counter(y)
    pe = sum(cx[k] * cy[k] for k in set(x) | set(y)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


systems = sorted({s for _, s in rate}); ids = sorted(bank)
ka = [ok(i, v["A"]) for (i, s), v in rate.items()]; kb = [ok(i, v["B"]) for (i, s), v in rate.items()]
print(f"inter-monitor agreement on correct/incorrect: {sum(p == q for p, q in zip(ka, kb))}/{len(ka)}; Cohen's kappa = {kappa(ka, kb):.3f}")
corr = {s: [ok(i, final[(i, s)]) for i in ids] for s in systems}
rnd = random.Random(1)
for s in systems:
    v = corr[s]; n = len(v)
    bs = sorted(sum(v[rnd.randrange(n)] for _ in range(n)) / n for _ in range(5000))
    len_ = sum(ok(i, final[(i, s)], True) for i in ids)
    print(f"{s}: {sum(v)}/{n} = {100*sum(v)/n:.1f}% (95% CI {100*bs[125]:.1f}-{100*bs[4874]:.1f}); lenient (partial counted) {len_}/{n}")
for i1, s1 in enumerate(systems):
    for s2 in systems[i1 + 1:]:
        x = sum(p and not q for p, q in zip(corr[s1], corr[s2])); y = sum(q and not p for p, q in zip(corr[s1], corr[s2]))
        print(f"{s1} vs {s2}: only-{s1}={x}, only-{s2}={y}, McNemar p={binomtest(x, x + y, .5).pvalue if x + y else 1:.3g}")
