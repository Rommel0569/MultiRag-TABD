# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi             import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic            import BaseModel
from pipeline            import pipeline
from cache               import get_cache_stats

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
app = FastAPI(
    title="CEPRUNSA Multi-RAG API",
    description="Sistema de recuperación semántica sobre documentos PDF de admisión",
    version="1.0.0"
)

# CORS para el frontend React en localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# -----------------------------
# MODELOS DE REQUEST/RESPONSE
# -----------------------------
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer:      str
    sources:     list
    category:    str
    phase:       str
    cache_hit:   bool
    tokens_used: int
    similarity:  float | None

# -----------------------------
# ENDPOINTS
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """Endpoint principal — recibe consulta y retorna respuesta."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía.")

    result = pipeline(request.query)
    return QueryResponse(**result)

@app.get("/stats")
def stats_endpoint():
    """Retorna estadísticas de la caché para el StatsPanel."""
    return get_cache_stats()

@app.get("/health")
def health_check():
    """Verificación de estado del servidor."""
    return {"status": "ok", "service": "CEPRUNSA Multi-RAG"}