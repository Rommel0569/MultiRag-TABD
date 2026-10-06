# Artículo 67 — respuestas a revisores y propuesta de cambios del manuscrito

**Borrador de trabajo para revisión de autores; no enviado a SIMBig/Springer.** Se cotejó el PDF completo de 14 páginas con los dos informes de revisión y con las corridas archivadas. En el repositorio no se encontró el `.tex` ni un Word fuente del artículo; por eso este documento contiene respuestas y texto listo para integrar, pero no modifica el PDF editorial.

## 1. Criterio para revisar el manuscrito

Mantener separados tres experimentos que no son intercambiables:

1. **Artículo enviado:** 30 consultas, cuatro variantes RAGAS, juez Llama 3 8B local. La tabla original informa que V4 solo tiene la media más alta en answer relevancy; no es significativa (p=.957), y V1 supera V4 en faithfulness, context precision y context recall. No cambiar estas cifras por las corridas nuevas.
2. **Evaluación RAGAS adicional:** 500 consultas y cuatro variantes generadas por Ollama `llama3:8b` (temperatura 0.1) sobre `data/index_textract_85_v9`; juez independiente Gemini `gemini-3.1-flash-lite` (temperatura 0); RAGAS 0.2.14; embeddings locales `intfloat/multilingual-e5-base`. Se procesaron 2,000 filas, con resultados por fila, manifiesto, hashes y uso de tokens guardados. Presentar como experimento adicional de la versión revisada, no como reproducción del experimento enviado.
3. **Verificación manual adicional:** el autor revisó las 500 referencias y ambas respuestas contra los PDF. Hubo 450 preguntas en dominio y 50 OOD. Fue una revisión de un evaluador, no ciega; no es doble anotación ni validación independiente. Reportar por separado de RAGAS.

La nueva comparación RAGAS usa 450 preguntas en dominio como análisis principal y separa las 50 OOD, porque una negativa correcta puede recibir puntajes de contexto bajos aunque sea la conducta apropiada. En los 450 pares, V4 supera V1 en las cuatro medias; pruebas de Wilcoxon signed-rank bilaterales pareadas con corrección Holm para cuatro métricas: faithfulness Δ=.2953, pHolm=8.09e-34; answer relevancy Δ=.0720, pHolm=.000120; context precision Δ=.2171, pHolm=1.40e-22; context recall Δ=.1741, pHolm=1.95e-17. Estas diferencias corresponden a esta corrida, este banco, estos outputs y este juez; no borran ni invalidan el resultado original de n=30. En las 50 OOD, tres fases logró 50/50 abstenciones correctas y baseline 47/50 (McNemar p=.25). RAGAS sobre OOD debe informarse aparte.

La verificación manual dentro del dominio registró 438/450 exactas (97.33%) para tres fases frente a 336/450 (74.67%) para baseline; diferencia pareada de 22.67 puntos; 106 pares favorecieron solo a tres fases y 4 solo a baseline; McNemar exacta bilateral p=9.2369e-27. Por categoría, tres fases fue peor en Cronograma (18/25 vs. 22/25), mejor en Vacantes (175/175 vs. 148/175), Temario (143/145 vs. 140/145) y Reglamento (102/105 vs. 26/105). Estas etiquetas fueron adjudicadas por un autor no ciego. La conclusión admisible es una mejora observada en este banco revisado y esta versión, no una garantía para otras consultas o instituciones.

La corrida RAGAS adicional en 500 contiene 50 OOD, con lo cual sus promedios de las 500 filas mezclan evaluación factual y comportamiento de abstención. El resultado exacto del CSV usa todas las filas, pero las cifras primarias de comparación propuestas abajo se calculan sobre las 450 consultas en dominio y reportan OOD por separado. No resumir estas cuatro dimensiones con un “puntaje total” nuevo.

## 2. Respuesta al Reviewer 1

### R1.1 — Calificación: weak accept

**Respuesta en inglés:**

> We thank the reviewer for the weak-accept recommendation and for recognizing the clarity of the workflow, methodology, and ablation. We have revised the manuscript to state the contribution and empirical claims more precisely, and we address the concerns below point by point.

**Cambio:** no se inserta la calificación en el cuerpo del artículo. Se corrigen alcance, resultados, limitaciones y presentación según los puntos siguientes.

### R1.2 — Evaluación general: novedad, calidad técnica, claridad, significancia y relevancia

#### R1.2a — Novedad incremental y ausencia de mejora sobre baseline

**Respuesta en inglés:**

> We agree that the contribution is primarily an empirical study of an integrated architecture rather than a new retrieval algorithm. The original 30-query RAGAS experiment did not establish that the complete system consistently outperformed the dense baseline. We retain those results and narrow the contribution claim. We additionally report a separate 500-query source-checked evaluation of a later system snapshot, while clearly distinguishing its corpus, judge, and single-reviewer procedure from the submitted experiment.

**Cambios en Introduction y Conclusion:** quitar declaraciones de novedad algorítmica o superioridad general; conservar la contribución como ensamblaje evaluado, análisis de fallos y caso de admisión universitaria peruana. Añadir el alcance explícito:

> This work does not introduce a new retrieval primitive. Its contribution is an empirical case study of how semantic caching, intent routing, hybrid retrieval, and reranking behave when integrated for colloquial questions about official university-admission documents. We report component-level trade-offs and failure cases. The findings are specific to the evaluated CEPRUNSA corpus, system snapshots, and query banks; they do not establish general superiority across institutions or document collections.

#### R1.2b — Muestra pequeña

**Respuesta en inglés:**

> We agree that the original 30-query benchmark limits the strength and scope of the submitted study. To address this concern, we add a separate paired evaluation on 500 queries for a later system snapshot: 450 in-domain and 50 out-of-domain. The author manually checked the 500 references and both systems’ outputs against the source PDFs. Because this review was conducted by one non-blinded author, we report it as single-reviewer source verification rather than independent annotation. We retain the original experiment and report the expanded evaluation as additional evidence, not as a replication.

**Agregar a Methods, subsección “Additional source-verified evaluation”:**

> In a separate follow-up evaluation, we compared the dense baseline and the complete three-phase system on a fixed bank of 500 questions: 450 in-domain questions (25 schedule, 175 available-places, 145 syllabus, and 105 regulations questions) and 50 out-of-domain questions. Both systems used the same 85-page Textract-v9 index and the same query bank. Answers were generated locally with Ollama `llama3:8b` at temperature 0.1. One author checked every reference and both system answers against the source PDFs. An in-domain answer counted as exact only when marked fully correct; partial answers were not counted as exact. Correct out-of-domain abstentions were analyzed separately. This single-reviewer, non-blinded assessment evaluates a later system and corpus snapshot and is not a replication of the original 60-page, 30-query experiment.

**Agregar a Results, separando exactitud manual y RAGAS:**

> In the author-reviewed source-based assessment, the three-phase system produced fully correct answers for 438/450 in-domain questions (97.33%), compared with 336/450 (74.67%) for the baseline, a paired difference of 22.67 percentage points. Among discordant pairs, 106 were correct only for the three-phase system and 4 only for the baseline; the two-sided exact McNemar test yielded p=9.24×10⁻²⁷. By category, three phases was less accurate on schedule questions (18/25 vs. 22/25), and more accurate on available places (175/175 vs. 148/175), syllabus (143/145 vs. 140/145), and regulations (102/105 vs. 26/105). On out-of-domain questions, it abstained correctly on 50/50 cases versus 47/50 for the baseline (p=.25); we report this separately from factual accuracy. The manual labels were provided by one non-blinded author, so this result is conditional on that review and the evaluated bank.

**Limitación:** no describir 97.33% como una propiedad garantizada del sistema, ni 97.6% como exactitud factual; el 97.6% combina respuestas en dominio y abstenciones OOD correctas.

#### R1.2c — El mismo Llama como generador y juez

**Respuesta en inglés:**

> We agree that using the same local model family for generation and evaluation can introduce correlated or self-preference bias. The submitted 30-query scores used local Llama 3 8B as the RAGAS judge, so they are evaluator-dependent comparative signals rather than independent human ratings. The additional 500-query RAGAS run uses Gemini 3.1 Flash-Lite as an independent judge of frozen Ollama-generated outputs. We report both experiments separately and do not claim that an LLM judge is fully reproducible or equivalent to human evaluation.

**Cambios:** actualizar §3.6 para registrar juez y configuraciones **por experimento**. Para el experimento adicional se puede documentar con manifiesto: RAGAS 0.2.14, Gemini `gemini-3.1-flash-lite`, temperatura 0, embeddings locales `intfloat/multilingual-e5-base`; generación Ollama `llama3:8b`, temperatura 0.1; 500 consultas, cuatro variantes, archivos de entrada con SHA-256. Para el artículo original no completar parámetros que no estén en el registro histórico.

**Agregar a Limitations:**

> The submitted 30-query RAGAS evaluation used local Llama 3 8B both to generate answers and as the judge. This shared model can introduce correlated evaluation bias, and LLM-based scores should not be interpreted as human judgments. The follow-up 500-query RAGAS evaluation used Gemini 3.1 Flash-Lite to judge frozen outputs generated by Ollama; it reduces same-model overlap but remains an LLM-as-a-judge evaluation. The follow-up run is separately versioned and does not reproduce the original experiment. Independent multi-annotator validation remains future work.

#### R1.2d — OCR y disponibilidad de PDF en texto

**Respuesta en inglés:**

> We agree that OCR should not be applied when a reliable native text layer is available. The official CEPRUNSA PDFs used in the scanned-document experiment required OCR because they were image-based. We clarify that OCR is a corpus-dependent preprocessing choice, not a requirement for all university documents. The original article used EasyOCR; the later 500-query index used AWS Textract v9. These extraction configurations belong to separate system snapshots and are not conflated in the revised results.

**Cambio en §3.3:** sustituir cualquier generalización que presente OCR como intrínseco al sistema por:

> The source files in the original CEPRUNSA experiment were scanned PDFs without a usable text layer, so OCR was required to obtain searchable text. OCR is not required for born-digital documents: when a PDF provides a reliable text layer, native text extraction is preferable. The original experiment used EasyOCR. A later, separately evaluated system snapshot used an 85-page Textract-v9 index; its results are reported as a follow-up and are not attributed to the original EasyOCR pipeline.

**Nota editorial:** antes de fijar el texto, asegurar que el PDF/hashes del corpus original de 60 páginas estén identificados. No sustituir EasyOCR por Textract en la descripción del experimento enviado. No afirmar que AWS por sí mismo mejoró RAGAS/end-to-end: la comparación manual adicional mide dos sistemas completos usando el mismo índice Textract-v9.

#### R1.2e — Punto extra al final de página 2

**Respuesta en inglés:**

> Corrected. The duplicated punctuation at the end of page 2 has been removed.

**Cambio:** eliminar el punto duplicado en Related Work. Confirmar en el `.tex` y en la prueba de galeras.

#### R1.2f — Table 1 ilegible

**Respuesta en inglés:**

> We agree that Table 1 was difficult to read. We replace it with a smaller, legible comparison containing only directly relevant studies and comparable dimensions. Where protocols and datasets are not comparable, we use a concise narrative synthesis instead of juxtaposing their scores.

**Cambio:** reducir Table 1 a cinco o seis trabajos clave, fuente/tarea/método/diferencia relevante; usar tamaño de fuente normal de Springer. No comparar scores heterogéneos sin describir tareas y protocolos.

#### R1.2g — Cursiva inconsistente de “embeddings”

**Respuesta en inglés:**

> Corrected. We use a consistent roman typeface for “embedding(s)” throughout the manuscript.

**Cambio:** buscar globalmente `embedding`, `embeddings`, y normalizar estilo tipográfico.

#### R1.2h — Figuras 1 y 5 en español

**Respuesta en inglés:**

> Corrected. All figure labels and category names are now in English. We consolidate the useful architecture and execution-flow information into a single legible diagram.

**Cambio:** rehacer a vector/alta resolución en inglés; categorías: `Schedule`, `Available places`, `Syllabus`, `Regulations`, `Out-of-domain`. El diagrama debe representar la versión evaluada en cada resultado y no incorporar silenciosamente componentes de la corrida posterior.

#### R1.2i — Espacio entre “Figures” y “2–4”

**Respuesta en inglés:**

> Corrected. We removed the redundant figure-range sentence after consolidating the figures and updated all cross-references.

**Cambio:** corregir o retirar la referencia de §3.2 y actualizar automáticamente numeración y referencias.

#### R1.2j — Capturas de Figure 2 ilegibles

**Respuesta en inglés:**

> We removed the low-resolution interface screenshots because they did not provide evidence needed to understand the method. The revised manuscript uses the space for methodological details.

**Cambio:** eliminar capturas de UI. Si el editor requiere una captura, sustituirlas por una sola imagen original en alta resolución.

#### R1.2k — Figure 3 pequeña y Figure 4/logs

**Respuesta en inglés:**

> We redrew the architecture figure at a readable width and removed the backend log screenshot. The cache behavior and measured outcomes are explained in the text and table.

**Cambio:** conservar una única figura técnica vectorial; eliminar captura de logs Fig. 4; explicar caché con texto y cifras observadas. Renumerar figuras, tablas y referencias cruzadas.

#### R1.2l — Texto que desborda los márgenes

**Respuesta en inglés:**

> Corrected. We shortened the long reranker model description in the body text and reformatted the numerical result to fit within the column. We checked the rendered pages for overflow.

**Cambios:** en p. 7 usar en el texto `multilingual cross-encoder reranker`; reservar el identificador completo para Table 2 o material suplementario con cortes correctos. En p. 8 reescribir la diferencia como oración: `The mean answer-relevancy score was 0.6578 for Multi-RAG and 0.6122 for the baseline (mean difference, +0.0456); the paired difference was not statistically significant.` Verificar PDF renderizado.

#### R1.2m — Referencias arXiv con publicación posterior

**Respuesta en inglés:**

> We checked the cited preprints against the proceedings and publisher records. We updated the entries for RAGAs, Confident RAG, and ARES to cite their published versions, and corrected the IEEE Access entry. We retain the cited works that remain preprints as preprints and do not infer a venue where none could be verified.

**Cambios bibliográficos:**

| N.º | Tratamiento propuesto |
|---|---|
| [11] RAGAs | Citar EACL 2024 System Demonstrations, pp. 150–158, DOI `10.18653/v1/2024.eacl-demo.16`, reemplazando la entrada solo-arXiv. |
| [17] Confident RAG | Citar ICLR 2026 Workshop on Logical Reasoning of Large Language Models; indicar explícitamente que es paper de workshop, no track principal. |
| [24] ARES | Citar NAACL-HLT 2024, pp. 338–354, DOI `10.18653/v1/2024.naacl-long.20`. |
| [18] Automated Software Test Case Generation | La entrada ya contiene DOI IEEE Access, pero dice también `preprint, SSRN`; eliminar la descripción contradictoria y completar IEEE Access 14, pp. 31124–31145 (2026). |
| [8] Adaptive Query Routing | No se encontró una publicación de proceedings para el preprint citado; conservar como arXiv salvo nueva verificación. |
| [23] LLMs-as-Judges survey | Conservar como preprint arXiv:2412.05579 salvo que los autores aporten una versión revisada publicada distinta. No confundirlo con otros surveys sobre LLM judges. |
| [13] ELSSA | Identificar correctamente como SSRN/preprint; no etiquetarlo como arXiv ni como conferencia. Verificar que aporte al artículo antes de conservarlo. |

La revisión de referencias debe repetirse sobre toda la bibliografía durante edición; las acciones anteriores cubren las entradas rastreadas y las identificables en el PDF, no certifican toda la bibliografía como libre de errores.

### R1.3 — Impacto/relevancia para América Latina

**Respuesta en inglés:**

> We have made the regional relevance explicit: the application concerns Spanish-language admissions information from a public university in Peru, including local administrative terminology and scanned institutional documents. This establishes a regional use case, not measured social impact. We did not conduct a user study with applicants or admissions staff.

**Agregar a Introduction o Discussion:**

> The study addresses a regionally relevant use case: Spanish-language admissions information published by a public university in Peru, including local administrative terminology and official scanned documents. This context motivates the application but does not constitute evidence of measured social impact; no study with applicants or admissions staff was conducted.

## 3. Respuesta al Reviewer 2

### R2.1 — Descripción de arquitectura y nombres de categorías

**Respuesta en inglés:**

> We thank the reviewer for recognizing the clear architecture and the two-stage cache. We translated the figures and category names into English and retained the category identifiers only once where needed to explain the implementation.

**Cambio en Methods:**

> The router assigns one of five categories: Schedule (`CRONOGRAMA`), Available places (`VACANTES`), Syllabus (`TEMARIO`), Regulations (`REGLAMENTO`), or Out-of-domain (`FUERA_DE_DOMINIO`). English labels are used throughout the manuscript; Spanish strings are implementation identifiers.

### R2.2 — Mecanismo de caché

**Respuesta en inglés:**

> We thank the reviewer for the positive assessment of the cache design. We clarify the observed trade-off: in the paraphrase evaluation, the two-stage verification accepted 13 cases, of which 9 were correct and 4 were incorrect (69.2% correctness conditional on acceptance). The cache can reduce repeated work, but the tested threshold did not eliminate false accepts.

**Cambio en Results/Discussion:** conservar los detalles de las dos etapas y la comparación con coseno; cambiar cualquier frase que diga `prevents false positives` o sugiera garantía. Distinguir cobertura (aceptados / consultas) de precisión condicionada (correctos / aceptados) y exactitud end-to-end.

### R2.3 — Ablation

**Respuesta en inglés:**

> We thank the reviewer for recognizing the ablation as useful. We retain the original four-variant experiment and report its actual trade-offs without describing a component as uniformly beneficial. The later 500-query ablation is added as a separate run with a different judge and system snapshot.

**Cambio:** preservar Table 9 original; añadir una tabla adicional o apéndice claramente rotulado para los resultados Gemini del nuevo banco. No reemplazar las medias de las 30 preguntas.

### R2.4 — Resultados globales no concluyentes frente al baseline

**Respuesta en inglés:**

> We agree. In the submitted 30-query RAGAS results, the baseline has higher means on faithfulness, context precision, and context recall; V4 has a higher answer-relevancy mean, but its paired difference is not significant. We retain this result and state that the original study did not establish general superiority. A separate source-checked evaluation on 450 in-domain queries favors the later three-phase snapshot in exact answer correctness, but the schedule category regresses and the labels come from one non-blinded reviewer. These are distinct outcomes and are not used to reinterpret the original RAGAS table.

**Cambio:** reemplazar en Abstract/Discussion/Conclusion cualquier “outperforms the baseline” sin alcance por texto acotado. Si el límite de páginas impide incluir las dos evaluaciones, priorizar un resumen transparente en texto y una tabla compacta suplementaria.

### R2.5 — Router zero-shot, calidad y 24.1% de latencia; SVM/Naive Bayes

**Respuesta en inglés:**

> We agree that the original router results merit deeper analysis. The submitted evaluation reported 23/30 correct labels (76.7%), only 1/6 Regulations queries recalled, and a mean router time of 2.68 s (24.1% of end-to-end latency). We retain these limitations. The later 500-query results evaluate a revised end-to-end pipeline with structured extraction; they do not isolate router classification and are not a replacement router benchmark. We discuss SVM and Naive Bayes as supervised alternatives that require a separately labeled development set and leakage-safe held-out evaluation; no such comparison has yet been run.

**Agregar a Discussion (incluye rationale, editar el corchete con la razón real de diseño):**

> The original zero-shot router classified 23/30 queries correctly (76.7%), with recall of 1/6 for Regulations, and accounted for 24.1% of measured end-to-end latency (2.68 s). **[State the authors’ documented reason for selecting zero-shot routing; do not invent a rationale.]** A supervised SVM or Naive Bayes baseline may reduce inference latency, but a fair comparison requires a larger labeled training set and a held-out split grouped by query intent/paraphrase to avoid leakage. We leave this controlled comparison for future work. The follow-up end-to-end results include additional structured extraction and should not be interpreted as an isolated measurement of router accuracy.

No decir que el router “ya está solucionado” por la revisión de 500 respuestas. La revisión manual end-to-end registra 102/105 respuestas de Reglamento completas, pero no es un benchmark de clasificación aislado.

### R2.6 — Figuras, Table 6 y espacio para metodología

**Respuesta en inglés:**

> We agree that the original presentation used space inefficiently. We remove low-resolution interface/log screenshots, consolidate the architecture figures, and shorten redundant tables. We use the space to state the evaluation inputs, metric definitions, judge configuration, aggregation, and limitations.

**Cambios:** borrar Fig. 2 (capturas), Fig. 4 (logs); fusionar/reconstruir Fig. 1/3/5 en un diagrama inglés legible. Eliminar o resumir Table 6 si repite el diagnóstico de Table 5; reconsiderar Table 4 si duplica Table 9. No quitar los datos diagnósticos necesarios del router; trasladarlos a una frase o suplemento.

### R2.7 — Definiciones de Faithfulness, Answer Relevancy, Context Precision y Context Recall

**Respuesta en inglés:**

> We agree that these definitions are necessary for interpreting the scores. We added operational descriptions of all four RAGAS metrics and clarified that they measure different dimensions and are not equivalent to exact answer accuracy.

**Reemplazar/expandir §3.6 con:**

> For each evaluation row, we provide the question, generated answer, retrieved contexts, and reference answer. Faithfulness estimates the share of answer claims supported by the retrieved context. Answer relevancy estimates how well the answer addresses the question by generating questions implied by the answer and comparing their embeddings with the original question. Context precision measures whether relevant retrieved passages are ranked ahead of irrelevant passages. Context recall estimates how much of the reference answer’s information is supported by the retrieved context. Each metric is reported separately on a 0–1 scale, with higher values indicating better performance for that dimension. These LLM-assisted metrics are not interchangeable with source-verified exact answer accuracy. The submitted and follow-up runs used different judge configurations, which are reported separately.

**Cambios cuantitativos nuevos a reportar en Results, como evaluación adicional:**

| Métrica (n=450 en dominio) | V1 baseline | V2 reranking | V3 router+híbrido | V4 completo |
|---|---:|---:|---:|---:|
| Faithfulness | 0.6368 | 0.6730 | 0.6328 | **0.9322** |
| Answer relevancy | 0.8204 | 0.8254 | 0.8160 | **0.8924** |
| Context precision | 0.7135 | 0.7414 | 0.7142 | **0.9306** |
| Context recall | 0.7937 | 0.8302 | 0.7893 | **0.9678** |

En la comparación pareada V4−V1 sobre esas 450 preguntas, las cuatro pruebas Wilcoxon signed-rank fueron significativas después de Holm: faithfulness Δ=.2953, pHolm=8.09×10⁻³⁴; answer relevancy Δ=.0720, pHolm=.000120; context precision Δ=.2171, pHolm=1.40×10⁻²²; context recall Δ=.1741, pHolm=1.95×10⁻¹⁷. Informar el código, filas pareadas, versión de SciPy y método estadístico en suplemento/registro reproducible. Los promedios reflejan RAGAS 0.2.14 con Gemini judge y las salidas congeladas de esta corrida; no prueban generalidad ni corrigen el resultado original de n=30.

### R2.8 — Uso de “fail-fast”

**Respuesta en inglés:**

> We agree that “fail-fast” was not the appropriate term. We replaced it with “staged early-exit workflow,” which describes progression to more costly stages until an answer is accepted or the system abstains.

**Cambios globales:** reemplazar `fail-fast` / `fail-fast logic` por `staged early-exit workflow` o `early-exit cascade` en Abstract, Introduction, Methods, Table 2 y pies de figura. No describir una consulta no resuelta como fallo de ejecución.

### R2.9 — Reproducibilidad y estabilidad de RAGAS

**Respuesta en inglés:**

> We agree that RAGAS scores depend on the judge and configuration. For the submitted 30-query experiment, the judge was local Llama 3 8B; the archived records do not preserve every prompt, package, and inference parameter. The new 500-query run is separately reproducible from its frozen inputs, hashes, manifest, and per-row output: Ollama `llama3:8b` generated the answers at temperature 0.1, Gemini `gemini-3.1-flash-lite` judged them at temperature 0, RAGAS 0.2.14 was used, and embeddings were computed locally with `intfloat/multilingual-e5-base`. We do not assert deterministic repeated scores; exact repetition may vary by provider/model version and inference implementation.

**Cambios:** reportar inputs (`question`, `answer`, `contexts`, `ground_truth`), versión, modelo proveedor/juez, temperatura, embedding model, fechas, hashes, número de queries y política de exclusión de valores inválidos. El nuevo run tiene `max_workers=64`, `max_retries=2`, `timeout=180`, `seed=42`; incluirlos en material de reproducibilidad. El número de API calls no equivale necesariamente a filas × métricas, pues Context Precision puede realizar llamadas por contexto. Mantener artefactos y costos fuera del cuerpo si el límite de páginas lo exige; ponerlos en suplemento.

## 4. Cambios globales que aplicar al manuscrito

### Quitar o reemplazar

1. Quitar afirmaciones de que la combinación es un algoritmo novedoso o supera generalmente al baseline.
2. Quitar `fail-fast`; usar `staged early-exit workflow`.
3. Quitar capturas de UI/log de Figures 2 y 4; redibujar las otras figuras en inglés, vectoriales y legibles.
4. Compactar Table 1 y retirar/combinar Table 6/duplicaciones de Table 4 con justificación.
5. Corregir la etiqueta estadística Table 10: `Wilcoxon signed-rank test`, no `rank-sum`.
6. Eliminar afirmaciones absolutas de que la caché previene falsos positivos; el test registró 4 incorrectos entre 13 hits aceptados.
7. No presentar RAGAS como determinista, reproducible por sí solo o equivalente a juicio humano.
8. No mezclar en una misma tabla sin marcación el RAGAS original de 30 (Llama judge) con el RAGAS adicional de 500 (Gemini judge, corpus/index posterior).

### Agregar

1. Aclaración de contribución empírica y límites de generalización.
2. Distinción expresa entre el experimento enviado y la evaluación posterior de 500 preguntas.
3. Definiciones de las cuatro métricas RAGAS y configuraciones separadas por corrida.
4. Resultados source-checked de 450 en dominio y 50 OOD, con limitación de un autor revisor.
5. Resultados RAGAS de 450 en dominio con V1–V4, y análisis estadístico pareado con corrección Holm; OOD en separado.
6. Trade-off del router y propuesta futura de comparar SVM/Naive Bayes en un test no contaminado.
7. Contexto peruano/latinoamericano sin afirmar impacto social medido.
8. Referencias corregidas a versiones de publicación verificadas.

### Conservar

- La tabla y conclusión originales del benchmark de 30 consultas, explicando que no establecieron superioridad global.
- La observación de que Regulations tuvo recall bajo en el experimento original.
- El resultado cache 9/13 correctos condicionado a aceptación, con sus cuatro falsos accepts observados.
- El tiempo del router y la latencia end-to-end como mediciones de la versión original, sin transferirlos a la versión nueva.

## 5. Edición tipográfica y de producción

- Página 2: borrar punto duplicado.
- Tabla 1: rehacer en tamaño legible y reducir a trabajos comparables.
- Normalizar cursiva de `embedding(s)`.
- Figuras 1/3/5: una figura vectorial a ancho completo con etiquetas inglesas; revisar coherencia de componentes.
- Figura 2 y Figura 4: retirar capturas borrosas/logs.
- Actualizar referencias a Figuras 2–4 y renumerar todas las tablas/figuras tras eliminar y fusionar.
- Página 7: evitar desborde del identificador largo del reranker.
- Página 8: reescribir `+0.0456` en frase fluida y dentro de margen.
- Bibliografía: usar nombres/venues/capitalización/DOI correctos; revisar ortografía, URLs y entradas no arbitradas.
- Generar el PDF final desde fuente Springer, renderizar todas sus páginas y comprobar legibilidad/márgenes antes de enviarlo.

## 6. Estado y pendientes verificables

- **Evidencia nueva disponible:** evaluación RAGAS 500×4 completa; outputs/inputs y manifiesto con hashes; comparación pareada adicional; revisión manual del autor registrada.
- **No hecho aquí:** edición del PDF camera-ready o envío a SIMBig/Springer. No hay fuente `.tex`/Word editable en el proyecto.
- **Antes de reemplazar el texto del artículo:** los autores deben confirmar que desean incorporar el estudio de seguimiento de 500 consultas al manuscrito revisado, identificar/hacer disponibles los PDF/hashes del corpus original de 60 páginas y confirmar el rationale real de zero-shot routing.
- **Pendiente científico:** segundo anotador independiente para medir acuerdo; evaluación en banco externo/otra convocatoria; benchmark aislado del router contra SVM/NB; más consultas de Cronograma por la regresión observada; intervalos de confianza y estabilidad del juez; evaluación por consulta publicada de latencia para baseline y tres fases bajo el mismo protocolo.

## 7. Evidencia local asociada

- RAGAS nuevo: `evaluation/revision_20260930/manual_validation/ragas_gemini_500_ablation_4variants_20260930/tabla_ablacion_gemini_final.csv`, `ragas_scores_checkpoint.csv`, `manifest.json`.
- Entradas congeladas y configuración de generación: `evaluation/revision_20260930/manual_validation/ragas_input_4variants_500/`.
- Revisión manual autor: `evaluation/revision_20260930/manual_validation/HUMAN_REVIEW_ATTESTATION_500_20260930.md` y `source_validation_500_completed.csv`.
- Artículo original de 30 consultas: `evaluation/resultados_ragas.txt` y los CSV originales V1–V4. Se conservan como evidencia histórica, no reemplazada.
- Índice posterior: `data/index_textract_85_v9/`.

