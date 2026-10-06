# Evaluation with real applicant questions (protocol)

Goal: measure the system with questions that the authors did **not** write, and with human validation by two annotators. This protocol has not been run yet; the paper's question banks were written by the authors, and the paper lists that as a limitation.

CSV column names in the templates are in Spanish (`origen` = source, `fecha` = date) and are kept as they appear in the scripts.

## 1. Collection (done by a CEPRE monitor)

- Possible sources: the cycle's WhatsApp or Telegram group, a query form, questions asked in class or by email.
- **Target: 150-250 questions** (minimum 100). The more varied, the better. Do not filter out "bad" or badly written questions: they are part of real use.
- Save **only the text of the question**. Remove names, national ID numbers, phone numbers, applicant codes, and any other personal data. Do not record who asked.
- Ask CEPRUNSA (or the person in charge) for permission to use the questions for research, and record who authorized it and when. If you collect them from a group, tell the group what they will be used for.
- Fill `plantilla_preguntas.csv` (one question per row, column `query`; in `origen` put whatsapp / form / class; in `fecha` the month).

## 2. Annotation of the correct answer (annotator A and annotator B, separately)

- For each question, each annotator looks for the answer in the official PDFs and fills `plantilla_gold.csv`:
  - `category`: CRONOGRAMA (schedule), VACANTES (vacancies), TEMARIO (syllabus), REGLAMENTO (regulations), SIN_RESPUESTA (in-domain but the document does not say), or FUERA_DE_DOMINIO (out-of-domain).
  - `gold`: the correct answer in one sentence, with the exact datum.
  - `source`: file and page.
- Each annotator works **without seeing** the other's work. Afterwards the agreement (kappa of the category) is computed and disagreements are resolved between the two; one final gold remains.
- If a question is ambiguous or has no clear answer, mark it `AMBIGUA` and exclude it (report how many).

## 3. Freeze and seal (before running)

- Seal the bank with a hash (`sha256`) and record the date. Freeze the code (hashes of `app/*.py` and of the index), as with `heldout/FREEZE2.json`.
- Change nothing in the system after seeing the real questions.

## 4. Run once

- Systems: V1 (dense baseline), V6 (hybrid + reranker without router), and the system under test. Use the same runner as for the held-out banks (see [`../heldout/`](../README.md)) with the real bank.

## 5. Blind human grading

- `prepare_blind_sheets.py` shuffles the answers of the systems into random order, **without saying which is which**, and produces one sheet per annotator.
- Each annotator marks every answer: `C` correct, `P` partial, `I` incorrect, `A` abstention (the system says it did not find the information).
  - If the question is SIN_RESPUESTA or FUERA_DE_DOMINIO, abstaining is correct (computed automatically).
- `score_human.py` computes accuracy per system, kappa between annotators, confidence intervals, and McNemar between systems.

## 6. What to report

- How many questions, from where, how many excluded, and the agreement between annotators (kappa).
- Accuracy of each system with 95% CIs and paired tests. Report whatever comes out.
- The real distribution of categories (and the router's accuracy on real questions).
- This addresses two weaknesses that a reviewer pointed out: a small dataset and questions written by the authors.
