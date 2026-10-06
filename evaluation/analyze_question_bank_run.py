"""Summarize routing, source-hit and literal fact checks for one JSONL run.

These are diagnostics, not semantic accuracy or independent judging metrics.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text or "").casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text)


def fact_tokens(text):
    return set(re.findall(r"\b\d{1,4}(?:[.,]\d+)?(?:/\d{1,4}(?:/\d{2,4})?)?\b", str(text or "")))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.run_dir / "answers.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    per_category = defaultdict(list)
    for row in rows:
        per_category[row["expected_category"]].append(row)

    categories = {}
    for category, items in per_category.items():
        completed = [x for x in items if not x.get("error")]
        source_grounded = [x for x in completed if x.get("source_pdf") and any(
            c.get("source") == x["source_pdf"] and c.get("page") == x.get("source_page")
            for c in x.get("contexts", []))]
        answer_fact_hits = []
        for item in completed:
            expected_facts = fact_tokens(item.get("expected_answer"))
            answer_facts = fact_tokens(item.get("answer"))
            if expected_facts:
                answer_fact_hits.append(len(expected_facts & answer_facts) / len(expected_facts))
        categories[category] = {
            "n": len(items),
            "completed": len(completed),
            "route_correct": sum(x.get("route_correct", False) for x in completed),
            "route_accuracy": round(sum(x.get("route_correct", False) for x in completed) / max(1, len(completed)), 4),
            "source_page_in_top_contexts": len(source_grounded),
            "source_page_hit_rate": round(len(source_grounded) / max(1, len(completed)), 4) if any(x.get("source_pdf") for x in completed) else None,
            "mean_expected_numeric_date_token_coverage": round(sum(answer_fact_hits) / max(1, len(answer_fact_hits)), 4) if answer_fact_hits else None,
        }
    errors = sum(bool(x.get("error")) for x in rows)
    result = {
        "n": len(rows),
        "errors": errors,
        "overall_route_accuracy": round(sum(x.get("route_correct", False) for x in rows if not x.get("error")) / max(1, len(rows) - errors), 4),
        "by_category": categories,
        "metric_warning": "Literal number/date coverage and retrieved source-page hit are diagnostic checks only. They do not establish semantic correctness, OCR correctness, or human-validated accuracy.",
    }
    output = args.run_dir / "analysis_diagnostics.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[SAVED] {output}")


if __name__ == "__main__":
    main()
