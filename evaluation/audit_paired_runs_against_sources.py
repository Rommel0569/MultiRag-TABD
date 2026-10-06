"""Audit paired answer runs against the Textract page index and PDF page review.

This script checks every bank row. It does not present OCR-derived references or
lexical checks as a semantic gold standard; mismatches are flagged for manual
adjudication against the rendered source page.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def norm(value: object) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9/.,%°º-]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokens(value: object) -> set[str]:
    return set(re.findall(r"[a-z0-9]+(?:[.,/%°º-][a-z0-9]+)*", norm(value)))


def numbers(value: object) -> set[str]:
    return set(re.findall(r"\b\d{1,4}(?:[.,]\d+)?(?:/\d{1,4}(?:/\d{2,4})?)?\b", str(value or "")))


def number_atoms(value: object) -> Counter[str]:
    atoms = Counter()
    for token in re.findall(r"\d+(?:[.,]\d+)?", str(value or "")):
        if "," in token or "." in token:
            try:
                key = str(float(token.replace(",", "."))).rstrip("0").rstrip(".")
            except ValueError:
                key = token
        else:
            key = str(int(token))
        atoms[key] += 1
    return atoms


def dates(value: object) -> list[str]:
    return re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", str(value or ""))


def quoted_topic(query: str) -> str:
    for pattern in (r"«([^»]+)»", r"“([^”]+)”", r'"([^\"]+)"', r"'([^']+)'", r"‘([^’]+)’"):
        match = re.search(pattern, query)
        if match:
            return match.group(1)
    return ""


STOP = {"el", "la", "de", "del", "los", "las", "y", "un", "una", "que", "en", "para", "por", "con", "segun", "sobre", "cual", "como", "articulo", "dice", "indica", "establece", "trata", "temas", "tema", "contenido", "postulante", "puede", "son", "ser", "debe", "deben", "sus", "esta", "este", "fue", "al", "se", "es", "a", "o", "no", "del", "and", "or"}


def page_texts(index_dir: Path) -> dict[tuple[str, int], str]:
    collected: dict[tuple[str, int], list[str]] = defaultdict(list)
    for path in index_dir.glob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(document, list):
            continue
        for item in document:
            if isinstance(item, dict) and item.get("source"):
                key = (norm(item.get("source")), int(item.get("page") or 0))
                collected[key].append(str(item.get("text", "")))
    return {key: "\n".join(value) for key, value in collected.items()}


def index_rows(path: Path) -> dict[int, dict]:
    output = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            output[int(row["id"])] = row
    return output


def extract_topic_anchor(query: str) -> set[str]:
    phrase = quoted_topic(query)
    if not phrase:
        return set()
    return {t for t in tokens(phrase).union() if t not in STOP and len(t) > 2}


def expected_facts(item: dict) -> set[str]:
    category = item.get("expected_category")
    expected = str(item.get("expected_answer", ""))
    if category == "CRONOGRAMA":
        ds = dates(expected)
        q = norm(item.get("query", ""))
        if ds and re.search(r"\b(hasta|fecha limite|ultimo dia|finaliza)\b", q):
            return {ds[-1]}
        if ds and re.search(r"\b(desde|empiez|inicia|comienza)\b", q) and "inscrip" in q:
            return {ds[0]}
        return set(ds)
    if category == "VACANTES":
        values = numbers(expected)
        return values if values else set()
    return set()


def key_terms(item: dict) -> set[str]:
    category = item.get("expected_category")
    query = str(item.get("query", ""))
    quote = str(item.get("evidence_quote", ""))
    if category == "TEMARIO":
        return extract_topic_anchor(query)
    if category == "REGLAMENTO":
        # Source-backed terms from the cited provision, excluding generic legal wording.
        terms = {t for t in tokens(quote) if t not in STOP and len(t) > 3 and not t.isdigit()}
        return terms
    return set()


def is_visual_page_listed(doc: str, page: int) -> bool:
    # All source pages cited by this candidate bank have been opened as rendered
    # originals during this review. This is a page-level flag, not per-answer human grading.
    reviewed = {
        "CRONOGRAMA DE ADMISION 2027.PDF": set(range(2, 4)),
        "CUADRO DE VACANTES 2027.PDF": {3},
        "TEMARIO Y MATRIZ DE EVALUACION 2027.PDF": set(range(3, 18)) | set(range(19, 30)),
        "REGLAMENTO DE ADMISION 2027.PDF": set(range(4, 8)) | set(range(9, 26)),
    }
    return int(page or 0) in reviewed.get(norm(doc).upper(), set())


def structured_table_cell_verified(row: dict, context_text: str, primary_facts: set[str]) -> bool | None:
    """Verify structured date/vacancy answers against their serialized source row."""
    phase = str(row.get("phase") or "")
    context_norm = norm(context_text)
    if phase == "structured_table_date_cell":
        match = re.match(r"^\s*(.+?):\s*(.+?)\s+[—-]\s*(.+?)\s*\.?\s*$", str(row.get("answer") or ""))
        if not match:
            return False
        exam, item, _value = match.groups()
        expected = primary_facts
        actual_dates = set(dates(context_text))
        required_dates = set()
        if expected:
            required_dates = set(expected)
        return (norm(exam) in context_norm and norm(item) in context_norm
                and bool(required_dates) and required_dates.issubset(actual_dates)
                and required_dates.issubset(set(dates(row.get("answer") or ""))))
    if phase == "structured_table_cell":
        answer = str(row.get("answer") or "")
        match = re.match(r"^\s*(.+?):\s*([\d.,]+)\s+vacantes\s+\((.+?)\)\s*\.?\s*$", answer, flags=re.IGNORECASE)
        if not match:
            return False
        program, value, column = match.groups()
        answer_facts = numbers(answer)
        context_facts = numbers(context_text)
        return (norm(program) in context_norm and norm(column) in context_norm
                and bool(primary_facts) and primary_facts.issubset(answer_facts)
                and primary_facts.issubset(context_facts)
                and numbers(value).issubset(context_facts))
    return None


def audit_one(row: dict, source_pages: dict, visual_flag: bool) -> dict:
    source = row.get("source_pdf") or ""
    page = int(row.get("source_page") or 0)
    category = row.get("expected_category")
    query = str(row.get("query") or "")
    answer = str(row.get("answer") or "")
    expected = str(row.get("expected_answer") or "")
    quote = str(row.get("evidence_quote") or "")
    expected_page_text = source_pages.get((norm(source), page), "") if source and page else ""
    page_norm = norm(expected_page_text)
    quote_norm = norm(quote)
    quote_found = bool(quote_norm and quote_norm in page_norm)
    quote_num = numbers(quote)
    quote_nums_found = quote_num.issubset(numbers(expected_page_text)) if quote_num else None
    primary = expected_facts(row)
    answer_date_and_numbers = numbers(answer) | set(dates(answer))
    primary_coverage = (len(primary & answer_date_and_numbers) / len(primary)) if primary else None
    expected_numeric = number_atoms(expected)
    answer_numeric_atoms = number_atoms(answer)
    expected_numeric_coverage = (
        sum((expected_numeric & answer_numeric_atoms).values()) / sum(expected_numeric.values())
        if sum(expected_numeric.values()) >= 20 else None
    )
    terms = key_terms(row)
    answer_terms = tokens(answer)
    term_coverage = (len(terms & answer_terms) / len(terms)) if terms else None
    contexts = row.get("contexts") or []
    expected_page_retrieved = bool(source and any(
        norm(c.get("source")) == norm(source) and int(c.get("page") or 0) == page for c in contexts
    ))
    context_text = "\n".join(str(c.get("text", "")) for c in contexts)
    unsupported_numbers = numbers(answer) - numbers(context_text)
    structured_table_verified = structured_table_cell_verified(row, context_text, primary)
    ood = category == "FUERA_DE_DOMINIO"
    abstained = bool(re.search(r"fuera del alcance|no encontre informacion relevante|no encontr[eé] informaci[oó]n relevante", norm(answer)))
    reference_reviewed = str(row.get("validation_status") or "").startswith("partially_source_reviewed")
    expected_pages = [int(p) for p in (row.get("source_pages") or ([page] if page else []))]
    retrieved_pages = {
        int(c.get("page") or 0) for c in contexts
        if norm(c.get("source")) == norm(source)
    }
    all_expected_pages_retrieved = bool(expected_pages) and set(expected_pages).issubset(retrieved_pages)
    checks = []
    if row.get("error"):
        checks.append("runtime_error")
    if not ood:
        if not expected_page_text:
            checks.append("source_page_missing_from_index")
        if not quote_found and not structured_table_verified and not reference_reviewed:
            checks.append("evidence_quote_not_found_on_index_page")
        if quote_nums_found is False and not structured_table_verified and not reference_reviewed:
            checks.append("quote_numbers_mismatch_index_page")
        if primary_coverage is not None and primary_coverage < 1:
            checks.append("requested_number_or_date_missing_from_answer")
        if term_coverage is not None and term_coverage < 0.5:
            checks.append("topic_or_provision_anchor_coverage_low")
        if not expected_page_retrieved:
            checks.append("expected_source_page_not_retrieved")
        if unsupported_numbers:
            checks.append("answer_contains_numbers_absent_from_retrieved_context")
        if expected_numeric_coverage is not None and expected_numeric_coverage < 1:
            checks.append("table_numeric_completeness_below_reference")
    else:
        if contexts or not abstained:
            checks.append("ood_not_abstained_cleanly")
    # A clean automated check is not the same as an independently human-
    # verified answer. Keep these outcomes separate in the CSV and summary.
    if checks:
        status = "needs_manual_adjudication"
    elif ood:
        status = "ood_abstention_check_passed"
    elif reference_reviewed:
        status = "source_reviewed_reference_checks_passed"
    else:
        status = "automated_checks_passed_unreviewed_reference"
    return {
        "id": row.get("id"), "category": category, "query": query,
        "source_pdf": source, "source_page": page, "source_page_visually_reviewed": visual_flag,
        "expected_answer_candidate": expected, "evidence_quote_candidate": quote,
        "model_answer": answer, "phase": row.get("phase"), "runtime_error": row.get("error"),
        "evidence_quote_found_in_index_page": quote_found,
        "evidence_quote_numeric_tokens_in_page": quote_nums_found,
        "structured_table_source_cell_verified": structured_table_verified,
        "source_reference_manually_reviewed": reference_reviewed,
        "source_quote_not_found_in_ocr_index": bool(source and quote and not quote_found),
        "required_dates_or_numbers": ",".join(sorted(primary)),
        "answer_required_fact_coverage": primary_coverage,
        "candidate_table_numeric_completeness": expected_numeric_coverage,
        "provision_or_topic_key_term_coverage": term_coverage,
        "expected_source_page_retrieved": expected_page_retrieved,
        "source_pages_expected": ",".join(map(str, expected_pages)),
        "source_pages_retrieved_for_document": ",".join(map(str, sorted(retrieved_pages))),
        "all_expected_source_pages_retrieved": all_expected_pages_retrieved if expected_pages else None,
        "answer_numeric_tokens_unsupported_by_retrieved_context": ",".join(sorted(unsupported_numbers)),
        "ood_abstained": abstained if ood else None,
        "audit_status": status, "audit_flags": ";".join(checks),
        "source_reference_validation_status": row.get("validation_status", "unvalidated_candidate"),
        "source_reference_individually_reviewed": reference_reviewed,
        "individual_semantic_human_grade": "not_assigned",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--three-phase", type=Path, required=True)
    p.add_argument("--queries", type=Path, required=True)
    p.add_argument("--index-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    bank = json.loads(a.queries.read_text(encoding="utf-8"))
    bank_rows = {int(x["id"]): x for x in bank["consultas"]}
    page_map = page_texts(a.index_dir)
    outputs = {}
    summaries = {}
    audited_by_label = {}
    for label, path in (("baseline", a.baseline), ("three_phase", a.three_phase)):
        answers = index_rows(path)
        audited = []
        for item_id, item in sorted(bank_rows.items()):
            row = answers.get(item_id)
            if row is None:
                row = {"id": item_id, "query": item.get("query"), "expected_category": item.get("categoria_correcta"),
                       "expected_answer": item.get("ground_truth"), "source_pdf": item.get("source_pdf"),
                       "source_page": item.get("source_page"), "source_pages": item.get("source_pages"),
                       "evidence_quote": item.get("evidence_quote"),
                       "validation_status": item.get("validation_status", "unvalidated_candidate"),
                       "answer": "", "contexts": [], "error": "missing_answer_row", "phase": "missing"}
            else:
                # The reviewed scoring copy is authoritative for evaluation;
                # references were never included in the generation prompt.
                row = {**row,
                       "expected_category": item.get("categoria_correcta"),
                       "expected_answer": item.get("ground_truth"),
                       "source_pdf": item.get("source_pdf"),
                       "source_page": item.get("source_page"),
                       "source_pages": item.get("source_pages"),
                       "evidence_quote": item.get("evidence_quote"),
                       "validation_status": item.get("validation_status", "unvalidated_candidate")}
            flag = is_visual_page_listed(item.get("source_pdf") or "", item.get("source_page") or 0)
            audited.append(audit_one(row, page_map, flag))
        audited_by_label[label] = audited
        a.output_dir.mkdir(parents=True, exist_ok=True)
        out = a.output_dir / f"{label}_500_source_audit.csv"
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(audited[0]) if audited else ["id"])
            w.writeheader(); w.writerows(audited)
        counts = Counter(x["audit_status"] for x in audited)
        category_counts = {}
        for cat in sorted({x["category"] for x in audited}):
            subset = [x for x in audited if x["category"] == cat]
            category_counts[cat] = {
                "n": len(subset),
                "automated_checks_passed_unreviewed_reference": sum(x["audit_status"] == "automated_checks_passed_unreviewed_reference" for x in subset),
                "source_reviewed_reference_checks_passed": sum(x["audit_status"] == "source_reviewed_reference_checks_passed" for x in subset),
                "ood_abstention_check_passed": sum(x["audit_status"] == "ood_abstention_check_passed" for x in subset),
                "manual_review": sum(x["audit_status"] == "needs_manual_adjudication" for x in subset),
                "expected_page_retrieved": sum(bool(x["expected_source_page_retrieved"]) for x in subset),
                "all_expected_pages_retrieved": sum(bool(x["all_expected_source_pages_retrieved"]) for x in subset if x["all_expected_source_pages_retrieved"] is not None),
                "unsupported_number_answers": sum(bool(x["answer_numeric_tokens_unsupported_by_retrieved_context"]) for x in subset),
            }
        num_rows = [x for x in audited if x["answer_required_fact_coverage"] is not None]
        summaries[label] = {
            "n_expected": len(bank_rows), "n_answer_rows": len(answers), "audit_counts": dict(counts),
            "reference_validation_status_counts": dict(Counter(x["source_reference_validation_status"] for x in audited)),
            "category_counts": category_counts,
            "mean_required_numeric_date_fact_coverage": round(sum(x["answer_required_fact_coverage"] for x in num_rows)/max(1,len(num_rows)),4),
            "mean_table_numeric_completeness": round(sum(x["candidate_table_numeric_completeness"] for x in audited if x["candidate_table_numeric_completeness"] is not None)/max(1,sum(x["candidate_table_numeric_completeness"] is not None for x in audited)),4) if any(x["candidate_table_numeric_completeness"] is not None for x in audited) else None,
            "all_cited_pages_visually_reviewed": all(x["source_page_visually_reviewed"] for x in audited if x["source_pdf"]),
            "warning": "Automated source/page/fact checks do not assign an individual human semantic grade. Only rows explicitly marked partially_source_reviewed_visual_manual have their reference visually corrected; the rest remain OCR candidates or OOD labels pending review.",
            "output_csv": str(out),
        }
    paired = {}
    for metric in ("expected_source_page_retrieved", "evidence_quote_found_in_index_page", "answer_required_fact_coverage"):
        paired[metric] = {}
        for label, audited in audited_by_label.items():
            eligible = [r[metric] for r in audited if r[metric] is not None]
            paired[metric][label] = {
                "n": len(eligible),
                "count_true": sum(bool(v) for v in eligible) if metric != "answer_required_fact_coverage" else None,
                "mean": round(sum(eligible) / len(eligible), 4) if metric == "answer_required_fact_coverage" and eligible else None,
            }
    summary = {"baseline": summaries["baseline"], "three_phase": summaries["three_phase"], "paired_diagnostics": paired}
    (a.output_dir / "paired_500_source_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
