# Architecture review against reviewer comments

This maps reviewer concerns to the current three-phase implementation. It is
not a claim that the camera-ready manuscript or system has passed validation.

## Phase 1 — response cache

**Current behavior.** `app/cache.py` defaults to exact normalized-query matches
(`CEPRUNSA_CACHE_MODE=exact`). Semantic matching is opt-in. The prior cache
experiment accepted 13/30 paraphrases, with 4 wrong responses among the 13
accepted hits; that is a material precision risk, not safe paraphrase reuse.

**Reviewer link.** The cache is an operational feature, but its quality/coverage
trade-off must be reported. It does not establish general superiority over the
baseline.

**Improve before enabling semantic mode by default.** Keep exact mode as the
safe default. If semantic reuse is retained, tune thresholds on a separate
calibration set with hard negative pairs; add an abstain path; check answer
intent, source pages and corpus version before reuse; report accepted-hit
precision and coverage with confidence intervals. Expand the namespace hash
to include retrieval/pipeline policy and thresholds so configuration changes
cannot silently reuse stale entries.

## Phase 2 — intent router

**Current behavior.** `app/router.py` asks an Ollama model for one of five
labels with temperature 0. The historical benchmark had 30 items and only six
regulation queries; REGLAMENTO recall was 1/6 (0.167). The routing output has no
confidence or alternate category. A misroute can return plausible chunks from
the wrong collection, so the current fallback (only when the chosen category
returns zero chunks) does not catch every wrong route. Technical router errors
currently raise a service error; they must remain distinct from out-of-domain
decisions.

**Reviewer link.** Explain the 24.1% latency share and the weak regulation
recall. The current evidence does not justify saying the LLM router is better
than SVM/Naive Bayes; any small-set comparison is exploratory, not a held-out
benchmark.

**Improve next.** Use the 500-query pool only after human reference/category
review; preserve its 50 out-of-domain challenge items. Report per-class
precision/recall and confusion matrix with a held-out split. Add a calibrated
low-confidence fallback: search the routed category and a global/top-two
candidate set, then rerank and abstain when evidence is weak. Benchmark router
latency separately. Compare a light classifier only on the same labeled,
grouped, held-out queries.

## Phase 3 — hybrid retrieval and answer generation

**Current behavior.** `app/retriever.py` fuses FAISS dense retrieval and BM25,
then uses a multilingual cross-encoder. `app/ingest.py` currently chunks text
by 200 words with 20-word overlap. Existing `data/index/` has only 7 schedule,
11 vacancies, 58 syllabus and 82 regulation chunks for the present 85-page
corpus. The table/page sequence in its schedule chunks is visibly misaligned.
In an initial 5-query Ollama smoke run against that index, category routing was
5/5 correct but all 5 schedule answers were factually wrong or unsupported;
retrieved contexts mixed dates and phases. The source image of schedule p. 2
clearly shows distinct rows, so this is a retrieval/index representation
problem, not an ambiguity in the source date table.

**Reviewer link.** Different chunk sizes between variants are a confounder.
Table extraction quality and OCR limitations must be stated; new results cannot
replace historical results unless the corpus/index versions and conditions
are matched.

**Improve next.** Build a separate experimental index from the saved 85-page
Textract JSON; never re-send PDFs to AWS for this step. For tables, create
self-contained row passages that repeat headers and preserve empty cells and
column identity (for example, program + phase labels + counts). Keep chunking
and top-k identical across ablation variants. Save index/source hashes. Add a
retrieval-evidence check and cite only the source pages present in the selected
contexts. Run the validated 500-query bank against the baseline and experimental
index with the same generator and configuration before isolating the OCR
effect.

## Generator and evaluator are separate experiment controls

DeepSeek can replace the answer generator for a new run; it does not repair
retrieval or the router. Gemini can serve as an independent RAGAS judge; it
does not make OCR references correct. The local Ollama run is a diagnostic
condition, not a substitute for the requested DeepSeek/Gemini experiment. All
variants must use the same generator and the same judge for a valid comparison.

## What the 500-item bank can and cannot establish

Once its 450 OCR-derived in-domain references are visually verified and its 50
synthetic out-of-domain labels reviewed, it can support broader router,
retrieval and answer evaluations. It cannot answer reviewer questions about
RAGAS definitions, historical model versions, missing repetitions, chunk-size
confounds, table denominators, statistical test names, literature references,
or Springer figure/layout corrections. Those need explicit methods/results
text, verified calculations and the editable manuscript source.
