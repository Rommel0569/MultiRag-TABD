# Revisión final del banco de 500 y comparación de arquitecturas

Fecha de revisión: 2026-09-30. Proyecto: `ceprunsa_mvrag`.

## Actualización posterior: revisión humana de las 500

El autor confirmó que revisó manualmente las 500 consultas, referencias y respuestas de ambos sistemas contra los PDF originales. Los veredictos se registran como evaluación humana de un solo autor; `llama3:8b` participó en el triage/adjudicación inicial, pero no se considera el evaluador final. La revisión no fue ciega ni independiente y no hubo un segundo anotador. La actualización queda asentada en `manual_validation/HUMAN_REVIEW_ATTESTATION_500_20260930.md` y en `manual_validation/source_validation_500_verdict_summary.md`.

El CSV de revisión coincide exactamente, para las 500 filas y ambos brazos, con las respuestas de las corridas baseline y tres fases reportadas aquí. La adjudicación humana resumida es: en dominio, tres fases 438 correctas, 9 parciales y 3 incorrectas; baseline 336 correctas, 6 parciales y 108 incorrectas. En las 50 consultas OOD, tres fases tuvo 50 abstenciones correctas y baseline 47.

Con `correct` como único acierto completo dentro del dominio, la exactitud es 97.33% (438/450) para tres fases y 74.67% (336/450) para baseline, una diferencia de 22.67 puntos. En la comparación pareada, 106 respuestas fueron exactas solo en tres fases y 4 solo en baseline; McNemar exacta bilateral `p=9.2369e-27`. Las abstenciones OOD se analizan aparte: 50/50 frente a 47/50, `p=0.25`. Estos valores son condicionales a la revisión manual no ciega de un único autor y al banco fijado; no son una estimación de rendimiento poblacional.

## Resumen del resultado

Se ejecutaron las 500 consultas en las dos arquitecturas. Ambas terminaron 500/500 sin errores de ejecución. Las corridas compartieron las mismas preguntas, el índice experimental Textract v9, `llama3:8b`, temperatura 0.1 y caché deshabilitada. No se modificó ni sustituyó el índice baseline del artículo.

En el banco, la versión de tres fases recuperó la página citada para las 450 preguntas dentro del dominio, frente a 399/450 del baseline. Su cobertura automática de los datos numéricos/fechas pedidos en Cronograma y Vacantes fue 200/200 (1.0), frente a 173/200 (0.865) del baseline. La revisión humana posterior confirma una mejora en exactitud de respuestas en este banco, con una caída específica en Cronograma; son resultados de un corpus/configuración concretos y de un solo revisor, no evidencia de superioridad general.

## Qué se mejoró

| Área | Cambio | Archivo(s) principal(es) | Evidencia |
|---|---|---|---|
| Reglamento | La pregunta por un artículo recupera el encabezado exacto, corta al llegar al artículo/capítulo siguiente, conserva continuaciones entre páginas solo mientras la disposición sigue abierta y adjunta filas de tabla cuando la disposición las introduce. | `app/structured_answers.py`, `app/retriever.py` | 105/105 consultas reglamentarias del banco localizaron la página fuente en tres fases. Se corrigieron manualmente las referencias candidatas de los artículos 5, 9, 38 y 53. |
| Reglamento sin número de artículo | Se añadió una resolución guiada por contenido para preguntas generales sobre documentos: detecta una disposición con lista de preinscripción, serializa todos sus numerales y continuaciones entre páginas, limpia ruido OCR y deja modalidades especiales al recuperador ordinario. La respuesta es extractiva para no omitir cláusulas al resumir. | `app/structured_answers.py`, `app/pipeline.py`, `evaluation/run_question_bank.py` | La consulta de regresión conserva todos los numerales 27.1–27.4, las alternativas por identidad, la condición de estudios en el extranjero, la exoneración y las especificaciones de fotografía. Cita páginas físicas 10–11; las imágenes originales se cotejaron visualmente. |
| Tablas | Cronograma y vacantes se responden con intersección explícita fila × columna; el código exige una coincidencia única y evita que Llama vuelva a calcular la cifra. Se conservan etiquetas de encabezados multinivel. | `app/structured_answers.py`, `evaluation/build_index_from_textract.py` | 25/25 fechas y 175/175 celdas de vacantes pasaron los chequeos automáticos de hechos, contexto y página en tres fases. Completitud numérica automática: 1.0; baseline: 0.0 según el diagnóstico de tabla usado. |
| Temario | Se extrae el renglón de la sección identificada y se adjunta una continuación solo cuando la siguiente página continúa esa sección. El parser no confunde identificadores punteados como `5.3.1` con encabezados de tabla. | `app/structured_answers.py`, `evaluation/build_index_from_textract.py`, `app/router.py` | 145/145 respuestas de Temario pasaron los chequeos automáticos de ancla temática y página en tres fases. |
| Registro de auditoría | Los estados separan chequeos automáticos, referencias confirmadas/corregidas, abstenciones fuera de dominio y juicio de exactitud. | `evaluation/audit_paired_runs_against_sources.py`, `manual_validation/source_validation_500_completed.csv` | El audit automático registra evidencia por fila; la revisión manual posterior del autor aporta juicio humano final para las 500 consultas y ambas respuestas. No hubo segundo revisor ni cegamiento. |

El índice `data/index_textract_85_v9` se reconstruyó localmente con JSON de Textract ya guardados; esta corrida no hizo llamadas a AWS. Tiene 36 pasajes de Cronograma, 141 de Vacantes, 441 de Temario y 274 de Reglamento. El índice baseline `data/index` permanece intacto.

## Resultado pareado

El banco tiene 25 consultas de Cronograma, 175 de Vacantes, 145 de Temario, 105 de Reglamento y 50 consultas sintéticas fuera de dominio. Los textos de consulta fueron idénticos entre brazos (`query_texts_match=true`).

| Diagnóstico | Baseline V1 | Tres fases final | Lectura correcta |
|---|---:|---:|---|
| Consultas ejecutadas sin error | 500/500 | 500/500 | Salud de ejecución, no exactitud. |
| Categoría del router correcta | No aplica | 500/500 | Exactitud en este banco con etiquetas conocidas; no generaliza automáticamente a usuarios nuevos. |
| Página fuente esperada recuperada | 399/450 dentro del dominio | 450/450 dentro del dominio | Tres fases mejora el recall de la página citada en este banco. Las 50 consultas OOD no esperan página. |
| Cobertura de números/fechas de referencia | 0.5773 | 0.8522 | Comparación léxica sobre cifras presentes en las referencias candidatas; no es nota semántica. |
| Cobertura del hecho primario pedido (200 filas numéricas: cronograma + vacantes) | 0.865 (173/200) | 1.000 (200/200) | Cálculo automático original contra referencias OCR candidatas, cotejado con el contexto serializado. La revisión humana posterior aportó veredictos por respuesta; si se publican estas coberturas, recalcularlas contra las referencias corregidas. |
| Completitud de números de tabla | 0.0 | 1.0 | Diagnóstico de cobertura numérica contra la referencia candidata de tabla. |
| Frase de referencia exacta encontrada en la respuesta | 158/500 | 414/500 | Coincidencia de frase con referencias del banco, muchas aún OCR; no equivale a juicio de significado. |
| Tiempo acumulado informado por la corrida | 1058.44 s | 11.44 s | No comparar como latencia pura: las 450 consultas de tres fases se respondieron mediante extracción estructurada y no llamaron al generador; V1 sí generó respuesta. |

En tres fases, las fases de salida fueron: 25 extracciones de celda de fecha, 175 de celda de vacantes, 145 de sección del Temario, 105 extracciones de artículo y 50 abstenciones OOD. **Ninguna de las 450 preguntas dentro del dominio activó la recuperación híbrida + generación de respaldo.** La consulta general sobre documentos se añadió como prueba independiente de la nueva extracción estructurada, no como prueba del fallback híbrido. Hace falta una evaluación más amplia de consultas no resueltas por los extractores.

### Igualdad de condiciones y versión de código

El script de comparación valida en los manifiestos que coincidan ID de pareja, generador, modelo, temperatura, hash de consultas, hashes del índice, modo de caché y cantidad de preguntas; `paired_conditions_match=true`. El baseline se ejecutó antes de incorporar el extractor general sin número de artículo. Los hashes de `pipeline.py` y `structured_answers.py` difieren entre manifiestos; el camino V1 (búsqueda densa global y generación) no llama a ese extractor, `llm.py` no cambió y ninguna de las 500 consultas activa la nueva regla (comprobación: 0). La corrida final de tres fases sí se repitió con la versión final del código. Por tanto las entradas y condiciones del baseline siguen emparejadas, aunque los manifiestos dejan visible esa diferencia de fuente.

## Qué significa “verificar las 500” en estos artefactos

- Hay exactamente 500 salidas en cada JSONL y una fila por consulta en cada CSV de auditoría.
- Las 50 páginas físicas citadas por el banco fueron abiertas como imágenes de los PDF originales: Cronograma pp. 2–3; Vacantes p. 3; Temario pp. 3–17 y 19–29; Reglamento pp. 4–7 y 9–25. El número físico y el impreso del Reglamento difieren por tres páginas.
- Los scripts comparan página, contexto, anclas temáticas, fechas/números, números no respaldados y abstención. Tres fases pasó los chequeos automáticos en las 450 consultas de dominio; las 50 OOD se abstuvieron.
- Tras el informe inicial, el autor confirmó haber revisado manualmente las 500 referencias y ambas respuestas contra los PDF. El resumen adjudicado registra 257 referencias apoyadas y 243 corregidas; las 50 consultas OOD se juzgaron por abstención. Esto sí permite reportar un juicio humano de un autor para este banco, con sesgo potencial de autor y sin acuerdo entre anotadores.

Por eso no se informa “500 respuestas correctas”. El resultado es: revisión humana del autor con 438/450 correctas, 9 parciales y 3 incorrectas en dominio para tres fases; baseline 336/450 correctas, 6 parciales y 108 incorrectas; y 50/50 abstenciones OOD correctas en tres fases. La comprobación automática de páginas/contexto sigue siendo una métrica distinta del juicio humano de exactitud.

## Qué hace realmente el baseline

En este proyecto, **V1 baseline** significa búsqueda FAISS densa global: consulta cada una de las cuatro colecciones (`CRONOGRAMA`, `VACANTES`, `TEMARIO`, `REGLAMENTO`), junta candidatos, ordena por distancia densa y se queda con los cinco mejores globales. Después Llama genera la respuesta. No tiene router, BM25, fusión RRF, reranker, extracción estructurada ni una decisión explícita OOD.

Las variantes documentadas en `evaluation/ablation.py` son:

- V1: búsqueda densa global top‑5.
- V2: búsqueda densa global top‑20 y reranker a top‑5.
- V3: router y búsqueda densa + BM25 con fusión RRF top‑5, sin reranker.
- V4: router, recuperación híbrida y reranker.

“Tres caminos” no es la descripción exacta del baseline. El baseline busca en **cuatro colecciones documentales en paralelo**. “Tres fases” describe la otra arquitectura: (1) caché semántica, (2) router de intención y (3) recuperación/respuesta. En el flujo final, la fase 3 primero intenta extraer una celda, tema o artículo estructurado; cuando eso no aplica, usa híbrido FAISS + BM25/RRF/reranker con respaldo global y genera con el LLM. La caché se deshabilitó para la comparación pareada.

El resultado pareado compara el paquete completo (router + extracciones estructuradas + abstención OOD) con V1; no aísla causalmente cuánto aporta cada componente. Para afirmar qué componente mejora el sistema hace falta una ablación sobre referencias ya validadas.

## Pendiente para una evaluación científica final

1. La revisión manual del autor de referencias y respuestas del banco quedó completada según su confirmación. Para reforzar independencia, conseguir un segundo evaluador para una muestra o el conjunto, medir acuerdo y conservar desacuerdos/adjudicación.
2. Comprobar que cada pregunta tiene una respuesta única y que el banco retenido no duplica preguntas de desarrollo; documentar este control como parte del protocolo.
3. Ampliar el banco con consultas que no sean únicamente preguntas extractivas: preguntas coloquiales abiertas, multihop, preguntas con modalidad ambigua, fuera de dominio y casos sin evidencia. Incluir una división de desarrollo y una prueba retenida.
4. Evaluar la recuperación híbrida de Reglamento y las preguntas que no resuelva el extractor estructurado con un conjunto de oro; el smoke test actual encontró y corrigió un fallo real, pero solo cubre un caso.
5. Recalcular RAGAS sobre las referencias ahora revisadas y con preguntas/modelos/contextos congelados. El intento Gemini se interrumpió antes de guardar CSV; los resultados RAGAS históricos fueron mixtos y no mostraron diferencia pareada significativa. La revisión humana de un autor no sustituye la evaluación de faithfulness, relevancy o context precision.
6. Reportar intervalos de confianza pareados, ablaciones por componente y latencia/costo por arquitectura en ejecuciones comparables. La latencia de esta pareja no es comparable porque los caminos de generación difieren.

## Archivos reproducibles

- Preguntas usadas en generación: `evaluation/queries_500_disambiguated_candidates.json` (SHA‑256 `47de5f36529322810bdda0680c19eb1a89773ae7b234292a46364ef13f533004`). IDs 233 y 239 se aclararon para resolver ambigüedades de Temario. Ambos brazos recibieron los mismos textos.
- Copia de puntuación con 4 referencias revisadas: `evaluation/queries_500_source_reviewed_refs.json` (SHA‑256 `b2c09ee9d4267a7b3c15928d874ca34b7cf0b29bfe27c6735f2bbc03458030db`). Esta copia solo se usa para puntuar; las referencias no se enviaron al generador.
- Salidas por pregunta: `evaluation/runs/paired500_20260930_baseline_v9/answers.jsonl` y `evaluation/runs/paired500_20260930_three_phase_final_v3/answers.jsonl`.
- Comparación pareada por fila: `evaluation/revision_20260930/paired500_final_v3_comparison.csv` y `.summary.json`.
- Auditorías por fila: `evaluation/revision_20260930/paired500_final_v3_audit/baseline_500_source_audit.csv`, `three_phase_500_source_audit.csv` y `paired_500_source_audit_summary.json`.
- Revisión visual de páginas: `evaluation/revision_20260930/SOURCE_PAGE_VISUAL_REVIEW_20260930.md`.
- Banco con 4 referencias fuente-revisadas: `evaluation/revise_source_reviewed_candidates.py`.
- Caso de regresión general de Reglamento (fuera del banco principal): `evaluation/queries_reglamento_smoke_source_reviewed.json` y `evaluation/runs/reglamento_docs_smoke_final_v3/answers.jsonl`.

## Comandos de reproducción

Las corridas originales usaron estos comandos; el baseline se conserva en su carpeta original y el brazo de tres fases final repite las 500 filas con el extractor general de documentos ya incorporado:

```powershell
.\venv\Scripts\python.exe evaluation\run_question_bank.py --queries evaluation\queries_500_disambiguated_candidates.json --output-dir evaluation\runs\paired500_20260930_baseline_v9 --variant baseline --pair-id paired500_20260930_textractv9_llama3 --model llama3:8b --index-dir data\index_textract_85_v9 --allow-unvalidated-candidates

.\venv\Scripts\python.exe evaluation\run_question_bank.py --queries evaluation\queries_500_disambiguated_candidates.json --output-dir evaluation\runs\paired500_20260930_three_phase_final_v3 --variant three_phase --pair-id paired500_20260930_textractv9_llama3 --model llama3:8b --index-dir data\index_textract_85_v9 --allow-unvalidated-candidates

.\venv\Scripts\python.exe evaluation\compare_bank_runs.py evaluation\runs\paired500_20260930_baseline_v9 evaluation\runs\paired500_20260930_three_phase_final_v3 --queries evaluation\queries_500_source_reviewed_refs.json --output evaluation\revision_20260930\paired500_final_v3_comparison.csv

.\venv\Scripts\python.exe evaluation\audit_paired_runs_against_sources.py --baseline evaluation\runs\paired500_20260930_baseline_v9\answers.jsonl --three-phase evaluation\runs\paired500_20260930_three_phase_final_v3\answers.jsonl --queries evaluation\queries_500_source_reviewed_refs.json --index-dir data\index_textract_85_v9 --output-dir evaluation\revision_20260930\paired500_final_v3_audit

.\venv\Scripts\python.exe evaluation\run_question_bank.py --queries evaluation\queries_reglamento_smoke_source_reviewed.json --output-dir evaluation\runs\reglamento_docs_smoke_final_v3 --variant three_phase --pair-id smoke_general_reglamento_docs_v9_v3 --model llama3:8b --index-dir data\index_textract_85_v9
```

La sintaxis se validó con `py_compile`; `git diff --check` no reportó errores de espacios/conflictos. El estado Git incluye muchos cambios previos del proyecto y no se hizo stage, commit, revert ni limpieza de esos archivos.
# Registro histórico (estado RAGAS supersedido)

> Este documento se redactó antes de terminar la corrida Gemini RAGAS de 500×4. La evaluación ya está completa. Para métricas finales y respuesta a revisores, consultar `RESPUESTA_REVISORES_Y_CAMBIOS_MANUSCRITO_FINAL.md`, `manual_validation/ragas_gemini_500_ablation_4variants_20260930/` y `manual_validation/analyze_ragas_500_paired.py`. Se conserva aquí el plan y los estados que eran ciertos al momento de su creación.

