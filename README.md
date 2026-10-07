# Multi-RAG for University Admission Documents

A local, staged early-exit retrieval-augmented question answering system for university admission documents. It was built and evaluated on the official 2027 admission documents of the Pre-University Center of the Universidad Nacional de San Agustín de Arequipa (CEPRUNSA), and tested on the admission regulation of one other university.

It answers colloquial questions about regulations, schedules, vacancy tables, and syllabi, cites the source file and page, and abstains when the documents do not contain the answer. Generation and routing run locally with [Ollama](https://ollama.com/); OCR for scanned pages uses AWS Textract and is opt-in.

> **Paper.** *3-Phase Multi-RAG Architecture: Optimization of Routing and Information Retrieval in University Admissions Processes.* R. Chambi-Velasquez, A. Hilacondo-Begazo, A. Arroyo-Paz. Accepted at SIMBig 2026 (Springer CCIS). This repository contains the code, the question banks, the frozen configurations, and the run logs behind the paper.

## Contents

- [How it works](#how-it-works)
- [Results at a glance](#results-at-a-glance)
- [Scope and portability](#scope-and-portability)
- [Repository layout](#repository-layout)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Uploading documents and OCR](#uploading-documents-and-ocr)
- [API](#api)
- [Evaluation](#evaluation)
- [What is not in this repository](#what-is-not-in-this-repository)
- [Limitations](#limitations)
- [Security and privacy](#security-and-privacy)
- [Authors, citation, and license](#authors-citation-and-license)

## How it works

A query passes through up to four phases. Each phase either answers with the source file and page, or hands the query to the next, more expensive one (*early exit*, also called succeed-fast: the pipeline stops at the first phase that answers with sufficient confidence).

| Phase | What it does |
|---|---|
| **1. Verified semantic cache** | Up to three stored queries with cosine similarity ≥ 0.80 are shortlisted; a cross-encoder must accept the equivalence with probability ≥ 0.50. The cache is disabled in all evaluations. |
| **2. Intent router** | Regular expressions first, then a zero-shot LLM prompt, assign one of five categories: Schedule (`CRONOGRAMA`), Vacancies (`VACANTES`), Syllabus (`TEMARIO`), Regulations (`REGLAMENTO`), Out-of-domain (`FUERA_DE_DOMINIO`). An *evidence check* overrides an LLM out-of-domain verdict when hybrid retrieval finds a passage with cross-encoder probability ≥ 0.50. |
| **3a. Structured extraction** | Conservative resolvers answer only when exactly one row, cell, or section matches. The table resolver infers the entity column, chooses the table by header and row-name match, and picks the column by header-path matching (`ORDINARY / Total`). It answers cell, comparison, superlative, sum, group, and reverse-lookup questions; sums and differences are computed by code, not by the LLM. Also: schedule items, days between two schedule events, syllabus sections, and regulation articles. A verbalizer turns the extracted fact into one or two sentences and accepts the text only if every number in it comes from the fact, the source, or the query. |
| **3b. Hybrid retrieval and generation** | FAISS (HNSW) and BM25 each return 10 fragments, Reciprocal Rank Fusion merges them, and a multilingual cross-encoder reranks the candidates. The generator is restricted to the context and must use a fixed abstention sentence when the context is insufficient. |

Offline, each PDF page is inspected: the native text layer is used when it is reliable, ruled tables of born-digital files are extracted with `pdfplumber`, and only pages without a usable text layer go to OCR. Text is split into 200-word segments with 20 words of overlap, and every table row is also stored as one segment that keeps its column headers as `header: value` pairs.

### System versions

The paper compares several versions. They differ in what they add:

| Version | Description | Evaluated on |
|---|---|---|
| `V1` | Dense retrieval over all categories (top-5), terse prompt (baseline) | all banks |
| `V1c` | `V1` with the contextual answer style (separates style from architecture) | Test-2 |
| `V6` | Hybrid retrieval + reranking, no router | Dev, Test-1 |
| `V4` | First complete system: cache, router, hybrid retrieval, reranking | Experiments A and B, Dev, Test-1 |
| `V4b` | `V4` + evidence check, header-path resolver, resolvers tried in all categories, revised prompt | Dev, Test-1 |
| `V4d` | Final: `V4b` + aggregate and schedule-days resolvers, verbalizer, contextual style, top-8 retrieval with same-page neighbours | Dev, Test-2 |

The application code in `app/` is the final version (`V4d`). Earlier versions are preserved as frozen snapshots under `evaluation/heldout/` (see [Evaluation](#evaluation)).

## Results at a glance

All numbers come from the logs in `evaluation/`. Gold-key accuracy is deterministic (regular expressions written from the source PDFs, no LLM judge). Intervals are 95% bootstrap CIs; differences use the exact McNemar test.

| Evaluation | n | Result |
|---|---|---|
| **Test-1** (sealed, run once) | 138 | `V4b` 113 correct (81.9%) vs. `V1` 105 (76.1%): **+5.8 points**, 95% CI −0.7 to +12.3, McNemar p = 0.13 (not significant). Significantly better than `V4` (+7.2 points, p = 0.002). The advantage concentrates in vacancy-table questions (39 vs. 29 of 47). |
| **Test-2** (sealed, run once, different generator) | 60 | `V4d` 47 correct (78.3%) = `V1` 47; `V1c` 45. Table lookups 19/19 vs. 16/19 and aggregates 5/6 vs. 2/6, but worse on long syllabus lists. About twice the latency. |
| Ablation of `V4d` on Test-2 (one component removed at a time) | 60 | Without structured extraction 42 correct; without the evidence check 44; without the verbalizer 44; terse style 46; top-5 without neighbours 47; complete 47. No difference is significant. The structured-extraction and evidence-check losses have a clear cause (three table questions the generator cannot add; three valid questions rejected as out-of-domain); the others are within run-to-run noise, because generation at temperature 0.1 is not deterministic. |
| RAGAS on Test-2 (Gemini judge) | 44 | Faithfulness 0.572 (`V4d`) vs. 0.673 (`V1`) vs. 0.549 (`V1c`): the contextual style lowers faithfulness without changing accuracy. |
| Second institution (born-digital, no OCR) | 63 | 85.7%–90.5% across four retrieval pipelines; no significant differences. |
| Experiment A (30 queries, RAGAS) | 30 | Answer relevancy 0.6578 vs. 0.6122, not significant; router accuracy 76.7%; verified cache 43.3% hit rate at 69.2% accuracy. |

We read the overall accuracy advantage as a **trend, not an established improvement**. The reliable gain is on table questions. Details, limitations, and the exact protocol are in the paper and below.

## Scope and portability

The design is not tied to one institution. The resolvers contain no institution-specific strings; the table resolver infers the entity column and the header path from the serialized tables; and the workspace pipeline lets you upload your own PDFs. A born-digital regulation of another university was ingested without OCR and answered with 85.7%-90.5% accuracy on 63 questions.

What is specific to admissions: the five routing categories (schedule, vacancies, syllabus, regulations, out-of-domain) with their rules and prompt, and the evaluation questions. Using the system for another domain would need new categories and prompts, and we have not tested that. Two institutions is also a small sample, and the table resolver assumes tables serialized as `header: value` rows. For historical reasons, configuration variables and some module names keep the `CEPRUNSA_` prefix.

## Repository layout

```
app/                      FastAPI backend: pipeline, router, resolvers, retrieval, workspaces
  pipeline.py             early-exit orchestration (cache → router → 3a → 3b)
  router.py               rules + zero-shot routing
  structured_answers.py   table, schedule, section, and article resolvers
  verbalizer.py           validated rewriting of extracted facts
  retriever.py            FAISS + BM25 + RRF + cross-encoder reranking
  llm.py                  generator (Ollama by default)
  workspace_manager.py    isolated document workspaces (upload, extract, index, query)
  pdf_text.py, ocr_engine.py, textract_engine.py   text layer, OCR, AWS Textract
  ingest.py               builds the reference index from data/pdfs
fronted/fronted/          React + Vite + Tailwind interface (the directory name is historical)
data/pdfs/                the four official CEPRUNSA 2027 documents
data/index/               versioned baseline index (see "What is not in this repository")
evaluation/               experiments, question banks, run logs, and results
  heldout/                development and sealed banks, frozen code snapshots, scorers, run logs
  evidence/               supplementary evidence: 500-question bank, OCR comparison, latency, reviews
  real_users/             protocol and scripts for validating questions with real applicants
```

## Getting started

Developed and tested on Windows 11 with Python 3.13 and Node.js. The commands below use PowerShell.

**Requirements**

- Python 3.13 and Node.js / npm.
- [Poppler](https://poppler.freedesktop.org/) (`pdftotext`) on `PATH`, or set `CEPRUNSA_PDFTOTEXT_BIN`.
- [Ollama](https://ollama.com/) with the model named in `.env` (default `llama3:8b`; the final evaluation used `qwen2.5:7b`). Without a GPU, generation on CPU takes tens of seconds per answer.

**Backend**

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
if (!(Test-Path venv)) { py -m venv venv }
venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull llama3:8b
Set-Location app
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Frontend** (second terminal)

```powershell
Set-Location fronted/fronted
npm install
npm run dev -- --host 127.0.0.1
```

The interface is at `http://127.0.0.1:5173/`, the API at `http://127.0.0.1:8000/`, and its interactive documentation at `http://127.0.0.1:8000/docs`.

The `.env.example` points to the versioned index `data/index`. To use another local index, set `CEPRUNSA_INDEX_DIR`.

**Local checks**

```powershell
venv\Scripts\python.exe -m compileall -q app
Set-Location fronted/fronted
npm run lint
npm run build
```

## Configuration

Settings are read from `.env` (copy `.env.example`). The main ones:

| Variable | Default | Purpose |
|---|---|---|
| `CEPRUNSA_GENERATOR_PROVIDER` / `_MODEL` / `_TEMPERATURE` | `ollama` / `llama3:8b` / `0.1` | Generator |
| `CEPRUNSA_ROUTER_PROVIDER` / `_MODEL` | `ollama` / `llama3:8b` | Zero-shot router |
| `CEPRUNSA_INDEX_DIR` | `data/index` | Index of the reference corpus |
| `CEPRUNSA_CACHE_MODE` | `semantic` | Cache behaviour |
| `CEPRUNSA_OCR_ENGINE` | `textract` | OCR backend for pages without a usable text layer |
| `CEPRUNSA_ENABLE_PAID_TEXTRACT` | `0` | Must be `1` for Textract to run (second safeguard, see below) |
| `CEPRUNSA_TEXTRACT_REGION` | `us-east-1` | AWS region |
| `CEPRUNSA_AWS_PROFILE` | empty | Named AWS profile to use (optional) |
| `CEPRUNSA_WORKSPACES_DIR` | `data/workspaces` | Where uploaded documents live |
| `CEPRUNSA_MAX_PDF_BYTES` / `_PAGES` | 50 MB / 500 | Upload limits |
| `GOOGLE_API_KEY`, `CEPRUNSA_GEMINI_JUDGE_MODEL` | empty / `gemini-3.1-flash-lite` | RAGAS judge (evaluation only) |

Never commit `.env`, API keys, or AWS credentials. `.env` is git-ignored.

## Uploading documents and OCR

Besides the reference corpus, the interface lets you upload PDFs into isolated *workspaces* under `data/workspaces/<id>/`. Queries and statistics use only the selected workspace. The application asks you to confirm that the document belongs to the declared context; it does not verify the institution by itself.

For each page, the application first reads the native text layer with Poppler. Pages without usable text go to OCR, and **the OCR engine is AWS Textract**, which also detects tables so that each table row can be indexed with its column headers for the structured-extraction phase. In the paper, EasyOCR was used only in the first experiment (Experiment A); the later experiments use Textract. The extraction code does not call Tesseract.

Textract is a paid cloud service that receives the pages sent to it. It runs only when (1) you accept the upload of that document in the interface and (2) the server has `CEPRUNSA_ENABLE_PAID_TEXTRACT=1`. To install the optional SDK:

```powershell
venv\Scripts\python.exe -m pip install -r requirements-aws.txt
```

Configure the region and credentials with the standard AWS profile or credential chain. On the paper's development sample of 79 numeric cells, Textract matched exactly 93.67% of the cells against 18.99% for EasyOCR; this is a small sample and does not generalize to every document. Complex tables, low resolution, or unusual layouts still need review.

### Setting up AWS Textract, step by step

You only need this if you want to OCR scanned PDFs (including rebuilding the evaluation index). Born-digital PDFs with a text layer never go to Textract.

1. **Create an AWS account.** Go to <https://aws.amazon.com/> and choose *Create an AWS account*. You need an email address, a password, contact details, a payment card, and a phone number for verification. Textract is a paid service: check the current prices and any free tier for new accounts at <https://aws.amazon.com/textract/pricing/>. The application calls `AnalyzeDocument` with the *Tables* feature, which is priced per page.
2. **Protect the account and set a spending alert.** Enable multi-factor authentication on the root user. In the console open *Billing and Cost Management → Budgets* and create a cost budget with an email alert, so that an unexpected run does not surprise you.
3. **Create an IAM user for the project (do not use the root user).** In *IAM → Users → Create user*, attach the managed policy `AmazonTextractFullAccess`, or a least-privilege custom policy:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{ "Effect": "Allow", "Action": "textract:AnalyzeDocument", "Resource": "*" }]
   }
   ```

4. **Get credentials on your machine.** Install the [AWS CLI v2](https://aws.amazon.com/cli/) and choose one option:
   - *Access keys:* in the IAM user open *Security credentials → Create access key → Command Line Interface*, then run `aws configure --profile ceprunsa` and enter the access key ID, the secret key, the region (for example `us-east-1`), and the output format (`json`). Keep the keys secret and never commit them.
   - *Browser sign-in (short-lived credentials):* run `aws login --profile ceprunsa` if your AWS CLI version supports it.

   Check that it works: `aws sts get-caller-identity --profile ceprunsa`.
5. **Install the optional SDK:** `venv\Scripts\python.exe -m pip install -r requirements-aws.txt`.
6. **Enable Textract in `.env`** (this is the server-side safeguard, off by default):

   ```ini
   CEPRUNSA_OCR_ENGINE=textract
   CEPRUNSA_ENABLE_PAID_TEXTRACT=1
   CEPRUNSA_TEXTRACT_REGION=us-east-1
   CEPRUNSA_AWS_PROFILE=ceprunsa
   ```

   Restart the backend after changing `.env`.
7. **Use it.** In the interface, create a workspace, upload a scanned PDF, and accept the Textract confirmation for that document. Only the pages whose text layer fails the reliability check are sent to AWS; the rest are read locally.
8. **When you are done,** deactivate or delete the access keys you do not need and review the *Billing* page.

`CEPRUNSA_OCR_ENGINE=easyocr` is still accepted by the code if you install `easyocr` and `torch` yourself, but it is not what the paper's evaluation used (except in Experiment A).

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/query` | Answer a question (optionally within a workspace) |
| `GET` | `/stats` | Session statistics |
| `GET`, `POST` | `/workspaces` | List or create workspaces |
| `GET`, `POST` | `/workspaces/{id}/documents` | List or upload documents |
| `POST` | `/workspaces/{id}/documents/{doc_id}/process` | Extract and index a document |
| `GET` | `/health` | Health check |

## Evaluation

### Question banks

The paper's names and the directories in this repository differ; use this map:

| In the paper | Questions | Where |
|---|---|---|
| Experiment A | 30 | `evaluation/queries.json`, `evaluation/ragas_*.csv`, `evaluation/resultados_*.txt` |
| Experiment B (development) | 500 | `evaluation/evidence/` |
| **Dev** | 89 | `evaluation/heldout/heldout_bank.json` |
| **Test-1** (sealed) | 138 | `evaluation/heldout/test2/` |
| **Test-2** (sealed) | 60 (+15 abstention probes) | `evaluation/heldout/test3/` |
| **UNT** (other university, no OCR) | 63 | `evaluation/heldout/unt/` |

Provenance: we wrote every question (drafted with LLM assistance in the style of applicant questions) and verified each gold answer against the source PDF. None is a logged query of real applicants. `evaluation/real_users/` contains a protocol and scripts to collect and score such questions. Test-1 and Test-2 were sealed with a SHA-256 hash (`SEAL.json`) before the version of the system that they evaluate was designed.

### Protocol

- Each system is developed only on the Dev bank.
- Before a sealed run, code and index hashes are recorded in a freeze file (`evaluation/heldout/FREEZE*.json`); the runner refuses to start if the code differs.
- Every system runs once per sealed bank, with the same generator, index, and temperature, and no cache.
- Scoring is deterministic: each question has a gold answer and `must` regular expressions; a lookup answer that lists more than five distinct numbers counts as wrong; unanswerable and out-of-domain questions are correct only if the system abstains.
- Test-1 is no longer a clean test for `V4d`, because its failure categories were known when the aggregate resolvers were designed. Test-2 was created for that reason.
- Frozen code snapshots are in `evaluation/heldout/app_v4_frozen/` and `app_v4c_snapshot/`.

### Reproducing a run

Scorers write Markdown tables to `evaluation/heldout/results/`:

```powershell
# score the sealed 60-question bank for three systems
venv\Scripts\python.exe evaluation\heldout\score_generic.py `
  --bank evaluation\heldout\test3\test3_bank.json --tag test3 `
  --run V1=evaluation\heldout\test3\runs\V1.jsonl `
  --run V1c=evaluation\heldout\test3\runs\V1c.jsonl `
  --run V4d=evaluation\heldout\test3\runs\V4d.jsonl `
  --compare V4d:V1 --compare V4d:V1c
```

To generate answers again, see `evaluation/heldout/run_v4d.py` (the final system) and `run_baselines_bank.py`; `evaluation/heldout/test3/run_final.sh` is the exact chain used for the final run. RAGAS with a Gemini judge is in `evaluation/heldout/ragas_test3/` (with a hard spending cap; the measured spend was S/ 2.42 of S/ 2.55 and covered 44 of the 60 questions). RAGAS and Textract can incur charges: run them only on purpose.

Temperature 0 does not guarantee identical scores on repeated runs of a hosted LLM judge, and each answer set was scored once; treat RAGAS differences as trends.

## What is not in this repository

- **The 85-page Textract index used in the sealed runs** (`data/index_textract_85_v9`) and the raw Textract page JSON are local and git-ignored. The versioned `data/index/` is a baseline index built before table-aware extraction, so results will not reproduce exactly with it. To rebuild an evaluation index you need to run Textract over `data/pdfs/` (a paid step, see [Setting up AWS Textract](#setting-up-aws-textract-step-by-step)). In outline:
  1. With Textract enabled, call `ocr_pdf` from `app/ingest.py` on each PDF with `allow_paid_textract=True` and an `audit_dir`; it writes one `page_NNN.json` per page under `<audit_dir>/<PDF name>/`.
  2. Point the `DOCUMENTS` constants at the top of `evaluation/build_index_from_textract.py` to those folders (they currently refer to local folders under `evaluation/revision_20260929/`), then run it with `--output-dir data/index_textract_85_v9` (or another name). It builds header-aware row passages and the FAISS and BM25 data without further AWS calls.
  3. Compare the SHA-256 of the resulting index files with those in the freeze files (`evaluation/heldout/FREEZE*.json`). Textract output can change between runs and the index was built iteratively (versions v1 to v9), so a rebuilt index may differ slightly from ours; if the hashes differ, treat your numbers as a new run and not as an exact reproduction. We have not re-run this exact recipe from a clean checkout.
- Local caches, uploaded workspaces, temporary audits (`tmp/`), archived historical runs (`evaluation/archive/`), and `.env`.

## Limitations

- All question banks were written by the authors. There is no second annotator and no log of real applicants, and the 60-question bank gives intervals of about ±13 points.
- Test-1 and Test-2 use different system versions and generators, so they are not pooled.
- The overall accuracy advantage over a dense baseline is not statistically significant. Individual changes were not ablated one by one.
- One CEPRUNSA corpus (two versions) and one other university; the table resolver needs tables serialized as `header: value` rows (Textract, native, or ruled-table extraction).
- Latencies were measured on a CPU; the final configuration is about twice as slow as the dense baseline.
- Textract-based extraction and accuracy on documents of other institutions require validation on those documents.

## Security and privacy

- Keep secrets in `.env` or the process environment only. The repository contains no API keys.
- Textract sends the pages that need OCR to AWS; uploading is gated by a per-document confirmation and a server flag.
- Runtime latency audits are stored under `tmp/latency_audit/<id>/`, do not store question or answer text, and are kept for seven days by default.

## Authors, citation, and license

Rommel Chambi-Velasquez, Andre Hilacondo-Begazo, Antonio Arroyo-Paz. Universidad Nacional de San Agustín de Arequipa, Arequipa, Peru.

If you use this work, please cite the paper (SIMBig 2026, Springer CCIS; reference to be updated when the volume is published).

The code, the question banks, and the evaluation scripts are released under the [MIT License](LICENSE). The paper itself is published by Springer under its own terms. The four CEPRUNSA documents in `data/pdfs/` are official public documents of CEPRUNSA and are not covered by this license: they remain under their publisher's terms.
