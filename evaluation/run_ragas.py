# evaluation/run_ragas.py
"""
Evalúa con RAGAS los archivos ablacion_*.json generados por ablation.py.

Produce:
  - ragas_<variante>.csv     : scores por consulta de cada variante (tabla de ablación, O9)
  - ragas_por_consulta.csv   : formato que espera stats_wilcoxon.py (O5)
                               multirag = V4_completo, baseline = V1_baseline

Requisitos:
  pip install ragas datasets langchain-google-genai langchain-huggingface langchain-openai

Juez (LLM que califica las respuestas):
  - Gemini (recomendado):  $env:GOOGLE_API_KEY = "tu_api_key"
      API key gratis en https://aistudio.google.com/apikey
  - Ollama local (gratis pero lento y menos confiable como juez):
      python evaluation\\run_ragas.py --judge ollama

IMPORTANTE: antes de correr, completa el campo "ground_truth" de cada
consulta en queries.json (la respuesta correcta según los documentos
oficiales de CEPRUNSA). La métrica context_recall lo necesita.
"""
import os
import sys
import json
import glob
import argparse
import hashlib
import importlib.metadata
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
from dotenv import load_dotenv
load_dotenv(Path(HERE).parent / ".env", override=False)


def cargar_ground_truths(queries_path):
    with open(queries_path, encoding="utf-8") as f:
        consultas = json.load(f)["consultas"]
    faltantes = [c["id"] for c in consultas if not c.get("ground_truth", "").strip()]
    if faltantes:
        print(f"[ERROR] Consultas sin 'ground_truth' en {queries_path}: {faltantes}")
        print("Completa la respuesta correcta de cada consulta y vuelve a correr.")
        sys.exit(1)
    return {c["query"]: c["ground_truth"] for c in consultas}


def construir_juez(judge: str, model: str | None):
    from ragas.llms import LangchainLLMWrapper
    if judge == "gemini":
        if not os.environ.get("GOOGLE_API_KEY"):
            print("[ERROR] Falta la variable de entorno GOOGLE_API_KEY.")
            print('PowerShell:  $env:GOOGLE_API_KEY = "tu_api_key"')
            sys.exit(1)
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model=model, temperature=0)
    else:  # ollama
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(base_url="http://localhost:11434/v1",
                         api_key="ollama", model=model,
                         temperature=0)
    return LangchainLLMWrapper(llm)


def construir_embeddings():
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_huggingface import HuggingFaceEmbeddings
    return LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base",
            model_kwargs={'local_files_only': os.environ.get('CEPRUNSA_LOCAL_MODELS_ONLY', '1') == '1'})
    )


def evaluar_variante(path: str, ground_truths: dict, juez, embeddings,
                     max_workers: int):
    from datasets import Dataset
    from ragas import evaluate, RunConfig
    from ragas.metrics import (faithfulness, answer_relevancy,
                               context_precision, context_recall)

    with open(path, encoding="utf-8") as f:
        datos = json.load(f)
    queries = [d['query'] for d in datos]
    if len(set(queries)) != len(queries):
        raise ValueError(f'Duplicate queries in {path}')
    missing = [q for q in queries if not ground_truths.get(q)]
    if missing:
        raise ValueError(f'Missing references for {len(missing)} queries in {path}')

    dataset = Dataset.from_dict({
        "question":     [d["query"] for d in datos],
        "contexts":     [d["contexts"] for d in datos],
        "answer":       [d["answer"] for d in datos],
        "ground_truth": [ground_truths.get(d["query"], "") for d in datos],
    })

    resultado = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=juez,
        embeddings=embeddings,
        # Ajustable según el proveedor/cuota; los reintentos cubren 429 transitorios.
        run_config=RunConfig(max_workers=max_workers, max_retries=15, max_wait=90, timeout=180, seed=42),
    )
    df = resultado.to_pandas()
    df["query"] = [d["query"] for d in datos]
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge", choices=["gemini", "ollama"], default="gemini")
    parser.add_argument("--model", default=None,
                        help="Modelo juez (default: CEPRUNSA_GEMINI_JUDGE_MODEL o gemini-3.8-flash)")
    parser.add_argument("--queries", default=os.path.join(HERE, "queries.json"),
                        help="JSON con consultas y ground_truth de referencia")
    parser.add_argument("--allow-unvalidated-candidates", action="store_true",
                        help="Permite solo exploración técnica con respuestas OCR aún no validadas; no usar como evidencia científica")
    parser.add_argument('--input-dir', default=HERE)
    parser.add_argument('--output-dir', required=True, help='Directorio NUEVO por repetición/juez')
    parser.add_argument('--max-workers', type=int, default=1,
                        help='Máximo de evaluaciones simultáneas (ajustar según la cuota del juez)')
    parser.add_argument("--variants", default=None,
                        help="Lista separada por comas para evaluar solo esas "
                             "variantes (ej. V1_baseline,V4_completo)")
    args = parser.parse_args()
    if args.max_workers < 1:
        parser.error('--max-workers debe ser al menos 1')
    if args.model is None:
        if args.judge == "gemini":
            args.model = os.environ.get("CEPRUNSA_GEMINI_JUDGE_MODEL", "gemini-3.8-flash")
        else:
            args.model = os.environ.get("CEPRUNSA_LOCAL_JUDGE_MODEL", "llama3")
    queries_path = Path(args.queries)
    with queries_path.open(encoding="utf-8") as f:
        query_document = json.load(f)
    candidate_status = query_document.get("status") == "CANDIDATE_POOL_NOT_A_VALIDATED_BENCHMARK"
    if candidate_status and not args.allow_unvalidated_candidates:
        parser.error("Este archivo contiene candidatos OCR sin validar. Verifica cada respuesta en el PDF visual antes de usarlo; para una corrida solo exploratoria añade --allow-unvalidated-candidates.")
    if args.judge == "gemini" and not os.environ.get("GOOGLE_API_KEY"):
        parser.error("Falta GOOGLE_API_KEY; configúrala en el entorno local o en el .env del proyecto.")
    ground_truths = cargar_ground_truths(queries_path)
    archivos = sorted(glob.glob(os.path.join(args.input_dir, "ablacion_*.json")))
    if args.variants:
        pedidas  = {v.strip() for v in args.variants.split(",")}
        archivos = [a for a in archivos
                    if os.path.basename(a).replace("ablacion_", "").replace(".json", "") in pedidas]
    if not archivos:
        print("[ERROR] No hay archivos ablacion_*.json — corre primero ablation.py")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {'utc': datetime.now(timezone.utc).isoformat(), 'judge': args.judge,
                'model': args.model, 'judge_temperature': 0,
                'ragas_runconfig': {'max_workers': args.max_workers, 'max_retries': 15, 'max_wait': 90, 'timeout': 180, 'seed': 42},
                'python': sys.version, 'versions': {p: importlib.metadata.version(p)
                    for p in ['ragas', 'datasets', 'langchain-openai', 'langchain-google-genai',
                              'langchain-huggingface', 'sentence-transformers']},
                'inputs_sha256': {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in archivos},
                'queries_path': str(queries_path.resolve()),
                'references_sha256': hashlib.sha256(queries_path.read_bytes()).hexdigest(),
                'candidate_references_unvalidated': candidate_status,
                'note': 'Temperature zero does not guarantee reproducibility. New directory required for every repetition.'}
    (output_dir/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    print(f"[INFO] Juez: {args.judge} | Variantes encontradas: {len(archivos)}")
    juez = construir_juez(args.judge, args.model)
    embeddings = construir_embeddings()

    METRICAS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    resultados = {}

    import pandas as pd
    for path in archivos:
        variante = os.path.basename(path).replace("ablacion_", "").replace(".json", "")
        out = str(output_dir/f"ragas_{variante}.csv")

        # Checkpoint: si la variante ya fue evaluada, cargar el CSV y saltar
        if os.path.exists(out):
            print(f"\n[SKIP] {variante} ya evaluada ({out}) — borra el CSV para repetirla")
            resultados[variante] = pd.read_csv(out)
            continue

        print(f"\n{'='*60}\n[INFO] Evaluando variante: {variante}")
        df = evaluar_variante(path, ground_truths, juez, embeddings, args.max_workers)
        resultados[variante] = df

        df.to_csv(out, index=False, encoding="utf-8")
        print(f"[GUARDADO] {out}")
        print("Promedios (para la tabla de ablación):")
        for m in METRICAS:
            if m in df.columns:
                print(f"  {m:<20} {df[m].mean():.4f}")

    # CSV combinado para stats_wilcoxon.py: V4_completo vs V1_baseline
    if "V4_completo" in resultados and "V1_baseline" in resultados:
        import pandas as pd
        v4, v1 = resultados["V4_completo"], resultados["V1_baseline"]
        if set(v4['query']) != set(v1['query']):
            raise ValueError('The variants do not contain the same queries')
        combinado = v4[['query'] + METRICAS].merge(v1[['query'] + METRICAS],
            on='query', validate='one_to_one', suffixes=('_multirag', '_baseline'))
        out = str(output_dir/'ragas_por_consulta.csv')
        combinado.to_csv(out, index=False, encoding="utf-8")
        print(f"\n[GUARDADO] {out} — listo para stats_wilcoxon.py")

    print("\n[DONE] Evaluación RAGAS completa.")


if __name__ == "__main__":
    main()
