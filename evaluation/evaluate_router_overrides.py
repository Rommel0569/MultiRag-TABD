"""Retrospectively measure explicit-intent overrides on an existing run."""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from router import _explicit_intent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.run_dir / "answers.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    before, after = 0, 0
    overrides = []
    categories = defaultdict(lambda: {"n": 0, "before": 0, "after": 0})
    for row in rows:
        expected = row["expected_category"]
        original = row.get("predicted_category")
        cue = _explicit_intent(row["query"])
        proposed = cue or original
        before += original == expected
        after += proposed == expected
        categories[expected]["n"] += 1
        categories[expected]["before"] += original == expected
        categories[expected]["after"] += proposed == expected
        if cue and cue != original:
            overrides.append({"id": row["id"], "query": row["query"], "expected": expected,
                              "previous": original, "override": cue, "correct": cue == expected})
    result = {
        "n": len(rows), "baseline_route_accuracy": round(before / max(1, len(rows)), 4),
        "simulated_override_route_accuracy": round(after / max(1, len(rows)), 4),
        "explicit_overrides": len(overrides),
        "correct_overrides": sum(x["correct"] for x in overrides),
        "by_category": {k: {**v, "baseline_accuracy": round(v["before"] / max(1, v["n"]), 4),
                            "simulated_accuracy": round(v["after"] / max(1, v["n"]), 4)}
                        for k, v in categories.items()},
        "overrides": overrides,
        "warning": "Retrospective policy simulation on an exploratory bank, not an independent held-out router evaluation.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "overrides"}, ensure_ascii=False, indent=2))
    print(f"[SAVED] {args.output}")


if __name__ == "__main__":
    main()
