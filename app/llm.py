from openai import OpenAI

# Ollama corre por defecto en el puerto 11434
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

SYSTEM_PROMPT = """Eres un asistente académico especializado en el proceso 
de admisión de CEPRUNSA. Responde ÚNICAMENTE basándote en el contexto.
Si la información no está en el contexto, responde: "No encontré esa información en los documentos oficiales de CEPRUNSA."
Responde en español, claro y conciso."""

def generate_response(query: str, context_chunks: list) -> dict:
    if not context_chunks:
        return {"answer": "No encontré información relevante en los documentos.", "sources": [], "tokens_used": 0}

    context_text = "\n\n".join([f"[{c.get('source','?')}, p.{c.get('page','?')}] {c.get('text','')}" for c in context_chunks])

    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXTO:\n{context_text}\n\nCONSULTA: {query}\n\nRESPUESTA:"

    response = client.chat.completions.create(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    answer = response.choices[0].message.content.strip()
    sources = list({f"{c.get('source','')} (p.{c.get('page','?')})" for c in context_chunks})

    return {
        "answer": answer,
        "sources": sources,
        "tokens_used": 0 # Ollama local no contabiliza tokens de la misma forma
    }