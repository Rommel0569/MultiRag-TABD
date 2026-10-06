"""Validate and concatenate completed page-level Textract audit runs."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluation" / "revision_20260929"
OUTPUT_DIR = BASE / "textract_full"
RUNS = [
    ("CUADRO DE VACANTES 2027.pdf", BASE / "textract_v3"),
    ("CRONOGRAMA DE ADMISIÓN 2027.pdf", OUTPUT_DIR / "cronograma_v2"),
    ("REGLAMENTO DE ADMISIÓN 2027.pdf", OUTPUT_DIR / "reglamento"),
    ("TEMARIO Y MATRIZ DE EVALUACIÓN 2027.pdf", OUTPUT_DIR / "temario"),
]


def main():
    all_pages = []
    documents = []
    missing = []
    for source, run_dir in RUNS:
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            raise SystemExit(f"Missing run manifest: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        page_numbers = sorted(page["page"] for page in manifest["pages"])
        if page_numbers != list(range(1, len(page_numbers) + 1)):
            raise SystemExit(f"Non-contiguous page list in {run_dir}: {page_numbers}")
        doc_summary = {"source": source, "run": str(run_dir.relative_to(ROOT)),
                       "pages": len(page_numbers), "tables": 0, "cells": 0,
                       "text_characters": 0, "empty_text_pages": [],
                       "elapsed_s": 0.0}
        for page_no in page_numbers:
            stem = f"page_{page_no:03}"
            json_path, txt_path, png_path = (run_dir / f"{stem}.json",
                                              run_dir / f"{stem}.txt",
                                              run_dir / f"{stem}.png")
            for required in (json_path, txt_path, png_path):
                if not required.is_file() or (required != txt_path and required.stat().st_size == 0):
                    missing.append(str(required.relative_to(ROOT)))
                    continue
            if (not json_path.is_file() or json_path.stat().st_size == 0
                    or not txt_path.is_file() or not png_path.is_file() or png_path.stat().st_size == 0):
                continue
            result = json.loads(json_path.read_text(encoding="utf-8"))
            text = txt_path.read_text(encoding="utf-8")
            tables = result.get("tables", [])
            cells = sum(len(table.get("cells", [])) for table in tables)
            elapsed = float(result.get("elapsed_s", 0.0))
            doc_summary["tables"] += len(tables)
            doc_summary["cells"] += cells
            doc_summary["text_characters"] += len(text)
            doc_summary["elapsed_s"] += elapsed
            if not text.strip():
                doc_summary["empty_text_pages"].append(page_no)
            all_pages.append((source, page_no, text))
        documents.append(doc_summary)
    if missing:
        raise SystemExit("Incomplete artifacts: " + ", ".join(missing))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    combined = []
    for source, page_no, text in all_pages:
        combined.append(f"\n\n===== {source} | PÁGINA {page_no} =====\n{text.rstrip()}\n")
    (OUTPUT_DIR / "OCR_ALL_DOCUMENTS.txt").write_text("".join(combined), encoding="utf-8")
    report = {
        "method": "AWS Textract AnalyzeDocument(TABLES), per-page JSON/TXT and rendered PNG retained.",
        "external_transmission": "All source pages represented here were sent to AWS Textract.",
        "total_pages": sum(doc["pages"] for doc in documents),
        "total_tables": sum(doc["tables"] for doc in documents),
        "total_cell_blocks": sum(doc["cells"] for doc in documents),
        "total_text_characters": sum(doc["text_characters"] for doc in documents),
        "empty_text_pages": sum(len(doc["empty_text_pages"]) for doc in documents),
        "documents": documents,
        "accuracy_note": "Completeness checks confirm one saved OCR artifact per page; they do not establish transcription accuracy.",
    }
    (OUTPUT_DIR / "FULL_RUN_SUMMARY.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for doc in documents:
        print(f"{doc['source']}: pages={doc['pages']}, tables={doc['tables']}, cells={doc['cells']}, "
              f"chars={doc['text_characters']}, empty={len(doc['empty_text_pages'])}")
    print(f"TOTAL: pages={report['total_pages']}, tables={report['total_tables']}, "
          f"cells={report['total_cell_blocks']}, chars={report['total_text_characters']}")
    print(f"Text: {OUTPUT_DIR / 'OCR_ALL_DOCUMENTS.txt'}")
    print(f"Report: {OUTPUT_DIR / 'FULL_RUN_SUMMARY.json'}")


if __name__ == "__main__":
    main()
