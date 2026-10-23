#!/bin/bash
# Wait for the Infestation download (scripts/fetch_infestation.sh) to finish,
# then convert everything new to CSV. Run detached:
#   setsid nohup bash scripts/infestation_after_download.sh &
cd /home/madi/Desktop/hayette || exit 1
while ps -eo args | grep -q "^bash scripts/fetch_infestation.sh"; do sleep 60; done
.venv/bin/python -I scripts/infestation_to_csv.py Infestation/raw Infestation > Infestation/convert.log 2>&1
echo "finished $(date)" >> Infestation/convert.log
