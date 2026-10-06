#!/bin/bash
cd /c/Users/USER/Documents/TOPICOS/ceprunsa_mvrag
PY=venv/Scripts/python.exe; R=evaluation/heldout/run_v4d.py; B=evaluation/heldout/heldout_bank.json; O=evaluation/heldout/runs_dev_v4d
$PY $R --bank $B --out $O --label Q_top5   --gen-model qwen2.5:7b --retrieval top5
$PY $R --bank $B --out $O --label L_top5   --gen-model llama3:8b  --retrieval top5
$PY $R --bank $B --out $O --label Q_nbr    --gen-model qwen2.5:7b --retrieval top8_nbr
echo ALLDONE
