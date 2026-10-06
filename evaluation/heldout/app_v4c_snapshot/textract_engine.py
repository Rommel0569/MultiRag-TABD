"""AWS Textract TABLES adapter with the same audit schema as the EasyOCR path.

This module never calls AWS by itself. Callers must create a client and make
the paid/networked request explicitly. Textract is the default OCR backend
when a page requires OCR; local PDF text extraction still runs first.
"""
from io import BytesIO

import numpy as np
from PIL import Image


def create_textract_client(region_name=None, profile_name=None):
    """Create a client using the standard chain or a named local AWS profile."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise RuntimeError(
            "AWS Textract is optional; install requirements-aws.txt to use it."
        ) from exc
    # Carry region into the session as well as the service client. The
    # aws-login credential provider creates a sign-in client during refresh;
    # client-only region configuration can leave that refresh without a region.
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    return session.client(
        "textract",
        region_name=region_name,
        config=Config(
            retries={"total_max_attempts": 4, "mode": "standard"},
            connect_timeout=10,
            read_timeout=90,
            max_pool_connections=8,
        ),
    )


def _serialize_page_image(image, max_bytes=9_500_000):
    """Keep synchronous Textract requests under the 10 MB image limit."""
    rgb = image.convert("RGB")
    lossless = BytesIO()
    rgb.save(lossless, format="PNG", optimize=True)
    if lossless.tell() <= max_bytes:
        return lossless.getvalue()

    width, height = rgb.size
    while max(width, height) > 1200:
        width = max(500, int(width * 0.85))
        height = max(500, int(height * 0.85))
        resized = rgb.resize((width, height), Image.Resampling.LANCZOS)
        compressed = BytesIO()
        resized.save(compressed, format="JPEG", quality=92, optimize=True)
        if compressed.tell() <= max_bytes:
            return compressed.getvalue()
        rgb = resized
    raise ValueError(
        "La imagen de página excede el límite de carga síncrona de Textract "
        "incluso tras una compresión conservadora. Divide o reduce el PDF."
    )


def _bbox(block, width, height):
    box = block.get("Geometry", {}).get("BoundingBox", {})
    x0 = max(0, min(width, round(box.get("Left", 0) * width)))
    y0 = max(0, min(height, round(box.get("Top", 0) * height)))
    x1 = max(x0, min(width, round((box.get("Left", 0) + box.get("Width", 0)) * width)))
    y1 = max(y0, min(height, round((box.get("Top", 0) + box.get("Height", 0)) * height)))
    return [x0, y0, x1, y1]


def parse_blocks(blocks, width, height):
    """Convert a Textract AnalyzeDocument response into the shared JSON schema."""
    by_id = {block.get("Id"): block for block in blocks if block.get("Id")}
    tables = []

    for table_block in (b for b in blocks if b.get("BlockType") == "TABLE"):
        cell_ids = [rel_id for rel in table_block.get("Relationships", [])
                    if rel.get("Type") == "CHILD" for rel_id in rel.get("Ids", [])]
        cell_blocks = [by_id[cell_id] for cell_id in cell_ids
                       if cell_id in by_id and by_id[cell_id].get("BlockType") == "CELL"]
        if not cell_blocks:
            continue
        cells = []
        nrows = max(int(c.get("RowIndex", 1)) + int(c.get("RowSpan", 1)) - 1 for c in cell_blocks)
        ncols = max(int(c.get("ColumnIndex", 1)) + int(c.get("ColumnSpan", 1)) - 1 for c in cell_blocks)
        rows = [[""] * ncols for _ in range(nrows)]
        for cell_block in cell_blocks:
            child_ids = [child_id for rel in cell_block.get("Relationships", [])
                         if rel.get("Type") == "CHILD" for child_id in rel.get("Ids", [])]
            child_blocks = [by_id[child_id] for child_id in child_ids if child_id in by_id]
            words = [child.get("Text", "") for child in child_blocks
                     if child.get("BlockType") == "WORD"]
            selected = [child.get("SelectionStatus") == "SELECTED" for child in child_blocks
                        if child.get("BlockType") == "SELECTION_ELEMENT"]
            text = " ".join(words).strip()
            if selected and not text:
                text = "X" if any(selected) else ""
            row = int(cell_block.get("RowIndex", 1)) - 1
            col = int(cell_block.get("ColumnIndex", 1)) - 1
            row_span = int(cell_block.get("RowSpan", 1))
            col_span = int(cell_block.get("ColumnSpan", 1))
            if 0 <= row < nrows and 0 <= col < ncols:
                rows[row][col] = text
            child_conf = [float(child["Confidence"]) / 100 for child in child_blocks
                          if child.get("BlockType") in ("WORD", "SELECTION_ELEMENT")
                          and child.get("Confidence") is not None]
            cells.append({
                "bbox": _bbox(cell_block, width, height), "text": text,
                "confidence": min(child_conf) if child_conf else None,
                "blank": not bool(text), "row": row, "row_end": row + row_span,
                "column": col, "column_end": col + col_span,
                "is_header": "COLUMN_HEADER" in cell_block.get("EntityTypes", []),
            })
        table_box = _bbox(table_block, width, height)
        tables.append({
            "bbox": table_box, "cells": cells, "rows": rows,
            "x_boundaries": [], "y_boundaries": [],
        })

    table_boxes = [table["bbox"] for table in tables]
    detections = []
    for block in blocks:
        if block.get("BlockType") != "LINE" or not block.get("Text"):
            continue
        box = _bbox(block, width, height)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        # The table is represented by cell text/rows, so avoid duplicate lines.
        if any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in table_boxes):
            continue
        polygon = block.get("Geometry", {}).get("Polygon", [])
        if polygon:
            quad = [[round(p.get("X", 0) * width, 2), round(p.get("Y", 0) * height, 2)]
                    for p in polygon[:4]]
            if len(quad) < 4:
                x0, y0, x1, y1 = box
                quad = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        else:
            x0, y0, x1, y1 = box
            quad = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        detections.append({"bbox": quad, "text": block["Text"],
                           "confidence": float(block.get("Confidence", 0)) / 100})

    table_text = []
    for table in tables:
        table_text.append("\n".join(" | ".join(row) for row in table["rows"]))
    prose = sorted(detections, key=lambda d: (np.mean(np.asarray(d["bbox"])[:, 1]),
                                               np.min(np.asarray(d["bbox"])[:, 0])))
    # Insert each structured table at its vertical position among prose lines.
    pieces = [(float(np.mean(np.asarray(d["bbox"])[:, 1])), d["text"]) for d in prose]
    pieces.extend((table["bbox"][1], text) for table, text in zip(tables, table_text))
    page_text = "\n".join(text for _, text in sorted(pieces, key=lambda item: item[0]))
    return {
        "page_text": page_text, "deskew_degrees": 0.0,
        "affine_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        "tables": tables, "detections": detections, "engine": "aws-textract",
    }


def extract_page(image, client):
    """Call Textract AnalyzeDocument(TABLES) on one rendered page image."""
    response = client.analyze_document(
        Document={"Bytes": _serialize_page_image(image)}, FeatureTypes=["TABLES"]
    )
    result = parse_blocks(response.get("Blocks", []), image.width, image.height)
    result["textract_model_version"] = response.get("AnalyzeDocumentModelVersion")
    return result
