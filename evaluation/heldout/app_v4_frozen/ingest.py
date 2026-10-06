# app/ingest.py
import os
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import faiss
from pdf2image import convert_from_path, pdfinfo_from_path
try:
    from .pdf_text import assess_text_layer, extract_native_pdf_pages, image_ink_ratio, resolve_pdftotext
except ImportError:
    from pdf_text import assess_text_layer, extract_native_pdf_pages, image_ink_ratio, resolve_pdftotext
try:
    from .ocr_engine import extract_page
except ImportError:
    from ocr_engine import extract_page

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
PDF_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "data", "pdfs")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR  = str(PROJECT_ROOT / "data" / "index")
# Las extracciones experimentales pueden escribirse en otro directorio sin
# reemplazar los índices que produjeron las cifras del artículo.
_INDEX_DIR = Path(os.environ.get("CEPRUNSA_INDEX_DIR", INDEX_DIR)).expanduser()
INDEX_DIR = str((_INDEX_DIR if _INDEX_DIR.is_absolute() else PROJECT_ROOT / _INDEX_DIR).resolve())
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
_AUDIT_BASE = os.environ.get("CEPRUNSA_OCR_AUDIT_DIR", os.path.join(_DATA_DIR, "ocr_runs"))
_AUDIT_RUN_ID = os.environ.get("CEPRUNSA_OCR_RUN_ID") or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
OCR_AUDIT_DIR = os.path.join(_AUDIT_BASE, _AUDIT_RUN_ID)
_PDFTOTEXT_BIN = resolve_pdftotext(os.environ.get("CEPRUNSA_POPPLER_PATH"))
POPPLER_PATH = os.environ.get("CEPRUNSA_POPPLER_PATH") or (
    str(Path(_PDFTOTEXT_BIN).parent) if _PDFTOTEXT_BIN else None
)

os.makedirs(INDEX_DIR, exist_ok=True)

CATEGORIES = {
    "CRONOGRAMA": ["CRONOGRAMA DE ADMISIÓN 2027.pdf"],
    "VACANTES":   ["CUADRO DE VACANTES 2027.pdf"],
    "TEMARIO":    ["TEMARIO Y MATRIZ DE EVALUACIÓN 2027.pdf"],
    "REGLAMENTO": ["REGLAMENTO DE ADMISIÓN 2027.pdf"]
}
requested_categories = os.environ.get("CEPRUNSA_INGEST_CATEGORIES")
if requested_categories:
    requested_categories = {value.strip().upper() for value in requested_categories.split(",")}
    unknown = requested_categories - set(CATEGORIES)
    if unknown:
        raise ValueError(f"Categorías de ingesta desconocidas: {sorted(unknown)}")
    CATEGORIES = {key: value for key, value in CATEGORIES.items()
                  if key in requested_categories}

# -----------------------------
# OCR se inicializa solo cuando el texto PDF local requiere OCR.
# -----------------------------
OCR_ENGINE = os.environ.get("CEPRUNSA_OCR_ENGINE", "textract").strip().lower()
if OCR_ENGINE not in {"auto", "easyocr", "textract"}:
    raise ValueError("CEPRUNSA_OCR_ENGINE must be 'auto', 'easyocr' or 'textract'.")
ocr_reader = None
textract_extract_page = None
_OCR_BACKEND_LOADED = None


class OCRRequiredError(RuntimeError):
    """Raised when a scanned page needs an OCR choice/authorization."""


def _get_ocr_backend(engine_override=None, allow_paid_textract=None):
    """Load the selected OCR provider only after a page fails local text checks."""
    global ocr_reader, textract_extract_page, _OCR_BACKEND_LOADED
    requested_engine = (engine_override or OCR_ENGINE).strip().lower()
    if requested_engine == "disabled":
        raise OCRRequiredError(
            "OCR_REQUIRED: hay páginas escaneadas; vuelve a procesar el documento "
            "y autoriza Textract si deseas enviarlas a AWS."
        )
    if requested_engine not in {"auto", "easyocr", "textract"}:
        raise ValueError("OCR engine must be auto, easyocr, textract or disabled.")
    backend = "easyocr" if requested_engine == "auto" else requested_engine
    if backend == "textract":
        if allow_paid_textract is False:
            raise OCRRequiredError(
                "OCR_REQUIRED: el documento necesita OCR. La página no se envió a AWS; "
                "autoriza Textract para procesar este documento."
            )
        if os.environ.get("CEPRUNSA_ENABLE_PAID_TEXTRACT") != "1":
            raise RuntimeError(
                "This scanned/low-quality page needs OCR. Textract sends the page "
                "to AWS and may incur charges. Set CEPRUNSA_ENABLE_PAID_TEXTRACT=1 "
                "only after the user approves external processing and cost."
            )
        if ocr_reader is None or _OCR_BACKEND_LOADED != backend:
            try:
                from .textract_engine import create_textract_client, extract_page
            except ImportError:
                from textract_engine import create_textract_client, extract_page
            region = (os.environ.get("CEPRUNSA_TEXTRACT_REGION")
                      or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1")
            ocr_reader = create_textract_client(region, os.environ.get("CEPRUNSA_AWS_PROFILE"))
            textract_extract_page = extract_page
            _OCR_BACKEND_LOADED = backend
            print("[INFO] Textract seleccionado; solo se enviarán páginas que fallen la lectura local.")
    elif ocr_reader is None or _OCR_BACKEND_LOADED != backend:
        print("[INFO] Cargando EasyOCR local (español + inglés)...")
        import easyocr
        import torch
        torch.set_num_threads(int(os.environ.get("CEPRUNSA_TORCH_THREADS", "4")))
        ocr_reader = easyocr.Reader(['es', 'en'], gpu=False)
        textract_extract_page = None
        _OCR_BACKEND_LOADED = backend
        print("[INFO] EasyOCR listo.")
    return backend


# -----------------------------
# Lectura local del texto PDF antes de invocar cualquier motor OCR.
def ocr_pdf(pdf_path, *, engine_override=None, allow_paid_textract=None, return_details=False, audit_dir=None):
    """Use clean local PDF text; OCR only pages with absent/suspect text layers."""
    try:
        page_count = int(pdfinfo_from_path(pdf_path, poppler_path=POPPLER_PATH)["Pages"])
    except Exception:
        page_count = None
    native_pages, text_extractor = extract_native_pdf_pages(
        pdf_path, poppler_path=POPPLER_PATH, page_count=page_count
    )
    if native_pages is None:
        # Poppler text extraction is unavailable: conservatively OCR every page.
        rendered = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
        page_count = len(rendered)
        native_pages = [""] * page_count
        print("  [WARN] No se pudo extraer texto PDF local; se evaluarán todas las páginas con OCR.")
    else:
        page_count = len(native_pages)
        rendered = None
        print(f"  [PDF] Inspección local de texto: {text_extractor or 'Poppler'}; páginas={page_count}.")
    texts = []

    for i, native_text in enumerate(native_pages):
        page_num = i + 1
        text_quality = assess_text_layer(native_text)
        image = None
        page_ink_ratio = None
        if text_quality["status"] == "native_text":
            result = {
                "page_text": native_text.strip(), "deskew_degrees": 0.0,
                "affine_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                "tables": [], "detections": [],
            }
            method = "native_pdf_text"
        else:
            if rendered is not None:
                image = rendered[i]
            else:
                page_images = convert_from_path(
                    pdf_path, dpi=300, first_page=page_num, last_page=page_num,
                    poppler_path=POPPLER_PATH,
                )
                image = page_images[0]
            page_ink_ratio = image_ink_ratio(image)
            if page_ink_ratio < 0.0001:
                # Skip nearly blank scans locally; do not pay to send blank pages.
                result = {
                    "page_text": "", "deskew_degrees": 0.0,
                    "affine_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                    "tables": [], "detections": [],
                }
                method = "blank_page_skip"
            else:
                backend = _get_ocr_backend(engine_override, allow_paid_textract)
                if backend == "textract":
                    result = textract_extract_page(image, ocr_reader)
                    method = "aws_textract_analyze_document_tables"
                else:
                    result = extract_page(image, ocr_reader)
                    method = "local_easyocr"
        page_text = result["page_text"]
        detections = result["detections"]
        confidences = [item["confidence"] for item in detections]
        cell_confidences = [cell["confidence"] for table in result["tables"]
                            for cell in table["cells"] if cell["confidence"] is not None]

        audit_root = str(Path(audit_dir).resolve()) if audit_dir else OCR_AUDIT_DIR
        audit_path = os.path.join(audit_root, os.path.basename(pdf_path))
        os.makedirs(audit_path, exist_ok=True)
        audit_file = os.path.join(audit_path, f"page_{page_num:03d}.json")
        with open(audit_file, "w", encoding="utf-8") as audit:
            json.dump({
                "source": os.path.basename(pdf_path),
                "page": page_num,
                "dpi": 300 if method != "native_pdf_text" else None,
                "extraction_method": method,
                "text_layer_quality": text_quality,
                "rendered_page_ink_ratio": page_ink_ratio,
                "local_text_extractor": text_extractor,
                "preprocessing": ("automatic deskew + grayscale + CLAHE; ruled tables detected geometrically"
                                  if method == "local_easyocr" else
                                  "AWS Textract AnalyzeDocument(TABLES)" if method.startswith("aws_") else
                                  "local near-blank image check; OCR skipped" if method == "blank_page_skip" else
                                  "Poppler local PDF text extraction with layout preservation"),
                "page_text": page_text,
                "deskew_degrees": result["deskew_degrees"],
                "mean_prose_confidence": float(np.mean(confidences)) if confidences else None,
                "low_confidence_prose_detections": int(sum(c < 0.50 for c in confidences)),
                "mean_cell_confidence": float(np.mean(cell_confidences)) if cell_confidences else None,
                "table_count": len(result["tables"]),
                "table_cell_count": sum(len(table["cells"]) for table in result["tables"]),
                "detections": detections,
                "tables": result["tables"],
            }, audit, ensure_ascii=False, indent=2)
        if return_details:
            detailed_result = dict(result)
            detailed_result["extraction_method"] = method
            detailed_result["text_layer_quality"] = text_quality
            texts.append((page_num, detailed_result))
        else:
            texts.append((page_num, page_text))
        print(f"  [{method}] Página {page_num}/{page_count} — {len(page_text)} chars; "
              f"{len(result['tables'])} tablas, {sum(len(t['cells']) for t in result['tables'])} celdas")

    return texts

# -----------------------------
# CHUNKING
# -----------------------------
def chunk_text(text, chunk_size=200, overlap=20):
    """
    Divide texto en chunks de ~200 palabras con solapamiento de 20.
    200 palabras ≈ 280 tokens en español, bien dentro del límite de 512
    tokens de multilingual-e5-base. Antes era 512 palabras (>700 tokens),
    lo que causaba truncamiento silencioso del embedding.
    """
    words  = text.split()
    chunks = []
    start  = 0
    while start < len(words):
        end   = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 20:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# -----------------------------
# INGESTA PRINCIPAL
# -----------------------------
def ingest():
    """
    Procesa PDFs → OCR → embeddings → índice FAISS + JSON de metadatos.
    Genera en data/index/:
      <CATEGORIA>.index  — índice FAISS HNSW
      <CATEGORIA>.json   — textos y metadatos
    """
    # El OCR puede ejecutarse por separado sin inicializar ni descargar el
    # modelo de embeddings; el modelo solo se necesita al construir índices.
    from embeddings import embed_passage, EMBED_DIM

    for category, pdf_list in CATEGORIES.items():
        print(f"\n{'='*55}")
        print(f"[INFO] Categoría: {category}")

        all_texts   = []
        all_vectors = []

        for pdf_file in pdf_list:
            pdf_path = os.path.join(PDF_DIR, pdf_file)
            if not os.path.exists(pdf_path):
                print(f"[WARN] No encontrado: {pdf_path}")
                continue

            print(f"[INFO] Procesando: {pdf_file}")
            pages_text = ocr_pdf(pdf_path)

            for page_num, page_text in pages_text:
                if not page_text.strip():
                    print(f"  [SKIP] Página {page_num} vacía")
                    continue

                chunks = chunk_text(page_text)
                print(f"  [CHUNK] Página {page_num} → {len(chunks)} chunks")

                for chunk in chunks:
                    vector = embed_passage(chunk)
                    all_vectors.append(vector)
                    all_texts.append({
                        "id":       str(uuid.uuid4()),
                        "text":     chunk,
                        "source":   pdf_file,
                        "page":     page_num,
                        "category": category
                    })

        if not all_vectors:
            print(f"[WARN] Sin vectores para {category}")
            continue

        # -----------------------------
        # CONSTRUIR ÍNDICE FAISS HNSW
        # -----------------------------
        vectors_np = np.array(all_vectors, dtype=np.float32)

        index = faiss.IndexHNSWFlat(EMBED_DIM, 32)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch        = 50
        index.add(vectors_np)

        # Guardar índice FAISS
        index_path = os.path.join(INDEX_DIR, f"{category}.index")
        faiss.write_index(index, index_path)

        # Guardar textos y metadatos
        json_path = os.path.join(INDEX_DIR, f"{category}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_texts, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] {category}:")
        print(f"     Vectores indexados : {index.ntotal}")
        print(f"     Chunks guardados   : {len(all_texts)}")
        print(f"     Índice FAISS       : {index_path}")
        print(f"     Metadatos JSON     : {json_path}")

    print(f"\n{'='*55}")
    print("[DONE] Ingesta completa.")

if __name__ == "__main__":
    ingest()
