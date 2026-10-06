"""Promote the 500-candidate worksheet only after every row is reviewed."""
import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("worksheet", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"El destino ya existe y se protege contra sobrescritura: {args.output}")
    with args.worksheet.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    pending = [row["id"] for row in rows if row.get("review_status", "").strip().casefold() != "verified"]
    missing = [row["id"] for row in rows if not row.get("verified_answer", "").strip()]
    if pending or missing:
        parser.error(f"Promoción bloqueada: {len(pending)} filas no verificadas y {len(missing)} sin respuesta verificada. No se generó output.")
    queries = []
    for row in rows:
        queries.append({
            "id": int(row["id"]),
            "query": row["query"].strip(),
            "categoria_correcta": row["categoria_correcta"].strip(),
            "ground_truth": row["verified_answer"].strip(),
            "source_pdf": row["source_pdf"].strip() or None,
            "source_page": int(row["source_page"]) if row["source_page"].strip() else None,
            "evidence_quote": row["evidence_quote"].strip(),
            "validation_status": "human_verified",
            "reviewer_notes": row.get("reviewer_notes", "").strip(),
        })
    if len({item["query"].casefold() for item in queries}) != len(queries):
        parser.error("Promoción bloqueada: hay preguntas duplicadas.")
    result = {
        "status": "HUMAN_VALIDATED_BENCHMARK",
        "total": len(queries),
        "validation_method": "All rows marked verified in the accompanying human-review worksheet.",
        "consultas": queries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Validated set written to {args.output} ({len(queries)} questions)")


if __name__ == "__main__":
    main()
