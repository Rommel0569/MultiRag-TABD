"""Create a separate candidate bank with two source-disambiguated questions.

The original candidate file is never modified. Ground truths remain unvalidated.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = {
    233: "¿Qué temas entran sobre «VII. Coherencia y cohesión textual»?",
    239: "¿Qué temas entran sobre «V. Sistema de los números racionales (Q)»?",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "evaluation" / "queries_500_candidates.json")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "evaluation" / "queries_500_disambiguated_candidates.json")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"Refusing to overwrite {args.output}")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    original_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
    found = set()
    for row in data["consultas"]:
        if row["id"] in REVISIONS:
            row["query_original"] = row["query"]
            row["query"] = REVISIONS[row["id"]]
            row["query_revision_note"] = "Clarified the cited syllabus section; source, page, and unvalidated candidate reference preserved."
            found.add(row["id"])
    if found != set(REVISIONS):
        parser.error(f"Expected IDs {sorted(REVISIONS)}, found {sorted(found)}")
    data["source_status"] = data.get("status")
    data["status"] = "CANDIDATE_POOL_NOT_A_VALIDATED_BENCHMARK"
    data["source_queries_sha256"] = original_hash
    data["query_revisions"] = {str(key): value for key, value in REVISIONS.items()}
    data["validation_note"] = "Two ambiguous TEMARIO queries were disambiguated. No ground truth was marked human-verified."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "query_count": len(data["consultas"]),
                      "changed_ids": sorted(found), "source_sha256": original_hash,
                      "status": data["status"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
