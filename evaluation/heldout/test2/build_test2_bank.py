"""TEST bank #2 (final test set). Written BEFORE any system change and BEFORE any system is run on it.
Gold answers were read by the author from page images of the official CEPRUNSA PDFs (schedule p.2-3, vacancies p.3-4,
syllabus pp.9-33, regulation pp.14-17) and cross-checked for internal consistency (row sums of the vacancy table).
Questions here do NOT reuse the developing bank (89 items) nor the 500-item bank phrasing; articles/topics partly overlap in
the same documents (unavoidable: one cycle of documents) but with different wording and different items.
"""
import json, hashlib, datetime, random, difflib, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent


def N(n):
    return rf"(?<![\d.,/]){n}(?![\d/])"


def D(dd, mm, yyyy, month):
    return rf"{dd}[/-]{mm}[/-]{yyyy}|{int(dd)} de {month}"


items = []


def add(id_, cat, typ, q, gold, must=None, abstain=False, src=""):
    items.append(dict(id=id_, category=cat, type=typ, query=q, gold=gold, must=must or [], abstain=abstain, source=src))


# ---------------------------------------------------------------- VACANTES (table, transcribed from page 3 image)
cols = ["o1", "o2", "ot", "c1", "c2", "cq", "ct", "pe", "mo", "ca", "tg"]
T = {
    "Ingeniería Agronómica": (15, 23, 38, 10, 10, 12, 32, 70, 0, 0, 140), "Biología": (30, 30, 60, 8, 7, 8, 23, 0, 0, 0, 83),
    "Ciencias de la Nutrición": (20, 23, 43, 12, 13, 15, 40, 0, 0, 0, 83), "Ingeniería Pesquera": (14, 17, 31, 10, 11, 12, 33, 0, 0, 0, 64),
    "Enfermería": (15, 22, 37, 11, 12, 14, 37, 0, 0, 0, 74), "Medicina": (13, 17, 30, 12, 12, 13, 37, 0, 0, 0, 67),
    "Arquitectura": (25, 30, 55, 18, 18, 19, 55, 0, 0, 0, 110), "Física": (16, 20, 36, 11, 13, 11, 35, 0, 0, 0, 71),
    "Matemáticas": (15, 17, 32, 12, 11, 9, 32, 0, 0, 0, 64), "Química": (28, 30, 58, 14, 14, 14, 42, 0, 0, 0, 100),
    "Ingeniería Geológica": (24, 24, 48, 7, 7, 7, 21, 0, 0, 0, 69), "Ingeniería Geofísica": (15, 16, 31, 10, 10, 11, 31, 0, 0, 0, 62),
    "Ingeniería de Minas": (28, 28, 56, 14, 14, 16, 44, 0, 0, 0, 100), "Ingeniería Civil": (18, 23, 41, 13, 12, 13, 38, 0, 0, 0, 79),
    "Ingeniería Sanitaria": (6, 9, 15, 5, 4, 5, 14, 0, 0, 0, 29), "Ingeniería Metalúrgica": (16, 19, 35, 11, 11, 13, 35, 0, 0, 0, 70),
    "Ingeniería Química": (25, 27, 52, 16, 16, 20, 52, 0, 0, 0, 104), "Ingeniería de Industrias Alimentarias": (23, 33, 56, 18, 18, 18, 54, 0, 0, 0, 110),
    "Ingeniería de Materiales": (14, 21, 35, 12, 12, 11, 35, 0, 0, 0, 70), "Ingeniería Ambiental": (15, 16, 31, 11, 11, 10, 32, 0, 0, 0, 63),
    "Ingeniería Electrónica": (20, 27, 47, 15, 15, 17, 47, 0, 0, 0, 94), "Ingeniería Industrial": (27, 29, 56, 17, 18, 21, 56, 0, 0, 0, 112),
    "Ingeniería Mecánica": (23, 24, 47, 15, 15, 17, 47, 0, 0, 0, 94), "Ingeniería Eléctrica": (19, 23, 42, 13, 14, 15, 42, 0, 0, 0, 84),
    "Ingeniería de Sistemas": (18, 20, 38, 11, 12, 12, 35, 0, 0, 0, 73), "Ciencias de la Computación": (14, 16, 30, 10, 10, 10, 30, 0, 0, 0, 60),
    "Ingeniería de Telecomunicaciones": (14, 16, 30, 9, 9, 9, 27, 0, 0, 0, 57), "Administración": (25, 29, 54, 18, 17, 21, 56, 40, 40, 40, 230),
    "Marketing": (9, 11, 20, 8, 8, 9, 25, 0, 0, 0, 45), "Banca y Seguros": (9, 11, 20, 8, 8, 8, 24, 0, 0, 0, 44),
    "Gestión Pública": (5, 8, 13, 5, 4, 6, 15, 0, 0, 0, 28), "Gestión de Empresas": (7, 9, 16, 7, 7, 6, 20, 0, 0, 0, 36),
    "Contabilidad": (40, 50, 90, 31, 32, 27, 90, 0, 20, 0, 200), "Finanzas": (23, 28, 51, 15, 15, 13, 43, 0, 0, 0, 94),
    "Historia": (24, 26, 50, 7, 7, 9, 23, 0, 0, 0, 73), "Sociología": (24, 29, 53, 7, 7, 9, 23, 0, 0, 0, 76),
    "Trabajo Social": (38, 42, 80, 10, 10, 10, 30, 0, 0, 0, 110), "Antropología": (14, 16, 30, 10, 10, 10, 30, 0, 0, 0, 60),
    "Turismo y Hotelería": (28, 32, 60, 10, 10, 10, 30, 0, 0, 0, 90), "Derecho": (38, 42, 80, 29, 27, 24, 80, 0, 0, 0, 160),
    "Economía": (42, 48, 90, 30, 31, 29, 90, 0, 0, 0, 180), "Filosofía": (25, 29, 54, 3, 2, 7, 12, 0, 0, 0, 66),
    "Literatura y Lingüística": (18, 22, 40, 14, 13, 13, 40, 0, 0, 0, 80), "Psicología": (34, 47, 81, 27, 29, 24, 80, 0, 0, 0, 161),
    "Relaciones Industriales": (34, 40, 74, 21, 24, 29, 74, 0, 0, 0, 148), "Periodismo": (20, 25, 45, 19, 17, 11, 47, 0, 0, 0, 92),
    "Relaciones Públicas": (30, 35, 65, 25, 22, 16, 63, 0, 0, 0, 128),
}
for k, v in T.items():  # internal-consistency check of my transcription
    assert v[0] + v[1] == v[2], k
    assert v[3] + v[4] + v[5] == v[6], k
    assert v[2] + v[6] + v[7] + v[8] + v[9] == v[10], (k, v)
TPL = {
    "o1": ["¿Cuántas vacantes hay para {p} en la primera fase del ordinario?", "{p}: ¿cuántos cupos en el ordinario fase 1?", "vacantes de {p}, ordinario, fase I"],
    "o2": ["¿Cuántas vacantes hay para {p} en la segunda fase del ordinario?", "{p}: ¿cuántos cupos en el ordinario fase 2?", "vacantes de {p} ordinario segunda fase"],
    "ot": ["¿Cuántas vacantes tiene {p} en total en el proceso ordinario?", "total de vacantes ordinarias de {p}", "{p}: suma de las dos fases del ordinario"],
    "c1": ["¿Cuántas vacantes de {p} hay por CEPRUNSA primera fase?", "CEPRUNSA fase I, {p}: ¿cuántos cupos?"],
    "c2": ["¿Cuántas vacantes de {p} hay por CEPRUNSA segunda fase?", "CEPRUNSA fase II, {p}: ¿cuántos cupos?"],
    "cq": ["¿Cuántas vacantes de {p} hay en el ciclo quintos de CEPRUNSA?", "cupos de {p} para ciclo quintos"],
    "ct": ["¿Cuántas vacantes de {p} tiene CEPRUNSA en total?", "total de vacantes CEPRUNSA para {p}"],
    "tg": ["¿Cuántas vacantes tiene {p} sumando ordinario, CEPRUNSA y filiales?", "total general de vacantes de {p}"],
}
rnd = random.Random(7)
progs = sorted(T)
rnd.shuffle(progs)
cols_pool = ["o1", "o2", "ot", "c1", "c2", "cq", "ct", "tg"]
n = 0
for p in progs[:31]:
    c = rnd.choice(cols_pool)
    q = rnd.choice(TPL[c]).format(p=p)
    n += 1
    g = T[p][cols.index(c)]
    add(f"W{n:02d}", "VACANTES", "lookup", q, f"{g}", [N(g)], src="CUADRO DE VACANTES 2027 p.3")
add("W32", "VACANTES", "lookup", "¿Cuántas vacantes de Contabilidad hay en la filial de Mollendo?", "20", [N(20)], src="p.3")
add("W33", "VACANTES", "lookup", "¿Cuántas vacantes tiene Administración en El Pedregal?", "40", [N(40)], src="p.3")
add("W34", "VACANTES", "aggregate", "¿Cuántas vacantes ordinarias suman Medicina y Enfermería?", "67 (30 + 37)", [N(67)], src="p.3")
add("W35", "VACANTES", "multistep", "¿Cuántas vacantes de CEPRUNSA más que Medicina tiene Derecho en total?", "43 (80 - 37)", [N(43)], src="p.3")
add("W36", "VACANTES", "superlative", "¿Cuál es la ingeniería con más vacantes sumando todo?", "Ingeniería Industrial (112)", [r"industrial", N(112)], src="p.3")
add("W37", "VACANTES", "superlative", "¿Qué carrera del área de ciencias biológicas tiene más vacantes en total?", "Ingeniería Agronómica (140)", [r"agronomic", N(140)], src="p.3")
add("W38", "VACANTES", "aggregate", "¿Cuántas vacantes tiene el ordinario en la fase I sumando todas las carreras?", "1106", [N(1106) if False else r"1[ .,]?106"], src="p.3")
add("W39", "VACANTES", "aggregate", "¿Cuántas vacantes ofrece CEPRUNSA en total para todas las carreras?", "2105", [r"2[ .,]?105"], src="p.3")
add("W40", "VACANTES", "aggregate", "¿Cuántas vacantes hay en total en las tres filiales?", "210 (110 + 60 + 40)", [N(210)], src="p.3")
add("W41", "VACANTES", "aggregate", "¿Cuántas vacantes tienen en total las carreras biomédicas?", "511", [N(511)], src="p.3")
add("W42", "VACANTES", "locate", "¿Qué carrera tiene exactamente 29 vacantes en total?", "Ingeniería Sanitaria", [r"sanitaria"], src="p.3")
add("X11", "VACANTES", "lookup", "En el proceso extraordinario, ¿cuántas vacantes totales tiene Ingeniería Pesquera?", "27", [N(27)], src="p.4")
add("X12", "VACANTES", "lookup", "Extraordinario: ¿cuántos cupos de primeros puestos tiene Ciencias de la Nutrición?", "6", [N(6)], src="p.4")
add("X13", "VACANTES", "lookup", "¿Cuántas vacantes extraordinarias en total hay para Matemáticas?", "24", [N(24)], src="p.4")
add("X14", "VACANTES", "lookup", "En Biología, ¿cuántas vacantes del extraordinario son para personas con discapacidad?", "4", [N(4)], src="p.4")
add("X15", "VACANTES", "lookup", "¿Cuántos primeros puestos entran por el extraordinario a Arquitectura?", "7", [N(7)], src="p.4")

# ---------------------------------------------------------------- CRONOGRAMA
c2, c3 = "CRONOGRAMA p.2", "CRONOGRAMA p.3"
for i, (q, g, p, src) in enumerate([
    ("¿Cuándo empiezan las clases del ciclo quintos?", D("24", "08", "2026", "agosto"), "24/08/2026", c2),
    ("¿Cuándo es la evaluación previa del ordinario de primera fase?", D("02", "08", "2026", "agosto"), "02/08/2026", c2),
    ("¿Qué día es la evaluación de conocimientos del ordinario I fase?", D("09", "08", "2026", "agosto"), "09/08/2026", c2),
    ("¿Cuándo comienzan las clases del extraordinario?", D("01", "02", "2027", "febrero"), "01/02/2027", c2),
    ("¿Cuándo es la evaluación previa del examen extraordinario?", D("14", "02", "2027", "febrero"), "14/02/2027", c2),
    ("¿Desde cuándo me puedo inscribir al ordinario de segunda fase?", D("01", "02", "2027", "febrero"), "01/02/2027", c3),
    ("¿Cuándo es la evaluación previa del ordinario II?", D("07", "03", "2027", "marzo"), "07/03/2027", c3),
    ("¿Desde qué fecha abren inscripciones para las filiales?", D("01", "03", "2027", "marzo"), "01/03/2027", c3),
    ("¿Cuándo abren las inscripciones del ciclo quintos?", D("27", "07", "2026", "julio"), "27/07/2026", c2),
    ("¿Desde cuándo se puede inscribir uno al ordinario de primera fase?", D("22", "06", "2026", "junio"), "22/06/2026", c2),
    ("¿Cuándo empiezan las inscripciones de CEPRUNSA segunda fase?", D("12", "10", "2026", "octubre"), "12/10/2026", c2),
    ("¿Hasta qué día me puedo inscribir en CEPRUNSA II?", D("06", "11", "2026", "noviembre"), "06/11/2026", c2),
    ("¿Desde qué fecha me inscribo al extraordinario?", D("04", "01", "2027", "enero"), "04/01/2027", c2),
    ("¿Qué día es la evaluación de conocimientos del CEPRUNSA segunda fase?", D("24", "01", "2027", "enero"), "24/01/2027", c2),
    ("¿Cuándo se da la evaluación de conocimientos del ciclo quintos?", D("01", "11", "2026", "noviembre"), "01/11/2026", c2),
], 1):
    add(f"S{i:02d}", "CRONOGRAMA", "lookup", q, g if False else p, [g], src=src)
add("S16", "CRONOGRAMA", "multistep", "¿Cuántos días dura la inscripción del ordinario de primera fase?", "25 días (22/06/2026 a 17/07/2026)", [rf"{N(25)}|veinticinco"], src=c2)
add("S17", "CRONOGRAMA", "comparison", "¿Qué se rinde primero, el examen de conocimientos de CEPRUNSA I o el del ordinario I?",
    "CEPRUNSA I (05/07/2026) antes que ordinario I (09/08/2026)", [r"ceprunsa", D("05", "07", "2026", "julio")], src=c2)

# ---------------------------------------------------------------- TEMARIO (lists from the syllabus pages)
TM = "TEMARIO pp.9-33"
L = lambda *xs: list(xs)
add("Q01", "TEMARIO", "list", "¿Qué principios de configuración electrónica se estudian en química?", "Aufbau, Hund y exclusión de Pauli", L(r"aufbau", r"hund", r"pauli"), src=TM)
add("Q02", "TEMARIO", "list", "¿Qué propiedades periódicas entran en el examen?", "radio atómico e iónico, energía de ionización, electronegatividad, carácter metálico",
    L(r"radio atomico", r"ionizacion", r"electronegatividad", r"metalico"), src=TM)
add("Q03", "TEMARIO", "list", "¿Qué sistemas de nomenclatura química tengo que saber?", "tradicional, Stock y sistemática (IUPAC)", L(r"tradicional", r"stock", r"sistematica|iupac"), src=TM)
add("Q04", "TEMARIO", "list", "¿Qué funciones químicas inorgánicas se evalúan?", "óxidos, hidruros, ácidos, bases y sales", L(r"oxido", r"hidruro", r"acido", r"bases", r"sales"), src=TM)
add("Q05", "TEMARIO", "list", "¿Qué unidades de concentración entran en soluciones?", "porcentuales, molaridad y normalidad", L(r"porcentual", r"molaridad", r"normalidad"), src=TM)
add("Q06", "TEMARIO", "list", "¿Qué teorías ácido-base se estudian?", "Arrhenius y Brønsted-Lowry", L(r"arrhenius", r"bronsted|lowry"), src=TM)
add("Q07", "TEMARIO", "list", "¿Qué se ve del estado gaseoso en química?", "teoría cinético-molecular, leyes de los gases, gas ideal, Dalton, Graham", L(r"dalton", r"graham", r"gas ideal"), src=TM)
add("Q08", "TEMARIO", "list", "¿Qué tipos de cálculos estequiométricos hay?", "masa-masa, mol-mol, volumen-volumen", L(r"masa.{0,3}masa", r"mol.{0,3}mol", r"volumen.{0,3}volumen"), src=TM)
add("Q09", "TEMARIO", "list", "¿Qué entra en estática en física?", "fuerzas concurrentes, fuerza elástica, torque o momento de fuerza, condiciones de equilibrio",
    L(r"concurrentes", r"elastica", r"torque|momento", r"equilibrio"), src=TM)
add("Q10", "TEMARIO", "list", "¿Qué tipos de colisiones se estudian en física?", "elásticas e inelásticas", L(r"elastica", r"inelastica"), src=TM)
add("Q11", "TEMARIO", "locate", "¿En qué tema de física se ven las leyes de Kepler?", "Cantidad de movimiento y gravitación", L(r"gravitacion|cantidad de movimiento"), src=TM)
add("Q12", "TEMARIO", "list", "¿Qué se ve en hidrostática?", "densidad, presión, Pascal, Arquímedes, flotación, tensión superficial",
    L(r"densidad", r"presion", r"pascal", r"arquimedes", r"flotacion"), src=TM)
add("Q13", "TEMARIO", "list", "¿Qué leyes entran en inducción electromagnética?", "ley de Faraday, ley de Lenz (flujo magnético, generadores y transformadores)", L(r"faraday", r"lenz"), src=TM)
add("Q14", "TEMARIO", "list", "¿Qué temas de óptica se evalúan?", "propagación de la luz, reflexión, refracción, espejos, lentes delgadas, espectro electromagnético",
    L(r"reflexion", r"refraccion", r"espejos", r"lentes"), src=TM)
add("Q15", "TEMARIO", "list", "¿Qué medidas de dispersión entran en estadística descriptiva?", "rango, varianza y desviación estándar", L(r"rango", r"varianza", r"desviacion estandar"), src=TM)
add("Q16", "TEMARIO", "list", "¿Qué temas de análisis combinatorio hay en aritmética?", "factorial, variaciones, combinaciones, permutaciones", L(r"factorial", r"variaciones", r"combinaciones", r"permutaciones"), src=TM)
add("Q17", "TEMARIO", "list", "¿Qué métodos para resolver sistemas de ecuaciones se estudian?", "sustitución, igualación y reducción", L(r"sustitucion", r"igualacion", r"reduccion"), src=TM)
add("Q18", "TEMARIO", "list", "¿Cómo se estudia la división de polinomios?", "método clásico y regla de Ruffini; teoremas del residuo y del factor", L(r"ruffini", r"clasico"), src=TM)
add("Q19", "TEMARIO", "list", "¿Qué casos de factorización se ven?", "factor común, por agrupación, diferencia de cuadrados, trinomios, suma y diferencia de cubos",
    L(r"agrupacion", r"cuadrados", r"cubos"), src=TM)
add("Q20", "TEMARIO", "list", "¿Qué puntos notables del triángulo se estudian?", "baricentro, circuncentro, ortocentro, incentro, excentro",
    L(r"baricentro", r"circuncentro", r"ortocentro", r"incentro", r"excentro"), src=TM)
add("Q21", "TEMARIO", "list", "¿Qué cuerpos de revolución entran en geometría?", "cilindro, tronco de cilindro, cono, tronco de cono y esfera", L(r"cilindro", r"cono", r"esfera"), src=TM)
add("Q22", "TEMARIO", "list", "¿Qué sistemas de medida angular se usan en trigonometría?", "sexagesimal, centesimal y radial", L(r"sexagesimal", r"centesimal", r"radial"), src=TM)
add("Q23", "TEMARIO", "list", "¿Qué ángulos notables entran en trigonometría?", "30°, 45°, 60°, 37° y 53°", L(N(30), N(45), N(60), N(37), N(53)), src=TM)
add("Q24", "TEMARIO", "list", "¿Qué curvas se ven en geometría analítica?", "circunferencia, parábola y elipse (además de la recta)", L(r"circunferencia", r"parabola", r"elipse"), src=TM)
add("Q25", "TEMARIO", "aggregate", "¿Cuántos temas tiene álgebra?", "16 (I a XVI)", [rf"{N(16)}|dieciseis"], src=TM)
add("Q26", "TEMARIO", "list", "¿Qué se estudia de números complejos?", "definición y forma binómica, módulo, conjugado, operaciones", L(r"binomic", r"modulo", r"conjugado"), src=TM)
add("Q27", "TEMARIO", "list", "¿Qué aplicaciones aritméticas hay dentro de sumatorias?", "interés, descuento, mezclas y aleaciones", L(r"interes", r"descuento", r"mezclas", r"aleaciones"), src=TM)
add("Q28", "TEMARIO", "list", "¿Qué estados físicos de la materia se estudian en química?", "gaseoso, líquido y sólido", L(r"gaseoso", r"liquido", r"solido"), src=TM)
add("Q29", "TEMARIO", "list", "¿Qué clases de progresiones hay en aritmética?", "aritmética y geométrica", L(r"aritmetic", r"geometric"), src=TM)
add("Q30", "TEMARIO", "list", "¿Qué subtemas hay en la factorización de trinomios?", "trinomio cuadrado perfecto; x²+bx+c; ax²+bx+c con a≠1", L(r"trinomio"), src=TM)

# ---------------------------------------------------------------- REGLAMENTO (articles 39-80; colloquial, no article number)
RG = "REGLAMENTO pp.11-17 (printed)"
add("G01", "REGLAMENTO", "open", "Si no alcancé vacante en un examen, ¿puedo inscribirme en el siguiente?", "Sí, previo pago de los derechos correspondientes (Art. 39)", [r"\bsi\b|puede|podra", r"pago|derechos"], src=RG)
add("G02", "REGLAMENTO", "open", "¿Qué puntaje necesito para ganar vacante en el ordinario?", "igual o superior a la mediana calculada del programa, en estricto orden de mérito (Art. 41)", [r"mediana"], src=RG)
add("G03", "REGLAMENTO", "open", "Si hay empate en la última vacante, ¿qué pasa?", "ingresan todos los postulantes con ese puntaje (Art. 43)", [r"todos|ingresan|ingresaran"], src=RG)
add("G04", "REGLAMENTO", "open", "¿Cómo califican mi examen?", "de manera anónima y automatizada, con apoyo de la OTI (Art. 44)", [r"automatizad|anonim"], src=RG)
add("G05", "REGLAMENTO", "open", "¿Qué ficha me dan el día del examen?", "ficha óptica desglosable: identificación (izquierda) y respuestas (derecha) (Art. 45)", [r"ficha optica", r"identificacion", r"respuestas"], src=RG)
add("G06", "REGLAMENTO", "open", "¿Si uso un celular durante el examen qué me pasa?", "calificado con cero (Art. 48.7)", [r"cero|\b0\b"], src=RG)
add("G07", "REGLAMENTO", "list", "¿En qué casos me califican con cero?", "no rinde; llena mal el código o marca un tema que no corresponde; recibe ayuda; usa equipos de comunicación; altera el orden…",
    [r"ayuda", r"equipo|aparato|comunicacion", r"codigo|tema"], src=RG)
add("G08", "REGLAMENTO", "list", "¿Dónde están las filiales de la UNSA?", "provincias de Camaná, Caylloma (El Pedregal) e Islay (Mollendo) (Art. 49)", [r"camana", r"caylloma|pedregal", r"islay|mollendo"], src=RG)
add("G09", "REGLAMENTO", "lookup", "¿Cuál es el máximo de inasistencias en el CEPRUNSA?", "30% del total de clases (Art. 60)", [N(30)], src=RG)
add("G10", "REGLAMENTO", "lookup", "¿Cuándo se considera que asistí a una clase del CEPRUNSA?", "cuando permanezca más del 50% de la duración de la clase (Art. 60)", [N(50)], src=RG)
add("G11", "REGLAMENTO", "open", "¿Cuántas evaluaciones rindo en la modalidad CEPRUNSA?", "una sola (Art. 59)", [r"\buna\b|\b1\b|sola|unica"], src=RG)
add("G12", "REGLAMENTO", "open", "¿Qué pasa si incumplo las normas de convivencia del CEPRUNSA?", "puede dar lugar a la suspensión de su preparación (Art. 63)", [r"suspension|suspend"], src=RG)
add("G13", "REGLAMENTO", "open", "Si me inscribí en una filial, ¿me devuelven el pago?", "Por ningún motivo procede la devolución (p.14)", [r"ningun motivo|no procede|no .{0,25}devol"], src=RG)
add("G14", "REGLAMENTO", "lookup", "¿Cuánto dura el ciclo de preparación del extraordinario?", "tres (3) semanas (Art. 77)", [rf"{N(3)}|tres", r"semana"], src=RG)
add("G15", "REGLAMENTO", "list", "¿Qué días se dictan las clases del ciclo de preparación del extraordinario?", "de lunes a sábado, un solo turno, virtual sincrónica (Art. 77)", [r"lunes", r"sabado"], src=RG)
add("G16", "REGLAMENTO", "lookup", "En el ciclo del extraordinario, ¿qué porcentaje de inasistencias se permite?", "10% (Art. 77)", [N(10)], src=RG)
add("G17", "REGLAMENTO", "list", "¿Cómo se pondera la evaluación del ciclo del extraordinario?", "razonamiento lógico y matemático 50%; verbal y comprensión lectora 50% (Art. 78)", [N(50), r"verbal|comprension|logico|matematic"], src=RG)
add("G18", "REGLAMENTO", "open", "Quiero entrar a Arquitectura por traslado externo, ¿rindo evaluación previa?", "No, están exceptuados (Art. 80)", [r"\bno\b|exceptuad"], src=RG)
add("G19", "REGLAMENTO", "list", "¿Quiénes participan en el ciclo de preparación del examen extraordinario?", "primeros puestos, deportistas, Bachillerato Internacional, COAR, CAB, discapacidad, víctimas del terrorismo y de la violencia (Art. 76)",
    [r"deportista", r"coar", r"discapacidad", r"terroris|violencia"], src=RG)
add("G20", "REGLAMENTO", "list", "¿Qué periodo de violencia da derecho a las vacantes de víctimas?", "entre mayo de 1980 y noviembre de 2000 (Art. 76.8)", [r"1980", r"2000"], src=RG)
add("G21", "REGLAMENTO", "open", "En CEPRUNSA, ¿hasta cuándo puedo cambiar de programa de estudios?", "hasta antes del inicio de clases del programa, previa autorización de la DA (Art. 64)", [r"inicio de clases"], src=RG)
add("G22", "REGLAMENTO", "open", "¿Para qué sirve el CEPRUNSA según el reglamento?", "preparar y capacitar a los postulantes que se acogen voluntariamente (Art. 57)", [r"preparar|capacitar"], src=RG)
add("G23", "REGLAMENTO", "open", "Para el ciclo quintos, ¿qué documento piden además de los del artículo 27?", "constancia de matrícula emitida por el SIAGIE (Art. 70)", [r"siagie"], src=RG)
add("G24", "REGLAMENTO", "open", "En ciclo quintos, ¿quién se encarga de regularizar mi expediente?", "la OTI (Art. 74)", [r"oti|tecnologias de la informacion"], src=RG)
add("G25", "REGLAMENTO", "open", "¿En CEPRUNSA puedo pedir que me exoneren de la deuda?", "No, bajo ningún concepto (Art. 68.2)", [r"\bno\b"], src=RG)
add("G26", "REGLAMENTO", "open", "¿Qué pasa si no respondo las encuestas de satisfacción del CEPRUNSA?", "puede dar lugar a la suspensión de la preparación (Art. 61)", [r"suspension|suspend"], src=RG)
add("G27", "REGLAMENTO", "open", "¿Cuándo recogen las claves de respuesta?", "del internamiento el día del examen, inmediatamente después de culminada la evaluación (Art. 47.2)", [r"internamiento|inmediat"], src=RG)
add("G28", "REGLAMENTO", "open", "¿Qué hacen en el CEPRUNSA además de las clases normales?", "seminarios, clases de reforzamiento académico y envío de prácticas (Art. 62)", [r"seminario|reforzamiento|practicas"], src=RG)
add("G29", "REGLAMENTO", "open", "¿Cómo se me asignan los puntajes al calificarme?", "la DA, CPS y CSPA con apoyo de la OTI verifican tarjetas de identidad, respuestas, emparejamiento y puntajes (Art. 47)", [r"oti|tarjetas|emparejamiento|puntajes"], src=RG)

# ---------------------------------------------------------------- not in the documents / out of domain
for i, (q, g) in enumerate([
    ("¿Cuántos alumnos ingresaron el año pasado?", "no figura en los documentos"),
    ("¿Cuánto cuesta el ciclo de preparación del CEPRUNSA en soles?", "el reglamento remite a montos aprobados por el CU; no da cifras"),
    ("¿Hay vacantes para Ingeniería Naval?", "el programa no figura en el cuadro de vacantes"),
    ("¿Hay cronograma publicado para el proceso de ingreso del 2030?", "los documentos solo cubren el proceso 2027"),
    ("¿Hay vacantes para Ingeniería Aeronáutica?", "el programa no figura en el cuadro de vacantes"),
], 1):
    add(f"N{i:02d}", "SIN_RESPUESTA", "unanswerable", q, g, abstain=True, src="verified absent")
for i, q in enumerate([
    "¿Cuál es la capital de Chile?", "¿Quién descubrió América?", "Dame una receta de lomo saltado", "¿Cuánto es 48 entre 6?",
    "¿Cómo se juega ajedrez?", "¿Cuándo son las inscripciones de la Universidad de Piura?", "Escríbeme una canción de amor",
    "¿Qué películas hay en el cine hoy?", "¿Cómo se renueva el pasaporte?", "¿Qué temperatura hace en Lima?",
], 1):
    add(f"Z{i:02d}", "FUERA_DE_DOMINIO", "ood", q, "fuera del dominio", abstain=True, src="n/a")

# ---- leakage check against EVERY earlier bank used in development/evaluation
def norm(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


seen = []
for p in [HERE.parent.parent / "evidence/ragas_500/inputs/queries_500_pdf_verified_ai_adjudicated.json", HERE.parent.parent / "queries.json", HERE.parent / "heldout_bank.json"]:
    seen += [norm(c["query"]) for c in json.load(open(p, encoding="utf-8"))["consultas"]]
rows = []
for it in items:
    s = max(difflib.SequenceMatcher(None, norm(it["query"]), x).ratio() for x in seen)
    it["sim_to_dev"] = round(s, 3); rows.append((s, it["id"], it["query"]))
rows.sort(reverse=True)
assert rows[0][0] < 0.999, rows[0]
out = {"status": "TEST2_WRITTEN_BEFORE_ANY_SYSTEM_CHANGE_OR_RUN", "n": len(items), "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "max_similarity_to_any_dev_question": rows[0][0], "top5": [(round(a, 3), b, c) for a, b, c in rows[:5]], "consultas": items}
(HERE / "test2_bank.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
import collections
print(len(items), collections.Counter(i["category"] for i in items), collections.Counter(i["type"] for i in items))
print("max sim to dev:", rows[0]); print("sha256", hashlib.sha256((HERE / "test2_bank.json").read_bytes()).hexdigest())
