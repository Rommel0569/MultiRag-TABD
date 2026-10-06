# evaluation/eval_cache.py
"""
O2 — Evaluación de la caché SIN sesgo circular (protocolo train/test).

Protocolo correcto según el revisor:
  Fase TRAIN: se puebla la caché ejecutando el pipeline completo sobre
              las consultas ORIGINALES del banco.
  Fase TEST : se mide la tasa de acierto sobre las PARÁFRASIS
              (campo 'parafrasis' de queries.json), que nunca se usaron
              para poblar la caché.

Así, un cache hit refleja capacidad real de generalizar a consultas
nuevas semánticamente equivalentes — no la estructura del banco.

El script respalda el archivo de caché actual antes de limpiarlo.
Requiere Ollama corriendo (la fase TRAIN invoca al LLM).
"""
import os
import sys
import json
import shutil
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE    = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP_DIR)

from cache import CACHE_FILE, search_cache
from pipeline import pipeline


def main():
    with open(os.path.join(HERE, "queries.json"), encoding="utf-8") as f:
        consultas = json.load(f)["consultas"]

    sin_parafrasis = [c["id"] for c in consultas if not c.get("parafrasis")]
    if sin_parafrasis:
        print(f"[ERROR] Consultas sin 'parafrasis': {sin_parafrasis}. "
              f"Completa queries.json primero.")
        return

    # Respaldar y limpiar la caché actual
    if os.path.exists(CACHE_FILE):
        backup = CACHE_FILE + "." + datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"
        shutil.copy(CACHE_FILE, backup)
        os.remove(CACHE_FILE)
        print(f"[INFO] Caché respaldada en: {backup}")

    # ---------- FASE TRAIN: poblar caché con las consultas originales ----------
    print(f"\n{'='*60}\nFASE TRAIN — poblando caché con {len(consultas)} originales")
    for c in consultas:
        print(f"  [TRAIN] {c['query'][:55]}")
        pipeline(c["query"])   # ejecuta pipeline completo y guarda en caché

    # ---------- FASE TEST: medir hit rate con las paráfrasis ----------
    print(f"\n{'='*60}\nFASE TEST — evaluando con paráfrasis (nunca vistas)")
    hits_ok, hits_mal, misses = [], [], []
    for c in consultas:
        resultado = search_cache(c["parafrasis"])
        if resultado:
            # Un hit solo es CORRECTO si recuperó la respuesta de SU
            # consulta original (la paráfrasis N debe emparejar la query N).
            correcto = resultado["original_query"] == c["query"]
            (hits_ok if correcto else hits_mal).append(
                (c["parafrasis"], resultado["similarity"]))
            etiqueta = "HIT-OK  " if correcto else "HIT-MAL "
            print(f"  [{etiqueta}] sim={resultado['similarity']:.3f} — "
                  f"'{c['parafrasis'][:45]}' emparejó con '{resultado['original_query'][:45]}'")
        else:
            misses.append(c["parafrasis"])
            print(f"  [MISS    ] '{c['parafrasis'][:50]}'")

    n = len(consultas)
    n_hits = len(hits_ok) + len(hits_mal)
    print(f"\n{'='*60}")
    print("RESULTADO (para las Secciones 3.5/4 del artículo):")
    print(f"  Tasa de acierto (test separado)      : {n_hits/n:.1%} ({n_hits}/{n})")
    print(f"  Hits CORRECTOS (respuesta apropiada) : {len(hits_ok)/n:.1%} ({len(hits_ok)}/{n})")
    print(f"  Hits FALSOS (respuesta equivocada)   : {len(hits_mal)/n:.1%} ({len(hits_mal)}/{n})")
    if n_hits:
        print(f"  Precisión de la caché (hits correctos / hits): {len(hits_ok)/n_hits:.1%}")
    print(f"  Misses: {len(misses)}")


if __name__ == "__main__":
    main()
