#!/bin/bash
cd /c/Users/USER/Documents/TOPICOS/ceprunsa_mvrag
for v in no_structured no_evidence no_verbalizer terse_style top5; do
  venv/Scripts/python.exe evaluation/heldout/run_ablation.py --variant $v --bank evaluation/heldout/test3/test3_bank.json \
    --out evaluation/heldout/test3/ablation --gen-model qwen2.5:7b --freeze evaluation/heldout/FREEZE4.json
done
echo ABLATIONDONE
