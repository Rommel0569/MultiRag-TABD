#!/bin/bash
cd /c/Users/USER/Documents/TOPICOS/ceprunsa_mvrag
until [ "$(wc -l < evaluation/heldout/test2/runs/V4.jsonl)" -ge 138 ]; do sleep 20; done
sleep 5
venv/Scripts/python.exe evaluation/heldout/run_v4b.py --app evaluation/heldout/app_v4_frozen --systems V1,V6 --bank evaluation/heldout/test2/test2_bank.json --out evaluation/heldout/test2/runs > evaluation/heldout/test2/runs/run_baselines2.log 2>&1
echo RESTDONE >> evaluation/heldout/test2/runs/run_baselines2.log
