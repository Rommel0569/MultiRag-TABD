# app/main.py
import os
import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from fastapi             import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic            import BaseModel
from urllib.parse        import unquote
from pipeline            import pipeline
from cache               import get_cache_stats
try:
    from . import workspace_manager as workspaces
except ImportError:
    import workspace_manager as workspaces

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
app = FastAPI(
    title="CEPRUNSA Multi-RAG API",
    description="Sistema de recuperación semántica sobre documentos PDF de admisión",
    version="1.0.0"
)

cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "CEPRUNSA_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -----------------------------
# MODELOS DE REQUEST/RESPONSE
# -----------------------------
class QueryRequest(BaseModel):
    query: str
    workspace_id: str | None = None

class WorkspaceRequest(BaseModel):
    name: str
    description: str

class TextractConsentRequest(BaseModel):
    allow_textract: bool = False

class QueryResponse(BaseModel):
    answer:      str
    sources:     list[str]
    category:    str
    phase:       str
    cache_hit:   bool
    tokens_used: int
    similarity:  float | None
    latency_ms: float | None = None
    latency_breakdown_ms: dict[str, float] | None = None

# -----------------------------
# ENDPOINTS
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """Endpoint principal — recibe consulta y retorna respuesta."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía.")

    started = time.perf_counter()
    workspace_id = request.workspace_id or "ceprunsa_2027"
    try:
        result = (pipeline(request.query) if request.workspace_id in (None, "ceprunsa_2027")
                  else workspaces.query_workspace(request.workspace_id, request.query))
    except workspaces.WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    result["latency_ms"] = elapsed_ms
    breakdown = dict(result.get("latency_breakdown_ms") or {})
    breakdown.setdefault("pipeline_total", elapsed_ms)
    result["latency_breakdown_ms"] = breakdown
    workspaces.record_query_latency(workspace_id, request.query, result, elapsed_ms)
    return QueryResponse(**result)

@app.get("/stats")
def stats_endpoint(workspace_id: str | None = None):
    """Retorna estadísticas de la caché para el StatsPanel."""
    if workspace_id and workspace_id != "ceprunsa_2027":
        try:
            return workspaces.workspace_stats(workspace_id)
        except workspaces.WorkspaceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return get_cache_stats()

@app.get("/workspaces")
def list_workspaces_endpoint():
    return {"workspaces": workspaces.list_workspaces()}

@app.post("/workspaces", status_code=201)
def create_workspace_endpoint(request: WorkspaceRequest):
    try:
        return workspaces.create_workspace(request.name, request.description)
    except workspaces.WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

@app.get("/workspaces/{workspace_id}/documents")
def list_documents_endpoint(workspace_id: str):
    try:
        return {"documents": workspaces.list_documents(workspace_id)}
    except workspaces.WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

@app.post("/workspaces/{workspace_id}/documents", status_code=201)
async def upload_document_endpoint(workspace_id: str, request: Request, background_tasks: BackgroundTasks):
    try:
        max_bytes = workspaces.MAX_UPLOAD_BYTES
        declared = request.headers.get("content-length")
        if declared and int(declared) > max_bytes:
            raise HTTPException(status_code=413, detail="El PDF supera el límite configurado.")
        chunks = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > max_bytes:
                raise HTTPException(status_code=413, detail="El PDF supera el límite configurado.")
            chunks.append(chunk)
        content = b"".join(chunks)
        result = workspaces.add_pdf(
            workspace_id,
            unquote(request.headers.get("x-filename", "documento.pdf")),
            content,
            context_confirmed=request.headers.get("x-context-confirmed", "").lower() == "true",
            defer_processing=True,
        )
        if result.get("status") == "processing":
            background_tasks.add_task(workspaces.index_saved_native_document, workspace_id, result["id"])
        return result
    except workspaces.WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

@app.post("/workspaces/{workspace_id}/documents/{document_id}/process")
def process_scanned_document_endpoint(workspace_id: str, document_id: str, request: TextractConsentRequest, background_tasks: BackgroundTasks):
    try:
        result = workspaces.process_scanned_pdf(workspace_id, document_id, request.allow_textract, background=True)
        background_tasks.add_task(workspaces.run_scanned_processing, workspace_id, document_id)
        return result
    except workspaces.WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

@app.get("/health")
def health_check():
    """Verificación de estado del servidor."""
    return {"status": "ok", "service": "CEPRUNSA Multi-RAG"}
