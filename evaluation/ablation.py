# evaluation/ablation.py
"""
O9 — Experimento de ablación: aporte individual de cada componente.

Genera respuestas para 4 variantes (+ V5 opcional) del sistema (todas SIN caché):
  V1_baseline          : densa global top-5 (sin router, sin BM25, sin rerank)
  V2_baseline_rerank   : densa global top-20 → cross-encoder → top-5
  V3_router_hibrida    : router + FAISS+BM25+RRF top-5 (sin rerank)
  V4_completo          : router + híbrida + rerank (pipeline completo)
  V5_hibrido_sin_extractores : V4 sin extracción estructurada (camino híbrido + LLM)

Guarda ablacion_<variante>.json, checkpoints JSONL por fila y manifest.json.
Usa Ollama local por defecto o un proveedor remoto configurado explícitamente.
"""
import os
import sys
import json
import argparse
import hashlib
import importlib.metadata
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE    = os.path.dirname(os.path.abspath(__file__))
load_dotenv(Path(HERE).parent / ".env", override=False)
APP_DIR = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP_DIR)

from router    import route_query
from retriever import (CATEGORIES, dense_search, lexical_search,
                       reciprocal_rank_fusion, retrieve_with_global_fallback,
                       documents as indexed_documents)
from embeddings import rerank
from llm       import generate_response, generator_config
from structured_answers import resolve_structured_answer


def dense_global(query: str, top_k: int):
    """Búsqueda densa sobre TODO el corpus (sin enrutamiento).
    score_dense es distancia L2 sobre vectores normalizados: menor = más similar."""
    results = []
    for cat in CATEGORIES:
        results.extend(dense_search(query, cat, top_k=top_k))
    results.sort(key=lambda d: d["score_dense"])
    return results[:top_k]


def v1_baseline(query: str):
    return dense_global(query, top_k=5)

def v2_baseline_rerank(query: str):
    candidatos = dense_global(query, top_k=20)
    return rerank(query, candidatos, top_k=5)

def v3_router_hibrida(query: str):
    r = route_query(query)
    if not r["is_in_domain"]:
        return []
    cat     = r["category"]
    dense   = dense_search(query, cat, top_k=10)
    lexical = lexical_search(query, cat, top_k=10)
    return reciprocal_rank_fusion(dense, lexical, top_k=5)   # sin rerank

def v4_completo(query: str):
    r = route_query(query)
    if not r["is_in_domain"]:
        return []
    return retrieve(query, r["category"], top_k=5)           # híbrida + rerank


def v5_hibrido_sin_extractores(query: str):
    # Placeholder: la rama real (router -> hibrida + rerank -> generador, SIN
    # extractores estructurados) se ejecuta en main().
    return v4_completo(query)


VARIANTES = {
    "V1_baseline":        v1_baseline,
    "V2_baseline_rerank": v2_baseline_rerank,
    "V3_router_hibrida":  v3_router_hibrida,
    "V4_completo":        v4_completo,
    "V5_hibrido_sin_extractores": v5_hibrido_sin_extractores,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", default=os.path.join(HERE, "queries.json"))
    parser.add_argument("--allow-candidate-queries", action="store_true",
                        help="Permite generar solo respuestas exploratorias con referencias OCR sin validar; hasta 2,000 llamadas con 500 consultas")
    parser.add_argument("--output-dir", default=None,
                        help="Directorio nuevo; por defecto evaluation/runs/ablation_<UTC>.")
    parser.add_argument("--variants", default=None,
                        help="Variantes a ejecutar, separadas por coma (ej. V2_baseline_rerank,V3_router_hibrida). Por defecto ejecuta las cuatro.")
    parser.add_argument("--resume", action="store_true",
                        help="Reanuda en --output-dir usando el manifest y los checkpoints JSONL existentes.")
    args = parser.parse_args()

    if args.variants:
        requested = [name.strip() for name in args.variants.split(",") if name.strip()]
        unknown = sorted(set(requested) - set(VARIANTES))
        if unknown:
            parser.error(f"Variantes desconocidas: {unknown}. Opciones: {', '.join(VARIANTES)}")
        if len(set(requested)) != len(requested):
            parser.error("No repitas variantes en --variants.")
        variantes = [(name, VARIANTES[name]) for name in requested]
    else:
        variantes = [(n, f) for n, f in VARIANTES.items() if n != "V5_hibrido_sin_extractores"]

    queries_path = Path(args.queries)
    with queries_path.open(encoding="utf-8") as f:
        query_document = json.load(f)
    candidate_status = query_document.get("status") == "CANDIDATE_POOL_NOT_A_VALIDATED_BENCHMARK"
    if candidate_status and not args.allow_candidate_queries:
        raise SystemExit("El archivo contiene consultas candidatas OCR aún no validadas. Verifica referencias contra el PDF primero; usa --allow-candidate-queries solo para exploración técnica.")
    consultas = query_document["consultas"]

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output_dir = Path(args.output_dir) if args.output_dir else Path(HERE) / "runs" / f"ablation_{run_id}"
    if args.resume:
        if not output_dir.is_dir() or not (output_dir / "manifest.json").is_file():
            raise SystemExit("--resume requires an existing --output-dir with manifest.json.")
    else:
        output_dir.mkdir(parents=True, exist_ok=False)
    config = generator_config()
    if config["provider"] == "deepseek" and not config["api_key"]:
        raise SystemExit("Falta DEEPSEEK_API_KEY; define la variable o usa el .env local antes de iniciar.")
    if not consultas:
        raise SystemExit("El archivo de consultas no contiene consultas.")

    index_dir = Path(os.environ.get("CEPRUNSA_INDEX_DIR", Path(HERE).parent / "data" / "index"))
    expected_index_files = [f"{category}{suffix}"
                            for category in ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO"]
                            for suffix in [".index", ".json"]]
    missing_index_files = [name for name in expected_index_files if not (index_dir / name).is_file()]
    if missing_index_files:
        raise SystemExit(f"Índice incompleto en {index_dir}; faltan: {missing_index_files}")
    index_hashes = {
        name: hashlib.sha256((index_dir / name).read_bytes()).hexdigest()
        for name in expected_index_files
    }
    manifest = {
        "run_id": run_id,
        "utc": datetime.now(timezone.utc).isoformat(),
        "generator_provider": config["provider"],
        "generator_model": config["model"],
        "generator_temperature": float(os.environ.get("CEPRUNSA_GENERATOR_TEMPERATURE", "0.1")),
        "query_count": len(consultas),
        "selected_variants": [name for name, _ in variantes],
        "query_references_unvalidated": candidate_status,
        "queries_sha256": hashlib.sha256(queries_path.read_bytes()).hexdigest(),
        "index_dir": str(index_dir.resolve()),
        "index_files_sha256": index_hashes,
        "python": sys.version,
        "versions": {name: importlib.metadata.version(name) for name in ["openai", "numpy"]},
        "variant_files": [],
    }
    manifest_path = output_dir / "manifest.json"
    if args.resume:
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("generator_provider", "generator_model", "generator_temperature",
                    "query_count", "selected_variants", "queries_sha256", "index_dir",
                    "index_files_sha256"):
            if existing_manifest.get(key) != manifest.get(key):
                raise SystemExit(f"Resume refused: manifest field {key!r} differs from this run.")
        manifest = existing_manifest
        manifest["status"] = "running"
    else:
        manifest["status"] = "running"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    query_set = {c.get("query") for c in consultas}
    completed_total = 0
    for name, _ in variantes:
        checkpoint = output_dir / f"ablacion_{name}.jsonl"
        final_output = output_dir / f"ablacion_{name}.json"
        if checkpoint.is_file():
            completed_total += sum(1 for line in checkpoint.open(encoding="utf-8") if line.strip())
        elif final_output.is_file():
            completed_total += len(json.loads(final_output.read_text(encoding="utf-8")))

    for nombre, fn in variantes:
        print(f"\n{'='*60}\nVARIANTE: {nombre}")
        checkpoint_path = output_dir / f"ablacion_{nombre}.jsonl"
        out_path = output_dir / f"ablacion_{nombre}.json"
        salida_por_query = {}
        if checkpoint_path.is_file():
            for line in checkpoint_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    q_saved = row.get("query")
                    if q_saved not in query_set or q_saved in salida_por_query:
                        raise SystemExit(f"Invalid/duplicate query in checkpoint {checkpoint_path}")
                    salida_por_query[q_saved] = row
        elif out_path.is_file():
            saved_rows = json.loads(out_path.read_text(encoding="utf-8"))
            salida_por_query = {row["query"]: row for row in saved_rows}
            if len(salida_por_query) != len(saved_rows):
                raise SystemExit(f"Duplicate queries in completed output {out_path}")
        if len(salida_por_query) == len(consultas):
            print(f"  [RECUPERADO] {len(salida_por_query)}/{len(consultas)} ya completadas")
        for query_index, c in enumerate(consultas, start=1):
            q      = c["query"]
            if q in salida_por_query:
                continue
            if nombre == "V4_completo":
                route = route_query(q)
                if route["is_in_domain"]:
                    structured = resolve_structured_answer(q, route["category"], indexed_documents)
                    chunks = structured["contexts"] if structured else retrieve_with_global_fallback(q, route["category"], top_k=5)
                    resp = structured or generate_response(q, chunks)
                else:
                    chunks, resp = [], generate_response(q, [])
            elif nombre == "V5_hibrido_sin_extractores":
                # Igual que V4 pero sin resolve_structured_answer: ejerce el camino
                # de respaldo (FAISS + BM25 + RRF + reranker + generador).
                route = route_query(q)
                if route["is_in_domain"]:
                    chunks = retrieve_with_global_fallback(q, route["category"], top_k=5)
                    resp = generate_response(q, chunks)
                else:
                    chunks, resp = [], generate_response(q, [])
            else:
                chunks = fn(q)
                resp = generate_response(q, chunks)
            row = {
                "query":    q,
                "contexts": [ch["text"] for ch in chunks],
                "answer":   resp["answer"],
                "generator": resp.get("generator", f"{config['provider']}/{config['model']}"),
                "id": c.get("id", query_index),
                "category": c.get("category", c.get("categoria_correcta", "")),
            }
            with checkpoint_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            salida_por_query[q] = row
            completed_total += 1
            manifest.update({"status": "running", "current_variant": nombre,
                             "completed_rows_current_variant": len(salida_por_query),
                             "completed_rows_total": completed_total})
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  [OK {len(salida_por_query)}/{len(consultas)}] '{q[:50]}' ({len(chunks)} chunks)", flush=True)

        salida = [salida_por_query[c["query"]] for c in consultas]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(salida, f, ensure_ascii=False, indent=2)
        print(f"[GUARDADO] {out_path}")
        variant_record = {
            "name": nombre,
            "path": out_path.name,
            "sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
            "rows": len(salida),
        }
        manifest["variant_files"] = [record for record in manifest.get("variant_files", [])
                                     if record.get("name") != nombre] + [variant_record]
        manifest.pop("current_variant", None)
        manifest.pop("completed_rows_current_variant", None)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    manifest["status"] = "generation_complete"
    manifest["completed_rows_total"] = sum(len(json.loads((output_dir / f"ablacion_{name}.json").read_text(encoding="utf-8")))
                                            for name, _ in variantes)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] Evalúa los resultados de {output_dir} con run_ragas.py.")


if __name__ == "__main__":
    main()
