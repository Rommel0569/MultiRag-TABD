"""Blind rating sheets: shuffles the answers of the systems (system names hidden), one sheet per monitor, plus a key.
usage: python prepare_blind_sheets.py --bank real_bank.json --run V1=runs/V1.jsonl --run V6=runs/V6.jsonl --run V4b=runs/V4b.jsonl
Each monitor fills the `rating` column: C (correct), P (partial), I (incorrect), A (the system abstained / said it did not find it)."""
import argparse, csv, json, random
ap = argparse.ArgumentParser()
ap.add_argument("--bank", required=True); ap.add_argument("--run", action="append", required=True)
ap.add_argument("--seed-a", type=int, default=11); ap.add_argument("--seed-b", type=int, default=22)
a = ap.parse_args()
bank = {b["id"]: b for b in json.load(open(a.bank, encoding="utf-8"))["consultas"]}
runs = {}
for r in a.run:
    name, path = r.split("=", 1)
    runs[name] = {json.loads(l)["id"]: json.loads(l) for l in open(path, encoding="utf-8")}
items = [(i, s) for i in bank for s in runs if i in runs[s]]
key = {}
for tag, seed in (("A", a.seed_a), ("B", a.seed_b)):
    order = items[:]; random.Random(seed).shuffle(order)
    with open(f"rater_{tag}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "category", "gold", "source", "system_answer", "rating"])
        for n, (i, s) in enumerate(order, 1):
            b = bank[i]; w.writerow([n, b["query"], b["category"], b["gold"], b["source"], runs[s][i]["answer"].replace("\n", " "), ""])
            key[f"{tag}:{n}"] = {"id": i, "system": s}
json.dump(key, open("blind_key.json", "w"), indent=0)
print(f"{len(items)} answers x 2 monitors; sheets rater_A.csv / rater_B.csv; key in blind_key.json (do not share with the monitors)")
