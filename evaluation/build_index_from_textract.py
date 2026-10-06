"""Build an isolated FAISS index from saved Textract page JSON (no AWS calls).

Pages with detected tables are indexed as header-aware row passages instead of
flattened page text. Pages without tables use the project's fixed word chunker.
The baseline data/index is never read for writing or overwritten.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "evaluation" / "revision_20260929"
DOCUMENTS = {
    "CRONOGRAMA": ("CRONOGRAMA DE ADMISIÓN 2027.pdf", REV / "textract_full" / "cronograma_v2"),
    "VACANTES": ("CUADRO DE VACANTES 2027.pdf", REV / "textract_v3"),
    "TEMARIO": ("TEMARIO Y MATRIZ DE EVALUACIÓN 2027.pdf", REV / "textract_full" / "temario"),
    "REGLAMENTO": ("REGLAMENTO DE ADMISIÓN 2027.pdf", REV / "textract_full" / "reglamento"),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(value):
    return " ".join(str(value or "").split()).strip(" |")


def read_source_pages(category, filename, folder):
    pages = []
    for path in sorted(folder.glob("page_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        page = int(path.stem.split("_")[-1])
        pages.append((page, path, data))
    if not pages:
        raise RuntimeError(f"Missing Textract pages for {category}: {folder}")
    return pages


def table_headers(table):
    rows = {}
    cells_by_key = {}
    for cell in table.get("cells", []):
        row_id, col = int(cell.get("row", -1)), int(cell.get("column", -1))
        rows.setdefault(row_id, {})[col] = norm(cell.get("text"))
        cells_by_key[(row_id, col)] = cell
    header_row = None
    for row_id in sorted(rows):
        if row_id > 3:
            break
        values = [v for v in rows[row_id].values() if v]
        if len(values) < 3:
            continue
        # Numbered data rows such as 5.3.1 / CAB / definition are records,
        # not column headers. This prevents glossary/table identifiers from
        # being promoted to headers and then misaligning every later cell.
        has_numbered_record_key = any(
            re.fullmatch(r"\d+(?:\.\d+){1,}\.?", value.strip()) for value in values
        )
        if has_numbered_record_key:
            continue
        alpha = sum(any(ch.isalpha() for ch in v) and not any(ch.isdigit() for ch in v) for v in values)
        short = sum(len(v) <= 48 for v in values)
        if alpha / len(values) >= 0.65 and short / len(values) >= 0.8:
            header_row = row_id
    headers = {}
    if header_row is not None:
        for col, value in rows[header_row].items():
            if value:
                headers[col] = value

        # Recover sparse multi-level column groups (e.g. a parent heading over
        # several child columns). Textract serializes merged headings into one
        # cell without retaining a span. Estimate group boundaries from the
        # physical column grid and the centers of the sparse parent headings.
        ncols = max((max(values) for values in rows.values() if values), default=-1) + 1
        sparse_candidates = []
        for row_id in sorted(r for r in rows if r < header_row):
            nonempty = [(col, value) for col, value in rows[row_id].items() if value]
            if nonempty and len(nonempty) <= max(3, ncols // 3):
                sparse_candidates.append((row_id, nonempty))
        if sparse_candidates:
            parent_row, parent_cells = sparse_candidates[-1]
            anchors = []
            for col, label in parent_cells:
                cell = cells_by_key.get((parent_row, col), {})
                bbox = cell.get("bbox") or []
                if len(bbox) >= 4:
                    xcenter = (float(bbox[0]) + float(bbox[2])) / 2
                else:
                    xcenter = float(col)
                anchors.append((xcenter, label))
            anchors.sort()

            edges = set()
            centers = {}
            for col in range(ncols):
                cell = cells_by_key.get((header_row, col), {})
                bbox = cell.get("bbox") or []
                if len(bbox) >= 4:
                    left, right = float(bbox[0]), float(bbox[2])
                    edges.update((left, right))
                    centers[col] = (left + right) / 2
            ordered_edges = sorted(edges)
            if len(anchors) >= 2 and len(ordered_edges) >= ncols + 1:
                def nearest_edge(value):
                    return min(ordered_edges, key=lambda edge: abs(edge - value))

                group_bounds = []
                for i, (center, _) in enumerate(anchors):
                    if i == 0:
                        split = nearest_edge((center + anchors[i + 1][0]) / 2)
                        left = nearest_edge(center - (split - center))
                        right = split
                    elif i == len(anchors) - 1:
                        left = group_bounds[-1][1]
                        right = nearest_edge(center + (center - left))
                    else:
                        left = group_bounds[-1][1]
                        right = nearest_edge((center + anchors[i + 1][0]) / 2)
                    group_bounds.append((left, right))

                for (left, right), (_, group_label) in zip(group_bounds, anchors):
                    cols = [col for col, center in centers.items() if left <= center < right]
                    for col in cols:
                        if col in headers:
                            headers[col] = f"{group_label} / {headers[col]}"

                # OCR often loses the Roman numeral in repeated phase headers.
                # Restore the sequence only when a group contains repeated,
                # ambiguous "Fase" labels; leave all other headers untouched.
                grouped = {}
                for col, label in headers.items():
                    if " / " in label:
                        group, child = label.split(" / ", 1)
                        if norm(child).casefold().startswith("fase"):
                            grouped.setdefault(group, []).append((col, child))
                for group, phase_columns in grouped.items():
                    if len(phase_columns) > 1:
                        for phase_no, (col, child) in enumerate(sorted(phase_columns), start=1):
                            suffix = re.sub(r"^fase\s*", "", child.strip(), flags=re.IGNORECASE).strip()
                            if not re.fullmatch(r"(?:I{1,3}|IV|V|[1-9])", suffix, flags=re.IGNORECASE):
                                headers[col] = f"{group} / Fase {['I', 'II', 'III', 'IV'][min(phase_no - 1, 3)]}"
    return rows, header_row, headers


def page_exam_headings(page_text):
    headings = []
    for line in page_text.splitlines():
        line = norm(line)
        if line and line.upper().startswith("EXAMEN ") and len(line) <= 90:
            if line not in headings:
                headings.append(line)
    return headings


def make_table_passages(category, page, data):
    passages = []
    tables = data.get("tables", [])
    headings = page_exam_headings(data.get("page_text", "")) if category == "CRONOGRAMA" else []
    for table_idx, table in enumerate(tables):
        rows, header_row, headers = table_headers(table)
        exam = headings[table_idx] if table_idx < len(headings) else None
        ordered_rows = [(row_id, dict(cols)) for row_id, cols in sorted(rows.items())]
        merged_rows = []
        for row_id, cols in ordered_rows:
            values = [(col, value) for col, value in sorted(cols.items()) if value]
            if merged_rows and len(values) == 1 and values[0][0] > 0:
                prior_id, prior = merged_rows[-1]
                prior_key = str(prior.get(0, "")).strip()
                col, continuation = values[0]
                # A wrapped description beneath a numbered record key belongs
                # to that row when Textract has emitted it as a one-cell row.
                if (re.fullmatch(r"\d+(?:\.\d+){1,}\.?", prior_key)
                        and prior.get(col) and not re.search(r"\d", continuation)):
                    prior[col] = f"{prior[col]} {continuation}".strip()
                    continue
            merged_rows.append((row_id, cols))
        for row_id, cols in merged_rows:
            if row_id == header_row:
                continue
            values = [(col, value) for col, value in sorted(cols.items()) if value]
            if not values:
                continue
            fields = []
            for col, value in values:
                label = headers.get(col)
                if label:
                    fields.append(f"{label}: {value}")
                elif col == 0:
                    fields.append(f"Item: {value}")
                else:
                    fields.append(f"Dato {col}: {value}")
            passage = " | ".join(x for x in [category, exam, "; ".join(fields)] if x)
            if len(passage) >= 20:
                passages.append({"text": passage, "page": page, "table": table_idx + 1, "row": row_id})
    return passages


def chunk_prose(text, size=200, overlap=20):
    # Preserve legal articles as retrieval units when a page contains them.
    sections = re.split(r"(?=(?:Art[ií]culo|Art\.)\s*\d+\s*[°º]?)", text, flags=re.IGNORECASE)
    units = sections if sum(bool(re.match(r"(?:Art[ií]culo|Art\.)\s*\d+", s.strip(), re.I)) for s in sections) >= 2 else [text]
    result = []
    for unit in units:
        words = unit.split()
        start = 0
        while start < len(words):
            passage = " ".join(words[start:start + size])
            if len(passage) > 20:
                result.append(passage)
            start += size - overlap
    return result


def remove_serialized_table_rows(page_text):
    """Keep prose from mixed pages while excluding Textract's pipe-delimited table rows."""
    return "\n".join(line for line in page_text.splitlines() if "|" not in line)


def _tokens(text):
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)*", str(text or "").casefold(), flags=re.UNICODE)


def _fold_token(token):
    return "".join(ch for ch in unicodedata.normalize("NFKD", token) if not unicodedata.combining(ch))


def consensus_tokens(primary, secondary):
    """Align independent OCR tokens and retain only their in-order agreement."""
    left, right = _tokens(primary), _tokens(secondary)
    norm_left, norm_right = [_fold_token(x) for x in left], [_fold_token(x) for x in right]
    if not left or not right:
        return None
    dp = [[0] * (len(norm_right) + 1) for _ in range(len(norm_left) + 1)]
    for i in range(len(norm_left) - 1, -1, -1):
        for j in range(len(norm_right) - 1, -1, -1):
            if norm_left[i] == norm_right[j]:
                dp[i][j] = 1 + dp[i + 1][j + 1]
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])
    agreed = []
    i = j = 0
    while i < len(norm_left) and j < len(norm_right):
        if norm_left[i] == norm_right[j]:
            agreed.append(right[j])
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    ratio_left = len(agreed) / len(left)
    ratio_right = len(agreed) / len(right)
    if len(agreed) < 5 or ratio_left < 0.5 or ratio_right < 0.5:
        return None
    return " ".join(agreed)


def enhance_low_confidence_cells(data, image_path, reader, threshold):
    """Use local EasyOCR and conservative token consensus on uncertain cells."""
    import numpy as np
    from PIL import Image

    if not image_path.exists():
        return []
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    changes = []
    for table_idx, table in enumerate(data.get("tables", []), start=1):
        for cell in table.get("cells", []):
            confidence = cell.get("confidence")
            bbox = cell.get("bbox") or []
            original = cell.get("text", "")
            if confidence is None or confidence >= threshold or len(original.strip()) < 30 or len(bbox) < 4:
                continue
            x0, y0, x1, y1 = [int(round(float(v))) for v in bbox[:4]]
            x0, y0, x1, y1 = max(0, x0 - 5), max(0, y0 - 5), min(width, x1 + 5), min(height, y1 + 5)
            if x1 <= x0 or y1 <= y0:
                continue
            detections = reader.readtext(np.asarray(image.crop((x0, y0, x1, y1))), detail=1, paragraph=False)
            detections.sort(key=lambda item: ((item[0][0][1] + item[0][2][1]) / 2, item[0][0][0]))
            fallback = " ".join(item[1] for item in detections if float(item[2]) >= 0.2)
            agreed = consensus_tokens(original, fallback)
            if agreed:
                changes.append({"table": table_idx, "row": cell.get("row"), "column": cell.get("column"),
                                "confidence": confidence, "original": original, "easyocr": fallback,
                                "consensus": agreed})
                cell["text"] = agreed
    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(ROOT / "data" / "index_textract_85_v1"))
    parser.add_argument("--chunk-words", type=int, default=200)
    parser.add_argument("--overlap-words", type=int, default=20)
    parser.add_argument("--easyocr-fallback", action="store_true",
                        help="Usa EasyOCR local en celdas largas de baja confianza y conserva solo el consenso de ambos OCR")
    parser.add_argument("--easyocr-threshold", type=float, default=0.5)
    args = parser.parse_args()
    output_dir = Path(args.output_dir).resolve()
    baseline_dir = (ROOT / "data" / "index").resolve()
    if output_dir == baseline_dir or output_dir.exists():
        parser.error(f"El destino debe ser nuevo y separado de data/index: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)

    records = {category: [] for category in DOCUMENTS}
    input_hashes = {}
    page_counts = {}
    ocr_reader = None
    ocr_corrections = []
    for category, (filename, folder) in DOCUMENTS.items():
        pages = read_source_pages(category, filename, folder)
        page_counts[category] = len(pages)
        for page, source_json, data in pages:
            input_hashes[str(source_json.relative_to(ROOT))] = sha256(source_json)
            if args.easyocr_fallback:
                if ocr_reader is None:
                    import easyocr
                    ocr_reader = easyocr.Reader(["es", "en"], gpu=False)
                ocr_corrections.extend(enhance_low_confidence_cells(
                    data, source_json.with_suffix(".png"), ocr_reader, args.easyocr_threshold))
            tables = data.get("tables", [])
            if tables:
                for row in make_table_passages(category, page, data):
                    records[category].append({**row, "source": filename, "category": category,
                                              "extraction": "textract_table_row"})
                prose = remove_serialized_table_rows(data.get("page_text", ""))
            else:
                prose = data.get("page_text", "")
            # Mixed pages can contain prose (e.g. regulation articles) alongside
            # tables. Keep that prose while excluding the serialized table rows.
            for chunk_id, chunk in enumerate(chunk_prose(prose, args.chunk_words, args.overlap_words)):
                records[category].append({"text": chunk, "source": filename, "page": page,
                                          "category": category, "chunk": chunk_id,
                                          "extraction": "textract_prose_chunk"})

    sys.path.insert(0, str(ROOT / "app"))
    from embeddings import embed_passage, EMBED_DIM, EMBED_MODEL_NAME

    summaries = {}
    for category, docs in records.items():
        if not docs:
            raise RuntimeError(f"No indexable passages for {category}")
        # retriever.reciprocal_rank_fusion uses a stable per-category document id
        # to merge dense and BM25 results. Keep it local to the category index.
        for doc_id, doc in enumerate(docs):
            doc["id"] = doc_id
        vectors = np.asarray([embed_passage(doc["text"]) for doc in docs], dtype=np.float32)
        index = faiss.IndexHNSWFlat(EMBED_DIM, 32)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = 50
        index.add(vectors)
        faiss.write_index(index, str(output_dir / f"{category}.index"))
        (output_dir / f"{category}.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
        summaries[category] = {"pages": page_counts[category], "passages": len(docs),
                               "table_rows": sum(d["extraction"] == "textract_table_row" for d in docs),
                               "prose_chunks": sum(d["extraction"] == "textract_prose_chunk" for d in docs)}

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Saved Textract OCR JSON only; no AWS/API calls in this script",
        "output_dir": str(output_dir),
        "baseline_index_dir": str(baseline_dir),
        "baseline_modified": False,
        "chunk_words": args.chunk_words,
        "overlap_words": args.overlap_words,
        "easyocr_low_confidence_fallback": args.easyocr_fallback,
        "easyocr_threshold": args.easyocr_threshold if args.easyocr_fallback else None,
        "easyocr_consensus_corrections": ocr_corrections,
        "embedding_model": EMBED_MODEL_NAME,
        "faiss_index": "IndexHNSWFlat, M=32, efConstruction=200, efSearch=50",
        "source_page_json_sha256": input_hashes,
        "counts": summaries,
        "note": "Table rows retain within-row cell alignment and detected multi-level column headers. Mixed pages also retain prose after removing pipe-delimited serialized table lines, so prose adjacent to tables remains searchable without indexing flattened table sequences.",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "counts": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
