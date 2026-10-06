"""Audit deterministic source-backed lookup coverage against candidate questions.

This only evaluates coverage and agreement with the OCR-derived candidate
reference. It never promotes candidate answers to human-verified gold labels.
"""
import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from structured_answers import resolve_structured_answer


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=Path, default=ROOT / "evaluation" / "queries_500_candidates.json")
    parser.add_argument("--index-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    query_doc = json.loads(args.queries.read_text(encoding="utf-8"))
    documents = {}
    for path in args.index_dir.glob("*.json"):
        category = path.stem
        documents[category] = json.loads(path.read_text(encoding="utf-8"))

    results = []
    for item in query_doc["consultas"]:
        category = item["categoria_correcta"]
        resolved = resolve_structured_answer(item["query"], category, documents)
        answer = resolved["answer"] if resolved else ""
        ref_dates = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", item.get("ground_truth", ""))
        refs = set(ref_dates)
        got_dates = set(re.findall(r"\d{1,2}/\d{1,2}/\d{4}", answer))
        qnorm = norm(item["query"])
        if refs and resolved:
            if "hasta" in qnorm:
                fact_ok = ref_dates[-1] in got_dates
            elif "desde" in qnorm:
                fact_ok = ref_dates[0] in got_dates
            else:
                fact_ok = refs.issubset(got_dates)
        elif category == "VACANTES" and resolved:
            expected_numbers = re.findall(r"(?<!\w)\d+(?!\w)", item.get("ground_truth", ""))
            answer_numbers = re.findall(r"(?<!\w)\d+(?!\w)", answer)
            fact_ok = bool(expected_numbers and expected_numbers[-1] in answer_numbers)
        elif category == "TEMARIO" and resolved:
            quote = item.get("evidence_quote", "")
            fact_ok = bool(quote and norm(quote) in norm(answer))
        elif category == "REGLAMENTO" and resolved:
            article = re.search(r"art[ií]culo\s+0*(\d+)", item["query"], re.I)
            fact_ok = bool(article and re.search(rf"\bart[ií]culo\s+0*{article.group(1)}\b", answer, re.I))
        elif category == "FUERA_DE_DOMINIO":
            fact_ok = not bool(resolved)
        else:
            fact_ok = False
        source_match = bool(resolved and any(
            chunk.get("source") == item.get("source_pdf") and chunk.get("page") == item.get("source_page")
            for chunk in resolved.get("contexts", [])
        ))
        if category == "FUERA_DE_DOMINIO":
            status = "not_applicable_ood"
        elif not resolved:
            status = "no_structured_match_fallback_to_rag"
        elif not source_match:
            status = "resolved_but_source_page_differs"
        elif not fact_ok:
            status = "source_match_candidate_fact_mismatch"
        else:
            status = "source_match_candidate_fact_agrees_ocr_only"
        results.append({
            "id": item["id"], "category": category, "query": item["query"],
            "candidate_source_pdf": item.get("source_pdf"), "candidate_source_page": item.get("source_page"),
            "candidate_ground_truth_unvalidated": item.get("ground_truth"),
            "lookup_type": resolved.get("structured_lookup") if resolved else "",
            "lookup_hit": bool(resolved), "resolved_sources": "; ".join(resolved.get("sources", [])) if resolved else "",
            "candidate_page_in_lookup_context": source_match, "candidate_primary_fact_present": fact_ok,
            "audit_status": status, "answer_from_source_index": answer,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    counts = {}
    for row in results:
        counts[row["audit_status"]] = counts.get(row["audit_status"], 0) + 1
    print(json.dumps({"total": len(results), "counts": counts,
                      "warning": "Agreement is with OCR-derived candidate references, not a manual gold-standard review."},
                     ensure_ascii=False, indent=2))
    print(f"[SAVED] {args.output}")


if __name__ == "__main__":
    main()
