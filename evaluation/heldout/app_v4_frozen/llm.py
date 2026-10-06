"""Grounded response generation with local Ollama, DeepSeek, or Gemini API."""
import os
import re
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

from openai import OpenAI

# Load project-local credentials for CLI runs as well as the web app. Existing
# shell variables take precedence. The file is git-ignored; never commit it.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


SYSTEM_PROMPT = (
    "Eres un asistente académico especializado en el proceso de admisión de CEPRUNSA "
    "(Centro Preuniversitario de la Universidad Nacional de San Agustín, Arequipa, Perú). "
    "Responde ÚNICAMENTE basándote en el contexto proporcionado. "
    "Cita el fragmento relevante cuando sea posible. "
    "Si la información no está en el contexto, responde exactamente: "
    "'No encontré esa información en los documentos oficiales de CEPRUNSA.' No añadas recomendaciones, "
    "suposiciones ni información relacionada que el contexto no afirme explícitamente. "
    "Para preguntas sobre tablas, identifica la fila de la entidad solicitada y la columna cuyo encabezado coincide "
    "con el alcance pedido (proceso, fase, ciclo, sede o total); responde con el valor de esa celda. "
    "No mezcles columnas o filas parecidas, no calcules valores por diferencia y no infieras cifras. "
    "Si la relación entre la fila, la columna y el valor no es inequívoca en el contexto, usa la respuesta exacta de abstención. "
    "Cuando la consulta pida una lista completa (por ejemplo, qué temas incluye), enumera todos los elementos pertinentes que aparezcan en los fragmentos, en el orden del documento. "
    "Incluye elementos solo cuando el contexto los vincule al asunto exacto preguntado; no los agregues por compartir una palabra. "
    "No presentes una selección como si fuera la lista completa; si los fragmentos no permiten confirmarla, dilo con claridad. "
    "Conserva las siglas tal como aparecen en el contexto; no inventes ni infieras su significado desarrollado. "
    "Solo desarrolla una sigla si el propio contexto proporciona explícitamente esa equivalencia. "
    "Responde en español, de forma clara y concisa."
)


def generator_config():
    """Return the selected provider/model without exposing API credentials."""
    provider = os.environ.get("CEPRUNSA_GENERATOR_PROVIDER", "ollama").strip().lower()
    defaults = {
        "ollama": {"base_url": "http://localhost:11434/v1", "model": "llama3"},
        "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-flash"},
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-3.1-flash-lite",
        },
    }
    if provider not in defaults:
        raise ValueError("CEPRUNSA_GENERATOR_PROVIDER must be 'ollama', 'deepseek', or 'gemini'.")
    key = {
        "deepseek": os.environ.get("DEEPSEEK_API_KEY"),
        "gemini": os.environ.get("GOOGLE_API_KEY"),
    }.get(provider)
    if provider == "ollama":
        key = os.environ.get("CEPRUNSA_LLM_API_KEY", "ollama")
    return {
        "provider": provider,
        "base_url": os.environ.get("CEPRUNSA_LLM_URL", defaults[provider]["base_url"]),
        "model": os.environ.get("CEPRUNSA_GENERATOR_MODEL", defaults[provider]["model"]),
        "api_key": key,
    }


@lru_cache(maxsize=4)
def _client(base_url, api_key):
    return OpenAI(base_url=base_url, api_key=api_key, timeout=120, max_retries=2)


def generate_response(query: str, context_chunks: list, *, allow_article_extract: bool = False) -> dict:
    config = generator_config()
    if not context_chunks:
        return {
            "answer": "No encontré información relevante en los documentos.",
            "sources": [],
            "tokens_used": 0,
            "input_tokens_used": 0,
            "output_tokens_used": 0,
            "generator": "policy-abstention/no-context",
        }

    # For an explicit "what does Article N say?" lookup, preserve the OCR text
    # verbatim instead of letting a generative model expand acronyms or fill
    # gaps in the extracted provision. If the provision introduces a table,
    # retrieve() supplies its table rows in the same context list.
    article_match = re.search(r"\bart[ií]culo\s+(\d+)\b", query, flags=re.IGNORECASE)
    if allow_article_extract and article_match:
        number = article_match.group(1)
        anchor = next((chunk for chunk in context_chunks if re.match(
            rf"\s*Art[ií]culo\s+0*{re.escape(number)}(?!\d)(?:\s*[°º])?\.?(?=\s|$)",
            chunk.get("text", ""), flags=re.IGNORECASE)), None)
        if anchor:
            selected = [anchor]
            anchor_is_incomplete = not re.search(r"[.!?;:]\s*[\"'»)]*$", anchor.get("text", ""))
            if re.search(r"\b(tabla|siguiente forma|distribuci[oó]n|se distribuyen)\b",
                         anchor.get("text", ""), flags=re.IGNORECASE):
                selected.extend(chunk for chunk in context_chunks
                                if chunk is not anchor
                                and chunk.get("source") == anchor.get("source")
                                and chunk.get("page") == anchor.get("page")
                                and chunk.get("extraction") == "textract_table_row")
            continuation = next((chunk for chunk in context_chunks
                                 if chunk is not anchor
                                 and chunk.get("source") == anchor.get("source")
                                 and chunk.get("page") == (anchor.get("page") or 0) + 1
                                 and chunk.get("extraction") == "textract_prose_chunk"
                                 and len(chunk.get("text", "")) > 180
                                 and not re.match(r"\s*Art[ií]culo\s+\d+\b",
                                                  chunk.get("text", ""), flags=re.IGNORECASE)), None)
            if continuation:
                selected.append(continuation)
            passage = "\n".join(chunk.get("text", "").strip() for chunk in selected).strip()
            if passage and (anchor_is_incomplete or not re.search(r"[.!?;:]\s*[\"'»)]*$", passage)):
                passage += "\n[El fragmento OCR puede estar incompleto; consulte la página fuente.]"
            return {
                "answer": passage,
                "sources": sorted({f"{chunk.get('source', '')} (p.{chunk.get('page', '?')})"
                                   for chunk in selected}),
                "tokens_used": 0,
                "generator": "extractive-article-lookup",
            }
    if config["provider"] in {"deepseek", "gemini"} and not config["api_key"]:
        variable = "DEEPSEEK_API_KEY" if config["provider"] == "deepseek" else "GOOGLE_API_KEY"
        raise RuntimeError(f"{config['provider']} está seleccionado; configura {variable} en el entorno local.")

    context_text = "\n\n".join(
        f"[Fragmento {i+1} — {c.get('source','?')}, p.{c.get('page','?')}]\n{c.get('text','')}"
        for i, c in enumerate(context_chunks)
    )
    response = _client(config["base_url"], config["api_key"]).chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXTO:\n{context_text}\n\nCONSULTA: {query}"},
        ],
        temperature=float(os.environ.get("CEPRUNSA_GENERATOR_TEMPERATURE", "0.1")),
    )
    answer = (response.choices[0].message.content or "").strip()
    sources = sorted({f"{c.get('source','')} (p.{c.get('page','?')})" for c in context_chunks})
    usage = getattr(response, "usage", None)
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    return {
        "answer": answer,
        "sources": sources,
        "tokens_used": int(getattr(usage, "total_tokens", 0) or (input_tokens + output_tokens)),
        "input_tokens_used": input_tokens,
        "output_tokens_used": output_tokens,
        "generator": f"{config['provider']}/{config['model']}",
    }
