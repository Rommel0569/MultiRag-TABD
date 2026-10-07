# Evaluation and evidence

This folder holds everything behind the paper's results: the original 30-query benchmark, the held-out question banks, the frozen code snapshots, the run logs, and the scoring scripts. The main [README](../README.md) summarizes the results; this file explains where each evaluation lives and how to reproduce a run.

## Map: paper names to folders

| In the paper | Questions | Where |
|---|---|---|
| **Experiment A** | 30 | `queries.json`, `ragas_V1_baseline.csv` to `ragas_V4_completo.csv`, `ragas_por_consulta.csv`, `resultados_*.txt`, `ablacion_V*.json` (this folder's root) |
| **Experiment B** (development bank) | 500 | [`evidence/`](evidence/README.md) |
| **Dev** (development) | 89 | `heldout/heldout_bank.json` |
| **Test-1** (sealed) | 138 | `heldout/test2/` |
| **Test-2** (sealed) | 60 + 15 abstention probes | `heldout/test3/` |
| **UNT** (another university, no OCR) | 63 | `heldout/unt/` |

The directory names `test2` and `test3` are historical; they correspond to Test-1 and Test-2 in the paper.

## Original benchmark of the first experiment

The first experiment used the 30-query bank and RAGAS metrics with a local Llama 3 8B judge. These files are kept unchanged:

- `queries.json`
- `ragas_V1_baseline.csv` to `ragas_V4_completo.csv` and `ragas_por_consulta.csv`
- `resultados_ragas.txt`, `resultados_ablacion.txt`, `resultados_cache.txt`, `resultados_router.txt`, `resultados_latencia.txt`, and `resultados_wilcoxon.txt`
- `ablacion_V1_baseline.json` to `ablacion_V4_completo.json`

Later analyses (the 500-question bank and the held-out banks) use other runs and do not replace these tables.

## Held-out evaluations (`heldout/`)

- **Banks and seals.** `heldout_bank.json` (Dev), `test2/test2_bank.json` (Test-1), `test3/test3_bank.json` (Test-2), and `unt/unt_bank.json`. The two sealed banks have a `SEAL.json` with the SHA-256 of the bank, recorded before the system version they evaluate was designed.
- **Freeze files.** `FREEZE.json`, `FREEZE2.json`, and `FREEZE4.json` record SHA-256 hashes of the application code and of the index files used in a sealed run. The runners refuse to start if the code differs.
- **Frozen code.** `app_v4_frozen/` and `app_v4c_snapshot/` are the exact application snapshots of earlier versions.
- **Runs.** `runs*/`, `test2/runs/`, `test3/runs/`, and `unt/runs*/` contain the per-question answers (`*.jsonl`) and manifests of each run. `test2/invalid_runs_index_path_bug/` keeps a first pass that gave some systems an empty index through a path error; it was discarded and repeated unchanged.
- **Scoring.** `score_generic.py` scores any bank deterministically (gold-key regular expressions, no LLM judge) with paired bootstrap confidence intervals and the exact McNemar test. Results are written to `heldout/results/`.
- **Ablation of the final system.** `run_ablation.py` removes one component of `V4d` at a time on Test-2 without changing the frozen code (variants: `no_structured`, `no_evidence`, `top5`, `no_verbalizer`, `terse_style`); `test3/run_ablation.sh` is the chain that was run, the answers are in `test3/ablation/`, and the scores are in `results/test3_ablation_results.md`. Generation uses temperature 0.1, so two runs of the same variant can differ by a few questions.
- **RAGAS on Test-2.** `ragas_test3/` (the Gemini judge, with a hard spending cap; scores in `ragas_scores.csv`, measured spend in `spend.json`).
- **Router analysis.** `router_analysis.py` produces `results/router_analysis.json`.

### Reproducing a run

Score the answers of a sealed bank (no model calls):

```powershell
venv\Scripts\python.exe evaluation\heldout\score_generic.py `
  --bank evaluation\heldout\test3\test3_bank.json --tag test3 `
  --run V1=evaluation\heldout\test3\runs\V1.jsonl `
  --run V1c=evaluation\heldout\test3\runs\V1c.jsonl `
  --run V4d=evaluation\heldout\test3\runs\V4d.jsonl `
  --compare V4d:V1 --compare V4d:V1c
```

Generate new answers with `heldout/run_v4d.py` (final system), `heldout/run_baselines_bank.py` (dense baselines), or `heldout/test3/run_final.sh` (the exact chain of the final sealed run). These runs need a local Ollama model and the evaluation index described in the main README ("What is not in this repository").

New runs of the original pipeline:

```powershell
venv\Scripts\python.exe evaluation\ablation.py --queries evaluation\queries.json
venv\Scripts\python.exe evaluation\run_ragas.py --judge gemini `
  --queries evaluation\queries.json `
  --input-dir evaluation\runs\<run> `
  --output-dir evaluation\runs\ragas_<run>
```

RAGAS with a hosted judge and Textract can incur charges. Configure credentials locally in `.env` or in the process environment; never store keys in datasets, manifests, or the repository. Every new experiment should record versions, bank/index/code hashes, generator, judge, temperature, and evaluation settings.

## Supplementary evidence

See [`evidence/README.md`](evidence/README.md) for the files, configuration, and limits of each line of evidence:

- System audit and local integration test.
- OCR comparison on a four-page sample and a manual sample of numeric cells.
- The 500-question bank, the author's review log, and the answer comparison.
- The four-variant RAGAS run with Gemini as judge.
- Latency audit based on saved runs.
- Responses to reviewers and the status of the proposed corrections.

`real_users/` contains a protocol and scripts to collect and score questions from real applicants (not yet run). Intermediate experiments and large files are kept locally in `archive/`, which is excluded from the repository; do not cite them as main results merely because they were preserved.
