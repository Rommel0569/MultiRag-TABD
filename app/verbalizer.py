"""Turns an extracted fact (Phase 3a) into a short contextual answer, without letting the LLM change the fact.

The local LLM only rephrases: it receives the verified fact and the source row/passage. The result is accepted only if every
number and date it contains also appears in the fact, the source text, or the question; otherwise the original terse answer
is returned unchanged. The call is skipped for article extracts (verbatim legal text), which already carry context.
"""
import re

from llm import generator_config, _client

SYSTEM = (
    "Eres el asistente de admisión de CEPRUNSA (Universidad Nacional de San Agustín de Arequipa). "
    "Redacta la respuesta final para el postulante en 2 o 3 oraciones, en español natural y cordial. "
    "Usa EXCLUSIVAMENTE el DATO VERIFICADO y la FUENTE. Retoma lo que se preguntó, da el dato exacto sin modificarlo e indica a qué "
    "corresponde (programa, fase, modalidad, examen) y de qué documento y página proviene. "
    "No incluyas saludos ni fórmulas de cortesía: empieza respondiendo la pregunta. "
    "No agregues cifras, fechas ni nombres que no estén en el dato o en la fuente. No uses viñetas."
)
_NUM = re.compile(r"\d+(?:[./,]\d+)*")


def _numbers(text: str) -> set[str]:
    return {m.replace(",", ".").strip(".") for m in _NUM.findall(text or "")}


def verbalize(query: str, structured: dict) -> tuple[str, str]:
    """Return (answer, mode) where mode is 'contextual', 'terse_fallback' or 'terse_verbatim'."""
    fact = structured["answer"]
    if structured.get("structured_lookup") in {"article_extract", "document_requirements", "topic_section_extract", "topic_component_outline"}:
        return fact, "terse_verbatim"
    source = "\n".join(c.get("text", "") for c in structured.get("contexts", []))
    cfg = generator_config()
    try:
        r = _client(cfg["base_url"], cfg["api_key"]).chat.completions.create(
            model=cfg["model"], temperature=0.1,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": f"PREGUNTA: {query}\nDATO VERIFICADO: {fact}\n"
                                                  f"FUENTE: {', '.join(structured.get('sources', []))}\n{source}"}])
        out = (r.choices[0].message.content or "").strip()
    except Exception:
        return fact, "terse_fallback"
    allowed = _numbers(fact) | _numbers(source) | _numbers(query) | _numbers(" ".join(structured.get("sources", [])))
    if not out or not _numbers(out) <= allowed or len(out) < len(fact):
        return fact, "terse_fallback"
    return out, "contextual"
