"""Create a separate, source-linked pool of OCR-derived QA candidates.

These are NOT human-validated gold answers and must not be presented as a
benchmark until each answer has been checked against the rendered source PDF.
The source set and original evaluation/queries.json are left untouched.
"""
import hashlib
import json
import re
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "evaluation" / "revision_20260929"
OUT = ROOT / "evaluation" / "queries_500_candidates.json"
CSV_OUT = ROOT / "evaluation" / "queries_500_human_review.csv"
TARGETS = {"CRONOGRAMA": 25, "VACANTES": 175, "TEMARIO": 145,
           "REGLAMENTO": 105, "FUERA_DE_DOMINIO": 50}
DOCS = {
    "CRONOGRAMA": ("CRONOGRAMA DE ADMISIÓN 2027.pdf", "textract_full/cronograma_v2"),
    "VACANTES": ("CUADRO DE VACANTES 2027.pdf", "textract_v3"),
    "TEMARIO": ("TEMARIO Y MATRIZ DE EVALUACIÓN 2027.pdf", "textract_full/temario"),
    "REGLAMENTO": ("REGLAMENTO DE ADMISIÓN 2027.pdf", "textract_full/reglamento"),
}


def load_pages(category):
    filename, relative = DOCS[category]
    folder = (REV / relative).resolve()
    pages = []
    for path in sorted(folder.glob("page_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        page = int(re.search(r"page_(\d+)", path.stem).group(1))
        pages.append((page, data))
    return filename, pages


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip(" |\t\r\n")


def acceptable(text, low=28, high=1200):
    if not low <= len(text) <= high or len(text.split()) < 5:
        return False
    if text.count("\ufffd") / max(1, len(text)) > 0.01:
        return False
    letters = sum(ch.isalpha() for ch in text)
    return letters / max(1, len(text)) >= 0.45


def candidate(category, source, page, question, answer, evidence=None):
    answer = clean(answer)
    numeric_value = bool(re.fullmatch(r"[0-9][0-9.,]*", answer))
    if not acceptable(answer, low=18) and not numeric_value:
        return None
    return {
        "query": question,
        "categoria_correcta": category,
        "ground_truth": answer,
        "source_pdf": source,
        "source_page": page,
        "evidence_quote": clean(evidence or answer),
        "validation_status": "unreviewed_ocr_candidate",
        "paraphrase_group": None,
    }


def vacancy_candidates():
    source, pages = load_pages("VACANTES")
    result = []
    fields = [(3, "vacantes ordinarias de Fase I"), (4, "vacantes ordinarias de Fase II"),
              (5, "vacantes ordinarias totales"), (6, "vacantes CEPRUNSA de Fase I"),
              (7, "vacantes CEPRUNSA de Fase II"), (8, "vacantes CEPRUNSA del Ciclo Quintos"),
              (9, "vacantes CEPRUNSA totales"), (13, "vacantes del total general")]
    for page, data in pages:
        for table in data.get("tables", []):
            rows = {}
            for cell in table.get("cells", []):
                rows.setdefault(cell.get("row", -1), {})[cell.get("column", -1)] = clean(cell.get("text"))
            title_text = clean(data.get("page_text", "").splitlines()[0] if data.get("page_text") else "").upper()
            is_extraordinary = "EXTRAORDINARIO" in title_text
            if is_extraordinary:
                headers = rows.get(1, {})
                first_data_row = 2
                fields_for_page = [(col, value) for col, value in sorted(headers.items())
                                   if col > 2 and value]
            else:
                first_data_row = 3
                fields_for_page = [(3, "Fase I ordinaria"), (4, "Fase II ordinaria"),
                                   (5, "total por examen ordinario"), (6, "Fase I de CEPRUNSA"),
                                   (7, "Fase II de CEPRUNSA"), (8, "Ciclo Quintos de CEPRUNSA"),
                                   (9, "total por CEPRUNSA"), (13, "total general del proceso")]
            for row_id, cols in sorted(rows.items()):
                name = cols.get(2, "")
                if row_id < first_data_row or not name or any(
                    token in name.casefold() for token in
                    ("programa de estudios", "cuadro de vacantes", "subtotal", "total de vacantes", "total general")
                ):
                    continue
                row_evidence = " | ".join(value for _, value in sorted(cols.items()) if value)
                for col, label in fields_for_page:
                    value = cols.get(col, "")
                    if not value or value in {"-", "—"}:
                        continue
                    if is_extraordinary:
                        normalized_label = label.casefold()
                        if "total proceso extraordinario" in normalized_label:
                            q = f"¿Cuántas vacantes extraordinarias hay para {name} en total?"
                        else:
                            q = f"¿Cuántas vacantes extraordinarias hay para {name} por {label}?"
                    else:
                        phrase = {
                            3: "en el examen ordinario de Fase I",
                            4: "en el examen ordinario de Fase II",
                            5: "en total por examen ordinario",
                            6: "en CEPRUNSA Fase I",
                            7: "en CEPRUNSA Fase II",
                            8: "en el Ciclo Quintos de CEPRUNSA",
                            9: "en total por CEPRUNSA",
                            13: "sumando todo el proceso de admisión",
                        }[col]
                        q = f"¿Cuántas vacantes hay para {name} {phrase}?"
                    item = candidate("VACANTES", source, page, q, value, row_evidence)
                    if item:
                        result.append(item)
    return result


def table_cell_candidates(category):
    source, pages = load_pages(category)
    result = []
    seen = set()
    for page, data in pages:
        for table in data.get("tables", []):
            for cell in table.get("cells", []):
                answer = clean(cell.get("text"))
                if not acceptable(answer, low=55, high=1400):
                    continue
                key = answer.casefold()
                if key in seen:
                    continue
                seen.add(key)
                hint = " ".join(answer.split()[:5]).strip(".,:;() ")
                if category == "TEMARIO":
                    q = f"¿Qué temas entran sobre «{hint}»?"
                else:
                    q = f"¿Qué dato del cronograma aparece en la entrada que comienza «{hint}»?"
                item = candidate(category, source, page, q, answer)
                if item:
                    result.append(item)
    return result


def cronograma_line_candidates():
    source, pages = load_pages("CRONOGRAMA")
    result = []
    for page, data in pages:
        current_exam = None
        for raw in data.get("page_text", "").splitlines():
            line = clean(raw)
            heading = re.search(r"(?i)(EXAMEN\s+[A-ZÁÉÍÓÚÑ0-9 ]{3,50})", line)
            if heading and "|" not in line:
                current_exam = clean(heading.group(1))
                continue
            dates = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", line)
            if not current_exam or not dates or "|" not in line:
                continue
            event = clean(line.split("|", 1)[0])
            if not event:
                continue
            date_text = " al ".join(dates)
            answer = f"{current_exam}: {event} — {date_text}"
            if event.casefold().startswith("inscrip"):
                q = f"¿Hasta qué día me puedo inscribir para {current_exam}?"
                answer = f"{current_exam}: las inscripciones van del {date_text}"
            elif "conocimientos" in event.casefold():
                q = f"¿Qué día es el examen de conocimientos de {current_exam}?"
            elif "previa" in event.casefold():
                q = f"¿Qué día es la evaluación previa de {current_exam}?"
            elif "clases" in event.casefold():
                q = f"¿Cuándo empiezan las clases de {current_exam}?"
            else:
                q = f"¿Qué día es {event.lower()} para {current_exam}?"
            item = candidate("CRONOGRAMA", source, page, q, answer, line)
            if item:
                result.append(item)
    return unique(result)


def regulation_article_candidates():
    source, pages = load_pages("REGLAMENTO")
    result = []
    starts = re.compile(r"(?im)^\s*(Artículo|Articulo)\s+(\d{1,3})\s*[°º.]?\s*[:.\-]?\s*")
    seen_articles = set()
    for page, data in pages:
        text = data.get("page_text", "")
        matches = list(starts.finditer(text))
        for idx, match in enumerate(matches):
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = clean(text[match.start():end])
            number = match.group(2)
            if number in seen_articles or not acceptable(body, low=45, high=2400):
                continue
            seen_articles.add(number)
            q = f"¿Qué dice el artículo {number} del reglamento de admisión?"
            item = candidate("REGLAMENTO", source, page, q, body)
            if item:
                result.append(item)
    return result


def regulation_clause_candidates():
    source, pages = load_pages("REGLAMENTO")
    result = []
    seen = set()
    for page, data in pages:
        for raw in data.get("page_text", "").splitlines():
            line = clean(raw)
            if not acceptable(line, low=55, high=260):
                continue
            if not re.search(r"\b(deberá|deberán|podrá|podrán|prohíbe|impedid|requisit|inscrip|postul|examen|sancion|vacante|artículo|articulo)\b", line, re.I):
                continue
            key = line.casefold()
            if key in seen:
                continue
            seen.add(key)
            hint = " ".join(line.split()[:8]).strip(".,:;() ")
            q = f"En el reglamento, ¿qué dice sobre «{hint}»?"
            item = candidate("REGLAMENTO", source, page, q, line)
            if item:
                result.append(item)
    return result


def out_of_domain_candidates():
    questions = [
        "¿Qué restaurantes económicos recomiendas cerca de la UNSA?",
        "¿Qué cafeterías están abiertas ahora cerca de la universidad?",
        "¿Dónde puedo almorzar menú por menos de veinte soles en Arequipa?",
        "¿Cuál es el mejor lugar para comer rocoto relleno en Arequipa?",
        "¿Qué pizzería cerca del centro tiene delivery?",
        "¿Cómo estará el clima en Arequipa esta tarde?",
        "¿Va a llover mañana en Arequipa?",
        "¿Cuál es la temperatura actual en Lima?",
        "¿Qué ropa debería llevar para viajar a Cusco esta semana?",
        "¿Cómo estará el clima este fin de semana en Mollendo?",
        "¿Cuánto está el dólar hoy en Perú?",
        "¿A cuánto equivale 100 dólares en soles al cambio actual?",
        "¿Cuál fue el tipo de cambio del euro esta mañana?",
        "¿Conviene comprar dólares ahora?",
        "¿Cuál es el precio actual del bitcoin?",
        "¿Quién ganó el último partido de Melgar?",
        "¿A qué hora juega hoy la selección peruana?",
        "¿Cuál es la tabla de posiciones de la Liga 1?",
        "¿Cuándo juega Universitario contra Alianza Lima?",
        "¿Cómo quedó Perú en su último partido de fútbol?",
        "¿Qué ruta de bus me lleva desde el centro hasta el aeropuerto?",
        "¿Cuánto cuesta un taxi desde la UNSA hasta el terminal terrestre?",
        "¿Hay tráfico ahora en la avenida Independencia?",
        "¿Cuál es el horario del bus a Mollendo?",
        "¿Dónde compro una tarjeta para el transporte público?",
        "¿Qué puedo tomar para el dolor de garganta?",
        "¿Cuáles son los síntomas de la gripe?",
        "¿Qué clínica está de turno hoy en Arequipa?",
        "¿Necesito antibióticos para una infección?",
        "¿Cómo pido una cita médica en EsSalud?",
        "¿Qué ofertas de trabajo hay para programadores en Arequipa?",
        "¿Cómo preparo un currículum para buscar prácticas?",
        "¿Cuánto gana un ingeniero de software en Perú?",
        "¿Dónde puedo encontrar trabajo remoto?",
        "¿Qué preguntas hacen en una entrevista laboral?",
        "¿Cómo soluciono un error de sintaxis en Python?",
        "Explícame cómo crear una API con FastAPI.",
        "¿Qué laptop me recomiendas para programar?",
        "¿Cómo instalo Docker en Windows?",
        "Ayúdame a diseñar una base de datos para una tienda.",
        "¿Qué lugares turísticos debería visitar en Arequipa?",
        "¿Cuánto cuesta entrar al Monasterio de Santa Catalina?",
        "¿Qué hoteles recomiendas en el Valle del Colca?",
        "¿Cómo viajo desde Arequipa hasta Puno?",
        "¿Qué museos puedo visitar el domingo?",
        "Dame una receta sencilla de ají de gallina.",
        "¿Cuánto tiempo se hornea una torta de chocolate?",
        "¿Qué película de ciencia ficción me recomiendas?",
        "¿Quién ganó las elecciones municipales?",
        "¿Cuáles son las noticias principales de hoy?",
        "¿Qué significa la inflación y cómo afecta los precios?",
    ]
    answer = "Fuera de dominio: el sistema solo responde consultas sobre el proceso de admisión CEPRUNSA 2027 con los documentos oficiales disponibles."
    return [{
        "query": q,
        "categoria_correcta": "FUERA_DE_DOMINIO",
        "ground_truth": answer,
        "source_pdf": None,
        "source_page": None,
        "evidence_quote": "Definición del alcance del sistema; caso sintético de prueba del router, no derivado de un PDF.",
        "validation_status": "synthetic_scope_label_pending_review",
        "paraphrase_group": f"ood_{i // 5 + 1}",
    } for i, q in enumerate(questions, start=1)]


def unique(candidates):
    seen = set()
    output = []
    for item in candidates:
        key = (item["categoria_correcta"], item["query"].casefold(), item["ground_truth"].casefold())
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output


def main():
    pools = {
        "VACANTES": unique(vacancy_candidates()),
        "TEMARIO": unique(table_cell_candidates("TEMARIO")),
        "CRONOGRAMA": unique(cronograma_line_candidates()),
        "REGLAMENTO": unique(regulation_article_candidates() + regulation_clause_candidates()),
        "FUERA_DE_DOMINIO": unique(out_of_domain_candidates()),
    }
    insufficient = {k: (len(pools[k]), TARGETS[k]) for k in TARGETS if len(pools[k]) < TARGETS[k]}
    if insufficient:
        raise SystemExit(f"Insufficient candidate pool by category: {insufficient}")

    # Fixed source-order sampling is deterministic and keeps categories balanced.
    selected = []
    for category, target in TARGETS.items():
        selected.extend(pools[category][:target])
    for i, item in enumerate(selected, start=1):
        item["id"] = i
    manifest = {
        "status": "CANDIDATE_POOL_NOT_A_VALIDATED_BENCHMARK",
        "created_from": "AWS Textract page JSON outputs; exact PDF/page linked per item",
        "total": len(selected),
        "category_counts": TARGETS,
        "human_review_required": True,
        "warning": (
            "OCR-derived answers may contain transcription/table alignment errors. "
            "Do not report RAGAS scores from this set as scientific evidence until "
            "each answer is visually verified and the query set is reviewed for ambiguity/duplicates."
        ),
        "input_summary_sha256": hashlib.sha256((REV / "textract_full" / "FULL_RUN_SUMMARY.json").read_bytes()).hexdigest(),
        "consultas": selected,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    review_fields = ["id", "categoria_correcta", "query", "provisional_answer", "source_pdf",
                     "source_page", "evidence_quote", "verified_answer", "review_status", "reviewer_notes"]
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=review_fields)
        writer.writeheader()
        for item in selected:
            writer.writerow({
                "id": item["id"],
                "categoria_correcta": item["categoria_correcta"],
                "query": item["query"],
                "provisional_answer": item["ground_truth"],
                "source_pdf": item["source_pdf"],
                "source_page": item["source_page"],
                "evidence_quote": item["evidence_quote"],
                "verified_answer": "",
                "review_status": "pending",
                "reviewer_notes": "",
            })
    print(f"Wrote {len(selected)} candidate queries to {OUT}")
    print(f"Wrote human-review worksheet to {CSV_OUT}")
    print("Pools:", {k: len(v) for k, v in pools.items()})


if __name__ == "__main__":
    main()
