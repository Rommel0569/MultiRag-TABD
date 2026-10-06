"""Create a separate scoring-reference copy with visually corrected examples.

The query wording and order stay identical to the paired run. Only source
references transcribed from rendered originals are corrected here; the
candidate bank and its historical references are preserved unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation" / "queries_500_disambiguated_candidates.json"
OUTPUT = ROOT / "evaluation" / "queries_500_source_reviewed_refs.json"

CORRECTIONS = {
    349: {
        "ground_truth": (
            "Artículo 5°. Glosario de términos y siglas. 5.1. Documento de identidad: "
            "Documento oficial que establece la identidad y la nacionalidad de una persona. "
            "Para fines del presente reglamento se denominará DNI, Carné de Extranjería o "
            "Carné de Permiso Temporal de Permanencia. 5.2. Proceso de Admisión: Permite a "
            "los postulantes, previo cumplimiento de los requisitos establecidos, postular "
            "a los diferentes programas de estudio que ofrece la UNSA en cualquiera de las "
            "modalidades de examen y, luego de ocupar una vacante, incorporarse como "
            "estudiante en la universidad. 5.3. Siglas: CAB — Convenio Andrés Bello; "
            "CEBA — Centro de Educación Básica Alternativa; CEPRUNSA — Centro "
            "Preuniversitario de la UNSA; COAR — Colegio de Alto Rendimiento; CONADIS — "
            "Consejo Nacional para la Integración de la Persona con Discapacidad; CPS — "
            "Comisión de Procesos de Selección; CSPA — Comisión Supervisora del Proceso "
            "de Admisión."
        ),
        "evidence_quote": "Artículo 5° Glosario de términos y siglas",
        "source_pages": [5],
        "source_review_note": "Cotejada visualmente la página física 5; las siete siglas se transcribieron como filas con sus definiciones y se descartó la serialización desalineada del índice v7.",
    },
    353: {
        "ground_truth": (
            "Artículo 9°. La CPS es designada por el Rector a propuesta del VRA, "
            "acreditada mediante resolución rectoral y está constituida por un máximo "
            "de siete (7) docentes ordinarios, uno de los cuales la preside. Es "
            "responsable de elaborar y ejecutar los diferentes procesos de selección "
            "de postulantes."
        ),
        # Stable excerpt visible on printed page 3/physical PDF page 6; the article
        # continues at the top of physical page 7 (printed page 4).
        "evidence_quote": (
            "Artículo 9°. La CPS es designada por el Rector a propuesta del VRA, "
            "acreditada mediante resolución rectoral y está constituida por un máximo "
            "de siete (7) docentes ordinarios"
        ),
        "source_pages": [6, 7],
        "source_review_note": "Corregida tras cotejar visualmente el original: se retiró texto de notas al pie mezclado por OCR y se añadió la continuación del artículo en la página siguiente.",
    },
    380: {
        "ground_truth": (
            "Artículo 38°. En el Proceso Ordinario se incluyen las áreas curriculares "
            "de Educación Básica Regular. Distribución del número de preguntas por "
            "componente, área temática y asignatura, en el orden Ingenierías / "
            "Biomédicas / Sociales: Aptitud Académica—Razonamiento lógico 4/4/4, "
            "Razonamiento matemático 5/5/5, Razonamiento verbal 4/4/4 y Comprensión "
            "lectora 5/5/5; Matemática—Álgebra 4/3/3, Aritmética 4/3/3, Geométrica "
            "4/3/3 y Trigonometría 3/3/3; Ciencias Sociales—Historia 4/5/8 y "
            "Geografía 4/4/5; Ciencia y Tecnología—Química 6/6/3, Biología 5/9/3 "
            "y Física 7/5/3; Desarrollo Personal, Ciudadanía y Cívica—Filosofía "
            "3/3/3, Psicología 4/4/5 y Educación cívica 3/3/3; Comunicación—Lenguaje "
            "4/4/8 y Literatura 3/3/5; Lengua Extranjera—Lectura 2/2/2 y Gramática "
            "2/2/2. El total es de 80 preguntas en cada área."
        ),
        "evidence_quote": (
            "Artículo 38°. En el Proceso Ordinario se incluyen las áreas curriculares "
            "de Educación Básica Regular, las cuales se distribuyen de la siguiente forma:"
        ),
        "source_pages": [13],
        "source_review_note": "Se cotejaron los 20 renglones, sus encabezados y los totales con la tabla del original; se retiró el residuo OCR «EGGSTIN COUPA» que no aparece en la fuente.",
    },
    395: {
        "ground_truth": (
            "Artículo 53°. Las vacantes de las Filiales corresponden a estos programas: "
            "Camaná — Administración; Mollendo — Administración; El Pedregal — "
            "Administración e Ingeniería Agronómica."
        ),
        "evidence_quote": (
            "Artículo 53° En este proceso de admisión, el número de vacantes es propuesto "
            "por las Facultades que cuentan con Filiales."
        ),
        "source_pages": [16],
        "source_review_note": "Cotejadas visualmente la introducción y las tres filas de la tabla: El Pedregal tiene dos programas en una celda que ocupa dos líneas.",
    },
}


def main() -> None:
    bank = json.loads(SOURCE.read_text(encoding="utf-8"))
    by_id = {int(row["id"]): row for row in bank["consultas"]}
    for item_id, correction in CORRECTIONS.items():
        row = by_id[item_id]
        for key, value in correction.items():
            row[key] = value
        row["validation_status"] = "partially_source_reviewed_visual_manual"
    bank["source_reference_review"] = {
        "status": "partial_visual_review_not_a_fully_validated_benchmark",
        "source_bank": SOURCE.name,
        "manually_corrected_ids": sorted(CORRECTIONS),
        "query_texts_unchanged": True,
        "note": "Only IDs 349, 353, 380, and 395 have manually corrected answer references in this copy. Other candidate references remain unvalidated and their per-answer audit flags must be retained.",
    }
    OUTPUT.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert [row["query"] for row in original["consultas"]] == [row["query"] for row in bank["consultas"]]
    assert len(bank["consultas"]) == 500
    print(f"[SAVED] {OUTPUT}")
    print(f"[CORRECTED] {len(CORRECTIONS)} source references; query text unchanged")


if __name__ == "__main__":
    main()
