#!/bin/bash
cd /c/Users/USER/Documents/TOPICOS/ceprunsa_mvrag
until grep -q "UNTV2DONE" evaluation/heldout/unt/run_v2.log 2>/dev/null; do sleep 30; done
venv/Scripts/python.exe evaluation/heldout/run_v4d.py --bank evaluation/heldout/heldout_bank.json --out evaluation/heldout/runs_dev_v4d --label L_nbr --gen-model llama3:8b --retrieval top8_nbr
echo LNBRDONE
