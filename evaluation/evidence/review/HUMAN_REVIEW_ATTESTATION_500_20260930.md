# Registro de revisión humana del banco de 500

- **Fecha del registro:** 2026-09-30.
- **Revisor:** autor del estudio, según confirmación expresa del autor en la conversación de trabajo.
- **Alcance confirmado:** revisión manual de las 500 consultas, sus referencias y las respuestas de baseline y de tres fases contra los PDF originales.
- **Uso de IA:** `llama3:8b` participó en el triage/adjudicación inicial que quedó registrado en los campos originales del CSV. El autor confirma haber revisado manualmente el conjunto completo; la salida del juez no se trata como validación humana.
- **Resultados consignados:** 257 referencias confirmadas y 243 corregidas; baseline: 336 correctas, 6 parciales y 111 incorrectas (incluye OOD); tres fases: 438 correctas, 9 parciales y 3 incorrectas, más 50 abstenciones correctas OOD.
- **Comparación pareada dentro del dominio:** contando solo `correct` como exacta, tres fases obtuvo 438/450 y baseline 336/450; 106 respuestas fueron correctas solo en tres fases y 4 solo en baseline. McNemar exacta bilateral: `p = 9.2369e-27`. En OOD, 50/50 frente a 47/50 abstenciones correctas; `p = 0.25`, informado aparte.
- **Alcance metodológico:** revisión de un autor. No hubo segundo evaluador, cegamiento ni medición de concordancia entre anotadores. La revisión corresponde al banco/corridas documentadas en `source_validation_500_completed.csv`; no convierte otras corridas o datos históricos en validación humana.
- **Trazabilidad:** se conserva el CSV original con sus campos de método y rationale. Este registro añade la confirmación humana global sin sobrescribir el método de triage ni inventar iniciales por fila.
- **Vinculación con las corridas:** una comprobación de los archivos confirmó que las 500 respuestas baseline y las 500 respuestas de tres fases del CSV coinciden exactamente, por ID y texto, con las respuestas de `paired500_20260930_baseline_v9` y `paired500_20260930_three_phase_final_v3`.
- **Análisis reproducible:** `analyze_human_500_exactness.py` recalcula conteos y pruebas pareadas desde el CSV sin modificarlo.

Este registro documenta la confirmación del autor; no afirma una evaluación independiente por terceros.
