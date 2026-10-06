# Optional AWS Textract comparison

The application first checks for usable PDF text locally. Its default OCR
backend (`auto`) is local EasyOCR; Textract remains opt-in for pages that need
OCR. The adapter requests `AnalyzeDocument` with `TABLES` and writes the same
auditable JSON shape (prose detections, table rows, cells, confidence, and
source-page geometry). Textract is not assumed to be more accurate: the
four-page manually transcribed sample is the only current accuracy reference.

## Current status (2026-09-29)

- The adapter, explicit billing/transmission guards, optional dependency
  manifest, and run instructions are implemented.
- AWS's Free account plan first rejected Textract with
  `SubscriptionRequiredException`; no page result was produced in that attempt.
  The user then upgraded the account. A read-only plan check reported `PAID`,
  `ACTIVE` (2026-09-29, profile `ceprunsa`), after which the user authorized
  the four-page experiment. AWS's plan distinction and billing behavior are
  documented in [AWS account plan choices](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).
- The authorized run completed for all four pages in
  `evaluation/revision_20260929/textract_v3/`. The synchronous
  `AnalyzeDocument(TABLES)` request returned prose on pages 1–2 and one table
  each on pages 3–4 (924 and 975 cell blocks). It did not identify tables on
  pages 1–2, which appear to be narrative pages. `comparison.json` preserves
  the item-level comparison against the visually transcribed development
  sample and saved EasyOCR baseline.
- On the fixed sample of 79 numeric cells, exact match is 93.67% (74/79),
  compared with 18.99% (15/79) for the previous EasyOCR audit. On four short
  visually transcribed development prose regions, CER is 0.00%, compared with 1.21% for
  that baseline. The five sampled numeric mismatches are: page 3, Ingeniería
  de Sistemas total (`EL` for expected `73`); page 3, Contabilidad two sampled
  cells (`20`/`0` in the opposite positions from the sampled reference); and
  page 4, Medicina two sampled cells left blank though the reference is `1`.
  These are meaningful gains on this sample, not 100% accuracy or evidence of
  generalization to other document types. The gold sample itself is marked as
  a development sample requiring a second human review and a held-out sample.
- A local-only Poppler `pdftotext` probe was run on all four source PDFs before
  full OCR. It classified all 85 pages as requiring OCR because none had a
  usable native text layer; the final Cronograma page is visually blank and
  contains only scan noise/seals. The probe is heuristic and its report is
  `evaluation/revision_20260929/LOCAL_PDF_TEXT_PROBE.json`.
- Following the user's request to finish reading all documents, Textract
  processed all 85 pages: Vacantes 4, Cronograma 4, Reglamento 32, Temario 45.
  The per-page outputs are retained in `textract_v3/` and
  `textract_full/`; `textract_full/FULL_RUN_SUMMARY.json` validates page files
  and `OCR_ALL_DOCUMENTS.txt` concatenates the recognized text. Consolidation
  found 59 detected tables, 3,726 cell blocks, 165,879 text characters, and
  one empty page (Cronograma page 4, visually blank in the source). This
  verifies extraction coverage, not word/cell accuracy for every page.
- The gross list-price estimate for 85 pages with TABLES in `us-east-1` is
  approximately US$1.275 before credits or offers. AWS's pricing page lists a
  short-term offer of up to 100 pages/month for Tables for new customers, but
  the Free Tier usage query returned no Textract record; actual eligibility,
  credit use, and billed amount are not confirmed. Check Billing after its
  usage data refreshes. [Official Textract pricing](https://aws.amazon.com/textract/pricing/).
- The 79 numeric and four prose samples belong only to Vacantes page 3–4 and
  pages 1–2. No hand-transcribed gold exists for the other 81 pages. Do not
  extrapolate the 93.67% cell match or 0% sample CER to the complete corpus.
- During the user's clarification about local PDF inspection, the four-page
  Cronograma run had already completed. The remaining 77 pages were sent only
  after the user reiterated the instruction to finish reading all documents.
  A partial `cronograma/` directory and the earlier `cronograma_v2/` run
  artifacts are preserved; use `cronograma_v2/` for the complete results.
- The latest local EasyOCR run (`ocr_v3`) compared 79 visually transcribed
  numeric samples: exact cell match improved from 18.99% in the saved prior
  audit to 63.29%; sampled prose CER rose from 1.21% to 2.60%. This is mixed
  evidence, not a validated general accuracy gain, and motivates comparing a
  table-structured service such as Textract rather than assuming it is better.
- Both the EasyOCR v3 and Textract v3 comparison artifacts were checked against
  the same `gold_sample.json` using the same exact-cell/CER implementation.
  Their `new` metrics are 63.29% (50/79) and 2.60% CER for EasyOCR v3, versus
  93.67% (74/79) and 0.00% CER for Textract v3. The Textract result is preserved
  in `textract_v3/comparison_vs_easyocr_audit.json`; EasyOCR's is in
  `ocr_v3/comparison.json`. This is still one development sample awaiting
  independent human verification, not a corpus-wide accuracy estimate.
- A draft paragraph describing Textract as a separate post-review experiment
  is in `MANUSCRIPT_REVISION_DRAFT.md`. The original article results are not
  replaced, and the 500-query end-to-end run changes other pipeline components
  too, so it does not isolate OCR's effect on RAG.
- These are OCR-region metrics; they do not establish retrieval/RAG improvement.

## Guardrails

- The default `requirements.txt` and application configuration do not use AWS.
- Install optional SDK dependencies with `venv\\Scripts\\python.exe -m pip install -r requirements-aws.txt`.
- The audit command requires `--allow-paid-textract`; no cloud request is made
  by importing the adapter or running the default EasyOCR command.
- The application ingest also requires `CEPRUNSA_ENABLE_PAID_TEXTRACT=1` and
  `CEPRUNSA_OCR_ENGINE=textract` before it can send pages to AWS.
- AWS credentials and region use boto3's standard credential chain and the
  configured `CEPRUNSA_TEXTRACT_REGION`/AWS region. A named local profile may
  be supplied with `--profile` or `CEPRUNSA_AWS_PROFILE`. Credentials must never
  be committed to the repository or printed in logs.
- Textract calls transmit page images and may incur usage charges. The user's
  requested 85-page corpus run is complete. Do not send more pages without
  fresh authorization. Credentials and account identifiers are not stored in
  the run manifest.

## Reproduce an audit run (requires current AWS access and user authorization)

```powershell
.
venv\Scripts\python.exe -m pip install -r requirements-aws.txt
$env:CEPRUNSA_TEXTRACT_REGION = 'us-east-1'
$env:AWS_DEFAULT_REGION = 'us-east-1'
venv\Scripts\python.exe evaluation\audit_ocr.py `
  --pdf 'data\pdfs\CUADRO DE VACANTES 2027.pdf' `
  --output 'evaluation\revision_YYYYMMDD\textract_run' `
  --engine textract --region $env:CEPRUNSA_TEXTRACT_REGION `
  --profile 'ceprunsa' `
  --allow-paid-textract
venv\Scripts\python.exe evaluation\compare_ocr.py `
  --run 'evaluation\revision_YYYYMMDD\textract_run' `
  --gold 'evaluation\revision_20260929\gold_sample.json' `
  --previous 'data\ocr_audit\CUADRO DE VACANTES 2027.pdf'
```

Use a new output directory for every run. The command compares Textract's
output to the fixed visual reference and the previously audited extraction.
It does not overwrite the original index or promote Textract to the production
default. Treat the current metrics as development-sample results; a held-out
sample and broader document validation are needed before claiming general OCR
accuracy or changing manuscript results.

Official references: [AnalyzeDocument API](https://docs.aws.amazon.com/textract/latest/APIReference/API_AnalyzeDocument.html),
[table block model](https://docs.aws.amazon.com/textract/latest/dg/how-it-works-tables.html),
and [Textract pricing](https://aws.amazon.com/textract/pricing/).
