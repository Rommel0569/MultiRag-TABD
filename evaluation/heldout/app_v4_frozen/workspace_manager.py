"""Context-isolated document intake, indexing, retrieval, and response generation."""
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from filelock import FileLock
from rank_bm25 import BM25Okapi

try:
    from .pdf_text import assess_text_layer, extract_native_pdf_pages
    from .ingest import ocr_pdf, OCRRequiredError
    from .retriever import _tokenize, reciprocal_rank_fusion
    from .embeddings import embed_passages, embed_query, relevance_probs, rerank
    from .llm import generator_config, _client
except ImportError:
    from pdf_text import assess_text_layer, extract_native_pdf_pages
    from ingest import ocr_pdf, OCRRequiredError
    from retriever import _tokenize, reciprocal_rank_fusion
    from embeddings import embed_passages, embed_query, relevance_probs, rerank
    from llm import generator_config, _client


ROOT = Path(__file__).resolve().parents[1]
WORKSPACES_ROOT = Path(os.environ.get("CEPRUNSA_WORKSPACES_DIR", ROOT / "data" / "workspaces")).expanduser()
if not WORKSPACES_ROOT.is_absolute():
    WORKSPACES_ROOT = (ROOT / WORKSPACES_ROOT).resolve()
MAX_UPLOAD_BYTES = int(os.environ.get("CEPRUNSA_MAX_PDF_BYTES", str(50 * 1024 * 1024)))
MAX_PDF_PAGES = int(os.environ.get("CEPRUNSA_MAX_PDF_PAGES", "500"))
DEFAULT_CONTEXT = {
    "id": "ceprunsa_2027", "name": "CEPRUNSA 2027 (corpus del artículo)",
    "description": "Proceso de admisión CEPRUNSA 2027: cronograma, vacantes, temario y reglamento.",
    "kind": "legacy", "read_only": True,
}


class WorkspaceError(RuntimeError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _now():
    return datetime.now(timezone.utc).isoformat()


def _workspace_id_valid(workspace_id):
    return bool(re.fullmatch(r"[a-f0-9]{32}", str(workspace_id or "")))


def _workspace_dir(workspace_id):
    if not _workspace_id_valid(workspace_id):
        raise WorkspaceError("Contexto no válido.", 404)
    path = (WORKSPACES_ROOT / workspace_id).resolve()
    if path.parent != WORKSPACES_ROOT.resolve():
        raise WorkspaceError("Contexto no válido.", 404)
    return path


def _manifest_path(workspace_id):
    return _workspace_dir(workspace_id) / "manifest.json"


def _read_manifest(workspace_id):
    path = _manifest_path(workspace_id)
    if not path.is_file():
        raise WorkspaceError("No se encontró el contexto seleccionado.", 404)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspaceError("El registro del contexto está dañado.", 500) from exc


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".upload-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def list_workspaces():
    results = [DEFAULT_CONTEXT]
    if WORKSPACES_ROOT.exists():
        for path in sorted(WORKSPACES_ROOT.iterdir()):
            manifest_path = path / "manifest.json"
            if path.is_dir() and manifest_path.is_file():
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    results.append({k: manifest[k] for k in ("id", "name", "description", "kind", "read_only")})
                except (OSError, KeyError, json.JSONDecodeError):
                    continue
    return results


def create_workspace(name, description):
    name = " ".join(str(name or "").split())
    description = " ".join(str(description or "").split())
    if not name or len(name) > 120:
        raise WorkspaceError("Indica un nombre de contexto de 1 a 120 caracteres.")
    if not description or len(description) > 800:
        raise WorkspaceError("Describe el alcance del contexto (máximo 800 caracteres).")
    WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
    workspace_id = uuid.uuid4().hex
    directory = _workspace_dir(workspace_id)
    (directory / "documents").mkdir(parents=True)
    manifest = {
        "id": workspace_id, "name": name, "description": description,
        "kind": "workspace", "read_only": False, "created_at": _now(),
        "updated_at": _now(), "documents": [], "index_version": 0,
    }
    _atomic_json(directory / "manifest.json", manifest)
    return {k: manifest[k] for k in ("id", "name", "description", "kind", "read_only")}


def _public_document(document):
    keys = ("id", "filename", "status", "pages", "native_pages", "ocr_pages", "segments", "tables", "error", "created_at")
    return {key: document.get(key) for key in keys if key in document}


def list_documents(workspace_id):
    if workspace_id == DEFAULT_CONTEXT["id"]:
        return []
    return [_public_document(item) for item in _read_manifest(workspace_id).get("documents", [])]


def _native_pages(pdf_path):
    pages, executable = extract_native_pdf_pages(pdf_path)
    if pages is None:
        return None, executable
    return [{"page": i + 1, "page_text": text, "text_layer_quality": assess_text_layer(text),
             "extraction_method": "native_pdf_text", "tables": [], "detections": []}
            for i, text in enumerate(pages)], executable


def _native_table_groups(text):
    """Detect repeated column-like layout rows without document-specific rules."""
    lines = text.splitlines()
    candidates = []
    for idx, line in enumerate(lines):
        cells = re.split(r"\t+|\s{2,}", line.strip())
        candidates.append((idx, cells) if len(cells) >= 2 and any(c.strip() for c in cells) else None)
    groups = []
    current = []
    previous = None
    for item in candidates:
        if item is None:
            if len(current) >= 2:
                groups.append(current)
            current, previous = [], None
            continue
        idx, cells = item
        if previous is not None and idx - previous > 1:
            if len(current) >= 2:
                groups.append(current)
            current = []
        current.append({"line": idx, "cells": [cell.strip() for cell in cells], "raw": lines[idx].strip()})
        previous = idx
    if len(current) >= 2:
        groups.append(current)
    return lines, groups


def _page_segments(page, source, workspace_id, document_id):
    page_no = int(page["page"])
    result = page
    segments = []
    table_ranges = []
    tables = result.get("tables") or []
    if not tables and result.get("extraction_method") == "native_pdf_text":
        lines, groups = _native_table_groups(result.get("page_text", ""))
        for group in groups:
            table_ranges.extend(item["line"] for item in group)
            rows = [item["cells"] for item in group]
            width = max(map(len, rows))
            rows = [row + [""] * (width - len(row)) for row in rows]
            tables.append({"rows": rows, "cells": [], "layout_text": [item["raw"] for item in group], "native_layout": True})
        prose = "\n".join(line for i, line in enumerate(lines) if i not in set(table_ranges)).strip()
        prose_parts = [prose] if prose else []
    else:
        detections = result.get("detections") or []
        detections = sorted(detections, key=lambda item: (
            float(np.mean(np.asarray(item.get("bbox", [[0, 0]]) )[:, 1])) if item.get("bbox") else 0,
            float(np.min(np.asarray(item.get("bbox", [[0, 0]]) )[:, 0])) if item.get("bbox") else 0,
        ))
        prose_parts = [item.get("text", "").strip() for item in detections if item.get("text", "").strip()]
        if not prose_parts and not tables and result.get("page_text", "").strip():
            prose_parts = [result["page_text"].strip()]

    for table_no, table in enumerate(tables, start=1):
        rows = table.get("rows") or []
        if not rows:
            continue
        cells = [c for c in table.get("cells", []) if c.get("text") or c.get("blank")]
        header_row = next((c.get("row", 0) for c in cells if c.get("is_header")), 0)
        headers = [str(value or "").strip() for value in rows[header_row]] if rows else []
        data_rows = [row for index, row in enumerate(rows) if index != header_row]
        if not data_rows:
            data_rows = rows
            headers = []
        for row_index, row in enumerate(data_rows):
            values = [str(value or "").strip() for value in row]
            width = max(len(headers), len(values))
            values += [""] * (width - len(values))
            header_values = headers + [""] * (width - len(headers))
            pairs = [f"{header_values[i]}: {values[i]}" if header_values[i] else values[i]
                     for i in range(width) if values[i]]
            row_text = " | ".join(pairs) or " | ".join(values)
            if not row_text.strip():
                continue
            segments.append({
                "id": f"{document_id}:{page_no}:table{table_no}:row{row_index}",
                "text": f"Tabla {table_no} — fila {row_index + 1}: {row_text}",
                "source": source, "page": page_no, "workspace_id": workspace_id,
                "document_id": document_id, "extraction": "table_row",
                "table": table_no, "row": row_index + 1,
                "cells": values, "headers": headers,
            })

    prose_text = "\n".join(prose_parts).strip()
    words = prose_text.split()
    for start in range(0, len(words), 200 - 20):
        chunk = " ".join(words[start:start + 200])
        if len(chunk.strip()) > 20:
            segments.append({
                "id": f"{document_id}:{page_no}:prose{start}", "text": chunk,
                "source": source, "page": page_no, "workspace_id": workspace_id,
                "document_id": document_id, "extraction": "prose_chunk",
            })
    return segments


def _save_extraction(workspace_id, document_id, pages):
    doc_dir = _workspace_dir(workspace_id) / "documents" / document_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    _atomic_json(doc_dir / "extraction.json", pages)
    return doc_dir


def _rebuild_index(workspace_id):
    directory = _workspace_dir(workspace_id)
    manifest = _read_manifest(workspace_id)
    segments = []
    for doc_meta in manifest["documents"]:
        if doc_meta.get("status") != "ready":
            continue
        extraction_path = directory / "documents" / doc_meta["id"] / "extraction.json"
        try:
            pages = json.loads(extraction_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            doc_meta["status"] = "error"
            doc_meta["error"] = "No se pudo leer el resultado de extracción guardado."
            continue
        for page in pages:
            segments.extend(_page_segments(page, doc_meta["filename"], workspace_id, doc_meta["id"]))
    if segments:
        from embeddings import embed_passages, EMBED_DIM
        vectors = embed_passages([segment["text"] for segment in segments])
        index = faiss.IndexFlatIP(EMBED_DIM)
        index.add(vectors)
        index_temp = directory / f"index-{uuid.uuid4().hex}.tmp"
        try:
            faiss.write_index(index, str(index_temp))
            os.replace(index_temp, directory / "index.faiss")
        finally:
            index_temp.unlink(missing_ok=True)
    else:
        (directory / "index.faiss").unlink(missing_ok=True)
    _atomic_json(directory / "segments.json", segments)
    manifest["segment_count"] = len(segments)
    manifest["index_version"] = int(manifest.get("index_version", 0)) + 1
    manifest["updated_at"] = _now()
    _atomic_json(directory / "manifest.json", manifest)


def _process_native(workspace_id, document_id, pages):
    with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
        manifest = _read_manifest(workspace_id)
        doc = next((item for item in manifest["documents"] if item["id"] == document_id), None)
        if not doc:
            raise WorkspaceError("Documento no encontrado.", 404)
        doc["status"] = "indexing"
        doc["native_pages"] = len(pages)
        doc["ocr_pages"] = 0
        _atomic_json(_manifest_path(workspace_id), manifest)
    try:
        _save_extraction(workspace_id, document_id, pages)
        with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
            manifest = _read_manifest(workspace_id)
            doc = next(item for item in manifest["documents"] if item["id"] == document_id)
            doc["status"] = "ready"
            doc["segments"] = sum(len(_page_segments(p, doc["filename"], workspace_id, document_id)) for p in pages)
            doc["tables"] = sum(len(p.get("tables") or []) for p in pages)
            doc.pop("error", None)
            _atomic_json(_manifest_path(workspace_id), manifest)
            _rebuild_index(workspace_id)
    except Exception as exc:
        with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
            manifest = _read_manifest(workspace_id)
            doc = next(item for item in manifest["documents"] if item["id"] == document_id)
            doc["status"] = "error"
            doc["error"] = str(exc)[:500]
            _atomic_json(_manifest_path(workspace_id), manifest)
        raise


def add_pdf(workspace_id, filename, content, *, context_confirmed=False, defer_processing=False):
    if workspace_id == DEFAULT_CONTEXT["id"]:
        raise WorkspaceError("El corpus CEPRUNSA del artículo está protegido. Crea un contexto para cargar documentos.", 409)
    if not context_confirmed:
        raise WorkspaceError("Confirma que este PDF corresponde solo al contexto activo antes de guardarlo.", 400)
    manifest = _read_manifest(workspace_id)
    if not content or not content.startswith(b"%PDF-"):
        raise WorkspaceError("El archivo no parece ser un PDF válido.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise WorkspaceError(f"El PDF supera el límite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.", 413)
    digest = hashlib.sha256(content).hexdigest()
    if any(doc.get("sha256") == digest for doc in manifest.get("documents", [])):
        raise WorkspaceError("Ese mismo PDF ya está guardado en este contexto.", 409)
    doc_id = uuid.uuid4().hex
    safe_name = Path(str(filename or "documento.pdf")).name[:180]
    if not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"
    doc_dir = _workspace_dir(workspace_id) / "documents" / doc_id
    doc_dir.mkdir(parents=True, exist_ok=False)
    pdf_path = doc_dir / "original.pdf"
    _atomic_bytes(pdf_path, content)
    native_pages, executable = _native_pages(pdf_path)
    if native_pages is None:
        native_pages = []
    page_count = len(native_pages)
    if page_count == 0:
        pdf_path.unlink(missing_ok=True)
        doc_dir.rmdir()
        raise WorkspaceError("No se pudo leer el PDF con el extractor local. Verifica Poppler y el archivo.", 422)
    if page_count > MAX_PDF_PAGES:
        pdf_path.unlink(missing_ok=True)
        doc_dir.rmdir()
        raise WorkspaceError(f"El PDF supera el límite configurado de {MAX_PDF_PAGES} páginas.", 413)
    needs_ocr = [p for p in native_pages if p["text_layer_quality"]["status"] != "native_text"]
    doc = {
        "id": doc_id, "filename": safe_name, "sha256": digest, "pages": page_count,
        "native_pages": page_count - len(needs_ocr), "ocr_pages": len(needs_ocr),
        "status": "awaiting_ocr_consent" if needs_ocr else "processing",
        "created_at": _now(), "pdf_tool": Path(executable).name if executable else None,
    }
    with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
        manifest = _read_manifest(workspace_id)
        manifest["documents"].append(doc)
        _atomic_json(_manifest_path(workspace_id), manifest)
    if not needs_ocr:
        clean_pages = [{k: v for k, v in page.items() if k != "text_layer_quality"} for page in native_pages]
        _save_extraction(workspace_id, doc_id, clean_pages)
        if not defer_processing:
            _process_native(workspace_id, doc_id, clean_pages)
    return _public_document(doc)


def index_saved_native_document(workspace_id, document_id):
    extraction_path = _workspace_dir(workspace_id) / "documents" / document_id / "extraction.json"
    try:
        pages = json.loads(extraction_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspaceError("No se pudo leer la extracción local guardada.", 500) from exc
    _process_native(workspace_id, document_id, pages)


def process_scanned_pdf(workspace_id, document_id, allow_textract, *, background=False):
    if not allow_textract:
        raise WorkspaceError("Confirma en la interfaz que autorizas enviar las páginas escaneadas a AWS Textract.", 400)
    if os.environ.get("CEPRUNSA_ENABLE_PAID_TEXTRACT") != "1":
        raise WorkspaceError("Textract está desactivado por la salvaguarda de costos del servidor.", 503)
    with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
        manifest = _read_manifest(workspace_id)
        doc = next((item for item in manifest["documents"] if item["id"] == document_id), None)
        if not doc:
            raise WorkspaceError("Documento no encontrado.", 404)
        if doc.get("status") != "awaiting_ocr_consent":
            raise WorkspaceError("El documento no está esperando autorización de OCR.", 409)
        doc["status"] = "processing_ocr"
        _atomic_json(_manifest_path(workspace_id), manifest)
        if background:
            return _public_document(doc)
    return _run_scanned_processing(workspace_id, document_id)


def run_scanned_processing(workspace_id, document_id):
    return _run_scanned_processing(workspace_id, document_id)


def _run_scanned_processing(workspace_id, document_id):
    try:
        pdf_path = _workspace_dir(workspace_id) / "documents" / document_id / "original.pdf"
        audit_dir = _workspace_dir(workspace_id) / "documents" / document_id / "ocr_audit"
        pages = ocr_pdf(
            str(pdf_path), engine_override="textract", allow_paid_textract=True,
            return_details=True, audit_dir=str(audit_dir),
        )
        normalized = []
        for page_num, result in pages:
            result["page"] = page_num
            normalized.append(result)
        _save_extraction(workspace_id, document_id, normalized)
        with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
            manifest = _read_manifest(workspace_id)
            doc = next(item for item in manifest["documents"] if item["id"] == document_id)
            doc["status"] = "ready"
            doc["native_pages"] = sum(p.get("extraction_method") == "native_pdf_text" for p in normalized)
            doc["ocr_pages"] = sum(str(p.get("extraction_method", "")).startswith("aws_") for p in normalized)
            doc["tables"] = sum(len(p.get("tables") or []) for p in normalized)
            doc["segments"] = sum(len(_page_segments(p, doc["filename"], workspace_id, document_id)) for p in normalized)
            doc.pop("error", None)
            _atomic_json(_manifest_path(workspace_id), manifest)
            _rebuild_index(workspace_id)
    except Exception as exc:
        with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
            manifest = _read_manifest(workspace_id)
            doc = next(item for item in manifest["documents"] if item["id"] == document_id)
            doc["status"] = "awaiting_ocr_consent" if isinstance(exc, OCRRequiredError) else "error"
            doc["error"] = str(exc)[:500]
            _atomic_json(_manifest_path(workspace_id), manifest)
        raise WorkspaceError(f"Falló el procesamiento OCR: {exc}", 503) from exc
    return _public_document(doc)


def _classify_query(query, manifest):
    provider = os.environ.get("CEPRUNSA_ROUTER_PROVIDER", "ollama").strip().lower()
    if provider == "gemini":
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        model = os.environ.get("CEPRUNSA_ROUTER_MODEL", "gemini-3.1-flash-lite")
    else:
        base_url = os.environ.get("CEPRUNSA_ROUTER_URL", "http://localhost:11434/v1")
        api_key = os.environ.get("CEPRUNSA_ROUTER_API_KEY", "ollama")
        model = os.environ.get("CEPRUNSA_ROUTER_MODEL", "llama3")
    client = _client(base_url, api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": (
            "Clasifica si una consulta puede responderse usando exclusivamente el contexto documental activo. "
            "Devuelve IN_SCOPE si trata del tema descrito, incluso si la redacción es coloquial o parafraseada. "
            "Devuelve OUT_OF_SCOPE si trata de otro tema o exige información ausente del alcance. Devuelve solo una etiqueta."
        )}, {"role": "user", "content": (
            f"CONTEXTO ACTIVO: {manifest['name']}\nALCANCE: {manifest['description']}\nCONSULTA: {query}\nEtiqueta:"
        )}], temperature=0.0, max_tokens=8,
    )
    label = (response.choices[0].message.content or "").strip().upper().replace("-", "_")
    if label not in {"IN_SCOPE", "OUT_OF_SCOPE"}:
        raise WorkspaceError("El clasificador devolvió una etiqueta no válida.", 503)
    return label


def _cache_path(workspace_id):
    return _workspace_dir(workspace_id) / "cache.json"


_CACHE_GENERIC_TERMS = {
    "many", "much", "what", "which", "when", "where", "how", "number", "amount",
    "count", "total", "slots", "seats", "places", "vacantes", "plazas", "cantidad",
    "numero", "cuantos", "cuantas", "cual", "cuales", "cuando", "donde", "admission",
    "admision", "university", "universidad", "process", "proceso", "available", "listed",
}


def _cache_anchor_compatible(left, right):
    """Avoid semantic cache reuse across different named entities or years."""
    left_tokens, right_tokens = set(_tokenize(left)), set(_tokenize(right))
    left_numbers = {token for token in left_tokens if token.isdigit()}
    right_numbers = {token for token in right_tokens if token.isdigit()}
    if left_numbers != right_numbers:
        return False
    left_entities = {token for token in left_tokens if token not in _CACHE_GENERIC_TERMS and len(token) >= 3}
    right_entities = {token for token in right_tokens if token not in _CACHE_GENERIC_TERMS and len(token) >= 3}
    if left_entities and right_entities and not (left_entities & right_entities):
        return False
    return True


def _cache_get(workspace_id, query, index_version):
    mode = os.environ.get("CEPRUNSA_WORKSPACE_CACHE_MODE", "semantic").lower()
    if mode == "disabled":
        return None
    path = _cache_path(workspace_id)
    with FileLock(str(path) + ".lock"):
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {"index_version": index_version, "entries": {}, "hits": 0, "lookups": 0}
        else:
            data = {"index_version": index_version, "entries": {}, "hits": 0, "lookups": 0}
        data["lookups"] = int(data.get("lookups", 0)) + 1
        matched = None
        similarity = None
        if data.get("index_version") == index_version:
            key = " ".join(query.casefold().split())
            entry = data.get("entries", {}).get(key)
            if entry:
                entry["hits"] = int(entry.get("hits", 0)) + 1
                data["hits"] = int(data.get("hits", 0)) + 1
                matched, similarity = entry["response"], 1.0
            elif data.get("entries") and mode == "semantic":
                query_vector = embed_query(query)
                candidates = []
                for candidate in data["entries"].values():
                    cached_vector = candidate.get("vector")
                    if not candidate.get("query") or not cached_vector:
                        continue
                    if not _cache_anchor_compatible(query, candidate["query"]):
                        continue
                    vector = np.asarray(cached_vector, dtype=np.float32)
                    if vector.shape == query_vector.shape:
                        score = float(np.dot(query_vector, vector))
                        if score >= float(os.environ.get("CEPRUNSA_WORKSPACE_CACHE_SHORTLIST", "0.80")):
                            candidates.append((score, candidate))
                candidates.sort(key=lambda item: item[0], reverse=True)
                candidates = candidates[:3]
                if candidates:
                    verified = relevance_probs([(query, item[1]["query"]) for item in candidates])
                    best = int(np.argmax(verified))
                    similarity = float(verified[best])
                    if similarity >= float(os.environ.get("CEPRUNSA_WORKSPACE_CACHE_VERIFY", "0.60")):
                        selected = candidates[best][1]
                        selected["hits"] = int(selected.get("hits", 0)) + 1
                        data["hits"] = int(data.get("hits", 0)) + 1
                        matched = selected["response"]
        _atomic_json(path, data)
        return {"response": matched, "similarity": similarity} if matched else None


def _cache_put(workspace_id, query, response, index_version):
    if os.environ.get("CEPRUNSA_WORKSPACE_CACHE_MODE", "semantic").lower() == "disabled":
        return
    path = _cache_path(workspace_id)
    with FileLock(str(path) + ".lock"):
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, json.JSONDecodeError):
            data = {}
        if data.get("index_version") != index_version:
            data = {"index_version": index_version, "entries": {}, "hits": data.get("hits", 0), "lookups": data.get("lookups", 0)}
        data.setdefault("hits", 0)
        data.setdefault("lookups", 0)
        data.setdefault("entries", {})[" ".join(query.casefold().split())] = {
            "query": query, "vector": embed_query(query).tolist(),
            "response": response, "hits": 0, "created_at": _now(),
        }
        _atomic_json(path, data)


def workspace_stats(workspace_id):
    if workspace_id == DEFAULT_CONTEXT["id"]:
        return None
    manifest = _read_manifest(workspace_id)
    path = _cache_path(workspace_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        data = {}
    return {
        "total_entries": len(data.get("entries", {})), "total_hits": data.get("hits", 0),
        "total_queries": data.get("lookups", 0), "hit_rate": data.get("hits", 0) / max(data.get("lookups", 0), 1),
        "mode": os.environ.get("CEPRUNSA_WORKSPACE_CACHE_MODE", "semantic"), "top_queries": [],
        "documents": len(manifest.get("documents", [])), "indexed_segments": manifest.get("segment_count", 0),
    }


def record_query_latency(workspace_id, query, result, latency_ms):
    """Append a local, credential-free, privacy-minimal per-query timing record."""
    directory = ROOT / "tmp" / "latency_audit" / workspace_id
    timestamp = datetime.now(timezone.utc)
    path = directory / f"queries_{timestamp:%Y%m%d}.jsonl"
    try:
        config = generator_config()
    except (RuntimeError, ValueError):
        config = {"provider": "unknown", "model": "unknown"}
    record = {
        "timestamp": timestamp.isoformat(),
        "workspace_id": workspace_id,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "query_characters": len(query),
        "phase": result.get("phase"),
        "category": result.get("category"),
        "cache_hit": bool(result.get("cache_hit")),
        "tokens_used": int(result.get("tokens_used", 0) or 0),
        "latency_ms": round(float(latency_ms), 2),
        "latency_breakdown_ms": result.get("latency_breakdown_ms", {}),
        "generator_provider": config["provider"],
        "generator_model": config["model"],
        "router_provider": os.environ.get("CEPRUNSA_ROUTER_PROVIDER", "ollama"),
        "router_model": os.environ.get("CEPRUNSA_ROUTER_MODEL", "llama3"),
    }
    try:
        try:
            retention_days = max(1, int(os.environ.get("CEPRUNSA_LATENCY_AUDIT_RETENTION_DAYS", "7")))
        except ValueError:
            retention_days = 7
        directory.mkdir(parents=True, exist_ok=True)
        cutoff = (timestamp - timedelta(days=retention_days)).timestamp()
        audit_root = ROOT / "tmp" / "latency_audit"
        for old_log in audit_root.glob("**/queries_*.jsonl"):
            try:
                if old_log != path and old_log.stat().st_mtime < cutoff:
                    old_log.unlink(missing_ok=True)
            except OSError:
                continue
        with FileLock(str(path) + ".lock"):
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
    except OSError as exc:
        print(f"[WARN] No se pudo guardar el registro local de latencia: {exc}")


@lru_cache(maxsize=8)
def _load_workspace_retriever(workspace_id, index_version):
    directory = _workspace_dir(workspace_id)
    try:
        docs = json.loads((directory / "segments.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        docs = []
    if not docs or not (directory / "index.faiss").is_file():
        return None, docs, None
    index = faiss.read_index(str(directory / "index.faiss"))
    bm25 = BM25Okapi([_tokenize(item["text"]) for item in docs])
    return index, docs, bm25


def _retrieve(workspace_id, query, top_k=5):
    with FileLock(str(_workspace_dir(workspace_id) / ".workspace.lock")):
        manifest = _read_manifest(workspace_id)
        index, docs, bm25 = _load_workspace_retriever(workspace_id, int(manifest.get("index_version", 0)))
    if index is None or bm25 is None:
        return []
    vector = embed_query(query).reshape(1, -1)
    dense_scores, dense_ids = index.search(vector, min(20, len(docs)))
    dense = []
    for score, idx in zip(dense_scores[0], dense_ids[0]):
        if idx >= 0:
            item = docs[int(idx)].copy()
            item["score_dense"] = float(score)
            dense.append(item)
    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens) if query_tokens else np.zeros(len(docs))
    lexical = []
    for idx in np.argsort(scores)[::-1][:20]:
        if scores[idx] > 0:
            item = docs[int(idx)].copy()
            item["score_bm25"] = float(scores[idx])
            lexical.append(item)
    candidates = reciprocal_rank_fusion(dense, lexical, top_k=min(40, len(docs)))
    return rerank(query, candidates, top_k=top_k)


def query_workspace(workspace_id, query):
    if workspace_id == DEFAULT_CONTEXT["id"]:
        raise WorkspaceError("Usa la consulta CEPRUNSA predeterminada para ese corpus.", 400)
    started = time.perf_counter()
    manifest = _read_manifest(workspace_id)
    cache_started = time.perf_counter()
    cached = _cache_get(workspace_id, query, manifest.get("index_version", 0))
    cache_ms = round((time.perf_counter() - cache_started) * 1000, 2)
    if cached and cached.get("response"):
        return {**cached["response"], "phase": "FASE 1 — CACHÉ DEL CONTEXTO", "cache_hit": True,
                "tokens_used": 0, "similarity": cached["similarity"], "latency_ms": round((time.perf_counter()-started)*1000, 2),
                "latency_breakdown_ms": {"cache_lookup": cache_ms}}
    router_started = time.perf_counter()
    label = _classify_query(query, manifest)
    router_ms = round((time.perf_counter() - router_started) * 1000, 2)
    if label == "OUT_OF_SCOPE":
        return {
            "answer": f"La consulta no corresponde al contexto activo ({manifest['name']}).",
            "sources": [], "category": "OUT_OF_SCOPE", "phase": "FASE 2 — CLASIFICADOR DEL CONTEXTO",
            "cache_hit": False, "tokens_used": 0, "similarity": None,
            "latency_ms": round((time.perf_counter()-started)*1000, 2),
            "latency_breakdown_ms": {"cache_lookup": cache_ms, "context_router": router_ms},
        }
    retrieval_started = time.perf_counter()
    chunks = _retrieve(workspace_id, query, top_k=8)
    retrieval_ms = round((time.perf_counter() - retrieval_started) * 1000, 2)
    if not chunks:
        return {
            "answer": "No hay documentos procesados en este contexto para responder la consulta.",
            "sources": [], "category": "IN_SCOPE", "phase": "FASE 3 — RECUPERACIÓN DEL CONTEXTO",
            "cache_hit": False, "tokens_used": 0, "similarity": None,
            "latency_ms": round((time.perf_counter()-started)*1000, 2),
            "latency_breakdown_ms": {"cache_lookup": cache_ms, "context_router": router_ms, "retrieval": retrieval_ms},
        }
    config = generator_config()
    if config["provider"] in {"deepseek", "gemini"} and not config["api_key"]:
        raise WorkspaceError(f"Configura la credencial de {config['provider']} en el entorno local.", 503)
    context = "\n\n".join(
        f"[Fuente: {item.get('source','?')}, página {item.get('page','?')}; tipo: {item.get('extraction','texto')}]\n{item['text']}"
        for item in chunks
    )
    system_prompt = (
        f"Respondes preguntas usando exclusivamente los documentos del contexto activo {manifest['name']}. "
        f"Alcance declarado: {manifest['description']} Responde en español y con brevedad. "
        "No mezcles datos de otras universidades, documentos, contextos ni conocimiento externo. "
        "Para tablas, relaciona explícitamente encabezado, fila y valor; no unas columnas diferentes. "
        "Si los fragmentos no bastan o no permiten confirmar el dato, responde que no aparece en los documentos del contexto."
    )
    generation_started = time.perf_counter()
    response = _client(config["base_url"], config["api_key"]).chat.completions.create(
        model=config["model"], messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"EVIDENCIA:\n{context}\n\nPREGUNTA: {query}"},
        ], temperature=float(os.environ.get("CEPRUNSA_GENERATOR_TEMPERATURE", "0.1")),
    )
    answer = (response.choices[0].message.content or "").strip()
    generation_ms = round((time.perf_counter() - generation_started) * 1000, 2)
    sources = sorted({f"{item.get('source')} (p.{item.get('page', '?')})" for item in chunks})
    usage = getattr(response, "usage", None)
    tokens = int(getattr(usage, "total_tokens", 0) or 0)
    result = {
        "answer": answer, "sources": sources, "category": "IN_SCOPE",
        "phase": "FASE 3 — RECUPERACIÓN HÍBRIDA + RERANKING + GENERACIÓN",
        "cache_hit": False, "tokens_used": tokens, "similarity": None,
        "latency_ms": round((time.perf_counter()-started)*1000, 2),
        "latency_breakdown_ms": {
            "cache_lookup": cache_ms, "context_router": router_ms,
            "retrieval_and_reranking": retrieval_ms, "generation": generation_ms,
        },
    }
    _cache_put(workspace_id, query, result, manifest.get("index_version", 0))
    return result
