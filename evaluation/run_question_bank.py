"""Run one architecture on a query bank with local Ollama generation.

Writes to a unique run directory with per-query JSONL checkpoints. Candidate
answers/references remain exploratory until human-verified against source PDFs.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

LATENCY_FIELDS_MS = (
    "cache_lookup", "router", "structured_lookup", "out_of_domain_response",
    "retrieval_total", "faiss_dense_search",
    "bm25_lexical_search", "rrf_fusion", "cross_encoder_rerank",
    "retriever_article_anchor_lookup", "retrieval_anchor_check",
    "answer_generation",
)
TOP_LEVEL_LATENCY_FIELDS = (
    "cache_lookup", "router", "structured_lookup", "out_of_domain_response",
    "retrieval_total", "answer_generation",
)
RETRIEVAL_LATENCY_FIELDS = (
    "faiss_dense_search", "bm25_lexical_search", "rrf_fusion",
    "cross_encoder_rerank", "retriever_article_anchor_lookup", "retrieval_anchor_check",
)
LATENCY_SCHEMA = "stage_breakdown_ms_v2"


def _elapsed_ms(start_ns):
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def _timed_call(timings, field, function, *args, **kwargs):
    started = time.perf_counter_ns()
    try:
        return function(*args, **kwargs)
    finally:
        timings[field] += _elapsed_ms(started)


def _summary_stats(values):
    values = sorted(float(x) for x in values)
    if not values:
        return {"n": 0, "mean": None, "median": None, "p95": None}
    return {
        "n": len(values),
        "mean": round(sum(values) / len(values), 3),
        "median": round((values[(len(values) - 1) // 2] + values[len(values) // 2]) / 2, 3),
        "p95": round(values[max(0, math.ceil(.95 * len(values)) - 1)], 3),
    }


def _latency_group_summary(rows):
    total_ms = [float(r.get("elapsed_seconds", 0) or 0) * 1000 for r in rows]
    denominator = sum(total_ms)
    top_level = {}
    for field in TOP_LEVEL_LATENCY_FIELDS:
        values = [float((r.get("latency_breakdown_ms") or {}).get(field, 0) or 0) for r in rows]
        result = _summary_stats(values)
        result["share_of_group_request_time_percent"] = round(100 * sum(values) / denominator, 3) if denominator else None
        top_level[field + "_ms"] = result
    retrieval_total = sum(float((r.get("latency_breakdown_ms") or {}).get("retrieval_total", 0) or 0) for r in rows)
    retrieval_components = {}
    for field in RETRIEVAL_LATENCY_FIELDS:
        values = [float((r.get("latency_breakdown_ms") or {}).get(field, 0) or 0) for r in rows]
        result = _summary_stats(values)
        result["share_of_retrieval_time_percent"] = round(100 * sum(values) / retrieval_total, 3) if retrieval_total else None
        retrieval_components[field + "_ms"] = result
    return {
        "rows": len(rows),
        "request_time_ms": _summary_stats(total_ms),
        "top_level_components_non_overlapping": top_level,
        "retrieval_components_nested_within_retrieval_total": retrieval_components,
    }


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", default=str(ROOT / "evaluation" / "queries_500_candidates.json"))
    parser.add_argument("--output-dir", default=None, help="Directorio nuevo; permite reanudar si contiene manifest compatible")
    parser.add_argument("--limit", type=int, default=None, help="Solo para smoke check; omitir para todas las consultas")
    parser.add_argument("--allow-unvalidated-candidates", action="store_true",
                        help="Obligatorio para usar candidatos OCR aún no validados")
    parser.add_argument("--model", default="llama3:8b")
    parser.add_argument("--variant", choices=("baseline", "three_phase"), default="three_phase",
                        help="baseline = global dense top-5; three_phase = route + hybrid retrieval + structured extraction")
    parser.add_argument("--pair-id", default=None,
                        help="Shared experiment label for paired baseline/three-phase runs")
    parser.add_argument("--index-dir", default=None,
                        help="Índice alternativo aislado; por defecto data/index baseline")
    args = parser.parse_args()

    queries_path = Path(args.queries).resolve()
    query_doc = json.loads(queries_path.read_text(encoding="utf-8"))
    candidates = query_doc.get("status") == "CANDIDATE_POOL_NOT_A_VALIDATED_BENCHMARK"
    if candidates and not args.allow_unvalidated_candidates:
        parser.error("El banco contiene referencias OCR no validadas; añade --allow-unvalidated-candidates solo para corrida exploratoria.")
    queries = query_doc["consultas"][:args.limit]

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out_dir = Path(args.output_dir).resolve() if args.output_dir else ROOT / "evaluation" / "runs" / f"ollama_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=args.output_dir is not None)
    result_path = out_dir / "answers.jsonl"
    manifest_path = out_dir / "manifest.json"
    index_dir = Path(args.index_dir or os.environ.get("CEPRUNSA_INDEX_DIR", ROOT / "data" / "index")).resolve()
    os.environ["CEPRUNSA_INDEX_DIR"] = str(index_dir)
    index_files = sorted(index_dir.glob("*"))
    if not index_files:
        parser.error(f"No se encontraron archivos de índice en {index_dir}.")
    input_manifest = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "ollama",
        "model": args.model,
        "temperature": 0.1,
        "router_model": args.model if args.variant == "three_phase" else None,
        "variant": args.variant,
        "pair_id": args.pair_id,
        "query_file": str(queries_path),
        "query_file_sha256": sha256(queries_path),
        "query_count_requested": len(queries),
        "query_references_unvalidated": candidates,
        "query_bank_status": query_doc.get("status"),
        "query_bank_warning": query_doc.get("warning"),
        "index_dir": str(index_dir),
        "index_files_sha256": {p.name: sha256(p) for p in index_files if p.is_file()},
        "pipeline_source_sha256": {
            name: sha256(ROOT / "app" / name)
            for name in ("llm.py", "router.py", "retriever.py", "structured_answers.py", "pipeline.py")
        },
        "cache_mode": "disabled for paired architecture comparison",
        "scope": "paired architecture comparison on identical questions/index/generator; references remain unvalidated",
        "latency_profile": {
            "schema": LATENCY_SCHEMA,
            "clock": "time.perf_counter_ns",
            "unit": "milliseconds per component; elapsed_seconds remains request-processing total",
            "startup_recorded_separately": True,
            "adds_model_or_network_calls": False,
        },
        "setup_sessions": [],
    }
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("query_file_sha256", "index_files_sha256", "pipeline_source_sha256", "model", "variant", "pair_id", "latency_profile"):
            if old.get(key) != input_manifest.get(key):
                parser.error(f"No se puede reanudar: el manifest no coincide en {key}.")
        input_manifest = old
    else:
        manifest_path.write_text(json.dumps(input_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Isolate cache writes from any project/article cache evidence.
    os.environ["CEPRUNSA_CACHE_MODE"] = "disabled"
    os.environ["CEPRUNSA_CACHE_DIR"] = str(out_dir / "cache")
    os.environ["CEPRUNSA_GENERATOR_PROVIDER"] = "ollama"
    os.environ["CEPRUNSA_GENERATOR_MODEL"] = args.model
    os.environ["CEPRUNSA_GENERATOR_TEMPERATURE"] = "0.1"
    os.environ["CEPRUNSA_ROUTER_MODEL"] = args.model
    setup_started = time.perf_counter()
    sys.path.insert(0, str(ROOT / "app"))
    from cache import search_cache
    from llm import generate_response
    from router import route_query
    from retriever import (CATEGORIES, dense_search, retrieve_with_global_fallback,
                           documents as indexed_documents)
    from structured_answers import resolve_structured_answer
    from pipeline import OUT_OF_DOMAIN_RESPONSE

    setup_session = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(time.perf_counter() - setup_started, 3),
        "scope": "application imports, local model initialization, and index loading",
    }
    input_manifest.setdefault("setup_sessions", []).append(setup_session)
    manifest_path.write_text(json.dumps(input_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def dense_global(query, top_k=5, timings=None):
        """V1 baseline: dense search over every category, one global top-k."""
        results = []
        for category in CATEGORIES:
            results.extend(_timed_call(timings, "faiss_dense_search", dense_search,
                                        query, category, top_k=top_k))
        results.sort(key=lambda doc: doc.get("score_dense", float("inf")))
        return results[:top_k]

    done = {}
    if result_path.exists():
        with result_path.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    item = json.loads(line)
                    done[item["id"]] = item
    mode = "a" if result_path.exists() else "w"
    with result_path.open(mode, encoding="utf-8") as stream:
        for pos, item in enumerate(queries, start=1):
            if item["id"] in done:
                continue
            q = item["query"]
            started_ns = time.perf_counter_ns()
            timings = {name: 0.0 for name in LATENCY_FIELDS_MS}
            out = {
                "id": item["id"], "query": q,
                "expected_category": item.get("categoria_correcta", item.get("category")),
                "expected_answer": item["ground_truth"],
                "source_pdf": item.get("source_pdf"), "source_page": item.get("source_page"),
                "evidence_quote": item.get("evidence_quote"),
                "validation_status": item.get("validation_status", item.get("reference_status")),
                "contexts": [], "answer": None, "predicted_category": None,
                "phase": None, "cache_hit": False, "error": None,
                "router_mode": None, "router_input_tokens": 0, "router_output_tokens": 0,
            }
            try:
                cached = _timed_call(timings, "cache_lookup", search_cache, q)
                if cached:
                    out.update(answer=cached["answer"], predicted_category=cached.get("category"),
                               phase="cache_hit", cache_hit=True, sources=cached.get("sources", []))
                elif args.variant == "baseline":
                    chunks = _timed_call(timings, "retrieval_total", dense_global,
                                         q, top_k=5, timings=timings)
                    generated = _timed_call(timings, "answer_generation", generate_response, q, chunks)
                    out.update(answer=generated["answer"], phase="baseline_global_dense_top5",
                               sources=generated.get("sources", []), tokens_used=generated.get("tokens_used", 0))
                    out["contexts"] = [{"text": c.get("text", ""), "source": c.get("source"),
                                        "page": c.get("page"), "category": c.get("category")}
                                       for c in chunks]
                else:
                    route = _timed_call(timings, "router", route_query, q)
                    out["predicted_category"] = route["category"]
                    out["router_input_tokens"] = route.get("input_tokens_used", 0)
                    out["router_output_tokens"] = route.get("output_tokens_used", 0)
                    raw_route = route.get("raw_response")
                    out["router_mode"] = raw_route if raw_route in {"explicit_intent_rule", "explicit_out_of_domain"} else "llm_classifier"
                    if not route["is_in_domain"]:
                        stage_started = time.perf_counter_ns()
                        out.update(answer=OUT_OF_DOMAIN_RESPONSE, phase="router_ood", sources=[])
                        timings["out_of_domain_response"] += _elapsed_ms(stage_started)
                    else:
                        structured = _timed_call(timings, "structured_lookup", resolve_structured_answer,
                                                 q, route["category"], indexed_documents)
                        if structured:
                            chunks = structured["contexts"]
                            if structured.get("structured_lookup") == "document_requirements":
                                generated = structured
                                phase = "structured_document_requirements_extract"
                            else:
                                generated = structured
                                phase = f"structured_{structured['structured_lookup']}"
                        else:
                            chunks = _timed_call(timings, "retrieval_total",
                                                 retrieve_with_global_fallback, q, route["category"],
                                                 top_k=5, timings=timings)
                            generated = _timed_call(timings, "answer_generation", generate_response, q, chunks)
                            phase = "hybrid_retrieval_generation"
                        out["contexts"] = [{"text": c.get("text", ""), "source": c.get("source"),
                                            "page": c.get("page"), "category": c.get("category")}
                                           for c in chunks]
                        out.update(answer=generated["answer"], phase=phase,
                                   sources=generated.get("sources", []), tokens_used=generated.get("tokens_used", 0))
                out["route_correct"] = (out["predicted_category"] == out["expected_category"]
                                         if args.variant == "three_phase" else None)
            except Exception as exc:  # checkpoint failures as well; continue the bank
                out["error"] = f"{type(exc).__name__}: {exc}"
                out["route_correct"] = False
            out["elapsed_seconds"] = round((time.perf_counter_ns() - started_ns) / 1_000_000_000, 3)
            out["latency_breakdown_ms"] = {name: round(value, 3) for name, value in timings.items()}
            stream.write(json.dumps(out, ensure_ascii=False) + "\n")
            stream.flush()
            print(f"[{pos}/{len(queries)}] id={item['id']} route={out.get('predicted_category')} phase={out.get('phase')} error={bool(out['error'])}", flush=True)

    rows = list(done.values())
    with result_path.open(encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    completed = sum(not r.get("error") for r in rows)
    routed_rows = [r for r in rows if r.get("route_correct") is not None]
    route_ok = sum(bool(r.get("route_correct")) for r in routed_rows)
    profiled_rows = [r for r in rows if isinstance(r.get("latency_breakdown_ms"), dict)]
    latency_summary = _latency_group_summary(profiled_rows)
    router_modes = Counter(r.get("router_mode") for r in profiled_rows if r.get("router_mode"))
    latency_by_category = {
        str(category): _latency_group_summary([r for r in profiled_rows if r.get("expected_category") == category])
        for category in sorted({r.get("expected_category") for r in profiled_rows if r.get("expected_category")})
    }
    latency_by_phase = {
        str(phase): _latency_group_summary([r for r in profiled_rows if r.get("phase") == phase])
        for phase in sorted({r.get("phase") for r in profiled_rows if r.get("phase")})
    }
    summary = {
        "requested": len(queries), "completed_without_runtime_error": completed,
        "errors": len(rows) - completed,
        "variant": args.variant,
        "pair_id": args.pair_id,
        "route_correct_count": route_ok if routed_rows else None,
        "route_accuracy_on_completed": round(route_ok / max(len(routed_rows), 1), 4) if routed_rows else None,
        "latency_profile_schema": LATENCY_SCHEMA,
        "latency_profiled_rows": len(profiled_rows),
        "latency_overall": latency_summary,
        "latency_by_expected_category": latency_by_category,
        "latency_by_phase": latency_by_phase,
        "router_mode_counts": dict(router_modes),
        "router_tokens": {
            "input_sum": sum(int(r.get("router_input_tokens", 0) or 0) for r in profiled_rows),
            "output_sum": sum(int(r.get("router_output_tokens", 0) or 0) for r in profiled_rows),
        },
        "setup_sessions": input_manifest.get("setup_sessions", []),
        "latency_backfill": input_manifest.get("latency_backfill"),
        "metric_warning": input_manifest.get("query_bank_warning") or "Answer correctness requires source review or independent judging.",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] {summary}")
    print(f"[OUTPUT] {out_dir}")


if __name__ == "__main__":
    main()
