from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

SYSTEM_PROMPT = (
    "Eres un asistente académico especializado en el proceso de admisión de CEPRUNSA "
    "(Centro Preuniversitario de la Universidad Nacional de San Agustín, Arequipa, Perú). "
    "Responde ÚNICAMENTE basándote en el contexto proporcionado. "
    "Cita el fragmento relevante cuando sea posible. "
    "Si la información no está en el contexto, responde exactamente: "
    "'No encontré esa información en los documentos oficiales de CEPRUNSA.' "
    "Responde en español, de forma clara y concisa."
)


def generate_response(query: str, context_chunks: list) -> dict:
    if not context_chunks:
        return {
            "answer": "No encontré información relevante en los documentos.",
            "sources": [],
            "tokens_used": 0
        }

    context_text = "\n\n".join(
        f"[Fragmento {i+1} — {c.get('source','?')}, p.{c.get('page','?')}]\n{c.get('text','')}"
        for i, c in enumerate(context_chunks)
    )

    # System prompt en el rol correcto — Ollama/llama3 respeta los roles del chat.
    # Antes todo iba mezclado en un solo mensaje de usuario, lo que degradaba
    # el seguimiento de instrucciones del modelo.
    response = client.chat.completions.create(
        model="llama3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"CONTEXTO:\n{context_text}\n\nCONSULTA: {query}"}
        ],
        temperature=0.1
    )

    answer  = response.choices[0].message.content.strip()
    sources = list({f"{c.get('source','')} (p.{c.get('page','?')})" for c in context_chunks})

    return {
        "answer":      answer,
        "sources":     sources,
        "tokens_used": 0
    }