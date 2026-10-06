# Estado de correcciones de revisores — 2026-09-30 (registro histórico, supersedido)

> **Estado reemplazado:** este documento se guardó antes de finalizar la corrida Gemini de 500 consultas. Sus afirmaciones de que RAGAS Gemini estaba incompleto o pendiente ya no están vigentes. Usar `RESPUESTA_REVISORES_Y_CAMBIOS_MANUSCRITO_FINAL.md` para el mapa actualizado y `manual_validation/ragas_gemini_500_ablation_4variants_20260930/` para la corrida completa. Se conserva este registro para no alterar el historial de trabajo.

Este registro distingue cambios ejecutados en el código, análisis ya existentes,
propuestas para el manuscrito y trabajo aún pendiente. El PDF camera-ready no
se editó. En el proyecto no se encontró la fuente editable de Springer.

## Resumen del estado

- **Ya existe:** evaluación RAGAS guardada por consulta para cuatro variantes y
  30 preguntas; comparación pareada y valores del artículo están resumidos en
  `evaluation/resultados_ragas.txt` y los CSV originales. Los cuatro JSON de
  entrada contienen las mismas 30 preguntas en el mismo orden.
- **Banco de 500:** el autor confirmó revisión humana manual de las 500
  referencias y de ambas respuestas contra los PDF. El resumen registra
  438/450 correctas en dominio para tres fases y 336/450 para baseline; la
  revisión fue de un autor y no doble ciega. Entre los pares discordantes de
  exactitud hubo 106 aciertos solo de tres fases y 4 solo del baseline; la
  prueba exacta bilateral de McNemar dio p=9.24e-27, condicionada al banco y a
  esas etiquetas. OOD se mantiene separado: 50/50 frente a 47/50, p=.25.
  Gemini RAGAS no terminó y no produjo una comparación nueva de métricas RAGAS.
- **Reevaluación local completa de la comparación principal:** V1 baseline y
  V4 completo puntuados con `llama3:8b`, RAGAS 0.2.14 y respuestas/contextos
  congelados. V1 está en `ragas_ollama_repeat1/`; V4 en
  `ragas_ollama_repeat1_v4/`. Los CSV originales no se pisan. Se detuvo el
  intento de hacer las cuatro variantes seguidas después de V1 y parte de V2;
  esa carpeta queda anotada como parcial. V2/V3 históricos siguen intactos.
- **Resultado preliminar V1:** faithfulness 0.5640 → 0.6288, answer relevancy
  0.6122 → 0.6042, context precision 0.3600 → 0.3728 y context recall
  0.7011 → 0.6733. En V4, las medias nuevas son 0.6370, 0.5227, 0.2946 y
  0.6367 respectivamente. Para los pares disponibles, la correlación por pregunta fue
  baja en faithfulness (Pearson 0.239) y context recall (0.294); MAE 0.231 y
  0.326 respectivamente. En V4, las medias V4−V1 cambiaron de dirección en
  faithfulness (-0.0485 a +0.0081) y answer relevancy (+0.0456 a -0.0814).
  Las cuatro pruebas pareadas nuevas son no significativas (p=.879, .511, .420,
  .719; Holm: todas 1.0). La configuración histórica no tiene manifest
  completo, por lo que no atribuimos estas diferencias solo a aleatoriedad.
- El análisis regenerable está en `analyze_ragas_repeat.py` y
  `ragas_repeat_comparison.json`; resumen y comandos en `RAGAS_REPEAT_ANALYSIS.md`.
- **Importante:** `evaluation/queries.json` dice en sus instrucciones que se
  reemplacen sus preguntas si se conservan las 30 originales del artículo. No
  se ha demostrado que sean idénticas a las preguntas que produjeron las cifras
  enviadas. Por eso esta repetición no debe llamarse reproducción estricta del
  artículo hasta verificar esa procedencia.
- **No está terminado:** el manuscrito de Springer no recibió los cambios. Hay
  borrador de texto, pero falta la fuente editable, aplicación, paginación y
  revisión visual final.

## Seguimiento observación por observación

| Observación | Hecho verificable / código | Falta para cerrarla | Estado |
|---|---|---|---|
| Contribución y falta de superioridad global (R1 novedad; R2 mejora no convincente) | La revisión humana del banco nuevo registra 438/450 respuestas correctas en dominio para tres fases frente a 336/450 para baseline; en Cronograma tres fases obtiene menos respuestas completamente correctas (18/25 vs 22/25), por lo que la mejora no es uniforme. RAGAS histórico en las 30 consultas muestra V4 mayor solo en answer relevancy, sin diferencia significativa, y baseline mayor en faithfulness y context precision. | Presentar el banco de 500 como evidencia nueva delimitada al corpus/configuración evaluados; añadir limitaciones de un solo revisor y diferencias respecto del experimento original. No sustituir las cifras del artículo hasta reconciliar versiones, condiciones y resultados; no afirmar superioridad general ni causalidad de Textract. | Parcial; evidencia nueva disponible |
| Protocolo RAGAS: inputs, métricas, agregación, versión y juez (R2 métrica) | `evaluation/run_ragas.py` entrega `question`, `answer`, `contexts`, `ground_truth` a faithfulness, answer relevancy, context precision y context recall; salida por pregunta y media no ponderada por variante. Versión disponible: RAGAS 0.2.14. El borrador explica las definiciones y valores ausentes. El intento Gemini sobre 500 consultas se interrumpió por crédito agotado antes de guardar CSV. | Precisar en manuscrito versión/configuración histórica, si RAGAS usó sus prompts por defecto, modelo de embeddings y cómo se promediaron NaN. La repetición nueva sobre 500 tendría que ejecutarse completa; no hay resultado RAGAS Gemini que reportar. | Parcial |
| Estabilidad y sesgo del juez/generador (R1 mismo Llama; R2 reproducibilidad) | `resultados_ragas.txt` registra juez Ollama; V1 y V4 se reevaluaron sobre salidas congeladas, con manifest/hash/versiones. Medias/dirección cambiaron; la reevaluación V4−V1 dio cuatro p no significativos. | La corrida histórica no conserva toda la configuración, así que el cambio mezcla posibles diferencias de configuración/versiones y variación del juez. Temperatura 0 no garantiza determinismo. Llama 3 8B como generador y juez comparte sesgos. Si se usa nuevo juez independiente, puntuar V1–V4 sobre las mismas salidas y referencias. | Parcial; repetición principal terminada |
| Error del router en REGLAMENTO y costo de latencia (R2 análisis router) | La revisión humana del banco de 500 da 102/105 respuestas de Reglamento correctas en tres fases (1 parcial, 2 incorrectas), frente a 26/105 correctas del baseline (1 parcial, 78 incorrectas). Por separado, el informe pareado registra 105/105 páginas esperadas recuperadas automáticamente en Reglamento. El sistema añadió resolución estructurada de artículos y respaldo. | Reportar que es un benchmark cerrado y de un solo revisor; conectar con el 1/6 de recall del experimento original, cuantificar recuperación antes/después en condiciones comparables y medir latencia por consulta de forma interpretable. Las 11.44 s agregadas de tres fases no se comparan como latencia pura con baseline porque las respuestas se extrajeron sin invocar el generador. | Parcial; evidencia nueva disponible |
| Separación benchmark, calibración de caché y paráfrasis (R2 conjuntos) | `evaluation/eval_cache.py` entrena con las 30 consultas originales y prueba 30 paráfrasis emparejadas; comprueba a qué consulta original resolvió cada paráfrasis. RAGAS también usa las 30 consultas base. | Describir que no son tres muestras independientes: hay 30 originales y 30 paráfrasis derivadas. Precisar qué significa training/test solo para caché. Verificar si esas preguntas son las del artículo, pues el comentario de `queries.json` no lo garantiza. | Parcial |
| Tamaños de fragmento por variante (R2 confusor) | El pipeline actual comparte un índice entre las cuatro variantes de `ablation.py`; `app/ingest.py` usa 200 palabras/20 de solapamiento. | Reconstruir configuración histórica del índice/artículo. Si variantes se indexaron con tamaños distintos, reportar confusión y no atribuir causalidad; no afirmar el chunk actual como configuración de la corrida enviada sin hashes. | Pendiente |
| Tabla 8: denominador de accuracy | El borrador identifica la discrepancia: 5/30 = 16.7% end-to-end; 5/21 = 23.8% condicionada a 21 hits. Para dos etapas, 9/13 = 69.2%. | Cambiar encabezado, texto y valores de la fuente editable de modo consistente y revisar si la pregunta de la tabla es end-to-end o condicional. | Propuesta lista; falta aplicar |
| Tablas 4/9/10, comparación pareada y prueba estadística | `paired_analysis.py` y `revision_20260929/paired_analysis.json` contienen cuatro pruebas Wilcoxon signed-rank bilaterales pareadas y corrección Holm; el borrador separa medias globales de deltas en pares válidos. | `evaluation/resultados_wilcoxon.txt` es un resultado legado que solo muestra tres métricas y omite context precision; reconciliarlo con el JSON de cuatro métricas, regenerar una salida única, verificar los denominadores y corregir el rótulo de la fuente. | Parcial; hay resultados internos inconsistentes |
| Versiones/modelos, quantización, índices, cross-encoder y latencia | `run_ragas.py` ahora genera manifest con hashes, Python, versiones, juez, temperatura y RunConfig. El borrador tiene una lista de configuración por completar. | El manifest histórico no está; obtener las versiones/configuración exactas de la corrida del artículo. Añadir tag/digest Ollama, quantización, parámetros, modelo de reranker, configuración FAISS/HNSW, hardware, repeticiones y estadísticos de latencia. | Parcial |
| OCR y origen escaneado (R1 texto original / R2 OCR) | Se inspeccionó que los PDF actuales no tienen capa de texto. Comparación visual de desarrollo: Textract 74/79 celdas numéricas y CER 0.00%; EasyOCR 50/79 y CER 2.60%, en un PDF de vacantes. El artefacto está separado del baseline. | Confirmar que los hashes son del corpus exacto del artículo; obtener segunda transcripción humana de la referencia, ampliar muestra y no presentar cuatro páginas/79 celdas como exactitud general. Aclarar que OCR es condición de este corpus escaneado, no requisito del sistema. | Parcial |
| Figuras, tablas, inglés, tipografía y márgenes | El borrador mapea traducción de etiquetas, simplificación de figuras/tablas y correcciones tipográficas. | Conseguir fuente editable y rehacer/renderizar figuras; revisar legibilidad, duplicado de punto, cursivas, espacios y desbordes. | Pendiente por fuente editable |
| “Fail-fast” | El borrador propone “early-exit cascade” para describir el orden de etapas. | Aplicar y comprobar en la fuente; definir que es salida temprana por etapas y no una estrategia de tolerancia a fallos. | Propuesta lista; falta aplicar |
| Referencias [17] y cuatro prepublicaciones restantes | El borrador deja los metadatos corregidos para [11], [17], [24] y mantiene [8], [23] como preprints según las fuentes revisadas. | Repasar una por una las cinco entradas en la fuente Springer y verificar metadatos finales antes del envío. | Parcial |
| Relevancia regional | El borrador contextualiza corpus oficial en español de una institución pública peruana y niega validación de impacto con usuarios. | Insertar en discusión/limitaciones; no afirmar impacto social medido sin estudio de postulantes. | Propuesta lista; falta aplicar |

## Qué falta en el código antes de llamarlo listo

1. Para reforzar la evaluación de estabilidad, verificar la identidad del
   benchmark, recuperar la configuración histórica o declarar que no se pudo,
   y si es posible repetir con juez independiente sobre V1–V4 congeladas. La
   reevaluación actual no sustituye resultados del artículo.
2. Confirmar el benchmark original exacto, su hash y las 30 referencias. Hoy el
   comentario de `queries.json` deja abierta la posibilidad de que sea otro
   conjunto.
3. Rehacer el test router con consultas y etiquetas verificadas, sobre una
   versión congelada del código. Los rechecks 50/50 y 25/25 son subconjuntos
   dirigidos, no una corrida integral independiente.
4. La revisión humana manual de las 500 referencias y de ambas respuestas fue
   confirmada por el autor y quedó registrada en
   `manual_validation/HUMAN_REVIEW_ATTESTATION_500_20260930.md`. Los conteos
   pueden reportarse como adjudicación de un solo autor, no como gold estándar
   independiente o doble ciego; preservar esta limitación y la trazabilidad por
   ID al redactar el manuscrito.
5. Aislar una comparación OCR/índice controlada si se quiere afirmar impacto de
   Textract: mantener consultas, chunking, retrieval, modelo y prompt constantes.
6. Incorporar pruebas de regresión para ruteo, abstención, tablas/celdas y
   recuperación. Las ejecuciones exploratorias actuales no cubren de manera
   exhaustiva todas las regresiones.
7. Mejorar el manifest de `run_ragas.py` para incluir automáticamente el digest
   de Ollama, plantillas de evaluación RAGAS (o sus hashes), tag de embeddings y
   datos de hardware. En esta repetición se registró manualmente el digest
   `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1` porque
   el manifest captura el tag (`llama3:8b`) y las versiones Python, pero no el
   ID exacto del modelo ni la GPU.

## Frases científicamente defendibles hoy

- “En este corpus de documentos escaneados, Textract obtuvo mejores resultados
  que EasyOCR en la muestra visual de desarrollo evaluada; la muestra es
  pequeña y conserva errores numéricos.”
- “La arquitectura completa obtuvo una media mayor de answer relevancy, sin
  diferencia pareada significativa; el baseline fue mayor en otras métricas.
  El estudio no demuestra superioridad general.”
- “Los cambios recientes de código mejoraron el comportamiento en pruebas
  dirigidas de OOD, cronograma y recuperación de artículos; las corridas de 500
  consultas contienen referencias OCR sin validar y no son evidencia final de
  exactitud.”

No afirmar “100%”, mejora causal de Textract en RAG, validación con postulantes,
o reproducción exacta hasta resolver los puntos anteriores.
