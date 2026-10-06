"""Builds bank #3 (60 answerable questions) on parts of the four documents that the earlier banks did not touch.

Covered here and NOT in the Dev/Test banks: 20 regulation articles (13, 18, 19, 21, 22, 26, 55, 56, 89, 93, 95, 101, 104, 105,
108, 112, 118, 122, 124, 126), 16 syllabus topics of subjects not asked before (biology, geography, psychology, philosophy,
civics, language, literature, electrochemistry, modern physics, university law), 16 vacancy questions on programs not asked
before (including sums, differences and comparisons), and 8 schedule items. Golds come from the document text; vacancy golds
are asserted against the table rows (each row's totals were checked to add up). Written and sealed BEFORE the system
improvements that follow (see SEAL.json, which stores the application code hashes at sealing time)."""
import json, hashlib, datetime, glob, os, sys, unicodedata, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "app"))
import structured_answers as sa

n = lambda s: ''.join(c for c in unicodedata.normalize('NFKD', s.casefold()) if not unicodedata.combining(c)).strip()
docs = {'VACANTES': json.load(open(ROOT / 'data/index_textract_85_v9/VACANTES.json', encoding='utf-8'))}
T = {n(p): {k: int(v) for k, v in f if re.fullmatch(r'\d+', v)} for p, f, c in sa._program_rows(docs) if 'ORDINARIO / Total de Vacantes' in dict(f)}
tot = lambda p: T[n(p)]['TOTAL GENERAL']
col = lambda p, k: T[n(p)][k]

REG = "REGLAMENTO DE ADMISIÓN 2027.pdf"
VAC = "CUADRO DE VACANTES 2027.pdf p.3"
TEM = "TEMARIO Y MATRIZ DE EVALUACIÓN 2027.pdf"
CRO = "CRONOGRAMA DE ADMISIÓN 2027.pdf p.2-3"
items = []


def add(i, cat, typ, q, gold, must, src):
    items.append(dict(id=i, category=cat, type=typ, query=q, gold=gold, must=must, abstain=False, source=src))


# ---- REGLAMENTO (20)
add("K01", "REGLAMENTO", "open", "¿Puedo postular si todavía estoy en quinto de secundaria?", "Sí: pueden postular quienes están matriculados en el último año de secundaria (Art. 18.2)", ["ultimo ano", "matricul"], f"{REG} Art.18")
add("K02", "REGLAMENTO", "open", "¿Puedo postular a dos carreras a la vez?", "No: se inscribe en un programa de estudios como única opción (Art. 19)", ["unica opcion|un solo programa|una sola"], f"{REG} Art.19")
add("K03", "REGLAMENTO", "open", "Ya soy estudiante de la UNSA y quiero postular de nuevo al mismo programa, ¿qué necesito?", "Una resolución del VRA que autorice su inscripción (Art. 21)", ["resolucion", "vra|vicerrector"], f"{REG} Art.21")
add("K04", "REGLAMENTO", "open", "Estoy matriculado en dos carreras de la UNSA, ¿puedo postular?", "No, salvo que presente el retiro definitivo de uno de los programas (Art. 22)", ["retiro"], f"{REG} Art.22")
add("K05", "REGLAMENTO", "lookup", "¿Por dónde hago mi registro y mi preinscripción?", "A través de la plataforma SISADMISIÓN (Art. 26)", ["sisadmision"], f"{REG} Art.26")
add("K06", "REGLAMENTO", "open", "Si ingreso por una filial, ¿me puedo cambiar después a la sede Arequipa?", "No: está obligado a culminar sus estudios en la filial a la que postuló (Art. 55)", ["filial", "no (?:podra|puede)|obligad"], f"{REG} Art.55")
add("K07", "REGLAMENTO", "open", "Alcancé vacante en una filial, ¿puedo volver a postular a otro programa en este proceso?", "No: no podrá volver a postular al mismo programa u otro dentro del proceso vigente (Art. 56)", ["no (?:podra|puede)"], f"{REG} Art.56")
add("K08", "REGLAMENTO", "open", "¿Quiénes entran por la modalidad de primeros puestos?", "Dos estudiantes por institución educativa: quien ocupó el primer puesto y quien ocupó el segundo (Art. 89)", ["primer", "segundo|dos|2"], f"{REG} Art.89")
add("K09", "REGLAMENTO", "open", "¿Qué deportistas pueden postular por la modalidad de deportistas destacados?", "Deportistas calificados (DC) y deportistas calificados de alto nivel (DECAN) acreditados por el IPD (Art. 93)", ["decan|deportistas calificados"], f"{REG} Art.93")
add("K10", "REGLAMENTO", "open", "¿La UNSA permite postular a personas con discapacidad?", "Sí: garantiza el acceso y la permanencia de las personas con discapacidad, incluida su participación en el proceso de admisión (Art. 95)", ["garantiza"], f"{REG} Art.95")
add("K11", "REGLAMENTO", "open", "¿Quiénes pueden entrar por traslado externo?", "Estudiantes de cualquier universidad del Perú licenciada por la SUNEDU o del extranjero, solo a un programa de la misma o equivalente denominación (Art. 101)", ["sunedu"], f"{REG} Art.101")
add("K12", "REGLAMENTO", "open", "¿Qué necesito para postular por traslado interno?", "Matrícula vigente el año anterior y haber aprobado todas las asignaturas del primer año (Art. 104)", ["primer ano", "aprob"], f"{REG} Art.104")
add("K13", "REGLAMENTO", "open", "En traslado interno, ¿a qué carreras me puedo cambiar?", "Solo a programas de estudios de la misma Área Académica (Art. 105.3)", ["misma area"], f"{REG} Art.105")
add("K14", "REGLAMENTO", "open", "¿Quiénes pueden postular por Bachillerato Internacional?", "Los egresados de colegios secundarios que obtuvieron el grado de Bachillerato Internacional (Art. 108)", ["egresados|colegios"], f"{REG} Art.108")
add("K15", "REGLAMENTO", "lookup", "¿Qué ley respalda el ingreso de las víctimas de la violencia?", "Ley N° 28592 (Plan Integral de Reparaciones), según el DS 015-2006-JUS (Art. 112)", ["28592"], f"{REG} Art.112")
add("K16", "REGLAMENTO", "list", "¿Por qué causas me pueden anular el examen?", "Portar equipos electrónicos, suplantar o ser suplantado, impedir el desarrollo del examen, identificarse con documentos falsificados, plagiar (Art. 122)", ["suplant", "falsific|plagi|celular|electronic"], f"{REG} Art.122")
add("K17", "REGLAMENTO", "open", "¿Qué le pasa a alguien que suplanta a otra persona en el examen?", "Es derivado al Ministerio Público y sancionado con inhabilitación definitiva para postular a la UNSA (Art. 124)", ["ministerio publico", "inhabilit"], f"{REG} Art.124")
add("K18", "REGLAMENTO", "list", "¿En qué casos me anulan el ingreso aunque ya haya alcanzado vacante?", "Haber sido suplantado o suplantador, registrar información falsa o usar o entregar documentación falsa (Art. 126)", ["suplant", "falsa"], f"{REG} Art.126")
add("K19", "REGLAMENTO", "open", "Si pagué y ya no puedo postular, ¿me reembolsan el dinero?", "No: los pagos del proceso de admisión no son reembolsables bajo ningún concepto o circunstancia (Art. 13)", ["no (?:son |se )?(?:reembols|devuel)|no procede"], f"{REG} Art.13")
add("K20", "REGLAMENTO", "open", "En traslado externo, ¿puedo ir a una carrera distinta a la que estudiaba?", "No: solo a un programa de la misma denominación (o equivalente) que el de la universidad de origen (Art. 101 y 118)", ["misma denominacion|equivalente|misma o"], f"{REG} Art.101, 118")

# ---- VACANTES (16)
add("V01", "VACANTES", "lookup", "¿Cuántas vacantes de Ingeniería Geológica hay en el ordinario primera fase?", "24", [r"\b24\b"], VAC); assert col("Ingeniería Geológica", "ORDINARIO / Fase I") == 24
add("V02", "VACANTES", "lookup", "Ingeniería de Minas: ¿cuántos cupos hay por CEPRUNSA fase I?", "14", [r"\b14\b"], VAC); assert col("Ingeniería de Minas", "CEPRUNSA / Fase I") == 14
add("V03", "VACANTES", "lookup", "¿Cuántas vacantes tiene Economía en total?", "180", [r"\b180\b"], VAC); assert tot("Economía") == 180
add("V04", "VACANTES", "lookup", "cupos de Ingeniería Electrónica para ciclo quintos", "17", [r"\b17\b"], VAC); assert col("IngenieríaElectrónica", "CEPRUNSA / Ciclo Quintos") == 17
add("V05", "VACANTES", "lookup", "¿Cuántas vacantes de Relaciones Industriales hay en el ordinario segunda fase?", "40", [r"\b40\b"], VAC); assert col("Relaciones Industriales", "ORDINARIO / Fase II") == 40
add("V06", "VACANTES", "lookup", "¿Cuántas vacantes de Educación Inicial hay en el ordinario?", "17", [r"\b17\b"], VAC); assert col("Educación con Especialidad de Educación Inicial", "ORDINARIO / Total de Vacantes") == 17
add("V07", "VACANTES", "lookup", "¿Cuántas vacantes de Banca y Seguros tiene CEPRUNSA en total?", "24", [r"\b24\b"], VAC); assert col("Banca Seguros", "CEPRUNSA / Total de Vacantes") == 24
add("V08", "VACANTES", "lookup", "Ingeniería Mecánica, CEPRUNSA segunda fase: ¿cuántos cupos?", "15", [r"\b15\b"], VAC); assert col("Ingeniería Mecánica", "CEPRUNSA / Fase II") == 15
add("V09", "VACANTES", "aggregate", "¿Cuántas vacantes ordinarias suman Ingeniería de Minas e Ingeniería Geológica?", "104 (56 + 48)", [r"\b104\b"], VAC); assert col("Ingeniería de Minas", "ORDINARIO / Total de Vacantes") + col("Ingeniería Geológica", "ORDINARIO / Total de Vacantes") == 104
add("V10", "VACANTES", "multistep", "¿Cuántas vacantes más tiene Economía que Banca y Seguros en total?", "136 (180 - 44)", [r"\b136\b"], VAC); assert tot("Economía") - tot("Banca Seguros") == 136
add("V11", "VACANTES", "comparison", "¿Qué tiene más vacantes en total, Relaciones Industriales o Literatura y Lingüística?", "Relaciones Industriales (148 frente a 80)", ["relaciones industriales"], VAC); assert (tot("Relaciones Industriales"), tot("Literatura Lingüistica")) == (148, 80)
add("V12", "VACANTES", "aggregate", "¿Cuántas vacantes suman las dos fases del ordinario en Ingeniería de Telecomunicaciones?", "30 (14 + 16)", [r"\b30\b"], VAC); assert col("Ingeniería de Telecomunicaciones", "ORDINARIO / Fase I") + col("Ingeniería de Telecomunicaciones", "ORDINARIO / Fase II") == 30
add("V13", "VACANTES", "aggregate", "¿Cuántos cupos suman en total Artes con especialidad en Música y en Plásticas?", "118 (59 + 59)", [r"\b118\b"], VAC); assert tot("Artes con Especialidad de Música") + tot("Artes con Especialidad de Plásticas") == 118
add("V14", "VACANTES", "lookup", "¿Cuántas vacantes hay en Gestión de Empresas en el ordinario primera fase?", "7", [r"\b7\b"], VAC); assert col("Gestión con Mención en Gestión de Empresas", "ORDINARIO / Fase I") == 7
add("V15", "VACANTES", "comparison", "¿Qué tiene más vacantes en total, Periodismo o Relaciones Públicas?", "Relaciones Públicas (128 frente a 92)", ["relaciones publicas"], VAC)
add("V16", "VACANTES", "aggregate", "¿Cuántas vacantes ofrecen en total todas las especialidades de Educación?", "306 (9 especialidades de 34 vacantes cada una)", [r"\b306\b"], VAC)

# ---- TEMARIO (16)
add("T01", "TEMARIO", "list", "¿Qué se estudia sobre la célula en biología?", "teoría celular, tipos de células (procariota y eucariota), membranas y organelas, núcleo, ADN y código genético, síntesis de proteínas", ["teoria celular", "procariota", "eucariota"], f"{TEM} p.26")
add("T02", "TEMARIO", "list", "¿Qué temas de genética entran en el examen?", "conceptos básicos, experimentos de Mendel, leyes de la herencia, tipos de dominancia, alelos múltiples, herencia ligada al sexo, genética humana, mutaciones, bioética", ["mendel", "mutacion"], f"{TEM} p.27")
add("T03", "TEMARIO", "list", "¿Qué se ve de hidrografía en geografía?", "vertientes hidrográficas del Perú, el mar peruano, la Corriente Peruana (Humboldt), glaciares del Perú, manejo de cuencas", ["vertientes", "humboldt"], f"{TEM} p.20")
add("T04", "TEMARIO", "list", "¿Qué se estudia de inteligencia emocional en psicología?", "componentes de la inteligencia emocional, inteligencia intrapersonal e interpersonal", ["intrapersonal", "interpersonal"], f"{TEM} p.32")
add("T05", "TEMARIO", "list", "¿Qué entra en hábitos de estudio?", "planificación, organización y técnicas de estudio", ["planificacion", "tecnicas"], f"{TEM} p.31")
add("T06", "TEMARIO", "list", "¿Qué se estudia de ética en filosofía?", "ética y moral (concepto y diferencias), acto moral, valores y antivalores, dilemas éticos", ["antivalores", "dilemas"], f"{TEM} p.35")
add("T07", "TEMARIO", "list", "¿Qué disciplinas filosóficas hay en el temario?", "metafísica, ontología, gnoseología, epistemología, lógica, ética, estética y axiología", ["ontologia", "axiologia"], f"{TEM} p.33")
add("T08", "TEMARIO", "list", "¿Qué se estudia de derechos humanos en educación cívica?", "concepto y características, clasificación de los derechos humanos, derechos fundamentales en el Perú, garantías constitucionales", ["clasificacion", "garantias"], f"{TEM} p.36")
add("T09", "TEMARIO", "list", "¿Qué reglas de acentuación entran en lenguaje?", "acentuación general y especial: diacrítica, enfática y de expresiones complejas", ["diacritica", "enfatica"], f"{TEM} p.38")
add("T10", "TEMARIO", "list", "¿Qué autores de literatura de Arequipa entran en el examen?", "Mariano Melgar (yaravíes), Augusto Aguirre Morales (El pueblo del sol), Percy Gibson (poesía modernista), Oswaldo Reynoso (Los inocentes)", ["melgar", "reynoso"], f"{TEM} p.41")
add("T11", "TEMARIO", "list", "¿Qué se estudia de electroquímica?", "oxidación y reducción, celdas galvánicas, potencial estándar de reducción, electrólisis, leyes de Faraday", ["galvanicas", "electrolisis"], f"{TEM} p.25")
add("T12", "TEMARIO", "list", "¿Qué temas de física moderna entran?", "hipótesis de Planck, efecto fotoeléctrico, principio de incertidumbre, radiactividad, relatividad especial", ["fotoelectrico", "relatividad"], f"{TEM} p.31")
add("T13", "TEMARIO", "list", "¿Qué se ve de derecho universitario?", "la universidad como institución, autonomía universitaria, fines, comunidad universitaria, derechos y deberes del estudiante, participación estudiantil, universidad y desarrollo regional", ["autonomia", "deberes"], f"{TEM} p.37")
add("T14", "TEMARIO", "aggregate", "¿Cuántos temas tiene filosofía?", "13 (I a XIII)", [r"\b13\b|trece"], f"{TEM} pp.33-35")
add("T15", "TEMARIO", "aggregate", "¿Cuántos temas tiene psicología?", "15 (I a XV)", [r"\b15\b|quince"], f"{TEM} pp.31-33")
add("T16", "TEMARIO", "locate", "¿En qué tema de geografía se ven los glaciares del Perú?", "En el tema V, Hidrografía", ["hidrografia"], f"{TEM} p.20")

# ---- CRONOGRAMA (8)
add("C01", "CRONOGRAMA", "lookup", "¿Cuándo empiezan las clases de CEPRUNSA primera fase?", "27/04/2026", [r"27[/-]04[/-]2026|27 de abril"], CRO)
add("C02", "CRONOGRAMA", "lookup", "¿Cuándo es la evaluación de conocimientos del ordinario II fase?", "14/03/2027", [r"14[/-]03[/-]2027|14 de marzo"], CRO)
add("C03", "CRONOGRAMA", "lookup", "¿Hasta cuándo puedo inscribirme al ciclo quintos?", "14/08/2026", [r"14[/-]08[/-]2026|14 de agosto"], CRO)
add("C04", "CRONOGRAMA", "lookup", "¿Cuándo empiezan las clases de CEPRUNSA segunda fase?", "16/11/2026", [r"16[/-]11[/-]2026|16 de noviembre"], CRO)
add("C05", "CRONOGRAMA", "lookup", "¿Qué día es la evaluación previa de CEPRUNSA segunda fase?", "10/01/2027", [r"10[/-]01[/-]2027|10 de enero"], CRO)
add("C06", "CRONOGRAMA", "lookup", "¿Qué día se asignan las vacantes del extraordinario?", "23/02/2027", [r"23[/-]02[/-]2027|23 de febrero"], CRO)
add("C07", "CRONOGRAMA", "lookup", "¿Hasta cuándo me puedo inscribir al extraordinario?", "27/01/2027", [r"27[/-]01[/-]2027|27 de enero"], CRO)
add("C08", "CRONOGRAMA", "lookup", "¿Cuándo es el examen de las filiales de Mollendo, Camaná y El Pedregal?", "20/03/2027", [r"20[/-]03[/-]2027|20 de marzo"], CRO)

assert len(items) == 60 and len({i["id"] for i in items}) == 60
bank = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "n": 60,
        "note": "answerable questions only; all categories of the earlier banks except abstention; golds from the document text",
        "consultas": items}
out = HERE / "test3_bank.json"
out.write_text(json.dumps(bank, ensure_ascii=False, indent=1), encoding="utf-8")
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
seal = {"sealed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "test3_bank_sha256": sha(out), "n": 60,
        "statement": "Bank written and sealed BEFORE the system improvements (aggregate resolvers, regulation retrieval, generator choice) and before any system was run on it.",
        "app_code_hash_at_seal": {os.path.basename(p): sha(p) for p in sorted(glob.glob(str(ROOT / 'app' / '*.py')))}}
(HERE / "SEAL.json").write_text(json.dumps(seal, indent=1), encoding="utf-8")
print("ok", seal["test3_bank_sha256"], seal["sealed_utc"])
