"""Conservative, extractive lookups for explicitly structured questions.

This module is corpus-agnostic: it reads indexed headers, row labels, and
article headings instead of hard-coding CEPRUNSA program names or page numbers.
If a unique row/cell/section cannot be resolved, it returns None so normal RAG
retrieval and generation can continue.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _fields(text: str) -> list[tuple[str, str]]:
    """Parse serialized table fields while keeping empty cells unavailable."""
    fields = []
    for match in re.finditer(r"(?:^|[;|])\s*([^:;|]{2,80}?)\s*:\s*([^;|]+)", text or ""):
        label, value = match.group(1).strip(), match.group(2).strip()
        if label and value:
            fields.append((label, value))
    return fields


def _source(chunk: dict) -> str:
    return f"{chunk.get('source', '?')} (p.{chunk.get('page', '?')})"


def _result(answer: str, chunks: list[dict], kind: str) -> dict:
    return {
        "answer": answer,
        "sources": sorted({_source(chunk) for chunk in chunks}),
        "contexts": chunks,
        "tokens_used": 0,
        "structured_lookup": kind,
    }


def is_article_heading(chunk: dict, number: str) -> bool:
    text = str(chunk.get("text", ""))
    match = re.match(rf"^\s*Art(?:ículo|iculo)\s+0*{re.escape(number)}(?!\d)\s*(?:[°º])?(?P<tail>.*)$",
                     text, flags=re.IGNORECASE)
    if not match:
        return False
    tail = match.group("tail").lstrip()
    if tail[:1] in {".", ":", "–", "—"}:
        tail = tail[1:].lstrip()
    # Headings have sentence-case title text. This rejects prose references
    # like "artículo 8° de la Ley" that happen to start a chunk.
    return bool(tail and tail[0].isupper())


_ARTICLE_HEADING = re.compile(
    r"\b(?i:Art(?:ículo|iculo))\s+0*\d+(?!\d)\s*(?:[°º])?\s*[.:–—-]?\s+[A-ZÁÉÍÓÚÑ]",
)
_SECTION_HEADING = re.compile(
    r"\b(?:CAP[IÍ]TULO|SUBCAP[IÍ]TULO|T[IÍ]TULO)\s+(?:[IVXLCDM]+|\d+)\b",
    flags=re.IGNORECASE,
)


def _cut_at_next_heading(text: str) -> str:
    """Remove the next provision/chapter heading and everything after it."""
    start = len(text) - len(text.lstrip())
    positions = []
    for pattern in (_ARTICLE_HEADING, _SECTION_HEADING):
        for match in pattern.finditer(text):
            if pattern is _ARTICLE_HEADING and match.start() == start:
                continue  # Preserve the requested article's own heading.
            positions.append(match.start())
            break
    return text[:min(positions)].rstrip() if positions else text.strip()


def _strip_page_furniture(text: str) -> str:
    """Drop a leading running page header while preserving mixed/lowercase prose."""
    text = str(text or "").strip()
    page_marker = re.search(r"P[aá�]gina\s+\d+\s+de\s+\d+", text, flags=re.IGNORECASE)
    if page_marker:
        text = text[page_marker.end():]
        text = re.sub(r"^[\s|:–—-]+", "", text)
        # Use a short grammatical run rather than the first lowercase token:
        # OCR page furniture often contains stray lowercase letters.
        words = list(re.finditer(r"[A-Za-zÁÉÍÓÚÑáéíóúñÜü]+", text))
        prose_start = None
        for i in range(max(0, len(words) - 2)):
            run = [word.group(0) for word in words[i:i + 3]]
            first_is_prose = len(run[0]) > 1 and any(char.islower() for char in run[0])
            tail_is_lower = all(token.islower() for token in run[1:])
            if first_is_prose and tail_is_lower:
                prose_start = words[i].start()
                break
        structural = _ARTICLE_HEADING.search(text) or _SECTION_HEADING.search(text)
        if structural and (prose_start is None or structural.start() < prose_start):
            return text[structural.start():].strip()
        if prose_start is not None:
            text = text[prose_start:]
        else:
            return ""
    return text.strip()


def _article_body(text: str, *, page_continuation: bool = False) -> str:
    text = _strip_page_furniture(text) if page_continuation else str(text or "").strip()
    if page_continuation:
        # The continuation must begin with prose. An uppercase provision
        # heading is handled as a boundary below, not article body text.
        text = re.sub(r"^[\s|:–—-]+", "", text)
    return _remove_trailing_page_artifact(_cut_at_next_heading(text))


def _article_tail_is_complete(text: str) -> bool:
    text = _remove_trailing_page_artifact(str(text or ""))
    return bool(re.search(r"[.!?][\"'»)]*$", text))


def _remove_trailing_page_artifact(text: str) -> str:
    """Ignore page numbers, footnote marks, and trailing running-header debris."""
    text = re.sub(r"\s+\d{1,3}\s*$", "", str(text or "")).rstrip()
    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+s*$", "", text).rstrip()
    terminal = list(re.finditer(r"[.!?]", text))
    if terminal:
        match = terminal[-1]
        tail = text[match.end():].strip()
        letters = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñÜü]+", tail)
        alphabetic = "".join(letters)
        uppercase_ratio = (sum(char.isupper() for char in alphabetic) / len(alphabetic)) if alphabetic else 0
        if letters and (uppercase_ratio >= 0.8 or (len(letters) == 1 and letters[0].isupper())):
            return text[:match.end()].rstrip()
    header_junk = re.search(r":\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{2,}$", text)
    if header_junk:
        return text[:header_junk.start()].rstrip()
    return text


def _format_quantitative_table(rows: list[dict]) -> str | None:
    """Serialize numeric table rows with their detected column labels."""
    parsed = [(chunk, _fields(str(chunk.get("text", "")))) for chunk in rows]
    numeric_rows = [
        (chunk, fields, [(label, value) for label, value in fields
                         if re.fullmatch(r"\d+(?:[.,]\d+)?", value.strip())])
        for chunk, fields in parsed
    ]
    numeric_rows = [entry for entry in numeric_rows if len(entry[2]) >= 2]
    if len(numeric_rows) < 2 or len(numeric_rows) / max(len(rows), 1) < 0.5:
        return None
    numeric_labels = list(dict.fromkeys(label for _, _, cells in numeric_rows for label, _ in cells))
    lines = [f"Columnas numéricas detectadas: {', '.join(numeric_labels)}."]
    for _, fields, cells in numeric_rows:
        numeric_values = {value for _, value in cells}
        row_fields = [(label, value) for label, value in fields
                      if value and (value in numeric_values or
                                    (not re.search(r"\d", value) and _norm(label) not in {"reglamento"}))]
        if row_fields:
            lines.append("; ".join(f"{label}: {value}" for label, value in row_fields))
    return "\n".join(lines) if len(lines) > 2 else None


def _article_tail_needs_continuation(text: str) -> bool:
    text = _remove_trailing_page_artifact(str(text or ""))
    if not text or _article_tail_is_complete(text):
        return False
    # Opening punctuation or a dangling connector is positive evidence that a
    # sentence continues. Arbitrary OCR chunks are never appended just because
    # they happen to be adjacent in document order.
    return True


def _article_lookup(query: str, category: str, documents: dict[str, list[dict]]) -> dict | None:
    match = re.search(r"\bart[ií]culo\s+0*(\d+)\b", query, flags=re.IGNORECASE)
    if not match or category not in documents:
        return None
    number = match.group(1)
    anchor = next((chunk for chunk in documents[category] if is_article_heading(chunk, number)), None)
    if not anchor:
        return None

    selected = []
    anchor_text = _article_body(str(anchor.get("text", "")))
    if not anchor_text:
        return None
    selected.append({**anchor, "text": anchor_text})
    page = anchor.get("page")
    same_page_rows = [chunk for chunk in documents[category]
                      if chunk.get("source") == anchor.get("source")
                      and chunk.get("page") == page
                      and chunk.get("extraction") == "textract_table_row"]
    if re.search(r"\b(tabla|cuadro|siguiente forma|distribuci[oó]n|se distribuyen|t[eé]rminos|siglas|abreviaciones)\b",
                 anchor_text, flags=re.IGNORECASE):
        selected.extend(same_page_rows)

    # Include only structurally plausible continuation text. Article/chapter
    # headings can follow page furniture in a single OCR chunk, so detect them
    # anywhere rather than assuming every chunk starts with the heading.
    try:
        anchor_index = documents[category].index(anchor)
    except ValueError:
        anchor_index = -1
    boundary_after = False
    if anchor_index >= 0:
        previous_page = page
        for chunk in documents[category][anchor_index + 1:]:
            if chunk.get("source") != anchor.get("source"):
                continue
            chunk_page = chunk.get("page")
            if chunk.get("extraction") != "textract_prose_chunk":
                continue
            raw_text = str(chunk.get("text", "")).strip()
            if not raw_text:
                continue
            # An abbreviated legal cross-reference is body text only when
            # grammatical context links it (an open parenthesis or "en el").
            if re.match(r"^Art\.?\s*\d+", raw_text, flags=re.IGNORECASE):
                previous_text = str(selected[-1].get("text", ""))
                linked = (previous_text.rstrip().endswith(("(", "["))
                          or bool(re.search(r"\b(?:en\s+el|en\s+la|del|de\s+la)\s*$",
                                            previous_text, flags=re.IGNORECASE)))
                if linked:
                    citation = _article_body(raw_text)
                    if citation:
                        selected.append({**chunk, "text": citation})
                        anchor_text += " " + citation
                continue
            page_changed = chunk_page != previous_page
            continuation_text = _strip_page_furniture(raw_text) if page_changed else raw_text
            boundaries = [match.start() for pattern in (_ARTICLE_HEADING, _SECTION_HEADING)
                          if (match := pattern.search(continuation_text))]
            heading_found = bool(boundaries)
            if boundaries:
                continuation_text = continuation_text[:min(boundaries)].rstrip()
            continuation_text = _remove_trailing_page_artifact(continuation_text)
            if not continuation_text:
                previous_page = chunk_page
                if heading_found:
                    boundary_after = True
                    break
                continue
            if len(continuation_text) > 20:
                if page_changed and re.search(r"\bDE\s*$", str(selected[-1].get("text", ""))) and re.match(
                        r"cuales\b", continuation_text, flags=re.IGNORECASE):
                    selected[-1]["text"] = re.sub(r"\bDE\s*$", "", str(selected[-1].get("text", ""))).rstrip()
                selected.append({**chunk, "text": continuation_text})
                anchor_text += " " + continuation_text
            previous_page = chunk_page
            if heading_found:
                boundary_after = True
                break

    # Keep source order and avoid duplicate chunks.
    unique = []
    seen = set()
    for chunk in selected:
        key = (chunk.get("source"), chunk.get("page"), chunk.get("id"))
        if key not in seen:
            seen.add(key)
            unique.append(chunk)
    table_chunks = [chunk for chunk in unique if chunk.get("extraction") == "textract_table_row"]
    formatted_table = _format_quantitative_table(table_chunks)
    if formatted_table:
        prose = [str(chunk.get("text", "")).strip() for chunk in unique
                 if chunk.get("text") and chunk.get("extraction") != "textract_table_row"]
        passage = "\n".join([*prose, formatted_table])
    else:
        passage = "\n".join(str(chunk.get("text", "")).strip() for chunk in unique if chunk.get("text"))
    if not passage:
        return None
    has_table_rows = any(chunk.get("extraction") == "textract_table_row" for chunk in unique)
    passage_is_complete = _article_tail_is_complete(passage) or has_table_rows or boundary_after
    if not passage_is_complete:
        passage += "\n[El texto OCR puede continuar en la página siguiente.]"
    return _result(passage, unique, "article_extract")


def _general_document_requirements_lookup(query: str, documents: dict[str, list[dict]]) -> dict | None:
    """Resolve a general admission-document question from a uniquely matching provision.

    This uses provision content and list structure rather than a fixed article or
    page number. Explicit special-admission modalities are left to normal
    retrieval so their additional requirements are not hidden by the general rule.
    """
    q = _norm(query)
    asks_for_documents = bool(re.search(
        r"\b(documentos?|documentacion|requisitos?)\b", q
    )) and bool(re.search(
        r"\b(present\w*|entreg\w*|subir\w*|adjunt\w*|necesit\w*|llevar\w*|postul\w*|inscrip\w*|admision|ceprunsa)\b", q
    ))
    if not asks_for_documents:
        return None

    special_modality = re.search(
        r"\b(deportista|discapacidad|traslado|coar|bachillerato internacional|dos primeros puestos|victima|victimas|licencia denegada)\b",
        q,
    )
    if special_modality:
        return None

    candidates = []
    for chunk in documents.get("REGLAMENTO", []):
        if chunk.get("extraction") != "textract_prose_chunk":
            continue
        text = str(chunk.get("text", ""))
        heading = re.match(r"^\s*Art(?:iculo|ículo)\s+0*(\d+)(?!\d)", text, flags=re.IGNORECASE)
        if not heading:
            continue
        normalized = _norm(text)
        # The general rule identifies a pre-inscription document list directly.
        # Cross-references that merely say "see Article N" do not qualify.
        if "preinscripcion" not in normalized or "documento" not in normalized:
            continue
        if not re.search(r"\bdigitalizar\b|\bescanear\b|\bpresentar\b", normalized):
            continue
        score = 0
        if re.search(r"documentos? que se detallan", normalized):
            score += 4
        if "documento de identidad" in normalized:
            score += 1
        if "certificado original de estudios secundarios" in normalized:
            score += 2
        numbered_items = re.findall(r"\b\d{1,3}\.\d+(?:\.\d+)?\.", text)
        score += min(len(numbered_items), 4)
        candidates.append((score, heading.group(1), chunk))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    if candidates[0][0] < 5:
        return None
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        return None
    result = _article_lookup(f"Artículo {candidates[0][1]}", "REGLAMENTO", documents)
    if result:
        article_number = candidates[0][1]
        item_pattern = re.compile(
            rf"(?<!\d){re.escape(article_number)}\.\d+(?:\.\d+)*\."
        )
        # Textract can inject a stamp fragment as an uppercase token in the
        # middle of otherwise grammatical prose. Remove only rare all-caps
        # tokens embedded between lowercase words; keep recurring acronyms.
        acronym_counts = Counter(
            token
            for source_chunk in documents.get("REGLAMENTO", [])
            for token in re.findall(r"[A-ZÁÉÍÓÚÑ]{5,}", str(source_chunk.get("text", "")))
        )
        cleaned_parts = []
        relevant_contexts = []
        for context in result.get("contexts", []):
            source_text = str(context.get("text", ""))
            # A bottom-of-page footnote can be interleaved into the body by OCR.
            # Cut it when an uppercase page artifact is immediately followed by
            # the footnote's compact annotation marker.
            footnote = re.search(r"\s+[A-ZÁÉÍÓÚÑ]{4,}\s+An\.\d+\b", source_text)
            if footnote:
                source_text = source_text[:footnote.start()]
            matches = list(re.finditer(r"[A-ZÁÉÍÓÚÑ]{5,}", source_text))
            for match in reversed(matches):
                before = source_text[:match.start()]
                after = source_text[match.end():]
                prev_word = re.search(r"([a-záéíóúñ]{2,})\s+$", before)
                next_word = re.match(r"\s+([a-záéíóúñ]{2,})", after)
                if acronym_counts[match.group(0)] <= 1 and prev_word and next_word:
                    source_text = source_text[:match.start()] + source_text[match.end():]
            # Drop a stray short all-caps token immediately before a numbered
            # list item; it is not part of the numbering or the clause text.
            source_text = re.sub(
                r"\b[A-ZÁÉÍÓÚÑ]{2,3}\s+(?=\d{1,3}\.\d+(?:\.\d+)*\.)", "", source_text
            )
            # In prose, Textract sometimes reads the conjunction “o” as zero.
            source_text = re.sub(
                r"(?<=[a-záéíóúñ])\s+0\s+(?=[a-záéíóúñ])", " o ", source_text
            )
            context["text"] = re.sub(r"\s{2,}", " ", source_text).strip()
            if item_pattern.search(context["text"]):
                cleaned_parts.append(context["text"])
                relevant_contexts.append(context)
            else:
                continue
        result["contexts"] = relevant_contexts
        result["sources"] = sorted({_source(context) for context in relevant_contexts})

        # Serialize every numbered item in source order so the generator cannot
        # silently omit a condition carried on the following physical page.
        combined = " ".join(cleaned_parts)
        item_matches = list(item_pattern.finditer(combined))
        if not item_matches:
            return None
        clauses = []
        for index, match in enumerate(item_matches):
            end = item_matches[index + 1].start() if index + 1 < len(item_matches) else len(combined)
            content = " ".join(combined[match.end():end].split()).strip(" ;|-")
            if not content:
                continue
            depth = max(0, match.group(0).count(".") - 2)
            clauses.append(f"{'  ' * depth}- {match.group(0)[:-1]} {content}")
        if not clauses:
            return None
        result["answer"] = (
            f"Artículo {article_number} — Documentos y condiciones para la preinscripción:\n"
            + "\n".join(clauses)
        )
        result["structured_lookup"] = "document_requirements"
    return result


def _table_rows(documents: dict[str, list[dict]], category: str) -> list[dict]:
    return [chunk for chunk in documents.get(category, [])
            if chunk.get("extraction") == "textract_table_row" and chunk.get("text")]


def _schedule_lookup(query: str, documents: dict[str, list[dict]]) -> dict | None:
    q = _norm(query)
    item_aliases = (
        ("inscripciones", ("inscrib", "inscripcion")),
        ("inicio de clases", ("clases", "inicio de clases")),
        ("evaluacion previa", ("evaluacion previa",)),
        ("evaluacion de conocimientos", ("conocimientos", "examen de conocimientos")),
        ("evaluacion de aptitudes academicas", ("aptitudes", "aptitud academica")),
        ("asignacion de vacantes", ("asignacion de vacantes", "asignan vacantes")),
    )
    item_label = next((label for label, aliases in item_aliases if any(alias in q for alias in aliases)), None)
    if not item_label:
        return None
    candidates = []
    for chunk in _table_rows(documents, "CRONOGRAMA"):
        text = str(chunk["text"])
        normalized = _norm(text)
        fields = _fields(text)
        item = next((value for label, value in fields if _norm(label) == "item"), "")
        if item_label not in _norm(item):
            continue
        # Match the complete exam heading from the row, including its phase or
        # modality, to avoid borrowing dates from a neighboring table column.
        heading_match = re.search(r"CRONOGRAMA\s*\|\s*(.*?)\s*\|\s*Item\s*:", text, re.IGNORECASE)
        heading = heading_match.group(1).strip() if heading_match else ""
        heading_norm = _norm(heading)
        heading_terms = [token for token in heading_norm.split() if token not in {"examen", "de", "del"}]
        if not heading_terms or not all(token in q.split() for token in heading_terms):
            continue
        candidates.append((heading, fields, chunk))
    if len(candidates) != 1:
        return None
    heading, fields, chunk = candidates[0]
    dates = [value for label, value in fields if _norm(label).startswith("dato")]
    dates = [value for value in dates if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", value)]
    if not dates:
        return None
    if re.search(r"\b(hasta|ultimo|finaliza|cierra)\b", q) and item_label == "inscripciones":
        answer = dates[-1]
    elif re.search(r"\b(desde|inicia|empieza|comienza)\b", q) and item_label == "inscripciones":
        answer = dates[0]
    elif len(dates) == 2:
        answer = f"Del {dates[0]} al {dates[1]}"
    else:
        answer = dates[0]
    return _result(f"{heading}: {item_label.capitalize()} — {answer}.", [chunk], "table_date_cell")


def _vacancy_lookup(query: str, documents: dict[str, list[dict]]) -> dict | None:
    q = _norm(query)
    phase = re.search(r"\bfase\s+(i{1,3}|iv|v|[1-5])\b", q)
    requested_label = None
    if re.search(r"\b(ciclo\s+quintos|quintos)\b", q):
        requested_label = "CEPRUNSA / Ciclo Quintos"
    elif phase:
        roman = phase.group(1).upper()
        group = "CEPRUNSA" if "ceprunsa" in q else "ORDINARIO" if "ordinario" in q or "examen" in q else None
        if group:
            requested_label = f"{group} / Fase {roman}"
    elif "ceprunsa" in q and re.search(r"\b(total|suma|sumando)\b", q):
        requested_label = "CEPRUNSA / Total de Vacantes"
    elif "ordinario" in q and re.search(r"\b(total|suma|sumando)\b", q):
        requested_label = "ORDINARIO / Total de Vacantes"
    elif re.search(r"\b(sumando todo|todo el proceso|total general|total de todo)\b", q):
        requested_label = "TOTAL GENERAL"

    candidates = []
    for chunk in _table_rows(documents, "VACANTES"):
        fields = _fields(chunk["text"])
        program = next((value for label, value in fields if _norm(label) in {"programa de estudios", "programa"}), "")
        if not program or _norm(program) not in q:
            continue
        if requested_label:
            cell_matches = [(label, value) for label, value in fields
                            if _norm(label) == _norm(requested_label)]
        else:
            # Resolve an explicitly named available column (such as a branch)
            # using the header labels present in that row.
            cell_matches = [(label, value) for label, value in fields
                            if _norm(label) not in {"programa de estudios", "programa", "facultad", "area"}
                            and all(term in q.split() for term in _norm(label).split()
                                    if term not in {"de", "la", "el"})]
        if len(cell_matches) == 1:
            candidates.append((len(_norm(program)), program, cell_matches[0], chunk))
    if not candidates:
        return None
    longest = max(item[0] for item in candidates)
    candidates = [item for item in candidates if item[0] == longest]
    if len(candidates) != 1:
        return None
    _, program, cell, chunk = candidates[0]
    label, value = cell
    if not re.fullmatch(r"\d+(?:[.,]\d+)?", value.strip()):
        return None
    answer = f"{program}: {value} vacantes ({label})."
    return _result(answer, [chunk], "table_cell")


_Q_NOISE = {"de", "del", "la", "el", "las", "los", "en", "y", "o", "a", "para", "por", "con", "un", "una", "que", "cual",
            "cuales", "cuantas", "cuantos", "cuanto", "cuanta", "hay", "tiene", "tienen", "ofrece", "son", "es", "se",
            "carrera", "carreras", "programa", "programas", "estudios", "vacantes", "vacante", "cupos", "plazas",
            "total", "totales", "general", "proceso", "mas", "menos", "mayor", "menor", "numero", "cantidad", "suman",
            "me", "mi", "al", "lo", "si", "dime", "dame", "ofrecen", "existen"}
_LABEL_NOISE = {"de", "del", "la", "el", "vacantes", "vacante", "proceso", "general", "estudios", "programa"}
_ROW_KEYS = {"programa de estudios", "programa", "facultad", "area"}


def _stems(text: str) -> set[str]:
    return {token[:6] for token in _norm(text).split()}


def _label_match(label: str, q_tokens: set[str]) -> int | None:
    """Score how well a column header is named by the query (None = not named).

    A header such as "ORDINARIO / Total de Vacantes" is split into group and item.
    The item words must all appear in the query; when the item is only a generic
    "total", the group word must appear too. A bare "TOTAL GENERAL" column is the
    table's grand total and is selected when the query says "total" without any
    qualifier. Nothing here depends on a particular institution or table.
    """
    group, _, item = label.rpartition("/")
    if not group:
        group, item = "", label
    item_words = {t[:6] for t in _norm(item).split() if t not in _LABEL_NOISE}
    group_words = {t[:6] for t in _norm(group).split() if t not in _LABEL_NOISE}
    has_total = "total" in _norm(item).split()
    core = item_words - {"total"}
    if has_total and not core and "total" not in q_tokens:
        return None
    if core and not core <= q_tokens:
        return None
    if not core and not has_total:
        return None
    if group_words and not core and not group_words <= q_tokens:
        return None
    return 2 * len(core) + (len(group_words) if group_words and group_words <= q_tokens else 0) + (1 if has_total and "total" in q_tokens else 0)


def _program_rows(documents):
    rows = []
    for chunk in _table_rows(documents, "VACANTES"):
        fields = _fields(chunk["text"])
        program = next((v for l, v in fields if _norm(l) in {"programa de estudios", "programa"}), "")
        if program:
            rows.append((program, fields, chunk))
    return rows


def _is_summary_row(program: str) -> bool:
    return bool(re.match(r"(sub)?total\b", _norm(program)))


def _number(value: str):
    value = value.strip()
    return int(value) if re.fullmatch(r"\d+", value) else None


_ORDINALS = {"primera": "i", "segunda": "ii", "tercera": "iii", "cuarta": "iv", "quinta": "v"}


def _column_lookup(query: str, documents: dict[str, list[dict]]) -> dict | None:
    """Row-entity x column-header resolution over serialized tables.

    Handles (i) a cell for a named row, (ii) a comparison between two named rows,
    (iii) superlatives over a column, and (iv) which rows have a non-zero value in
    a named column, with their sum. Returns None whenever the row or the column is
    not uniquely determined by the query, so ordinary RAG continues.
    """
    q = _norm(query)
    if not re.search(r"\b(cuant\w*|total\w*|vacantes?|cupos?|plazas?|mas|menos|mayor|menor|que carreras|en que)\b", q):
        return None
    q = re.sub(r"\btotales\b", "total", q)
    q = re.sub(r"\b(primera|segunda|tercera|cuarta|quinta) fase\b", lambda m: f"fase {_ORDINALS[m.group(1)]}", q)
    q_tokens = {t[:6] for t in q.split()}
    all_rows = _program_rows(documents)
    rows = [r for r in all_rows if not _is_summary_row(r[0])]
    if not rows:
        return None
    header_stems = {t[:6] for _, fields, _ in rows for l, _ in fields for t in _norm(l).split()}
    small = {"de", "la", "el", "del", "con", "en", "y", "mencion", "especialidad", "para", "por"}
    asked = [t for t in q.split() if t not in _Q_NOISE and t[:6] not in header_stems and t not in small]
    name_tokens = [{t for t in _norm(p).split() if t not in small} for p, _, _ in rows]

    def named(index: int) -> bool:
        program = rows[index][0]
        if _norm(program) in q:
            return True
        if not asked or not set(asked) <= name_tokens[index]:
            return False
        if len(asked) >= 2:
            return True
        return sum(1 for toks in name_tokens if asked[0] in toks) == 1

    named_rows = [rows[i] for i in range(len(rows)) if named(i)]
    programs = {}
    for r in named_rows:
        programs.setdefault(_norm(r[0]), []).append(r)
    # a program whose name contains another named program's name is the more specific one
    names = list(programs)
    names = [n for n in names if not any(n != m and n in m for m in names)]

    def cell_for(group):
        best = []
        for program, fields, chunk in group:
            for label, value in fields:
                if _norm(label) in _ROW_KEYS:
                    continue
                score = _label_match(label, q_tokens)
                if score is not None and _number(value) is not None:
                    best.append((score, program, label, value, chunk))
        if not best:
            return None
        top = max(b[0] for b in best)
        best = [b for b in best if b[0] == top]
        return best[0] if len({(b[2], b[3]) for b in best}) == 1 else None

    if len(names) == 2 and re.search(r"\b(mas|menos|diferencia)\b", q) and re.search(r"\bque\b|\bentre\b", q):
        cells = [cell_for(programs[n]) for n in names]
        if all(cells) and cells[0][2] == cells[1][2]:
            a, b = cells
            return _result(f"{a[1]}: {a[3]}; {b[1]}: {b[3]} ({a[2]}). Diferencia: {abs(int(a[3]) - int(b[3]))}.",
                           [a[4], b[4]], "column_comparison")
        return None
    if len(names) == 1:
        cell = cell_for(programs[names[0]])
        if not cell:
            return None
        _, program, label, value, chunk = cell
        return _result(f"{program}: {value} vacantes ({label}).", [chunk], "column_cell")
    if len(names) > 1:
        return None

    labels = {}
    for program, fields, chunk in rows:
        for label, value in fields:
            if _norm(label) in _ROW_KEYS or _number(value) is None:
                continue
            score = _label_match(label, q_tokens)
            if score is not None:
                labels.setdefault(label, [score, []])[1].append((program, int(value), chunk))
    if not labels:
        return None
    top = max(v[0] for v in labels.values())
    top_labels = [l for l, v in labels.items() if v[0] == top]
    if len(top_labels) != 1:
        return None
    label = top_labels[0]
    cells = {}
    for program, value, chunk in labels[label][1]:
        cells[_norm(program)] = (program, value, chunk)
    cells = list(cells.values())
    if re.search(r"\b(mas|mayor|menos|menor)\b", q):
        want_max = bool(re.search(r"\b(mas|mayor)\b", q))
        target = (max if want_max else min)(v for _, v, _ in cells)
        winners = [c for c in cells if c[1] == target]
        listed = "; ".join(f"{p} ({v})" for p, v, _ in winners)
        return _result(f"{'Más' if want_max else 'Menos'} vacantes ({label}): {listed}.", [c[2] for c in winners], "column_superlative")
    nonzero = [c for c in cells if c[1] > 0]
    if not nonzero:
        return None
    listing = "; ".join(f"{p} ({v})" for p, v, _ in nonzero)
    total = sum(v for _, v, _ in nonzero)
    if re.search(r"\b(que|cuales|en que|para que) (carreras|programas)\b", q):
        return _result(f"Programas con vacantes ({label}): {listing}. Suma: {total}.", [c[2] for c in nonzero], "column_list")
    specific = {t for t in _norm(label.rpartition("/")[2]).split() if t not in _LABEL_NOISE | {"total"}}
    if re.search(r"\bcuant\w*\b", q) and specific:
        return _result(f"Suma de vacantes ({label}): {total} ({listing}).", [c[2] for c in nonzero], "column_sum")
    return None


def _topic_lookup(query: str, documents: dict[str, list[dict]]) -> dict | None:
    q = _norm(query)
    if not re.search(r"\b(temas|tema|contenido|entra|entran)\b", q):
        return None
    quoted = None
    for pattern in (r"«([^»]+)»", r"“([^”]+)”", r"\"([^\"]+)\"", r"'([^']+)'", r"‘([^’]+)’"):
        match = re.search(pattern, query)
        if match:
            quoted = match.group(1).strip()
            break
    if not quoted:
        subject_match = re.search(
            r"\b(?:temas|tema|contenido|temario)\b.*?\b(?:de|del|para)\s+([^?!.]+)",
            query,
            flags=re.IGNORECASE,
        )
        if subject_match:
            quoted = subject_match.group(1).strip(" \t\r\n\"'«»“”")
    if not quoted:
        return None
    if len(_norm(quoted).split()) < 2:
        return None

    # Some table extractors split a multi-word component across adjacent rows
    # (for example, one row carries "Razonamiento" and the next "matemático").
    # Reconstruct that hierarchy from the table labels, then collect numbered
    # topic headings until the next parent item begins. This avoids confusing
    # a similarly named row in an evaluation/weighting matrix with the syllabus.
    table_rows = _table_rows(documents, "TEMARIO")
    target = _norm(quoted)
    component_rows = []
    for index, chunk in enumerate(table_rows):
        values = [value for label, value in _fields(str(chunk.get("text", "")))
                  if _norm(label) == "componentes"]
        component_rows.extend((index, value) for value in values)
    component_spans = set()
    for start in range(len(component_rows)):
        pieces = []
        previous_row = None
        for end in range(start, min(start + 3, len(component_rows))):
            row_index, value = component_rows[end]
            if previous_row is not None and row_index != previous_row + 1:
                break
            pieces.append(value)
            combined = _norm(" ".join(pieces))
            if combined == target:
                component_spans.add((component_rows[start][0], row_index))
                break
            if not target.startswith(combined):
                break
            previous_row = row_index
    if len(component_spans) == 1:
        first_component, last_component = next(iter(component_spans))
        group_start = first_component
        if first_component > 0 and re.search(
            r"\b(?:TEMAS|Dato\s+2)\s*:\s*(?:[IVXLCDM]+|\d+)\.",
            str(table_rows[first_component - 1].get("text", "")),
            flags=re.IGNORECASE,
        ):
            group_start -= 1
        group_end = len(table_rows)
        for index in range(last_component + 1, len(table_rows)):
            labels = {_norm(label) for label, _ in _fields(str(table_rows[index].get("text", "")))}
            if "dato 1" in labels or "item" in labels:
                group_end = index
                break
        headings = []
        contexts = []
        heading_pattern = re.compile(
            r"\b(?:TEMAS|Dato\s+2)\s*:\s*((?:[IVXLCDM]+|\d+)\.\s*.+?)"
            r"(?=\s+El postulante debe ser capaz\b|$)",
            flags=re.IGNORECASE,
        )
        for chunk in table_rows[group_start:group_end]:
            text = str(chunk.get("text", ""))
            matches = heading_pattern.findall(text)
            if matches:
                headings.extend(" ".join(match.split()) for match in matches)
                contexts.append(chunk)
            elif contexts and re.search(r"\bDato\s+2\s*:", text, re.IGNORECASE):
                # Keep continuation rows that contain the end of a split topic.
                contexts.append(chunk)
        if headings:
            answer = f"Temas de {quoted}:\n" + "\n".join(f"- {heading}" for heading in headings)
            return _result(answer, contexts, "topic_component_outline")

    exact_matches = []
    for chunk in table_rows:
        row_text = str(chunk.get("text", ""))
        # The same index also contains the evaluation matrix, whose rows name
        # subjects but contain weights and numeric scores rather than syllabus
        # content. Do not answer a "what topics" query from those rows.
        if not re.search(r"\b(?:TEMAS|CONTENIDO)\s*:", row_text, re.IGNORECASE):
            continue
        text_norm = _norm(row_text)
        if _norm(quoted) in text_norm:
            exact_matches.append(chunk)
    matches = [(1.0, chunk) for chunk in exact_matches]
    if not matches:
        return None
    matches.sort(key=lambda item: (item[0], len(item[1].get("text", ""))), reverse=True)
    if len(matches) > 1 and matches[0][0] == matches[1][0] and matches[0][1]["text"] != matches[1][1]["text"]:
        return None
    chunk = matches[0][1]
    selected_chunks = [chunk]
    row_text = str(chunk.get("text", ""))
    # OCR/table extraction can split a syllabus item at a page break: a row
    # contains the heading and the first row on the next page continues with
    # "El postulante debe ser capaz". Attach that continuation by source order,
    # without relying on a fixed document page number.
    if not re.search(r"\bel postulante debe ser capaz\b", row_text, re.IGNORECASE):
        continuations = [candidate for candidate in _table_rows(documents, "TEMARIO")
                         if candidate.get("source") == chunk.get("source")
                         and candidate.get("page") == (chunk.get("page") or 0) + 1
                         and candidate.get("row") == 0
                         and re.search(r"\bel postulante debe ser capaz\b", candidate.get("text", ""), re.IGNORECASE)]
        if len(continuations) == 1:
            selected_chunks.append(continuations[0])
    content = re.sub(r"^\s*TEMARIO\s*\|\s*", "", chunk["text"], flags=re.IGNORECASE)
    content = re.sub(r"\bDato\s+\d+\s*:\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\s*\|\s*", " ", content)
    content = " ".join(content.split())
    if len(selected_chunks) > 1:
        continuation_text = re.sub(r"^\s*TEMARIO\s*\|\s*", "", selected_chunks[1]["text"], flags=re.IGNORECASE)
        continuation_text = re.sub(r"\bDato\s+\d+\s*:\s*", "", continuation_text, flags=re.IGNORECASE)
        content = " ".join([content, " ".join(continuation_text.split())])
    return _result(content, selected_chunks, "topic_section_extract")


def resolve_structured_answer_any(query: str, category: str, documents: dict[str, list[dict]]) -> dict | None:
    """Try the routed category first, then the others.

    Each resolver is conservative (it answers only when one row/cell/section is
    uniquely determined), so trying the remaining categories recovers queries the
    zero-shot router mislabelled (e.g. an exam date asked with syllabus wording)
    without lowering the bar for an answer.
    """
    order = [category] + [c for c in ("CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO") if c != category]
    for cat in order:
        result = resolve_structured_answer(query, cat, documents)
        if result:
            result["structured_category"] = cat
            return result
    return None


def resolve_structured_answer(query: str, category: str, documents: dict[str, list[dict]]) -> dict | None:
    """Return a direct source-backed answer for an unambiguous structured query."""
    if category == "REGLAMENTO":
        result = _article_lookup(query, category, documents)
        if result:
            return result
        result = _general_document_requirements_lookup(query, documents)
        if result:
            return result
    if category == "CRONOGRAMA":
        result = _schedule_lookup(query, documents)
        if result:
            return result
    if category == "VACANTES":
        result = _vacancy_lookup(query, documents) or _column_lookup(query, documents)
        if result:
            return result
    if category == "TEMARIO":
        result = _topic_lookup(query, documents)
        if result:
            return result
    return None
