"""Builds the held-out question bank (written AFTER freezing code/index; see FREEZE.json).

Every gold answer was read by the author of this script directly from the page images of the
official PDFs (not from the system's index or outputs). `must` is a list of regexes that must ALL
match the (accent-stripped, lower-cased) answer; `abstain` items must instead be an abstention.
"""
import json, hashlib, datetime, difflib, re, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent


def N(n):  # standalone number, not part of a longer number
    return rf"(?<![\d.,/]){n}(?![\d/])"


def D(dd, mm, yyyy, month):  # date, numeric or spelled out
    return rf"{dd}[/-]{mm}[/-]{yyyy}|{int(dd)} de {month}"


items = []


def add(id_, cat, typ, q, gold, must=None, abstain=False, src=""):
    items.append(dict(id=id_, category=cat, type=typ, query=q, gold=gold,
                      must=must or [], abstain=abstain, source=src))


CR2 = "CRONOGRAMA DE ADMISION 2027.pdf p.2"
CR3 = "CRONOGRAMA DE ADMISION 2027.pdf p.3"
# ---------------- Schedule ----------------
add("C01", "CRONOGRAMA", "lookup", "¿Hasta cuándo me puedo inscribir al ordinario de la primera fase?",
    "17/07/2026", [D("17", "07", "2026", "julio")], src=CR2)
add("C02", "CRONOGRAMA", "lookup", "¿Cuándo se da el examen ordinario de segunda fase?",
    "14/03/2027 (evaluación de conocimientos)", [D("14", "03", "2027", "marzo")], src=CR3)
add("C03", "CRONOGRAMA", "lookup", "cuando es la evaluacion previa del ciclo quintos de ceprunsa",
    "18/10/2026", [D("18", "10", "2026", "octubre")], src=CR2)
add("C04", "CRONOGRAMA", "lookup", "¿Desde qué día empiezan las clases de CEPRUNSA segunda fase?",
    "16/11/2026", [D("16", "11", "2026", "noviembre")], src=CR2)
add("C05", "CRONOGRAMA", "lookup", "En el examen extraordinario, ¿cuándo asignan las vacantes?",
    "23/02/2027", [D("23", "02", "2027", "febrero")], src=CR2)
add("C06", "CRONOGRAMA", "lookup", "Soy de Camaná, ¿qué día rindo el examen en filiales?",
    "20/03/2027 (evaluación de conocimientos, filiales)", [D("20", "03", "2027", "marzo")], src=CR3)
add("C07", "CRONOGRAMA", "lookup", "¿Qué día es la evaluación de aptitudes académicas del extraordinario?",
    "21/02/2027", [D("21", "02", "2027", "febrero")], src=CR2)
add("C08", "CRONOGRAMA", "aggregate", "¿Cuántos exámenes distintos hay en el cronograma de admisión 2027?",
    "7 (CEPRUNSA I fase, ordinario I, CEPRUNSA ciclo quintos, CEPRUNSA II fase, extraordinario, ordinario II, ordinario filiales)",
    [rf"{N(7)}|siete"], src=CR2 + "-3")
add("C09", "CRONOGRAMA", "multistep",
    "Si me inscribo el último día en CEPRUNSA I fase, ¿cuántos días faltan para que empiecen las clases?",
    "10 días (inscripción hasta 17/04/2026; inicio de clases 27/04/2026)", [rf"{N(10)}|diez"], src=CR2)
add("C10", "CRONOGRAMA", "comparison",
    "¿Qué cierra primero, las inscripciones del extraordinario o las del ordinario de segunda fase?",
    "Extraordinario (27/01/2027) cierra antes que ordinario II (26/02/2027)",
    [r"extraordinario", D("27", "01", "2027", "enero")], src=CR2 + "-3")
add("C11", "CRONOGRAMA", "lookup", "¿Cuándo es la evaluación de conocimientos de CEPRUNSA primera fase?",
    "05/07/2026", [D("05", "07", "2026", "julio").replace("{int", "") if False else r"05[/-]07[/-]2026|5 de julio"], src=CR2)
add("C12", "CRONOGRAMA", "lookup", "hasta que dia se puede inscribir uno en ciclo quintos",
    "14/08/2026", [D("14", "08", "2026", "agosto")], src=CR2)
add("C13", "CRONOGRAMA", "lookup", "¿Cuándo termina la inscripción para el ordinario de filiales?",
    "16/03/2027", [D("16", "03", "2027", "marzo")], src=CR3)
add("C14", "CRONOGRAMA", "lookup", "¿Cuándo es la evaluación previa de CEPRUNSA segunda fase?",
    "10/01/2027", [D("10", "01", "2027", "enero")], src=CR2)

# ---------------- Available places ----------------
VP = "CUADRO DE VACANTES 2027.pdf p.3"
VX = "CUADRO DE VACANTES 2027.pdf p.4"
add("V01", "VACANTES", "lookup", "¿Cuántas vacantes hay en total para Derecho?", "160", [N(160)], src=VP)
add("V02", "VACANTES", "lookup", "Medicina, ¿cuántos cupos hay en la segunda fase del ordinario?", "17", [N(17)], src=VP)
add("V03", "VACANTES", "superlative", "¿Qué carrera tiene más vacantes en total?", "Administración (230)",
    [r"administracion", N(230)], src=VP)
add("V04", "VACANTES", "lookup", "¿Cuántas vacantes ofrece en total el proceso ordinario 2027?", "4739",
    [r"4[ .,]?739"], src=VP)
add("V05", "VACANTES", "lookup", "cuantos cupos ay en ceprunsa pa ingenieria de sistemas", "35 (total CEPRUNSA)", [N(35)], src=VP)
add("V06", "VACANTES", "list", "¿En qué carreras hay vacantes para El Pedregal?",
    "Ingeniería Agronómica (70) y Administración (40)", [r"agronomic", r"administracion"], src=VP)
add("V07", "VACANTES", "multistep", "¿Cuántas vacantes más tiene Ingeniería Industrial que Ingeniería Civil en total?",
    "33 (112 - 79)", [N(33)], src=VP)
add("V08", "VACANTES", "lookup", "¿Cuántas vacantes de Enfermería hay en ciclo quintos de CEPRUNSA?", "14", [N(14)], src=VP)
add("V09", "VACANTES", "lookup", "Psicología: ¿cuántas vacantes en la fase I del ordinario?", "34", [N(34)], src=VP)
add("V10", "VACANTES", "lookup", "¿Cuál es el total de vacantes de Arquitectura?", "110", [N(110)], src=VP)
add("V11", "VACANTES", "list", "¿Para qué carreras hay cupos en Mollendo y cuántos en total?",
    "Administración (40) y Contabilidad (20): 60", [r"administracion", r"contabilidad", N(60)], src=VP)
add("V12", "VACANTES", "lookup", "¿Cuántas vacantes totales tiene Educación Inicial?", "34", [N(34)], src=VP)
add("V13", "VACANTES", "lookup", "vacantes de biologia en total", "83", [N(83)], src=VP)
add("V14", "VACANTES", "lookup", "¿Cuántas vacantes tiene Matemáticas en el ordinario, en total?", "32 (total ordinario)", [N(32)], src=VP)
add("V15", "VACANTES", "lookup", "¿Cuántos cupos hay para Ingeniería Química en la fase II del ordinario?", "27", [N(27)], src=VP)
add("V16", "VACANTES", "lookup", "¿Cuántas vacantes hay en la filial de Camaná?", "40", [N(40)], src=VP)
add("V17", "VACANTES", "lookup", "¿Cuántas vacantes tiene Ciencias de la Computación en total?", "60", [N(60)], src=VP)
add("V18", "VACANTES", "lookup", "¿Cuántas vacantes de Turismo y Hotelería hay por CEPRUNSA fase I?", "10", [N(10)], src=VP)
add("V19", "VACANTES", "aggregate", "¿Cuántas vacantes ordinarias suman todas las ingenierías?", "871 (subtotal ingenierías, ordinario)",
    [N(871)], src=VP)
add("V20", "VACANTES", "lookup", "¿Cuántas vacantes tiene Antropología en total?", "60", [N(60)], src=VP)
add("V21", "VACANTES", "superlative", "¿Cuál es la carrera con menos vacantes en total?",
    "Gestión con mención en Gestión Pública y en Gestión de Proyectos (28 cada una)", [r"gestion", N(28)], src=VP)
add("X01", "VACANTES", "lookup", "¿Cuántas vacantes extraordinarias hay para Medicina?", "21", [N(21)], src=VX)
add("X02", "VACANTES", "lookup", "En el extraordinario, ¿cuántos cupos de primeros puestos tiene Ingeniería Industrial?", "28", [N(28)], src=VX)
add("X03", "VACANTES", "lookup", "¿Cuántas vacantes extraordinarias en total tiene Ingeniería de Materiales?", "34", [N(34)], src=VX)
add("X04", "VACANTES", "lookup",
    "Ingeniería Agronómica: ¿cuántas vacantes del extraordinario son para personas con discapacidad?", "7", [N(7)], src=VX)

# ---------------- Syllabus ----------------
TM = "TEMARIO Y MATRIZ DE EVALUACION 2027.pdf pp.3-6"
add("T01", "TEMARIO", "list", "¿Qué se ve en probabilidad dentro de razonamiento matemático?",
    "espacio muestral simple; comparar probabilidades elementales; probabilidad clásica básica en contextos cotidianos",
    [r"espacio muestral", r"compar\w+ probabilidades|situaciones elementales", r"clasica"], src=TM)
add("T02", "TEMARIO", "list", "¿Qué tipos de analogías entran en razonamiento verbal?",
    "semánticas, funcionales, causa-efecto, parte-todo, inclusión-exclusión",
    [r"semantic", r"funcional", r"causa.{0,3}efecto", r"parte.{0,3}todo", r"inclusion"], src=TM)
add("T03", "TEMARIO", "list", "¿Qué conectores lógicos tengo que dominar?",
    "negación, conjunción, disyunción, condicional", [r"negacion", r"conjuncion", r"disyuncion", r"condicional"], src=TM)
add("T04", "TEMARIO", "aggregate", "¿Cuántos temas tiene razonamiento lógico?", "9 (I a IX)", [rf"{N(9)}|nueve"], src=TM)
add("T05", "TEMARIO", "list", "¿Qué falacias simples se evalúan?",
    "generalización indebida, contradicción, falsa causa, ambigüedad lógica",
    [r"generalizacion", r"contradiccion", r"falsa causa", r"ambiguedad"], src=TM)
add("T06", "TEMARIO", "list", "¿Qué contenidos hay en estadística y análisis de datos?",
    "tablas de datos; gráficos de barras y circulares; medidas de tendencia central; evaluar críticamente información numérica",
    [r"tablas", r"grafic", r"tendencia central", r"critica"], src=TM)
add("T07", "TEMARIO", "list", "Dime los temas de razonamiento verbal",
    "I relaciones semánticas básicas; II analogías verbales; III series y clasificaciones verbales; IV lógica de enunciados; "
    "V razonamiento argumentativo básico; VI pragmática en enunciados; VII corrección por sentido",
    [r"relaciones semanticas", r"analogias", r"series y clasificaciones", r"logica de enunciados",
     r"argumentativo", r"pragmatica", r"correccion por sentido"], src=TM)
add("T08", "TEMARIO", "list", "¿Qué debo saber sobre silogismos?",
    "premisa mayor, premisa menor, conclusión; validez de un silogismo simple; errores de razonamiento deductivo",
    [r"premisa mayor", r"premisa menor", r"conclusion", r"validez"], src=TM)
add("T09", "TEMARIO", "locate", "¿En qué tema de razonamiento matemático se ven problemas de edades?",
    "Razonamiento algebraico intuitivo (III)", [r"algebraic"], src=TM)
add("T10", "TEMARIO", "locate", "¿Dónde entran las simetrías en razonamiento matemático?",
    "Razonamiento geométrico (IV)", [r"geometric"], src=TM)
add("T11", "TEMARIO", "locate", "¿Se estudian diagramas de árbol? ¿en qué tema?",
    "Sí, en Análisis combinatorio intuitivo (V)", [r"combinatori"], src=TM)
add("T12", "TEMARIO", "list", "¿Qué se evalúa en pragmática en enunciados?",
    "intención comunicativa; presuposiciones explícitas; mensajes implícitos simples; adecuación del mensaje a la situación",
    [r"intencion comunicativa", r"presuposicion", r"implicit", r"adecuacion"], src=TM)
add("T13", "TEMARIO", "aggregate", "¿Cuántos temas tiene razonamiento matemático?", "7 (I a VII)", [rf"{N(7)}|siete"], src=TM)
add("T14", "TEMARIO", "list", "¿Qué piden en proposiciones y enunciados lógicos?",
    "identificar proposiciones; distinguir verdaderas y falsas; reconocer enunciados no proposicionales; analizar afirmaciones simples y compuestas",
    [r"identificar proposiciones", r"verdaderas y falsas", r"no proposicionales", r"simples y compuestas"], src=TM)
RG = "REGLAMENTO DE ADMISION 2027.pdf Art.38 (printed p.10)"
add("N01", "TEMARIO", "lookup", "¿Cuántas preguntas de química hay para biomédicas?", "6", [rf"{N(6)}|{N('06')}|seis"], src=RG)
add("N02", "TEMARIO", "lookup", "Para sociales, ¿cuántas preguntas de historia?", "8", [rf"{N(8)}|{N('08')}|ocho"], src=RG)
add("N03", "TEMARIO", "lookup", "¿Cuántas preguntas de física tiene el examen para ingenierías?", "7", [rf"{N(7)}|{N('07')}|siete"], src=RG)
add("N04", "TEMARIO", "lookup", "¿Cuántas preguntas tiene en total el examen ordinario?", "80", [N(80)], src=RG)
add("N05", "TEMARIO", "lookup", "¿Cuántas preguntas de biología para biomédicas?", "9", [rf"{N(9)}|{N('09')}|nueve"], src=RG)
add("N06", "TEMARIO", "lookup", "Razonamiento verbal en ingenierías: ¿cuántas preguntas?", "4", [rf"{N(4)}|{N('04')}|cuatro"], src=RG)

# ---------------- Regulations (colloquial, no article number) ----------------
add("R01", "REGLAMENTO", "open", "¿Pueden postular personas condenadas por terrorismo?",
    "No: están impedidas de inscribirse (Art. 23)", [r"impedid|no pueden|no podran|no se permite|prohib", r"terroris"], src="REGLAMENTO Art.23 p.7")
add("R02", "REGLAMENTO", "open", "Si no presento todos los requisitos antes del cierre, ¿qué pasa con mi preinscripción?",
    "No será autorizado a concluir la preinscripción (Art. 28)", [r"no sera autorizad|no podra concluir|no (se|sera) .{0,30}autoriz|no .{0,20}concluir"],
    src="REGLAMENTO Art.28 p.8")
add("R03", "REGLAMENTO", "open", "Pagué el cambio de carrera pero no terminé el trámite, ¿me devuelven la plata?",
    "No: no podrá solicitar la devolución bajo ningún concepto (Art. 29)",
    [r"no podra solicitar la devolucion|no .{0,25}devol|ningun concepto|no hay devolucion|no procede"], src="REGLAMENTO Art.29 p.8")
add("R04", "REGLAMENTO", "open", "¿Hasta cuándo puedo cambiar de carrera?",
    "Hasta antes del cierre de inscripciones, según cronograma (Art. 29)", [r"cierre de (las )?inscripciones|antes del cierre"], src="REGLAMENTO Art.29 p.8")
add("R05", "REGLAMENTO", "open", "¿Para Arquitectura hay una prueba adicional?",
    "Sí: evaluación previa propia del programa, 50% del puntaje final (Art. 30)", [r"evaluacion previa", r"50|cincuenta"], src="REGLAMENTO Art.30 p.8-9")
add("R06", "REGLAMENTO", "open", "¿Dónde me registro y de dónde descargo mi carné de postulante?",
    "En la plataforma SISADMISIÓN (Arts. 25-26)", [r"sisadmision"], src="REGLAMENTO Art.25-26 p.7")
add("R07", "REGLAMENTO", "open", "¿El carné de postulante me sirve para otro examen?",
    "No: es válido únicamente para el examen convocado según el cronograma (Art. 25)",
    [r"\bno\b|unicamente|solo|exclusiv", r"convocad|cada evaluacion|cronograma"], src="REGLAMENTO Art.25 p.7")
add("R08", "REGLAMENTO", "open", "Soy ingresante con CLA, ¿tengo que regularizar mi expediente?",
    "Sí, de manera obligatoria, según el cronograma (Art. 29)", [r"regulariz", r"obligatori|\bsi\b|debera|debe"], src="REGLAMENTO Art.29 p.8")
add("R09", "REGLAMENTO", "open", "¿Qué puedo llevar el día del examen?",
    "Carné de postulante, documento de identidad, lápiz HB o 2B, borrador y tajador (Art. 35)",
    [r"carne", r"identidad|dni", r"lapiz", r"borrador", r"tajador"], src="REGLAMENTO Art.35 p.10")
add("R10", "REGLAMENTO", "open", "¿Puedo entrar al examen con una casaca con capucha?",
    "No: no se permite vestimenta que contenga capucha (Art. 35)", [r"capucha", r"\bno\b|prohib|no se permite"], src="REGLAMENTO Art.35 p.10")
add("R11", "REGLAMENTO", "open", "Ya alcancé vacante en el primer examen, ¿puedo postular de nuevo en otro examen de este año?",
    "No: no podrá volver a postular en otros exámenes del mismo proceso del año en curso (Art. 37)",
    [r"\bno\b", r"mismo proceso|otros examenes|ano en curso|mismo ano"], src="REGLAMENTO Art.37 p.10")
add("R12", "REGLAMENTO", "open", "¿Qué pasa si hay una situación extrema durante el examen?",
    "La CPS con la DA y la CSPS evalúan de inmediato la conveniencia de suspender el examen (Art. 36)",
    [r"suspend|suspension", r"inmediat|evaluar"], src="REGLAMENTO Art.36 p.10")
add("R13", "REGLAMENTO", "open", "¿Qué pasa si descubren que puse datos falsos?",
    "Anulación de la inscripción o del ingreso, sin perjuicio de acciones administrativas y legales (Art. 33)",
    [r"anulacion", r"falsedad|adulteracion|inexactitud|falso|falsa"], src="REGLAMENTO Art.33 p.9")
add("R14", "REGLAMENTO", "open", "¿Cómo confirmo mi inscripción?",
    "Descargar el código web del SISADMISIÓN y pagar el derecho de admisión consignando ese código (Art. 31)",
    [r"codigo web", r"pago|pagar"], src="REGLAMENTO Art.31 p.9")
add("R15", "REGLAMENTO", "open", "¿Dónde se publica la fecha y la hora de mi examen?",
    "En la página web institucional de la UNSA, sección Admisión de Pregrado, y en el carné (Art. 34)",
    [r"web", r"admision de pregrado|institucional"], src="REGLAMENTO Art.34 p.9")

# ---------------- In-domain but not in the documents (must abstain) ----------------
for i, (q, g) in enumerate([
    ("¿A qué hora empieza el examen?", "no figura en los documentos"),
    ("¿Cuántos postulantes se presentan por cada vacante?", "no figura en los documentos"),
    ("¿Cuál fue el puntaje de ingreso a Medicina el año pasado?", "no figura en los documentos"),
    ("¿Cuántas vacantes hay para Medicina Veterinaria?", "el programa no figura en el cuadro de vacantes"),
    ("¿Cuántas vacantes hay para Odontología?", "el programa no figura en el cuadro de vacantes"),
    ("¿Cuándo es el examen de admisión 2028?", "los documentos solo cubren el proceso 2027"),
], 1):
    add(f"U{i:02d}", "SIN_RESPUESTA", "unanswerable", q, g, abstain=True, src="verified absent by text search + page review")

# ---------------- Out of domain ----------------
for i, q in enumerate([
    "¿Cuándo son las inscripciones de la Universidad Católica San Pablo?",
    "¿Qué carreras tiene la UNI en Lima?",
    "Recomiéndame una receta de rocoto relleno",
    "¿Cómo va a estar el clima mañana en Arequipa?",
    "¿Cuánto es 15 por 12?",
    "¿Quién ganó el último mundial de fútbol?",
    "Escríbeme un poema sobre el volcán Misti",
    "¿Dónde puedo comprar un celular barato en Arequipa?",
    "¿Cuál es la mejor universidad del Perú?",
], 1):
    add(f"O{i:02d}", "FUERA_DE_DOMINIO", "ood", q, "fuera del dominio de admisión", abstain=True, src="n/a")


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


# --- leakage check against every question the system was ever developed/evaluated on
seen = []
for p in [HERE.parent / "evidence/ragas_500/inputs/queries_500_pdf_verified_ai_adjudicated.json", HERE.parent / "queries.json"]:
    seen += [c["query"] for c in json.load(open(p, encoding="utf-8"))["consultas"]]
seen_n = [norm(s) for s in seen]
worst = []
for it in items:
    qn = norm(it["query"])
    r = max(difflib.SequenceMatcher(None, qn, s).ratio() for s in seen_n)
    worst.append((r, it["id"], it["query"]))
worst.sort(reverse=True)
exact = [w for w in worst if w[0] >= 0.999]
assert not exact, exact
out = {"status": "HELDOUT_BANK_WRITTEN_AFTER_CODE_FREEZE", "n": len(items),
       "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "max_similarity_to_any_seen_question": round(worst[0][0], 3),
       "top5_most_similar": [(round(a, 3), b, c) for a, b, c in worst[:5]], "consultas": items}
(HERE / "heldout_bank.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(items), "items; max similarity to seen:", out["max_similarity_to_any_seen_question"])
for a in out["top5_most_similar"]:
    print(a)
import collections
print(collections.Counter(i["category"] for i in items)); print(collections.Counter(i["type"] for i in items))
print("sha256", hashlib.sha256((HERE / "heldout_bank.json").read_bytes()).hexdigest())
