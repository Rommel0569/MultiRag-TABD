# Verificación de las 500 respuestas contra los PDF

El CSV contiene la referencia y los veredictos de baseline y tres fases para cada ID, además de la fuente, página, evidencia y rationale.

**Actualización 2026-09-30:** el autor confirmó que revisó manualmente las 500 consultas, las referencias y las respuestas de ambas arquitecturas contra los PDF originales. Para este registro, los veredictos resumidos abajo se consideran revisión humana final del autor; la adjudicación asistida por `llama3:8b` fue apoyo de triage, no sustituto de esa revisión. Es una evaluación de un solo revisor, no doble ciega ni independiente. La confirmación se conserva en `HUMAN_REVIEW_ATTESTATION_500_20260930.md`.

| Categoría | n | Referencias apoyadas | Referencias corregidas | Baseline correcto | Baseline parcial | Baseline incorrecto | 3 fases correcto | 3 fases parcial | 3 fases incorrecto | Abstención correcta 3 fases |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CRONOGRAMA | 25 | 25 | 0 | 22 | 3 | 0 | 18 | 7 | 0 | 0 |
| VACANTES | 175 | 175 | 0 | 148 | 0 | 27 | 175 | 0 | 0 | 0 |
| TEMARIO | 145 | 4 | 141 | 140 | 2 | 3 | 143 | 1 | 1 | 0 |
| REGLAMENTO | 105 | 3 | 102 | 26 | 1 | 78 | 102 | 1 | 2 | 0 |
| FUERA_DE_DOMINIO | 50 | 50 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 50 |

## Comparación pareada de exactitud humana

Para la exactitud dentro del dominio, solo `correct` cuenta como acierto completo; `partially_correct` no se cuenta como exacto. De 450 pares, 332 fueron correctos en ambas arquitecturas, 8 no fueron completamente correctos en ninguna, 106 fueron correctos solo en tres fases y 4 solo en el baseline. La exactitud fue 438/450 (97.33%) frente a 336/450 (74.67%), diferencia de +22.67 puntos porcentuales. La prueba exacta bilateral de McNemar da `p = 9.2369e-27` para estos veredictos en este banco.

En las 50 consultas fuera de dominio, hubo 3 casos con abstención correcta solo en tres fases y ninguno solo en el baseline (`p = 0.25` bilateral exacta); se reportan aparte y no se mezclan con exactitud factual dentro del dominio. La prueba de exactitud es condicional a las etiquetas de un único revisor no ciego, por lo que no elimina el posible sesgo de adjudicación ni demuestra generalización a consultas nuevas.

Reproducción: `python evaluation/revision_20260930/manual_validation/analyze_human_500_exactness.py`.

## Casos especiales

- Las 175 celdas de Vacantes se verificaron como valor de celda frente a la tabla renderizada; las 25 fechas se verificaron contra las páginas 2–3 de Cronograma.
- Las 50 consultas FUERA_DE_DOMINIO se evaluaron por abstención; sus referencias no son datos factuales extraídos de los PDF.
- El Reglamento tiene desplazamiento entre página física y página impresa. En la hoja se conserva la página física reproducible del PDF.
- IDs 249, 253, 329, 363, 369, 386, 395, 416 y 429 se cotejaron visualmente porque el juez OCR marcó la referencia como incierta. Se confirmó la referencia y se rectificó el veredicto contra la pregunta real de cada ID.
- Una primera hoja de anulaciones manuales se marcó como supersedida al detectar una asociación incorrecta entre un ID y su consulta; se conserva por trazabilidad y no se usa para RAGAS. La versión `source_adjudication_500_final.jsonl` se rehízo por ID explícito.

CSV: `source_validation_500_completed.csv`. Resumen JSON: `source_validation_500_verdict_summary.json`. La revisión humana global se basa en la confirmación expresa del autor; el CSV conserva los métodos de triage originales y no incluye iniciales por fila.
