#!/bin/bash
# Single pass over the sealed test bank. V4b uses FREEZE2-verified code; V1/V6/V4 use the frozen pre-improvement copy.
cd /c/Users/USER/Documents/TOPICOS/ceprunsa_mvrag
PY=venv/Scripts/python.exe; R=evaluation/heldout/run_v4b.py; B=evaluation/heldout/test2/test2_bank.json; O=evaluation/heldout/test2/runs
$PY $R --app app --systems V4b --bank $B --out $O --freeze evaluation/heldout/FREEZE2.json
$PY $R --app evaluation/heldout/app_v4_frozen --systems V4 --bank $B --out $O
$PY $R --app evaluation/heldout/app_v4_frozen --systems V1,V6 --bank $B --out $O
echo ALLDONE
