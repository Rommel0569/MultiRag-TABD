# Selected evidence

This package gathers evidence for understanding and reviewing the system. It does not turn supplementary results into results of the paper. The paper's main evaluations (held-out banks) are in [`../heldout/`](../README.md).

## System and integration

- `system/SYSTEM_E2E_AUDIT_20261001.md`: interfaces tested, PDF upload, context separation, and a local query. Includes limitations and commands.
- The synthetic sample verified native text extraction and table rows. The Textract parser was tested with synthetic blocks during that check; that test is not a real validation of the AWS service.

## OCR extraction

- `ocr/TEXTRACT_EXPERIMENT.md`: configuration, scope, and Textract/EasyOCR comparison.
- `ocr/gold_sample.json`, `ocr/textract_comparison.json`, `ocr/easyocr_comparison.json`, and `ocr/comparison_vs_easyocr_audit.json`: reference transcription and results of the four-page sample.
- `ocr/textract_manifest.json` and `ocr/easyocr_manifest.json`: configuration of those runs.
- `ocr/LOCAL_PDF_TEXT_PROBE.json`: text-layer diagnosis of the corpus.

On the development sample, Textract matched exactly 74 of 79 numeric cells (93.67%) against 18.99% for EasyOCR. The sample is limited to pages of the vacancy table; it does not estimate accuracy over all pages or over documents of other universities.

## Answer review and the 500-question bank

- `source_data/source_validation_500_completed.csv` and `source_validation_500_verdict_summary.*`: validation log of questions, references, and answers against the PDFs.
- `review/HUMAN_REVIEW_ATTESTATION_500_20260930.md`: scope of the manual review as confirmed by the author. It was done by one author; there was no second annotator, blinding, or inter-annotator agreement.
- `answer_runs/baseline_v9/` and `answer_runs/three_phase_final_v3/`: answers and manifests of the runs linked to the human log.
- `review/paired500_final_v3_comparison.*`: paired comparison for those runs.

This bank and its runs are development material (Experiment B in the paper), not a test of generalization: the router rules and extractors were written while inspecting it.

## Four-variant RAGAS run

- `ragas_500/run/`: manifest, final table, per-row scores, and reported usage for the four variants.
- `ragas_500/inputs/`: archived inputs and references, so that the manifest hashes can be verified.

The manifest identifies `gemini-3.1-flash-lite` as the judge, temperature 0, RAGAS 0.2.14, and local `intfloat/multilingual-e5-base` embeddings. It records 2,000 complete rows. It also records a cost estimate of S/ 23.39 from token usage, above the configured threshold of S/ 18.50; it must not be described as a run under that threshold.

## Latency

- `latency/500_query_audit/`: analysis and latency rows of saved runs.
- `answer_runs/three_phase_final_latency/`: the three-phase run linked to the latency analysis.

The analysis can be recomputed without model calls:

```powershell
venv\Scripts\python.exe evaluation\evidence\latency\500_query_audit\analyze_latency_runs.py
```

The analysis found hash differences in `pipeline.py` and `structured_answers.py` between the baseline and three-phase runs, and zero generation tokens in the 500 three-phase answers. It therefore describes those implementations and outputs; it does not isolate the causal effect of the router, and it does not by itself represent the latency of a later version.

The instrumentation that runs inside the application keeps a separate temporary log under `tmp/latency_audit/`, ignored by Git, with configurable retention.

## Reviewers

- `review/RESPUESTA_REVISORES_Y_CAMBIOS_MANUSCRITO_FINAL.md`: map of comments and proposed responses/changes (in Spanish).
- `review/REVIEW_STATUS_20260930.md`, `review/paired500_final_review.md`, and `review/VERIFICACION_500_RESPUESTAS_Y_COMPARACION_RAG.md`: complementary status and analysis (in Spanish).
- `review/ARCHITECTURE_REVIEW_3_PHASES.md`: architecture findings linked to the review.

These files document analyses and draft responses from an earlier revision round; the final paper and the final response letter may differ from them.
