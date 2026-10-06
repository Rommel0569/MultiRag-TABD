"""Builds the sealed real-user bank from the question CSV and the gold files of two monitors.

step 1: python make_bank.py --questions preguntas.csv --gold-a gold_A.csv --gold-b gold_B.csv
        -> prints Cohen's kappa on the category and writes disagreements.csv (resolve it by hand into gold_final.csv)
step 2: python make_bank.py --questions preguntas.csv --gold-a gold_A.csv --gold-b gold_B.csv --final gold_final.csv
        -> writes real_bank.json (same format as the other banks) and real_bank_SEAL.json (sha256 + timestamp)
Rows marked AMBIGUA in `category` (by either monitor) are excluded and counted."""
import argparse, csv, json, hashlib, datetime, collections
from pathlib import Path

LAB = ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO", "SIN_RESPUESTA", "FUERA_DE_DOMINIO"]
ap = argparse.ArgumentParser()
ap.add_argument("--questions", required=True); ap.add_argument("--gold-a", required=True); ap.add_argument("--gold-b", required=True)
ap.add_argument("--final"); ap.add_argument("--out", default="real_bank.json")
a = ap.parse_args()
rd = lambda p: {r["id"]: r for r in csv.DictReader(open(p, encoding="utf-8-sig")) if r.get("id") and r.get("category")}
Q = {r["id"]: r for r in csv.DictReader(open(a.questions, encoding="utf-8-sig")) if r.get("id") and r.get("query")}
A, B = rd(a.gold_a), rd(a.gold_b)
ids = [i for i in Q if i in A and i in B]
print(f"questions: {len(Q)}; annotated by both monitors: {len(ids)}")


def kappa(x, y):
    n = len(x); po = sum(p == q for p, q in zip(x, y)) / n
    cx, cy = collections.Counter(x), collections.Counter(y)
    pe = sum(cx[k] * cy[k] for k in set(x) | set(y)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


ca = [A[i]["category"].strip() for i in ids]; cb = [B[i]["category"].strip() for i in ids]
print(f"agreement on category: {sum(p == q for p, q in zip(ca, cb))}/{len(ids)}; Cohen's kappa = {kappa(ca, cb):.3f}")
dis = [i for i, p, q in zip(ids, ca, cb) if p != q]
if not a.final:
    with open("disagreements.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "query", "category_A", "category_B", "gold_A", "gold_B", "category_final", "gold_final", "source_final"])
        for i in dis:
            w.writerow([i, Q[i]["query"], A[i]["category"], B[i]["category"], A[i].get("gold", ""), B[i].get("gold", ""), "", "", ""])
    print(f"{len(dis)} disagreements written to disagreements.csv. Resolve them together, then build gold_final.csv "
          "(all ids: agreed rows copied from either monitor + the resolved ones) and rerun with --final.")
    raise SystemExit
F = rd(a.final)
bank, excluded = [], 0
for i in ids:
    f = F.get(i)
    if not f or f["category"].strip() not in LAB:
        excluded += 1; continue
    cat = f["category"].strip()
    bank.append(dict(id=i, category=cat, type="real", query=Q[i]["query"], gold=f.get("gold", ""), source=f.get("source", ""),
                     abstain=cat in ("SIN_RESPUESTA", "FUERA_DE_DOMINIO"), origen=Q[i].get("origen", "")))
print(f"bank: {len(bank)} questions; excluded (ambiguous or unresolved): {excluded}")
print("categories:", dict(collections.Counter(b["category"] for b in bank)))
out = Path(a.out)
out.write_text(json.dumps({"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "kappa_category": kappa(ca, cb),
                           "n_excluded": excluded, "consultas": bank}, ensure_ascii=False, indent=1), encoding="utf-8")
seal = {"sealed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "bank_sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "n": len(bank)}
Path("real_bank_SEAL.json").write_text(json.dumps(seal, indent=1), encoding="utf-8")
print("sealed:", seal)
