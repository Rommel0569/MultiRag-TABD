"""Local PDF text-layer extraction and conservative OCR routing heuristics.

This module only runs Poppler locally. It never contacts AWS or another service.
"""
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import numpy as np


def resolve_pdftotext(poppler_path=None):
    explicit = os.environ.get("CEPRUNSA_PDFTOTEXT_BIN")
    candidates = []
    if explicit:
        p = Path(explicit)
        candidates.append(p / ("pdftotext.exe" if os.name == "nt" else "pdftotext") if p.is_dir() else p)
    if poppler_path:
        candidates.append(Path(poppler_path) / ("pdftotext.exe" if os.name == "nt" else "pdftotext"))
    located = shutil.which("pdftotext")
    if located:
        candidates.append(Path(located))
    return str(next((path for path in candidates if path.is_file()), "")) or None


def assess_text_layer(text):
    """Classify extracted page text as usable or requiring OCR.

    This is a conservative triage heuristic, not a semantic accuracy proof.
    Low native-text volume, control/replacement characters, or too few word
    tokens routes the page to OCR.
    """
    compact = "".join(ch for ch in text if not ch.isspace())
    char_count = len(compact)
    alpha = sum(ch.isalpha() for ch in compact)
    digit = sum(ch.isdigit() for ch in compact)
    alnum = alpha + digit
    words = re.findall(r"\b[\w]{2,}\b", text, flags=re.UNICODE)
    suspicious = sum(
        ch == "\ufffd" or unicodedata.category(ch) in {"Cc", "Cs", "Co"}
        for ch in compact
    )
    alnum_ratio = alnum / char_count if char_count else 0.0
    suspicious_ratio = suspicious / char_count if char_count else 0.0
    digit_ratio = digit / alnum if alnum else 0.0

    table_like_lines = sum(
        len(re.split(r"\s{2,}|\t+", line.strip())) >= 2
        for line in text.splitlines() if line.strip()
    )
    if char_count < 28:
        status, reason = "needs_ocr", "too_little_native_text"
    elif suspicious_ratio > 0.01:
        status, reason = "needs_ocr", "suspicious_characters"
    elif alnum_ratio < 0.55:
        status, reason = "needs_ocr", "low_alphanumeric_ratio"
    elif table_like_lines >= 2 and char_count >= 40:
        status, reason = "native_text", "readable_layout_or_table_rows"
    elif len(words) >= 5 and char_count >= 48:
        status, reason = "native_text", "enough_readable_word_tokens"
    elif char_count >= 80 and alnum_ratio >= 0.85 and digit_ratio >= 0.35:
        status, reason = "native_text", "dense_numeric_or_table_text"
    else:
        status, reason = "needs_ocr", "native_text_below_conservative_threshold"
    return {
        "status": status,
        "reason": reason,
        "nonspace_characters": char_count,
        "word_tokens_2plus": len(words),
        "alphanumeric_ratio": round(alnum_ratio, 4),
        "digit_ratio_of_alphanumeric": round(digit_ratio, 4),
        "suspicious_character_ratio": round(suspicious_ratio, 4),
    }


def extract_native_pdf_pages(pdf_path, poppler_path=None, page_count=None):
    """Return (page_texts, executable) using local Poppler, or (None, None)."""
    executable = resolve_pdftotext(poppler_path)
    if not executable:
        return None, None
    try:
        proc = subprocess.run(
            [executable, "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
            capture_output=True, check=True, text=True, encoding="utf-8",
            errors="replace", timeout=180,
        )
    except (OSError, subprocess.SubprocessError):
        return None, executable
    pages = proc.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if page_count is not None:
        pages = (pages + [""] * page_count)[:page_count]
    return pages, executable


def image_ink_ratio(image, threshold=230):
    """Estimate the fraction of dark pixels in a rendered page, locally."""
    gray = np.asarray(image.convert("L"))
    return float(np.count_nonzero(gray < threshold) / gray.size)
