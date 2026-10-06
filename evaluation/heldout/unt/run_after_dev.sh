#!/bin/bash
cd /c/Users/USER/Documents/TOPICOS/ceprunsa_mvrag
until grep -q "ALLDONE" evaluation/heldout/runs_dev_v4d/run.log; do sleep 30; done
venv/Scripts/python.exe evaluation/heldout/unt/run_unt_v2.py > evaluation/heldout/unt/run_v2.log 2>&1
echo UNTV2DONE >> evaluation/heldout/unt/run_v2.log
