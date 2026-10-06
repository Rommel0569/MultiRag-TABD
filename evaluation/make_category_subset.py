"""Select deterministic review queries while retaining their original IDs."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("evaluation/queries_500_candidates.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-category", type=int, default=5)
    parser.add_argument("--categories", nargs="+", default=["VACANTES", "TEMARIO", "REGLAMENTO"])
    args = parser.parse_args()
    bank = json.loads(args.input.read_text(encoding="utf-8"))
    categories = [category.upper() for category in args.categories]
    selected = []
    for category in categories:
        rows = [row for row in bank["consultas"] if row.get("categoria_correcta") == category]
        if len(rows) < args.per_category:
            raise ValueError(f"Solo {len(rows)} consultas para {category}")
        selected.extend(rows[:args.per_category])
    output = dict(bank)
    output["consultas"] = selected
    output["subset_note"] = (f"First {args.per_category} stable examples from each requested category; "
                             "candidate OCR references remain unvalidated. Original item IDs retained.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"count": len(selected), "categories": {c: args.per_category for c in categories},
                      "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
