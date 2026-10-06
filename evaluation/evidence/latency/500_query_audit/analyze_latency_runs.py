"""Read-only audit of archived latency runs; writes a reproducible audit bundle."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RUNS = ROOT / "evaluation" / "evidence" / "answer_runs"
RUN_NAMES = [
    "baseline_v9",
    "three_phase_final_latency",
]
PRIMARY_BASELINE = "baseline_v9"
PRIMARY_SYSTEM = "three_phase_final_latency"
COMPONENT_LOG = ROOT / "evaluation" / "resultados_latencia.txt"
COMPONENT_SCRIPT = ROOT / "evaluation" / "profile_latency.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if p == 0.50:
        return statistics.median(values)
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def stats(values: list[float]) -> dict:
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return {
        "n": len(vals),
        "mean_s": statistics.mean(vals) if vals else None,
        "stddev_s_population": statistics.pstdev(vals) if len(vals) > 1 else (0.0 if vals else None),
        "min_s": min(vals) if vals else None,
        "p50_s": percentile(vals, 0.50),
        "p90_s": percentile(vals, 0.90),
        "p95_s": percentile(vals, 0.95),
        "p99_s": percentile(vals, 0.99),
        "max_s": max(vals) if vals else None,
    }


def read_run(name: str) -> tuple[dict, list[dict], dict]:
    d = RUNS / name
    manifest_path = d / "manifest.json"
    answers_path = d / "answers.jsonl"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in answers_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    valid = [r for r in rows if not r.get("error") and r.get("elapsed_seconds") is not None]
    summary = {
        "run_name": name,
        "manifest_sha256": sha256(manifest_path),
        "answers_sha256": sha256(answers_path),
        "created_utc": manifest.get("created_utc"),
        "variant": manifest.get("variant"),
        "pair_id": manifest.get("pair_id"),
        "model": manifest.get("model"),
        "temperature": manifest.get("temperature"),
        "cache_mode": manifest.get("cache_mode"),
        "index_dir": manifest.get("index_dir"),
        "query_file_sha256": manifest.get("query_file_sha256"),
        "index_files_sha256": manifest.get("index_files_sha256"),
        "pipeline_source_sha256": manifest.get("pipeline_source_sha256"),
        "query_references_unvalidated": manifest.get("query_references_unvalidated"),
        "rows": len(rows),
        "errors": sum(bool(r.get("error")) for r in rows),
        "phase_counts": dict(Counter(r.get("phase") for r in rows)),
        "category_counts": dict(Counter(r.get("expected_category") for r in rows)),
        "tokens_used_sum": sum(int(r.get("tokens_used", 0) or 0) for r in rows),
        "tokens_used_nonzero_rows": sum(int(r.get("tokens_used", 0) or 0) > 0 for r in rows),
        "elapsed_all": stats([float(r["elapsed_seconds"]) for r in valid]),
        "elapsed_in_domain": stats([float(r["elapsed_seconds"]) for r in valid if r.get("expected_category") != "FUERA_DE_DOMINIO"]),
        "elapsed_ood": stats([float(r["elapsed_seconds"]) for r in valid if r.get("expected_category") == "FUERA_DE_DOMINIO"]),
        "elapsed_excluding_first_row": stats([float(r["elapsed_seconds"]) for r in valid if r.get("id") != (rows[0].get("id") if rows else None)]),
    }
    return manifest, rows, summary


def old_component_profile() -> dict:
    raw = COMPONENT_LOG.read_bytes()
    encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8"
    text = raw.decode(encoding, errors="replace")
    # The persisted console table contains rounded mean, population SD, and share.
    names = ["enrutador", "densa_faiss", "lexica_bm25", "fusion_rrf", "rerank_crossenc", "generacion_llm", "total"]
    found = {}
    for name in names:
        match = re.search(rf"^{re.escape(name)}\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)%", text, re.M)
        if match:
            found[name] = {"mean_s_rounded": float(match.group(1)), "stddev_s_rounded": float(match.group(2)), "share_percent_rounded": float(match.group(3))}
    ok_count = len(re.findall(r"^\[OK\] '[^\n]*' -> total", text, re.M))
    skip_count = len(re.findall(r"^\[SKIP\]", text, re.M))
    return {"log_path": str(COMPONENT_LOG), "log_sha256": sha256(COMPONENT_LOG), "log_encoding": encoding, "script_path": str(COMPONENT_SCRIPT), "script_sha256": sha256(COMPONENT_SCRIPT), "ok_rows": ok_count, "skipped_ood_rows": skip_count, "components": found}


def main() -> None:
    loaded = {}
    run_summaries = []
    for name in RUN_NAMES:
        manifest, rows, summary = read_run(name)
        loaded[name] = (manifest, {r["id"]: r for r in rows})
        run_summaries.append(summary)

    base_manifest, base_rows = loaded[PRIMARY_BASELINE]
    system_manifest, system_rows = loaded[PRIMARY_SYSTEM]
    shared_ids = sorted(set(base_rows) & set(system_rows))
    paired = []
    for qid in shared_ids:
        b, s = base_rows[qid], system_rows[qid]
        paired.append({
            "id": qid,
            "expected_category": b.get("expected_category"),
            "baseline_phase": b.get("phase"),
            "system_phase": s.get("phase"),
            "baseline_elapsed_seconds_rounded": b.get("elapsed_seconds"),
            "three_phase_elapsed_seconds_rounded": s.get("elapsed_seconds"),
            "baseline_minus_three_phase_seconds": round(float(b.get("elapsed_seconds", 0)) - float(s.get("elapsed_seconds", 0)), 3),
            "baseline_tokens_used": b.get("tokens_used", 0),
            "three_phase_tokens_used": s.get("tokens_used", 0),
        })

    category_rows = []
    cats = sorted({r.get("expected_category") for r in base_rows.values()})
    for cat in cats:
        bvals = [float(r["elapsed_seconds"]) for r in base_rows.values() if r.get("expected_category") == cat and not r.get("error")]
        svals = [float(r["elapsed_seconds"]) for r in system_rows.values() if r.get("expected_category") == cat and not r.get("error")]
        diffs = [float(base_rows[qid]["elapsed_seconds"]) - float(system_rows[qid]["elapsed_seconds"]) for qid in shared_ids if base_rows[qid].get("expected_category") == cat]
        category_rows.append({"category": cat, "n": len(diffs), "baseline_mean_s": statistics.mean(bvals), "baseline_p50_s": statistics.median(bvals), "baseline_p95_s": percentile(bvals, .95), "three_phase_mean_s": statistics.mean(svals), "three_phase_p50_s": statistics.median(svals), "three_phase_p95_s": percentile(svals, .95), "paired_mean_difference_s": statistics.mean(diffs), "paired_median_difference_s": statistics.median(diffs)})

    bvals = [float(r["elapsed_seconds"]) for r in base_rows.values()]
    svals = [float(r["elapsed_seconds"]) for r in system_rows.values()]
    paired_diffs = [float(base_rows[qid]["elapsed_seconds"]) - float(system_rows[qid]["elapsed_seconds"]) for qid in shared_ids]
    source_hash_diffs = [name for name in sorted(set(base_manifest.get("pipeline_source_sha256", {})) | set(system_manifest.get("pipeline_source_sha256", {}))) if base_manifest.get("pipeline_source_sha256", {}).get(name) != system_manifest.get("pipeline_source_sha256", {}).get(name)]
    old_profile = old_component_profile()

    audit = {
        "audit_created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_script": str(Path(__file__).resolve()),
        "analysis_script_sha256": sha256(Path(__file__).resolve()),
        "primary_pair": {"baseline": PRIMARY_BASELINE, "three_phase": PRIMARY_SYSTEM},
        "primary_pair_checks": {
            "matching_pair_id": base_manifest.get("pair_id") == system_manifest.get("pair_id"),
            "matching_query_sha256": base_manifest.get("query_file_sha256") == system_manifest.get("query_file_sha256"),
            "matching_index_hashes": base_manifest.get("index_files_sha256") == system_manifest.get("index_files_sha256"),
            "matching_pipeline_source_hashes": base_manifest.get("pipeline_source_sha256") == system_manifest.get("pipeline_source_sha256"),
            "differing_pipeline_files": source_hash_diffs,
            "shared_question_ids": len(shared_ids),
            "baseline_refs_unvalidated_flag": base_manifest.get("query_references_unvalidated"),
            "three_phase_refs_unvalidated_flag": system_manifest.get("query_references_unvalidated"),
        },
        "primary_latency": {
            "baseline": stats(bvals),
            "three_phase": stats(svals),
            "paired_baseline_minus_three_phase": stats(paired_diffs),
            "paired_rows_three_phase_faster": sum(d > 0 for d in paired_diffs),
            "paired_rows_equal": sum(d == 0 for d in paired_diffs),
            "paired_rows_three_phase_slower": sum(d < 0 for d in paired_diffs),
            "baseline_token_rows": sum(int(r.get("tokens_used", 0) or 0) > 0 for r in base_rows.values()),
            "three_phase_token_rows": sum(int(r.get("tokens_used", 0) or 0) > 0 for r in system_rows.values()),
        },
        "per_category": category_rows,
        "older_27_query_component_profile": old_profile,
        "runs": run_summaries,
        "interpretation_limits": [
            "The two primary 500-query runs share the query-bank hash, index hashes, pair label, model setting, and disabled-cache mode, but pipeline.py and structured_answers.py source hashes differ.",
            "Each architecture timing is one run, collected sequentially rather than interleaved or repeated under randomized order; paired per-question differences are descriptive and are not a causal or significance test.",
            "Per-query elapsed_seconds are rounded to milliseconds and measure the runner's request interval, not cold-start/model-loading latency.",
            "The expanded three-phase run resolved all 450 in-domain rows through structured-answer phases and all 50 OOD rows through the OOD phase; generated-answer tokens_used was zero for every row. The baseline used the global dense top-5 plus Llama generator for all 500 rows.",
            "The run manifests mark the query references as unvalidated OCR candidates. That flag does not invalidate timing, but these runs cannot independently support answer-accuracy claims.",
            "Router token usage and per-component time were not recorded in the 500-query JSONL. The 24.1% router share belongs only to the older 27 successful in-domain profile, which timed a different all-components path.",
        ],
    }

    (OUT / "latency_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "latency_runs_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["run_name", "created_utc", "variant", "pair_id", "model", "temperature", "rows", "errors", "query_references_unvalidated", "mean_s", "stddev_s", "p50_s", "p90_s", "p95_s", "p99_s", "max_s", "tokens_used_sum", "tokens_used_nonzero_rows", "phase_counts", "manifest_sha256", "answers_sha256"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in run_summaries:
            row = {k: s.get(k) for k in fields if k in s}
            row.update({"mean_s": s["elapsed_all"]["mean_s"], "stddev_s": s["elapsed_all"]["stddev_s_population"], "p50_s": s["elapsed_all"]["p50_s"], "p90_s": s["elapsed_all"]["p90_s"], "p95_s": s["elapsed_all"]["p95_s"], "p99_s": s["elapsed_all"]["p99_s"], "max_s": s["elapsed_all"]["max_s"], "phase_counts": json.dumps(s["phase_counts"], ensure_ascii=False)})
            writer.writerow(row)
    with (OUT / "latency_by_category.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(category_rows[0]))
        writer.writeheader()
        writer.writerows(category_rows)
    with (OUT / "latency_paired_rows.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(paired[0]))
        writer.writeheader()
        writer.writerows(paired)

    p = audit["primary_latency"]
    checks = audit["primary_pair_checks"]
    comp = old_profile["components"]
    lines = [
        "LATENCY AUDIT — archived CEPRUNSA Multi-RAG runs",
        f"Generated UTC: {audit['audit_created_utc']}",
        "Purpose: quantify what can be established from saved latency artifacts without rerunning answer generation.",
        "",
        "PRIMARY 500-QUERY PAIR",
        f"Baseline run: {PRIMARY_BASELINE}",
        f"Three-phase run: {PRIMARY_SYSTEM}",
        f"Same pair_id: {checks['matching_pair_id']}; same query SHA-256: {checks['matching_query_sha256']}; same index file hashes: {checks['matching_index_hashes']}; same application source hashes: {checks['matching_pipeline_source_hashes']}.",
        f"Application source files with different recorded hashes: {', '.join(checks['differing_pipeline_files']) or 'none'}.",
        f"Shared query IDs: {checks['shared_question_ids']}; cache disabled in both manifests; both manifests flag OCR candidate references as unvalidated: {checks['baseline_refs_unvalidated_flag']} / {checks['three_phase_refs_unvalidated_flag']}.",
        "",
        "End-to-end request latency (seconds; one run per implementation; milliseconds-rounded JSONL values):",
        f"Baseline: n={p['baseline']['n']}, mean={p['baseline']['mean_s']:.4f}, population SD={p['baseline']['stddev_s_population']:.4f}, median={p['baseline']['p50_s']:.4f}, p90={p['baseline']['p90_s']:.4f}, p95={p['baseline']['p95_s']:.4f}, p99={p['baseline']['p99_s']:.4f}, max={p['baseline']['max_s']:.4f}.",
        f"Three-phase: n={p['three_phase']['n']}, mean={p['three_phase']['mean_s']:.4f}, population SD={p['three_phase']['stddev_s_population']:.4f}, median={p['three_phase']['p50_s']:.4f}, p90={p['three_phase']['p90_s']:.4f}, p95={p['three_phase']['p95_s']:.4f}, p99={p['three_phase']['p99_s']:.4f}, max={p['three_phase']['max_s']:.4f}.",
        f"Paired baseline-minus-three-phase difference: mean={p['paired_baseline_minus_three_phase']['mean_s']:.4f}s, median={p['paired_baseline_minus_three_phase']['p50_s']:.4f}s; three-phase faster in {p['paired_rows_three_phase_faster']}/{checks['shared_question_ids']} rows, equal in {p['paired_rows_equal']}, slower in {p['paired_rows_three_phase_slower']}.",
        f"Rows with nonzero recorded answer tokens: baseline={p['baseline_token_rows']}; three-phase={p['three_phase_token_rows']}.",
        "",
        "Interpretation of the selected 500-query runs:",
        "The baseline used global dense top-5 retrieval followed by Llama generation for all 500 queries. The selected three-phase run reports 175 structured_table_cell, 145 structured_topic_section_extract, 105 structured_article_extract, 25 structured_table_date_cell, and 50 router_ood rows. Thus all 450 in-domain answers bypassed answer generation; generated-answer tokens_used is zero. These values compare the end-to-end implementations as logged, but do not isolate the router or establish the speed of an LLM-generated-answer version of Multi-RAG.",
        "Although query and index hashes match, pipeline.py and structured_answers.py hashes differ between the selected baseline and three-phase runs. Runs were not repeated or randomized/interleaved. Therefore these are descriptive measurements, not a controlled causal latency claim or a statistical test. Startup/model loading is excluded, and JSONL elapsed_seconds is rounded to 0.001 s.",
        "The 500-run manifests also set query_references_unvalidated=true. This does not affect timing, but these runs should not be presented as independent accuracy validation.",
        "",
        "OLDER COMPONENT PROFILE (27 in-domain rows; 3 OOD rows skipped)",
        f"Source log: {COMPONENT_LOG.relative_to(ROOT)} (SHA-256 {old_profile['log_sha256']}). Profiler source: {COMPONENT_SCRIPT.relative_to(ROOT)} (SHA-256 {old_profile['script_sha256']}).",
        f"Timed rows: {old_profile['ok_rows']} successful, {old_profile['skipped_ood_rows']} OOD skipped. The profiler separately timed router, FAISS, BM25, RRF, cross-encoder reranking, Llama generation, and total; model/index initialization occurs before per-query timers.",
    ]
    for name, values in comp.items():
        lines.append(f"{name}: mean {values['mean_s_rounded']:.2f}s; SD {values['stddev_s_rounded']:.2f}s; {values['share_percent_rounded']:.1f}% of reported total.")
    lines += [
        "",
        "The reported 24.1% router share therefore applies only to this earlier 27-query profile and its specific pipeline. It is not a component share measured on the expanded 500-query run.",
        "",
        "ADDITIONAL SAVED THREE-PHASE RUNS",
        "latency_runs_summary.csv lists the other saved 500-query runs. They are retained for traceability, not pooled as repeats: their manifests record code-hash changes and/or different index versions.",
        "",
        "REPRODUCE",
        "From the project root, run: .\\venv\\Scripts\\python.exe evaluation\\revision_20261001\\latency_audit\\analyze_latency_runs.py",
        "Outputs: latency_audit.json, latency_runs_summary.csv, latency_by_category.csv, latency_paired_rows.csv, and this file.",
        "",
        "Manuscript consequence: report the 27-query component profile explicitly as preliminary, or obtain a component-timed profile under the exact final 500-query implementation. The Methodology must also state that the selected expanded three-phase run resolved in-domain questions through structured extraction rather than Llama answer generation. Do not label the aggregate difference as an isolated router effect.",
    ]
    (OUT / "latency_audit.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote audit bundle to {OUT}")
    print(f"[PRIMARY] baseline mean={p['baseline']['mean_s']:.4f}s; three-phase mean={p['three_phase']['mean_s']:.4f}s; paired difference={p['paired_baseline_minus_three_phase']['mean_s']:.4f}s")
    print(f"[LIMIT] same code hashes={checks['matching_pipeline_source_hashes']}; paired ids={checks['shared_question_ids']}; v4 generated-token rows={p['three_phase_token_rows']}")


if __name__ == "__main__":
    main()
