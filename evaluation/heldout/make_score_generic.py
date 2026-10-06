"""Derives score_generic.py from score_heldout.py (identical scoring rules) with a configurable bank / run files / tag.

usage: score_generic.py --bank B.json --tag T --run LABEL=path.jsonl [--run ...] [--relaxed] [--base LABEL] [--compare A:B ...]
"""
from pathlib import Path
HERE = Path(__file__).resolve().parent
s = (HERE / "score_heldout.py").read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


rep('SYS = ["V1", "V2", "V3", "V5", "V6", "V4"]',
    'import argparse\n_ap = argparse.ArgumentParser(); _ap.add_argument("--bank", required=True); _ap.add_argument("--tag", required=True)\n'
    '_ap.add_argument("--run", action="append", required=True); _ap.add_argument("--relaxed", action="store_true")\n'
    '_ap.add_argument("--compare", action="append", default=[]); ARGS = _ap.parse_args()\n'
    'RUNFILES = dict(r.split("=", 1) for r in ARGS.run); SYS = list(RUNFILES)')
rep('NAMES = {"V1": "V1 dense baseline", "V2": "V2 dense+rerank", "V3": "V3 router+hybrid", "V5": "V5 router+hybrid+rerank (no extraction)",\n         "V6": "V6 hybrid+rerank, no router", "V4": "V4 complete"}',
    'NAMES = {k: k for k in RUNFILES}')
rep('RELAX = "--relaxed" in sys.argv', 'RELAX = ARGS.relaxed')
rep('bank = json.load(open(HERE / "heldout_bank.json", encoding="utf-8"))', 'bank = json.load(open(ARGS.bank, encoding="utf-8"))')
rep('    p = HERE / "runs" / f"{s}.jsonl"', '    p = Path(RUNFILES[s])')
rep('P("bank sha256-based id:", bank["created_utc"], " | max sim to any dev question:", bank["max_similarity_to_any_seen_question"])',
    'P("bank:", ARGS.bank)')
rep('for a, b in [("V4", "V1"), ("V4", "V6"), ("V4", "V5"), ("V5", "V1"), ("V5", "V6"), ("V6", "V1")]:',
    'for a, b in [tuple(c.split(":")) for c in ARGS.compare]:')
rep('P("## V4 phase usage:", dict(collections.Counter(r["phase"] for r in runs["V4"].values())) if "V4" in runs else "")',
    'for _s in SYS:\n    P("## phase usage", _s, dict(collections.Counter(r["phase"] for r in runs[_s].values())))')
rep('"heldout_results_relaxed.md" if RELAX else "heldout_results.md"', 'f"{ARGS.tag}_results_relaxed.md" if RELAX else f"{ARGS.tag}_results.md"')
rep('"review_sheet_relaxed.csv" if RELAX else "review_sheet.csv"', 'f"{ARGS.tag}_review_relaxed.csv" if RELAX else f"{ARGS.tag}_review.csv"')
rep('"outcomes_relaxed.json" if RELAX else "outcomes.json"', 'f"{ARGS.tag}_outcomes_relaxed.json" if RELAX else f"{ARGS.tag}_outcomes.json"')
rep('"ALL (89)"', '"ALL"')
(HERE / "score_generic.py").write_text(s, encoding="utf-8")
print("written score_generic.py")
