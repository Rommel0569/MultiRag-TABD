"""Inspect locally extractable PDF text without sending document data anywhere.

Uses Poppler's pdftotext executable already needed alongside pdf2image. The
quality labels are triage heuristics, not an accuracy guarantee.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from pdf_text import assess_text_layer, extract_native_pdf_pages


def resolve_pdftotext(explicit=None):
    candidate = explicit or os.environ.get("CEPRUNSA_PDFTOTEXT_BIN")
    if candidate:
        path = Path(candidate)
        if path.is_dir():
            path = path / ("pdftotext.exe" if os.name == "nt" else "pdftotext")
        if path.is_file():
            return str(path)
    poppler = os.environ.get("CEPRUNSA_POPPLER_PATH")
    if poppler:
        path = Path(poppler) / ("pdftotext.exe" if os.name == "nt" else "pdftotext")
        if path.is_file():
            return str(path)
    located = shutil.which("pdftotext")
    if located:
        return located
    fallback = Path(r"C:\Users\USER\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin")
    path = fallback / "pdftotext.exe"
    return str(path) if os.name == "nt" and path.is_file() else None


def page_metrics(text):
    return assess_text_layer(text)


def inspect_pdf(path, executable):
    page_texts, used = extract_native_pdf_pages(path, poppler_path=str(Path(executable).parent))
    if page_texts is None:
        raise RuntimeError(f"Local text extraction failed for {path}")
    pages = [{"page": i, **page_metrics(text)} for i, text in enumerate(page_texts, 1)]
    return {
        "file": path.name,
        "pages": len(pages),
        "summary": {status: sum(p["status"] == status for p in pages)
                    for status in sorted({p["status"] for p in pages})},
        "page_results": pages,
        "text_extractor": used,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=Path, default=Path("data/pdfs"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pdftotext", help="Path to pdftotext executable or Poppler bin directory")
    args = parser.parse_args()
    executable = resolve_pdftotext(args.pdftotext)
    if not executable:
        raise SystemExit("pdftotext was not found; set CEPRUNSA_PDFTOTEXT_BIN or install Poppler locally.")
    pdfs = sorted(args.pdf_dir.glob("*.pdf"))
    report = {
        "method": "Local Poppler pdftotext text-layer probe; no page images or PDF content sent externally.",
        "heuristic_note": "Labels triage text-layer availability/quality only; they do not prove semantic correctness.",
        "engine": executable,
        "documents": [inspect_pdf(path, executable) for path in pdfs],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for doc in report["documents"]:
        print(f"{doc['file']}: {doc['pages']} pages — {doc['summary']}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
