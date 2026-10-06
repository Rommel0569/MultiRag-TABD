# Verificación de la corrida de 500 consultas y comparación baseline/RAG de tres fases

Fecha de revisión: 2026-09-29 (la corrida lleva timestamp UTC 2026-09-30)  
Corrida inspeccionada: `evaluation/runs/ollama_20260930T003458_695273Z/answers.jsonl`  
Banco: `evaluation/queries_500_candidates.json`

> **Actualización posterior:** este archivo conserva el triage inicial. El autor confirmó después haber revisado manualmente las 500 referencias y ambas respuestas contra los PDF. La evaluación humana final, sus conteos y su alcance metodológico se registran en [HUMAN_REVIEW_ATTESTATION_500_20260930.md](manual_validation/HUMAN_REVIEW_ATTESTATION_500_20260930.md) y [paired500_final_review.md](paired500_final_review.md); esas actualizaciones reemplazan las frases de este triage que indicaban que la revisión humana estaba pendiente.

## Estado del banco y alcance

Las 500 preguntas son el **banco previsto para la evaluación final**, según la decisión del autor. El nombre `candidates` y el manifiesto de la corrida indican que sus referencias aún no estaban validadas. Por ello, esta corrida sirve para encontrar fallos y orientar las correcciones, pero no se debe citar todavía como medición final de exactitud. Se conservaron intactas las respuestas, los índices y la hoja humana originales.

Se cotejaron las 500 respuestas automáticamente con la referencia candidata, el texto del índice y la fuente/página; las tablas de vacantes se cotejaron contra celdas detectadas, y se inspeccionaron visualmente páginas de los cuatro PDF y los fallos señalados. Una alerta de coincidencia con OCR no equivale a verificación humana de la respuesta. No se declara que las 500 respuestas hayan recibido una transcripción manual independiente línea por línea.

## Resultados de cotejo

| Grupo | Resultado de triage | Lectura correcta |
|---|---:|---|
| Cronograma | 25 consultas; el cotejo automático marcó una pregunta cuyo dato pedido no aparece en la respuesta | Las fechas principales de la tabla revisada se ven legibles; hace falta verificar la lista completa de respuestas una a una antes de calcular accuracy final. |
| Vacantes | 175 consultas; 142 respuestas terminan en el mismo número que la celda indicada y 33 no | Los 33 errores numéricos están listados abajo. El cotejo por fila/columna se verificó visualmente contra la tabla escaneada de la página 3; no son solo alertas de confianza OCR. |
| Temario | 145 consultas; cobertura literal de tokens de hechos esperados: 0.7692, diagnóstico automático | La métrica no prueba corrección semántica. Inspección visual y lectura de respuestas confirmaron respuestas incompletas y mezcla de fragmentos, ejemplos abajo. |
| Reglamento | 105 consultas; cinco no recuperaron la página de la fuente esperada (IDs 352, 353, 354, 359, 380) | Se verificó visualmente que los artículos 8 y 9 están en la página impresa 3; 10 y 15 en la impresa 4; y 38 en la impresa 10. Las cinco respuestas del modelo se abstuvieron: falló la recuperación, no la presencia de la regla en el PDF. |
| Fuera de dominio | 48/50 se abstuvieron; dos no | ID 469 deriva a contenido documental irrelevante tras iniciar una abstención. ID 482 especula sobre seminarios/prácticas después de decir que no encontró información. |

La auditoría de página clasifica 421 respuestas como “consistente con OCR; requiere confirmación visual”, 31 como “requiere revisión” y 48 como abstenciones OOD consistentes. La columna “consistente con OCR” no debe interpretarse como 421 respuestas verificadas.

## Errores numéricos confirmados en Vacantes

La imagen de la tabla distingue área, programa y columnas de Ordinario, CEPRUNSA, filiales y total general. Comparando la columna solicitada para el programa de cada pregunta con el valor final de la respuesta:

| IDs | Celdas pedidas: valor de la fuente → respuesta |
|---|---|
| 30, 33, 36, 41, 49 | Agronómica CEPRUNSA Fase II: 10→23; Agronómica total: 140→93; Biología Ordinario total: 60→299; Biología total: 83→206; Nutrición total: 83→111 |
| 60, 62, 65, 73, 74 | Enfermería Ordinario total: 37→2461; Enfermería CEPRUNSA Fase II: 12→22; Enfermería total: 74→2088; Medicina total: 67→71; Arquitectura Ordinario Fase I: 25→43 |
| 78, 81, 86, 88, 89 | Arquitectura CEPRUNSA Fase II: 18→30; Arquitectura total: 110→79; Física CEPRUNSA Fase II: 13→16; Física CEPRUNSA total: 35→24; Física total: 71→39 |
| 97, 100, 105, 121, 134 | Matemáticas total: 64→4; Química Ordinario total: 58→2482; Química total: 100→129; Geofísica total: 62→57; Civil CEPRUNSA Fase II: 12→23 |
| 137, 145, 153, 155, 158 | Civil total: 79→49; Sanitaria total: 29→38; Metalúrgica total: 70→5; Química Ordinario Fase II: 27→44; Química CEPRUNSA Fase II: 16→27 |
| 159, 161, 169, 177, 182 | Química Ciclo Quintos: 20→2; Química total: 104→78; Industrias Alimentarias total: 110→56; Materiales total: 70→94; Ambiental CEPRUNSA Fase II: 11→16 |
| 190, 193, 198 | Electrónica CEPRUNSA Fase II: 15→27; Electrónica total: 94→89; Industrial CEPRUNSA Fase II: 18→29 |

El baseline de OCR tampoco debe darse por bueno por defecto: esta tabla prueba que la combinación de recuperación/generación usada en esta corrida confunde fases, subtotales y carreras y, a veces, calcula mal los totales. Hay que hacer evaluación por separado de lectura de tabla, recuperación de celda y respuesta.

## Fallos de contenido observados en Temario y Reglamento

- **Temario ID 246, Análisis combinatorio:** omite “Factorial de un número” y mezcla “Análisis combinatorio intuitivo” de otro fragmento. La consulta cita una sección y la salida agrega contenido ajeno.
- **ID 321, Química orgánica:** devuelve solo átomo de carbono, hibridación, cadenas y reacciones; omite hidrocarburos, nomenclatura, isomería y compuestos orgánicos que aparecen en la página escaneada revisada.
- **ID 336, Clasificación y biodiversidad:** la salida omite los sistemas de clasificación biológica y deja incompleta la lista del Reino Animal.
- **IDs 352, 353, 354, 359 y 380:** las respuestas se abstienen porque la consulta no obtuvo la página pertinente, aunque los artículos solicitados sí son legibles en las páginas fuente revisadas. Esto es fallo de enrutamiento/recuperación y se debe corregir antes de congelar el benchmark.

Estos ejemplos no son una cuantificación completa de todos los errores de Temario/Reglamento. La base de referencia candidata también contiene OCR ruidoso, por lo que necesita normalización y revisión humana, no corrección ciega del modelo para que coincida con el texto extraído.

## Qué muestran los datos baseline frente a la arquitectura de tres fases

En los resultados históricos guardados para la comparación principal, el baseline V1 tuvo medias RAGAS de faithfulness **0.5640**, answer relevancy **0.6122**, context precision **0.3600** y context recall **0.7011**. V4 tuvo **0.5155**, **0.6578**, **0.2194** y **0.6841** respectivamente. V4 solo tuvo media mayor en answer relevancy; el baseline tuvo medias mayores en las otras tres. Las pruebas pareadas registradas no fueron significativas tras la corrección Holm. Por tanto, el artículo/datos disponibles no prueban que V4 sea superior en general.

En una reevaluación posterior de respuestas congeladas, las medias cambiaron: V1 **0.6288 / 0.6042 / 0.3728 / 0.6733**, V4 **0.6370 / 0.5227 / 0.2946 / 0.6367**. Tampoco hubo diferencia significativa. Que las medias cambien de dirección advierte que el resultado depende del juez/configuración/datos incompletos del histórico; no es evidencia de una mejora estable.

Hay explicaciones plausibles respaldadas por las pruebas, pero aún no aisladas causalmente:

1. El baseline recupera globalmente entre colecciones y no puede excluir el documento correcto mediante un error de router. El router de la arquitectura completa ya mostró recall muy bajo para Reglamento en el conjunto pequeño original; en esta corrida, cinco consultas reglamentarias tampoco recuperaron su página.
2. Las fases híbridas y el reranker agregan complejidad; la media inferior de context precision de V4 es compatible con que se estén añadiendo pasajes irrelevantes o desplazando evidencia útil. Se necesitan trazas por consulta para demostrar qué componente lo causa.
3. El caché semántico puede devolver respuestas incorrectas si el umbral permite falsos positivos: la auditoría previa detectó 9 respuestas correctas de 13 hits. Debe priorizar precisión sobre tasa de acierto y conservar fuente/cita verificable.
4. La generación desde tablas no está suficientemente restringida a la celda de la fila/columna solicitada: las 33 respuestas de vacantes que divergen del valor solicitado son evidencia directa de este cuello de botella.
5. La arquitectura completa tuvo mayor latencia en la medición previa (aprox. 24.1% sobre el baseline), y más pasos por consulta. Debe justificar esa complejidad con una mejora de calidad reproducible, que hoy no se ha demostrado.

## Qué mejorar antes de llamarlo evaluación final

1. Validar manualmente preguntas, respuesta de referencia, documento y página para todas las filas; corregir el OCR de referencia a partir del PDF y no a partir de la salida del modelo.
2. Rehacer la corrida con el código/configuración congelados que se quieran evaluar y las mismas 500 consultas; registrar hash de banco, índices, OCR, modelos, prompts, router, reranker, caché y parámetros.
3. Evitar que el router sea un bloqueo duro: permitir recuperación global de respaldo o segunda pasada cuando la evidencia obtenida no sustenta la pregunta.
4. Para tablas, conservar estructura con encabezados, filas y columnas; responder consultando la intersección exacta programa×modalidad×fase. Si se calcula total, sumar únicamente columnas componentes y validar contra el total publicado; si hay conflicto, citar celda/abstenerse.
5. Para Temario, recuperar bloques completos de sección y penalizar evidencia de páginas/secciones no solicitadas. Para Reglamento, revisar recall@k de páginas/artículos por categoría y consulta antes de tocar la generación.
6. Ajustar el caché para exigir similitud alta, intención/documento compatibles y verificación de evidencia; registrar hit/miss y falsos positivos.
7. Comparar baseline y cada ablación sobre el mismo benchmark corregido, índices/OCR/modelo generador/condiciones, y agregar intervalos pareados por pregunta. Reportar calidad y latencia/costo.

## Archivos de auditoría

- `evaluation/revision_20260930/answers_500_page_audit.csv`: triage por respuesta; no es una transcripción humana.
- `evaluation/revision_20260930/vacancies_cell_audit.csv`: cotejo por programa y celda numérica.
- `evaluation/revision_20260930/audit_500_answers_against_pages.py` y `audit_vacancies_answers.py`: scripts reproducibles.
- La corrida original, el manifiesto y la hoja humana no fueron sobrescritos.

## Actualización posterior: comparación final v9

La corrida pareada descrita en este archivo es histórica. Para el resultado final con índice Textract v9, corrección de referencias y auditoría que distingue chequeo automático de revisión humana, consulta [paired500_final_review.md](paired500_final_review.md). Los artefactos previos se conservan sin reemplazo.
