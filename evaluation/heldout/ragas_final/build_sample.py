"""Draws the question set for the final RAGAS run (budget: PEN 2.75 of Gemini credit).

Sources: (a) a stratified random sample (seed 2027) of ANSWERABLE questions of the sealed Test bank (123 answerable of 138);
(b) the 3 questions of the official CEPRUNSA FAQ page (https://admision.unsa.edu.pe/ceprunsa/preguntas-frecuentes/, read 2026-10-03),
verbatim, with the official answer as reference. Abstention questions are not scored with RAGAS (context metrics are meaningless
for a correct refusal). Writes sample_bank.json and its SHA-256 BEFORE any new answer is generated."""
import json, random, hashlib, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
bank = json.load(open(HERE.parent / "test2" / "test2_bank.json", encoding="utf-8"))["consultas"]
ans = [b for b in bank if not b["abstain"]]
quota = {"VACANTES": 24, "TEMARIO": 14, "REGLAMENTO": 14, "CRONOGRAMA": 5}   # 57 questions
rnd = random.Random(2027)
sample = []
for cat, n in quota.items():
    pool = sorted([b for b in ans if b["category"] == cat], key=lambda b: b["id"])
    sample += rnd.sample(pool, n)
items = [dict(id=b["id"], source_set="sealed_test", category=b["category"], type=b["type"], query=b["query"],
              ground_truth=f"{b['gold']} (fuente: {b['source']})") for b in sample]
faq = [
    ("F01", "¿Cómo puedo ingresar a las clases del CEPRUNSA?",
     "Acceder con la cuenta CEPRUNSA recibida al inscribirse, ingresar a Google Classroom, seleccionar el salón y hacer clic en el enlace de Google Meet."),
    ("F02", "¿Cómo puedo realizar el pago de las cuotas?",
     "Utilizar el código web asignado en SISADMISION en cualquier canal del BCP (agentes, banca móvil, banca por internet o Yape), seleccionando \"UNSA-VIRTUAL\"."),
    ("F03", "¿Puedo retirarme o solicitar la exoneración de cuotas del CEPRUNSA?",
     "No. El postulante no puede solicitar, bajo ningún concepto, devolución y/o reembolso del monto abonado ni exoneración de deuda."),
]
items += [dict(id=i, source_set="official_faq", category="FAQ", type="faq", query=q, ground_truth=a) for i, q, a in faq]
out = HERE / "sample_bank.json"
out.write_text(json.dumps({"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "seed": 2027, "quota": quota,
                           "n": len(items), "consultas": items}, ensure_ascii=False, indent=1), encoding="utf-8")
seal = {"sealed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "sample_bank_sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "n": len(items)}
(HERE / "sample_SEAL.json").write_text(json.dumps(seal, indent=1), encoding="utf-8")
print(len(items), seal)
