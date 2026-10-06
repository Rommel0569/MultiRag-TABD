# Auditoría funcional de punta a punta — 2026-10-01

## Alcance y entorno

- Interfaz React/Vite abierta en `http://127.0.0.1:5173/`.
- API FastAPI en `http://127.0.0.1:8000/`.
- Índices de prueba: `data/index_textract_85_v9` (CRONOGRAMA 36, VACANTES 141, TEMARIO 441 y REGLAMENTO 274 fragmentos).
- Caché de prueba aislada en `data/cache/e2e_ui_20261001`; no se usó el índice baseline ni se reemplazaron resultados de evaluación.
- Generación local por Ollama. Esta revisión no llamó Textract ni Gemini.

## Recorridos verificados en la interfaz

| Ruta | Consulta de prueba | Resultado visible | Evidencia |
|---|---|---|---|
| Fase 1, primera respuesta con dato estructurado | Vacantes de Ingeniería Industrial, CEPRUNSA Fase I | `17 vacantes`, fuente `CUADRO DE VACANTES 2027.pdf (p.3)` | respuesta marcada Fase 3 — Extracción estructurada |
| Fase 1, repetición exacta | La misma consulta de vacantes | respuesta reutilizada y marcada Fase 1 — Caché semántica | estadísticas: 2 consultas, 1 entrada, 1 uso de caché |
| Fase 2 | Clima de mañana en Arequipa | rechazo fuera del dominio; no genera respuesta documental | marca Fase 2 — Enrutador |
| Fase 3, generación híbrida | Finalidad del reglamento de admisión | respuesta apoyada por el fragmento de p.17 y fuentes de p.5 y p.7 | marca Fase 3 — Recuperación híbrida; el contenido responde a la finalidad citada |
| Fase 3, tabla de cronograma | Inicio de inscripciones de CEPRUNSA | `23/03/2026`, fuente `CRONOGRAMA DE ADMISIÓN 2027.pdf (p.2)` | contrastado con la fila de inscripciones de CEPRUNSA I Fase del índice v9 |
| Fase 3, lista del temario | Temas de Razonamiento Matemático | siete encabezados, I–VII, en orden; fuentes en pp.3–4 | respuesta contrastada con las filas y continuación de la tabla del índice v9 |

## Correcciones realizadas durante esta auditoría

1. `app/structured_answers.py`: la búsqueda de temas ya no acepta una fila de ponderaciones solo porque mencione el nombre de una asignatura. Para listas amplias, reconstruye componentes divididos entre filas consecutivas y recoge los encabezados del temario hasta el siguiente componente. La consulta de prueba había devuelto antes valores de ponderación de la p.44 como si fueran contenidos; ahora obtiene los siete encabezados desde pp.3–4.
2. `app/pipeline.py`: las consultas que piden listas amplían el contexto recuperado de 5 a 10 fragmentos; las consultas puntuales conservan 5.
3. `app/llm.py`: se indicó al generador que mantenga el orden del documento en listas, cubra todos los elementos respaldados por el contexto y no mezcle apartados por compartir palabras.
4. La respuesta estructurada con fuente se conserva en caché para que una repetición pueda salir por Fase 1.
5. La integración visual ya muestra fase, categoría y fuentes; actualiza las estadísticas después de responder, indica carga/error y usa una URL de API configurable. CORS permite el origen Vite local verificado.

## Verificaciones técnicas

- `GET /health`: HTTP 200, estado `ok`.
- `GET /stats`: HTTP 200; modo de caché `semantic`.
- `POST /query` con texto vacío: HTTP 400 y mensaje claro.
- Preflight CORS desde `http://127.0.0.1:5173`: origen autorizado.
- `npm run lint`: correcto.
- `npm run build`: correcto; Vite compiló 20 módulos. El primer intento dentro del sandbox falló por `spawn EPERM`; el build se repitió con permiso de ejecución y terminó correctamente.
- Parseo AST de 37 módulos Python: correcto.
- No se registró una métrica de latencia de esta sesión; no se estima a partir del reloj del navegador. La instrumentación y corridas previas de latencia están en `evaluation/revision_20261001/latency_audit/`.

## Límites que siguen abiertos

- La interfaz sirve consultas contra el corpus e índices ya cargados; no ofrece carga de PDF, gestión de documentos ni reconstrucción del índice. La ingesta está en `app/ingest.py` y usa cuatro nombres de PDF configurados. Si una página requiere OCR, Textract puede enviar esa imagen a AWS y tener costo; ese flujo todavía no está conectado a la interfaz.
- La validación visual de hoy cubrió recorridos representativos y errores de integración, no las 500 consultas. Las cifras del experimento de 500 preguntas y las evaluaciones previas permanecen en sus archivos originales y no se alteraron.
- El sistema entrega referencias de archivo y página, pero la cobertura/exactitud de preguntas distintas a las muestras aún requiere evaluación con el banco completo y control humano de resultados críticos.
- Hay una ruta de caché semántica anterior bajo `app/data/cache/` que ya aparece modificada en el árbol de trabajo. Esta auditoría utilizó exclusivamente el directorio de caché aislado indicado arriba y no la restauró ni la limpió.

## Comandos reproducibles

Desde la raíz del proyecto, en dos terminales:

```powershell
Set-Location app
$env:CEPRUNSA_INDEX_DIR = 'data/index_textract_85_v9'
$env:CEPRUNSA_CACHE_MODE = 'semantic'
$env:CEPRUNSA_CACHE_DIR = 'data/cache/e2e_ui_20261001'
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

```powershell
Set-Location fronted/fronted
npm run dev -- --host 127.0.0.1
npm run lint
npm run build
```

La configuración para la aplicación local se carga desde el `.env` del proyecto. No se copiaron credenciales a este registro.

## Seguimiento: contextos y documentos — 2026-10-01

Este seguimiento implementa la carga que estaba pendiente en la auditoría
anterior. El corpus fijo CEPRUNSA del artículo se mantiene de solo lectura;
cada colección nueva recibe un identificador propio y guarda originales,
extracciones, auditorías OCR, segmentos, índice FAISS y caché bajo
`data/workspaces/<id>`.
Las latencias quedan temporalmente en `tmp/latency_audit/<id>/`. El selector
de la interfaz envía ese identificador al
chat y a estadísticas. Las búsquedas y la caché leen únicamente ese espacio.

La carga acepta PDF de hasta 50 MB y 500 páginas por configuración. El original
se escribe atómicamente, se identifica por SHA-256 para evitar duplicados y se
indexa en segundo plano. Poppler extrae primero el texto local, conserva diseño
de columnas y evalúa cada página; texto normal y tablas legibles no llaman OCR.
Una carga con páginas sin texto utilizable queda en `awaiting_ocr_consent`. La
interfaz pide confirmación de que el archivo pertenece al contexto activo; para
OCR pide una segunda confirmación específica de envío a Textract. La llamada
requiere además `CEPRUNSA_ENABLE_PAID_TEXTRACT=1`. No se invocó AWS en esta
validación.

La extracción indexa prosa en fragmentos con solapamiento y tablas por fila,
repite los encabezados en los fragmentos de fila y conserva las celdas vacías
en los metadatos. Los vectores se crean en lotes; la recuperación combina
FAISS, BM25, RRF y el reranker. El clasificador y el generador reciben solo la
descripción del contexto activo y los fragmentos recuperados de su índice.
La caché semántica también es local a ese contexto y se invalida cuando cambia
la versión de su índice.

### Evidencia de la comprobación

- La interfaz local mostró el selector de contexto y reportó la API conectada.
- `GET /workspaces`, creación de contexto, carga PDF, listado de documentos,
  estadísticas por contexto y `POST /query` completaron con HTTP 200/201 en
  una comprobación de API aislada.
- Un PDF sintético con texto seleccionable se indexó sin OCR. Una consulta en
  lenguaje natural recorrió clasificación, recuperación híbrida, reranking y
  generación; devolvió la fuente `searchable.pdf (p.1)`. En una corrida con
  desglose instrumentado tardó 11.47 s: caché 7.82 ms, enrutador 8,711.46 ms,
  recuperación y reranking 1,676.67 ms, generación 975.50 ms. El enrutador fue
  el componente dominante en esta consulta. Es una sola muestra sintética local,
  no una estimación de latencia general.
- Las cuatro páginas de `CUADRO DE VACANTES 2027.pdf` se detectaron como
  necesitadas de OCR y quedaron pendientes de consentimiento. No se transmitió
  ninguna página a AWS durante la prueba.
- El parser Textract, con bloques sintéticos, preservó encabezados y una celda
  vacía. La caché semántica aislada recuperó una paráfrasis de prueba con score
  de reranker 0.998.
- La instrumentación HTTP devolvió `latency_ms` y desglose por fase. Como
  evidencia temporal, el JSONL diario bajo `tmp/latency_audit/<id>/` registra
  fecha, contexto, hash y longitud de pregunta, fase, tokens, modelos, latencia
  total y tiempos por etapa; no guarda el texto de la pregunta ni la respuesta.
  Los registros de más de siete días se purgan; el plazo se configura con
  `CEPRUNSA_LATENCY_AUDIT_RETENTION_DAYS`.
- `python -m compileall -q app`, `npm run lint` y `npm run build` finalizaron
  correctamente. El frontend se comprobó en `http://127.0.0.1:5173/` y la API
  en `http://127.0.0.1:8000/`.

### Alcance que todavía depende del uso real

- La separación por contexto es estructural: solo se consultan los documentos
  asignados al contexto elegido. La aplicación solicita confirmación al cargar,
  pero no puede verificar automáticamente que el contenido de cada PDF
  pertenezca a la universidad declarada.
- La detección nativa de columnas usa el texto y espaciado que conserva Poppler;
  PDF con tablas visuales complejas pero texto extraíble irregular pueden
  requerir revisión de su extracción. Para páginas escaneadas, se necesita una
  autorización explícita por archivo y Textract habilitado en el servidor.
- La muestra de texto y la prueba de tablas son sintéticas. La validación de
  precisión con PDFs de varias instituciones, idiomas, orientaciones y diseños
  aún debe hacerse antes de afirmar cobertura general. Las cifras del artículo
  y las evaluaciones existentes no fueron modificadas.
