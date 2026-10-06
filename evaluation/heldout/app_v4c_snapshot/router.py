import os
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
ROUTER_PROVIDER = os.environ.get("CEPRUNSA_ROUTER_PROVIDER", "ollama").strip().lower()
if ROUTER_PROVIDER == "gemini":
    ROUTER_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    ROUTER_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
    if not ROUTER_API_KEY:
        raise RuntimeError("Gemini router selected; configure GOOGLE_API_KEY in the local environment.")
elif ROUTER_PROVIDER == "ollama":
    ROUTER_BASE_URL = os.environ.get("CEPRUNSA_ROUTER_URL", "http://localhost:11434/v1")
    ROUTER_API_KEY = os.environ.get("CEPRUNSA_ROUTER_API_KEY", "ollama")
else:
    raise ValueError("CEPRUNSA_ROUTER_PROVIDER must be 'ollama' or 'gemini'.")

client = OpenAI(base_url=ROUTER_BASE_URL, api_key=ROUTER_API_KEY, timeout=60, max_retries=1)

VALID_CATEGORIES = ["CRONOGRAMA", "VACANTES", "TEMARIO", "REGLAMENTO"]

ROUTER_PROMPT = """Clasifica la intención principal de la consulta de admisión universitaria.
CRONOGRAMA: fechas, plazos y etapas del proceso.
VACANTES: cantidades de plazas disponibles por carrera o modalidad.
TEMARIO: contenidos académicos, cursos y estructura de la evaluación.
REGLAMENTO: requisitos, documentos, pagos, elegibilidad, sanciones y procedimientos.
FUERA_DE_DOMINIO: asuntos ajenos a la admisión universitaria.
Clasifica por el tema completo de la consulta, no por una palabra compartida: "cuándo" no implica cronograma de admisión si se pregunta por un partido, y "prácticas" no implica reglamento si se pregunta por empleo.
Para asignar una categoría de admisión debe haber una referencia clara al proceso de admisión, CEPRUNSA, un examen, inscripción, vacantes, temario o reglamento.
Una mención de una carrera no significa que se pregunte por cantidades de plazas.
Consulta: "{query}"
Responde SOLO con la categoría, nada más."""


def _explicit_intent(query: str):
    """Return a category only for unambiguous, explicit question intents."""
    text = re.sub(r"\s+", " ", query.casefold())
    if re.search(r"\b(temario|temas entran|contenido entra|qué entra|que entra|cursos entran)\b", text):
        return "TEMARIO"
    if re.search(r"\b(art[ií]culo|reglamento|requisito|documentos para postular|edad m[ií]nima|pago de inscripci[oó]n)\b", text):
        return "REGLAMENTO"
    if re.search(r"\b(cu[aá]ntas? (?:vacantes|plazas)|n[uú]mero de vacantes|plazas disponibles|vacantes hay)\b", text):
        return "VACANTES"
    if re.search(r"\b(cronograma|inscripciones van|inicio de clases|empiezan las clases|evaluaci[oó]n previa|examen de conocimientos|asignaci[oó]n de vacantes)\b", text):
        return "CRONOGRAMA"
    temporal_question = re.search(r"\b(qu[eé] d[ií]a|cu[aá]ndo|fecha de|hasta qu[eé] d[ií]a)\b", text)
    admissions_subject = re.search(r"\b(ceprunsa|admisi[oó]n|postul\w*|examen|inscrip\w*|vacantes?|plazas?|clases)\b", text)
    if temporal_question and admissions_subject:
        return "CRONOGRAMA"
    return None


def _explicit_out_of_domain(query: str):
    """Catch clearly non-admission topics that can share words with the corpus."""
    text = re.sub(r"\s+", " ", query.casefold())
    patterns = (
        r"\b(curr[ií]culum|hoja de vida|buscar empleo|buscar trabajo|entrevista laboral|pr[aá]cticas laborales)\b",
        r"\b(f[uú]tbol|liga 1|partido(?:s)?|juega\s+\w+\s+contra)\b",
        r"\b(restaurante|cafeter[ií]a|almorzar|pizzer[ií]a|rocoto relleno|men[uú] econ[oó]mico)\b",
        r"\b(clima|llover|lluvia|temperatura de hoy)\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)

def route_query(query: str) -> dict:
    try:
        # A syllabus topic such as climate change is still an in-domain TEMARIO
        # question. Give the explicit academic-question intent precedence over
        # the word "clima", which also appears in weather questions.
        explicit_category = _explicit_intent(query)
        if explicit_category == "TEMARIO":
            return {
                "category": explicit_category,
                "is_in_domain": True,
                "raw_response": "explicit_intent_rule",
                "intent_override": False,
                "input_tokens_used": 0,
                "output_tokens_used": 0,
            }
        if _explicit_out_of_domain(query):
            return {
                "category": "FUERA_DE_DOMINIO",
                "is_in_domain": False,
                "raw_response": "explicit_out_of_domain",
                "intent_override": True,
                "input_tokens_used": 0,
                "output_tokens_used": 0,
            }
        if explicit_category:
            return {
                "category": explicit_category,
                "is_in_domain": True,
                "raw_response": "explicit_intent_rule",
                "intent_override": False,
                "input_tokens_used": 0,
                "output_tokens_used": 0,
            }
        response = client.chat.completions.create(
            model=os.environ.get(
                "CEPRUNSA_ROUTER_MODEL",
                "gemini-3.1-flash-lite" if ROUTER_PROVIDER == "gemini" else "llama3",
            ),
            messages=[{"role": "user", "content": ROUTER_PROMPT.format(query=query)}],
            temperature=0.0
        )
        raw = response.choices[0].message.content.strip().upper()
        usage = getattr(response, "usage", None)
        input_tokens_used = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens_used = int(getattr(usage, "completion_tokens", 0) or 0)
        if ROUTER_PROVIDER == "gemini" and input_tokens_used + output_tokens_used == 0:
            raise RuntimeError("Gemini router returned no token usage metadata; stopping to avoid unmetered API use.")
        
        category = raw.strip(' \n\t\"\'`.')
        if category not in VALID_CATEGORIES + ['FUERA_DE_DOMINIO']:
            raise ValueError(f'Invalid router label: {raw!r}')

        final_category = category
        return {
            "category": final_category,
            "is_in_domain": final_category in VALID_CATEGORIES,
            "raw_response": raw,
            "intent_override": explicit_category is not None and explicit_category != category,
            "input_tokens_used": input_tokens_used,
            "output_tokens_used": output_tokens_used,
        }
    
    except Exception as e:
        print(f"[ERROR {ROUTER_PROVIDER.upper()} ROUTER] {e}")
        raise RuntimeError('El servicio de clasificación no está disponible o devolvió una etiqueta inválida.') from e
