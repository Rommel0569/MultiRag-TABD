"""Compare paired question-bank runs using diagnostic, non-semantic checks."""
import argparse
import csv
import json
import re
import statistics
import unicodedata
from collections import Counter
from pathlib import Path


def numbers(text):
    return Counter(str(int(token)) for token in re.findall(r"\d+", str(text or "")))


def norm(text):
    text = unicodedata.normalize("NFKD", str(text or "").casefold())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def load(path):
    rows = [json.loads(line) for line in (path / "answers.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["id"]: row for row in rows}


def load_manifest(path):
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Missing run manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def score(row, expected_answer=None, source_pages=None):
    expected = numbers(expected_answer if expected_answer is not None else row.get("expected_answer"))
    answer = numbers(row.get("answer"))
    numeric_coverage = sum((expected & answer).values()) / sum(expected.values()) if expected else None
    expected_norm = norm(expected_answer if expected_answer is not None else row.get("expected_answer"))
    answer_norm = norm(row.get("answer"))
    exact_answer_phrase = bool(expected_norm and expected_norm in answer_norm)
    pages = source_pages or ([row.get("source_page")] if row.get("source_page") else [])
    source_hit = any(c.get("source") == row.get("source_pdf") and c.get("page") in pages
                     for c in row.get("contexts", []))
    return numeric_coverage, exact_answer_phrase, source_hit


def main():
    p = argparse.ArgumentParser()
    p.add_argument("baseline", type=Path)
    p.add_argument("experimental", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--queries", type=Path, help="Source-reviewed reference copy; query text must match the run.")
    a = p.parse_args()
    base, exp = load(a.baseline), load(a.experimental)
    base_manifest, exp_manifest = load_manifest(a.baseline), load_manifest(a.experimental)
    paired_condition_keys = (
        "pair_id", "generator", "model", "temperature", "query_file_sha256",
        "index_files_sha256", "cache_mode", "query_count_requested",
    )
    condition_mismatches = {
        key: {"baseline": base_manifest.get(key), "experimental": exp_manifest.get(key)}
        for key in paired_condition_keys
        if base_manifest.get(key) != exp_manifest.get(key)
    }
    if condition_mismatches:
        p.error(f"Runs do not share paired conditions: {json.dumps(condition_mismatches, ensure_ascii=False)}")
    ids = sorted(set(base) & set(exp))
    references = {}
    if a.queries:
        bank = json.loads(a.queries.read_text(encoding="utf-8"))
        references = {row["id"]: row for row in bank["consultas"]}
        if any(references.get(item_id, {}).get("query") != exp[item_id].get("query") for item_id in ids):
            p.error("Reviewed bank query texts differ from the paired runs.")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    detail = []
    for item_id in ids:
        b, e = base[item_id], exp[item_id]
        ref = references.get(item_id, {})
        expected = ref.get("ground_truth")
        source_pages = ref.get("source_pages")
        bs, es = score(b, expected, source_pages), score(e, expected, source_pages)
        detail.append({
            "id": item_id, "query": e.get("query"), "category": e.get("expected_category"),
            "expected_answer_candidate": expected if expected is not None else e.get("expected_answer"),
            "source_pdf": ref.get("source_pdf", e.get("source_pdf")),
            "source_pages": ",".join(map(str, source_pages or ([ref.get("source_page", e.get("source_page"))] if ref.get("source_page", e.get("source_page")) else []))),
            "source_reference_validation_status": ref.get("validation_status", "unvalidated_candidate"),
            "baseline_answer": b.get("answer"), "experimental_answer": e.get("answer"),
            "baseline_phase": b.get("phase"), "experimental_phase": e.get("phase"),
            "baseline_elapsed_seconds": b.get("elapsed_seconds"),
            "experimental_elapsed_seconds": e.get("elapsed_seconds"),
            "baseline_route": b.get("predicted_category"), "experimental_route": e.get("predicted_category"),
            "baseline_source_page_hit": bs[2], "experimental_source_page_hit": es[2],
            "baseline_expected_number_coverage": bs[0], "experimental_expected_number_coverage": es[0],
            "baseline_exact_reference_phrase": bs[1], "experimental_exact_reference_phrase": es[1],
            "baseline_error": b.get("error"), "experimental_error": e.get("error"),
        })
    with a.output.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0]) if detail else ["id"])
        w.writeheader()
        w.writerows(detail)
    summary = {
        "paired_n": len(detail),
        "baseline_source_page_hit": sum(x["baseline_source_page_hit"] for x in detail),
        "experimental_source_page_hit": sum(x["experimental_source_page_hit"] for x in detail),
        "baseline_number_coverage_mean": round(sum(x["baseline_expected_number_coverage"] or 0 for x in detail) / max(1, sum(x["baseline_expected_number_coverage"] is not None for x in detail)), 4),
        "experimental_number_coverage_mean": round(sum(x["experimental_expected_number_coverage"] or 0 for x in detail) / max(1, sum(x["experimental_expected_number_coverage"] is not None for x in detail)), 4),
        "baseline_exact_reference_phrase": sum(x["baseline_exact_reference_phrase"] for x in detail),
        "experimental_exact_reference_phrase": sum(x["experimental_exact_reference_phrase"] for x in detail),
        "baseline_runtime_errors": sum(bool(base[item_id].get("error")) for item_id in ids),
        "experimental_runtime_errors": sum(bool(exp[item_id].get("error")) for item_id in ids),
        "baseline_elapsed_seconds_total": round(sum(float(base[item_id].get("elapsed_seconds") or 0) for item_id in ids), 2),
        "experimental_elapsed_seconds_total": round(sum(float(exp[item_id].get("elapsed_seconds") or 0) for item_id in ids), 2),
        "baseline_elapsed_seconds_mean": round(statistics.mean(float(base[item_id].get("elapsed_seconds") or 0) for item_id in ids), 3) if ids else None,
        "experimental_elapsed_seconds_mean": round(statistics.mean(float(exp[item_id].get("elapsed_seconds") or 0) for item_id in ids), 3) if ids else None,
        "baseline_phase_counts": dict(Counter(base[item_id].get("phase") for item_id in ids)),
        "experimental_phase_counts": dict(Counter(exp[item_id].get("phase") for item_id in ids)),
            "warning": "Lexical/source-page diagnostics do not establish semantic correctness. Only references explicitly marked source-reviewed were manually corrected; remaining candidate references are unvalidated.",
            "query_texts_match": all(base[item_id].get("query") == exp[item_id].get("query") for item_id in ids),
        "paired_conditions_match": not condition_mismatches,
        "paired_condition_keys_checked": list(paired_condition_keys),
        "baseline_run_manifest": str((a.baseline / "manifest.json").resolve()),
        "experimental_run_manifest": str((a.experimental / "manifest.json").resolve()),
        "pipeline_source_hash_differences": {
            name: {"baseline": base_manifest.get("pipeline_source_sha256", {}).get(name),
                   "experimental": exp_manifest.get("pipeline_source_sha256", {}).get(name)}
            for name in sorted(set(base_manifest.get("pipeline_source_sha256", {}))
                               | set(exp_manifest.get("pipeline_source_sha256", {})))
            if base_manifest.get("pipeline_source_sha256", {}).get(name)
            != exp_manifest.get("pipeline_source_sha256", {}).get(name)
        },
            "source_reviewed_reference_file": str(a.queries.resolve()) if a.queries else None,
    }
    summary_path = a.output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[SAVED] {a.output}")
    print(f"[SAVED] {summary_path}")


if __name__ == "__main__":
    main()
