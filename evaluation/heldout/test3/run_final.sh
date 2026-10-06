#!/bin/bash
# Single pass over the sealed bank #3 with the frozen final system and fair baselines (same generator).
cd /c/Users/USER/Documents/TOPICOS/ceprunsa_mvrag
PY=venv/Scripts/python.exe; H=evaluation/heldout; B=$H/test3/test3_bank.json; O=$H/test3/runs
mkdir -p $O
$PY $H/run_v4d.py --bank $B --out $O --label V4d --gen-model qwen2.5:7b --retrieval top8_nbr --freeze $H/FREEZE4.json
$PY $H/run_baselines_bank.py --bank $B --out $O --label V1  --gen-model qwen2.5:7b --freeze $H/FREEZE4.json
$PY $H/run_baselines_bank.py --bank $B --out $O --label V1c --gen-model qwen2.5:7b --freeze $H/FREEZE4.json
$PY $H/run_v4d.py --bank $H/test3/abstention_control_bank.json --out $O/control --label V4d --gen-model qwen2.5:7b --retrieval top8_nbr --freeze $H/FREEZE4.json
echo FINALDONE
