"""Scores the held-out runs with deterministic gold-key matching (no LLM judge, no cost).

Outcome per (system, item):
  correct    : all `must` regexes match the normalized answer (or, for abstain items, the system abstained)
  abstained  : in-domain answerable item, system declined to answer (safe but incorrect)
  wrong      : confidently wrong / missing facts / hallucinated answer to an unanswerable or out-of-domain item
"Shotgun guard": a single-value lookup whose answer lists more than 5 different numbers is counted wrong.
"""
import csv, difflib, json, re, sys, unicodedata, random, collections
from pathlib import Path
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SYS = ["D", "H", "F", "G"]
NAMES = {"D": "D dense top-8", "H": "H hybrid (RRF) top-8", "F": "F hybrid + rerank top-8", "G": "G shipped workspace pipeline (scope check + F)"}
ABSTAIN = re.compile(r"no encontre esa informacion|fuera del alcance|no aparece|no figura|no se encuentra|no hay informacion|"
                     r"no tengo informacion|no corresponde|no puedo (responder|ayudar)|no (esta|estan) (en|incluid)|"
                     r"no se (menciona|especifica|indica|proporciona)|no contiene|no cuento|no existe informacion|no hay datos")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def distinct_numbers(a):
    a = re.sub(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", " ", a)           # dates
    a = re.sub(r"(pagina|pag\.?|p\.)\s*\d+", " ", a)
    return set(re.findall(r"(?<![\d.,])\d+(?![\d])", a))


RELAX = "--relaxed" in sys.argv
STEMS = [(r"anulacion", r"anul\w+"), (r"suspend\|suspension", r"suspend\w*|suspension"), (r"regulariz", r"regulariz\w*"),
         (r"impedid", r"impedid\w*"), (r"devol", r"devol\w*")]


def relax(p):
    for a, b in STEMS:
        p = p.replace(a, b)
    return p


def outcome(item, ans):
    a = norm(ans)
    if RELAX:
        item = dict(item, must=[relax(p) for p in item["must"]])
    ab = bool(ABSTAIN.search(a))
    if item["abstain"]:
        return "correct" if ab else "wrong"
    ok = all(re.search(p, a) for p in item["must"])
    if ok and item["type"] == "lookup" and len(distinct_numbers(a)) > 5:
        return "wrong"
    if ok and not (ab and len(a) < 120):
        return "correct"
    return "abstained" if ab else "wrong"


HERE = HERE / "unt"
bank = json.load(open(HERE / "unt_bank.json", encoding="utf-8"))
items = bank["consultas"]
for it in items:
    it["sim"] = 0.0

runs = {}
for s in SYS:
    p = HERE / "runs" / f"{s}.jsonl"
    if p.exists():
        runs[s] = {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8"))}
SYS = [s for s in SYS if s in runs and len(runs[s]) == len(items)]
print("systems with complete runs:", SYS)
res = {s: {it["id"]: outcome(it, runs[s][it["id"]]["answer"]) for it in items} for s in SYS}
corr = {s: [res[s][it["id"]] == "correct" for it in items] for s in SYS}


def boot(vec, n=10000, seed=1):
    rnd = random.Random(seed); m = len(vec); out = []
    for _ in range(n):
        out.append(sum(vec[rnd.randrange(m)] for _ in range(m)) / m)
    out.sort(); return out[int(.025 * n)], out[int(.975 * n)]


def boot_diff(a, b, n=10000, seed=2):
    rnd = random.Random(seed); m = len(a); out = []
    for _ in range(n):
        idx = [rnd.randrange(m) for _ in range(m)]
        out.append(sum(a[i] - b[i] for i in idx) / m)
    out.sort(); return out[int(.025 * n)], out[int(.975 * n)]


def mcnemar(a, b):
    b01 = sum(1 for x, y in zip(a, b) if x and not y); b10 = sum(1 for x, y in zip(a, b) if y and not x)
    return b01, b10, (binomtest(b01, b01 + b10, 0.5).pvalue if b01 + b10 else 1.0)


lines = []
P = lambda *x: (lines.append(" ".join(str(i) for i in x)), print(*x))
def subset(pred): return [i for i, it in enumerate(items) if pred(it)]
groups = {"ALL (89)": subset(lambda it: True),
          "answerable in-domain": subset(lambda it: not it["abstain"]),
          "must abstain (unanswerable + OOD)": subset(lambda it: it["abstain"]),
          }
for t in ["lookup", "list", "open", "locate", "unanswerable", "ood"]:
    groups[f"type {t}"] = subset(lambda it, t=t: it["type"] == t)

P("# Held-out evaluation (n=%d), deterministic gold-key scoring" % len(items))
P("bank sha256-based id:", bank["created_utc"])
P()
for g, idx in groups.items():
    if not idx: continue
    P(f"## {g}  (n={len(idx)})")
    P("| system | correct | 95% CI | abstained (safe, incorrect) | wrong |")
    P("|---|---|---|---|---|")
    for s in SYS:
        v = [corr[s][i] for i in idx]; lo, hi = boot(v)
        ab = sum(res[s][items[i]["id"]] == "abstained" for i in idx); wr = sum(res[s][items[i]["id"]] == "wrong" for i in idx)
        P(f"| {NAMES[s]} | {sum(v)}/{len(v)} = {100*sum(v)/len(v):.1f}% | {100*lo:.1f}-{100*hi:.1f} | {ab} | {wr} |")
    P()
P("## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)")
for a, b in [("F", "D"), ("F", "H"), ("H", "D"), ("G", "D"), ("G", "F")]:
    if a in SYS and b in SYS:
        lo, hi = boot_diff(corr[a], corr[b]); b01, b10, p = mcnemar(corr[a], corr[b])
        d = (sum(corr[a]) - sum(corr[b])) / len(items)
        P(f"- {a} - {b}: {100*d:+.1f} pp (95% CI {100*lo:+.1f} to {100*hi:+.1f}); only-{a}={b01}, only-{b}={b10}, McNemar p={p:.3g}")
P()
P("## Latency per query (s): mean / median")
for s in SYS:
    t = sorted(r["elapsed_s"] for r in runs[s].values())
    P(f"- {NAMES[s]}: {sum(t)/len(t):.2f} / {t[len(t)//2]:.2f}")
P()


(HERE.parent / "results").mkdir(exist_ok=True)
(HERE.parent / "results" / ("unt_results_relaxed.md" if RELAX else "unt_results.md")).write_text("\n".join(lines), encoding="utf-8")
with open(HERE.parent / "results" / ("unt_review_sheet_relaxed.csv" if RELAX else "unt_review_sheet.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "category", "type", "query", "gold", "source"] + [f"{s}_outcome" for s in SYS] + [f"{s}_answer" for s in SYS] + ["author_check (ok/error)"])
    for it in items:
        w.writerow([it["id"], it["category"], it["type"], it["query"], it["gold"], it["source"]] +
                   [res[s][it["id"]] for s in SYS] + [runs[s][it["id"]]["answer"].replace("\n", " ")[:600] for s in SYS] + [""])
json.dump({"outcomes": res, "sim": {it["id"]: round(it["sim"], 3) for it in items}}, open(HERE.parent / "results" / ("unt_outcomes_relaxed.json" if RELAX else "unt_outcomes.json"), "w"), indent=1)
print("written", HERE.parent / "results")
