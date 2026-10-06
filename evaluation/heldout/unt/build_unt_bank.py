"""Question bank for a DIFFERENT institution: Universidad Nacional de Trujillo (UNT),
"Reglamento de Admision a los programas de estudios de pregrado" (R.C.U. 229-2026/UNT), a born-digital PDF
(native text layer, 23 pages, NO OCR). Source: https://www.admisionunt.info/docs/REGLAMENTO_DE_ADMISION___2027.pdf
Gold answers were read from the document text by the author of this script; none of the system's code was
designed or tuned with this document in view (app/*.py frozen, see ../FREEZE.json).
"""
import json, hashlib, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def N(n):
    return rf"(?<![\d.,/]){n}(?![\d/])"


items = []


def add(id_, typ, q, gold, must=None, abstain=False, src=""):
    items.append(dict(id=id_, category="UNT", type=typ, query=q, gold=gold, must=must or [], abstain=abstain, source=src))


# ---- numbers / percentages / short facts ----
add("U01", "lookup", "¿Cuántas preguntas tiene la prueba de admisión?", "100 (Art. 47)", [N(100)], src="Art.47 p.17")
add("U02", "lookup", "¿Cuántos puntos vale una respuesta correcta?", "4,079 puntos (Art. 51)", [r"4[.,]079"], src="Art.51 p.17")
add("U03", "lookup", "¿Y cuánto se descuenta por una respuesta mala?", "-1,021 puntos (Art. 51)", [r"1[.,]021"], src="Art.51 p.17")
add("U04", "lookup", "¿Cuántas pruebas de admisión se aplican?", "4, una por cada área de postulación (Art. 41)", [rf"{N(4)}|cuatro"], src="Art.41 p.14")
add("U05", "lookup", "¿Qué porcentaje de las vacantes ordinarias se reserva para el CEPUNT?", "40% (Art. 34)", [N(40)], src="Art.34 p.13")
add("U06", "lookup", "¿Qué porcentaje de las vacantes de cada carrera es para personas con discapacidad?", "5% (Art. 35)", [N(5)], src="Art.35 p.13")
add("U07", "lookup", "¿Cuántas vacantes por carrera están reservadas para los de quinto de secundaria?", "3 (Art. 32)", [rf"{N(3)}|tres"], src="Art.32 p.13")
add("U08", "lookup", "¿Cuál es el máximo de vacantes de traslados por programa profesional?", "6 (Art. 37)", [rf"{N(6)}|seis"], src="Art.37 p.14")
add("U09", "list", "¿Cuántas vacantes hay como máximo para segunda profesión y en qué fase participan?",
    "máximo 4 por programa, solo fase II (Art. 38)", [rf"{N(4)}|cuatro", r"fase ii|segunda fase|fase 2"], src="Art.38 p.14")
add("U10", "lookup", "¿Cuántos años no puedo volver a postular si me sorprenden copiando?", "5 años (Art. 56)", [rf"{N(5)}|cinco"], src="Art.56 p.18")
add("U11", "lookup", "¿Cuántos postulantes de Medicina clasifican al segundo examen?", "los 60 primeros puestos (Art. 39a)", [rf"{N(60)}|sesenta"], src="Art.39 p.14")
add("U12", "lookup", "¿Cuánto tiempo como máximo debe demandar resolver cada pregunta?", "1.8 minutos (Art. 48e)", [r"1[.,]8"], src="Art.48 p.17")
add("U13", "lookup", "¿Cuántas alternativas tiene cada pregunta?", "cinco (Art. 48a)", [rf"{N(5)}|cinco"], src="Art.48 p.17")
add("U14", "lookup", "¿Qué tamaño máximo puede tener la foto que subo al inscribirme?", "2 megabytes (Art. 15b)", [r"(?<!\d)2(?!\d)\s*(mb|megabyte)|dos megabyte"], src="Art.15 p.8")
add("U15", "lookup", "¿Qué porcentaje de las vacantes corresponde a la admisión ordinaria?", "55% (Art. 31)", [N(55)], src="Art.31 p.13")
add("U16", "lookup", "¿Cuántos créditos tengo que haber aprobado para un traslado externo?", "72 créditos (o cuatro semestres / dos años) (Art. 20)", [N(72)], src="Art.20 p.10")
add("U17", "list", "¿Qué porcentaje mínimo y máximo de vacantes se reserva para premios de excelencia?", "mínimo 5% y máximo 10% (Art. 33)", [N(5), N(10)], src="Art.33 p.13")
add("U18", "list", "¿Cuántos exámenes sumativos tiene el CEPUNT y de cuántas preguntas cada uno?", "tres sumativos de 100 preguntas cada uno (Art. 44)",
    [rf"{N(3)}|tres", N(100)], src="Art.44 p.16")
add("U19", "lookup", "Si estoy en quinto de secundaria, ¿a cuántas carreras puedo postular?", "una sola (Disposición Segunda)", [r"\buna\b|\b1\b|sola|unica"], src="Disp. Segunda p.23")
add("U20", "list", "¿Qué descuento hay en el derecho de inscripción para hijos de docentes?", "100% en la primera postulación y 50% en la segunda, hasta dos (Art. 70)",
    [N(100), N(50)], src="Art.70 p.20")
# ---- yes/no, rules, procedures (colloquial) ----
add("U21", "open", "¿Qué documentos tengo que subir para inscribirme por la modalidad ordinaria?",
    "recibo de pago; foto digital a color fondo blanco; DNI/carné/pasaporte (Art. 15)",
    [r"recibo|pago", r"fotografia|foto", r"dni|identidad|carne|pasaporte"], src="Art.15 p.8")
add("U22", "open", "Si no logro vacante por el CEPUNT, ¿puedo postular al examen ordinario?",
    "Sí, si me inscribo dentro de los plazos (Art. 14h)", [r"\bsi\b|puede", r"plazo|inscri"], src="Art.14 p.7")
add("U23", "open", "¿Me devuelven el pago de inscripción si ya me inscribí?",
    "No: no tiene derecho a la devolución (Art. 83)", [r"no (tendra|tiene|hay|se devuelve|se le devolvera|procede)|no .{0,25}devol|ninguna devolucion"], src="Art.83 p.22")
add("U24", "open", "¿Hasta cuántos procesos puede postular un egresado de COAR o premio de excelencia?",
    "hasta tres procesos consecutivos (Art. 75)", [rf"{N(3)}|tres"], src="Art.75 p.21")
add("U25", "open", "¿Se puede ingresar por segunda opción?", "No (Art. 61)", [r"\bno\b"], src="Art.61 p.19")
add("U26", "open", "¿Se pueden apelar o revisar los resultados del examen?", "No: son inapelables e irrevisables (Art. 40)",
    [r"inapelable|irrevisable|no .{0,30}(apel|revis)"], src="Art.40 p.14")
add("U27", "open", "¿Qué pasa si pongo datos falsos en mi ficha de inscripción?",
    "separado del concurso y sancionado (Art. 88)", [r"separad", r"sancion"], src="Art.88 p.22")
add("U28", "open", "¿Qué le pasa a un estudiante de la UNT que suplanta a un postulante?",
    "es denunciado ante el Tribunal de Honor para su separación (Art. 89)", [r"tribunal de honor"], src="Art.89 p.22")
add("U29", "open", "Soy titulado universitario, ¿puedo postular a pregrado ordinario?",
    "No; solo por segunda profesión o segunda especialidad (Art. 80)", [r"\bno\b", r"segunda profesion|segunda especialidad"], src="Art.80 p.21")
add("U30", "open", "¿Puedo cambiarme de carrera después de inscribirme?",
    "Sí, pagando un nuevo derecho de inscripción, dentro del cronograma y antes de los padrones finales (Art. 79)",
    [r"nuevo derecho|nuevo pago|pagar|pago", r"padrones|cronograma"], src="Art.79 p.21")
add("U31", "open", "¿Pueden postular personas condenadas por terrorismo?", "No, están impedidas (Art. 81)", [r"impedid|no pueden|no podran|prohib", r"terroris"], src="Art.81 p.22")
add("U32", "open", "¿Qué hace la universidad con las vacantes que sobran en el ordinario de la primera fase?",
    "pasan a incrementar las vacantes del ordinario de la segunda fase (Art. 29)", [r"fase ii|segunda fase|fase 2", r"increment|pasan|suman|aument"], src="Art.29 p.12")
add("U33", "list", "¿Cuáles son las modalidades de admisión de la UNT?",
    "ordinario (y 5to de secundaria), extraordinario, CEPUNT, traslados y segunda profesión, segundas especialidades, posgrado (Art. 10)",
    [r"ordinari", r"extraordinari", r"cepunt", r"traslado", r"segunda"], src="Art.10 p.6")
add("U34", "locate", "¿Qué prueba rinde Medicina?", "Prueba A (Ciencias de la vida y la salud) (Art. 42)", [r"prueba a"], src="Art.42 p.14")
add("U35", "locate", "¿Qué prueba rinde Ingeniería de Sistemas?", "Prueba B (Ciencias Básicas y Tecnológicas) (Art. 42)", [r"prueba b"], src="Art.42 p.14")
add("U36", "locate", "¿Quién califica las respuestas de los postulantes?", "la OTI (Art. 59)", [r"oti|tecnologias de la informacion"], src="Art.59 p.19")
add("U37", "locate", "¿Quién prepara la prueba de admisión?", "una comisión especial designada por la DAD con el Vicerrectorado Académico (Art. 46)", [r"comision"], src="Art.46 p.16")
add("U38", "locate", "¿Dónde se publican primero los resultados?", "página web de la Universidad, de la DAD y del CEPUNT (Art. 60)", [r"web|pagina"], src="Art.60 p.19")
add("U39", "open", "¿Puedo inscribirme en dos carreras a la vez, una en la sede central y otra en una filial?", "No (Art. 82)", [r"\bno\b"], src="Art.82 p.22")
add("U40", "open", "¿Qué pasa si no llego a la hora del examen?", "pierden todo derecho (Art. 55)", [r"pierd|perder"], src="Art.55 p.18")
add("U41", "open", "¿Los docentes que enseñan en academias pueden estar en las comisiones del examen?",
    "No en las comisiones de elaboración, traslado y calificación, ni en el cuidado de aulas (Art. 93)", [r"\bno\b|excepto|no pueden", r"comision|elaboracion|calificacion"], src="Art.93 p.22")
add("U42", "locate", "¿Quién aprueba el cronograma de admisión?", "el Consejo Universitario a propuesta de la DAD (Art. 13)", [r"consejo universitario"], src="Art.13 p.7")
add("U43", "open", "¿Un profesor de la UNT puede postular a una carrera de pregrado ahí mismo?", "No (Art. 95)", [r"\bno\b"], src="Art.95 p.22")
add("U44", "open", "¿Cuántos de los de quinto de secundaria ingresan directamente?", "los tres primeros puestos (Disposición Segunda)", [rf"{N(3)}|tres"], src="Disp. Segunda p.23")
add("U45", "open", "¿Qué se le exige al ingresante extranjero para acreditar su ingreso?",
    "los requisitos del art. 64 con certificados convalidados por el órgano competente del Ministerio de Educación (Art. 66)", [r"convalid"], src="Art.66 p.20")
add("U46", "open", "Me expulsaron del CEPUNT por indisciplina, ¿por cuánto tiempo?", "mínimo cinco años (Art. 87)", [rf"{N(5)}|cinco"], src="Art.87 p.22")
add("U47", "open", "¿El carnet o constancia de inscripción es suficiente para entrar al examen?",
    "Debe llevarse la constancia de inscripción y el DNI, carné de extranjería o pasaporte (Art. 25)", [r"constancia", r"dni|identidad|carne|pasaporte"], src="Art.25 p.10-11")
add("U48", "open", "¿Si hago trampa en el examen qué me pasa?",
    "separado inmediatamente, denunciado, y no puede postular a la UNT por cinco años (Art. 56)", [r"separad|denunci", rf"{N(5)}|cinco"], src="Art.56 p.18")
add("U49", "open", "¿Quién se encarga de todo el proceso de admisión en la UNT?",
    "la Dirección de Admisión (DAD), bajo supervisión del Vicerrectorado Académico (Art. 11)", [r"direccion de admision|dad"], src="Art.11 p.6")
# ---- in-domain but not in the document ----
for i, (q, g) in enumerate([
    ("¿Cuánto cuesta la inscripción en soles?", "el reglamento no indica montos"),
    ("¿En qué fecha es el examen de admisión?", "no hay cronograma en este documento"),
    ("¿Cuántas vacantes ofrece Medicina?", "no hay cuadro de vacantes en este documento"),
    ("¿Cuál es el puntaje mínimo aprobatorio para ingresar?", "el documento no fija un valor; lo determina la DAD"),
    ("¿Cuántos postulantes se presentaron el año pasado?", "no figura en el documento"),
    ("¿A qué hora empieza el examen?", "no figura en el documento"),
], 50):
    add(f"U{i}", "unanswerable", q, g, abstain=True, src="verified absent from the document text")
# ---- out of domain ----
for i, q in enumerate([
    "¿Cuál es la capital de Francia?", "¿Quién ganó el último mundial de fútbol?", "Escríbeme un poema sobre el mar",
    "¿Cuánto es 15 por 12?", "Recomiéndame una receta de ceviche", "¿Cómo va a estar el clima mañana en Trujillo?",
    "¿Cuándo son las inscripciones de la Universidad de Lima?", "¿Dónde puedo comprar un celular barato?",
], 56):
    add(f"U{i}", "ood", q, "fuera del dominio", abstain=True, src="n/a")

out = {"status": "UNT_BANK_WRITTEN_BEFORE_RUNNING", "n": len(items), "document": "Universidad Nacional de Trujillo, Reglamento de Admision (native-text PDF, 23 pp.)",
       "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "consultas": items}
(HERE / "unt_bank.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
import collections
print(len(items), collections.Counter(i["type"] for i in items))
print("sha256", hashlib.sha256((HERE / "unt_bank.json").read_bytes()).hexdigest())
