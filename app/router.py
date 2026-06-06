from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

VALID_CATEGORIES = ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO"]

ROUTER_PROMPT = """Clasifica la consulta en una de estas categorías: CRONOGRAMA, VACANTES, TEMARIO, REGLAMENTO, FUERA_DE_DOMINIO.
Consulta: "{query}"
Responde SOLO con la categoría, nada más."""

def route_query(query: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="llama3",
            messages=[{"role": "user", "content": ROUTER_PROMPT.format(query=query)}],
            temperature=0.0
        )
        raw = response.choices[0].message.content.strip().upper()
        
        category = "FUERA_DE_DOMINIO"
        for valid_cat in VALID_CATEGORIES:
            if valid_cat in raw:
                category = valid_cat
                break
                
        return {"category": category, "is_in_domain": category in VALID_CATEGORIES, "raw_response": raw}
    
    except Exception as e:
        print(f"[ERROR OLLAMA] {e}")
        return {"category": "FUERA_DE_DOMINIO", "is_in_domain": False, "raw_response": str(e)}