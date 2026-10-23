#!/bin/bash
# Download every file of the Données Québec datasets tagged "Infestation"
# (except the forest tent caterpillar, already in 2_forest/insect_defoliation_livree/).
# Resumable: partial files continue where they stopped; the MRNF server is very
# slow, so stalled transfers (<200 B/s for 2 min) are retried up to 40 times.
# Usage: bash fetch_infestation.sh <output folder>
OUT=${1:-Infestation/raw}
mkdir -p "$OUT" && cd "$OUT" || exit 1
curl -s -m 60 "https://www.donneesquebec.ca/recherche/api/3/action/package_search?fq=tags:Infestation&rows=100" |
python3 -c '
import sys, json
for p in json.load(sys.stdin)["result"]["results"]:
    if "livree" in p["name"]:
        continue
    for r in p["resources"]:
        if r.get("format") != "WMS":
            print(p["name"].split("insecte-")[1] + "\t" + r["url"].strip())
' > files.tsv
# Smallest files first so they can be converted early; the current-year
# geodatabase (same content as the current-year shapefile) goes last.
while IFS=$'\t' read -r ds url; do
  s=$(curl -sIL -m 30 "$url" | grep -i '^content-length' | tail -1 | tr -dc 0-9)
  case "$url" in *annee_en_cours_gdb.zip) s=999999999999;; esac
  printf '%s\t%s\t%s\n' "${s:-0}" "$ds" "$url"
done < files.tsv | sort -n | cut -f2- > files_ordered.tsv
while IFS=$'\t' read -r ds url; do
  mkdir -p "$ds"; f="$ds/${url##*/}"
  rc=1
  for try in $(seq 1 40); do
    curl -sfL -C - --speed-limit 200 --speed-time 120 -o "$f" "$url"; rc=$?
    [ $rc -eq 0 ] && break
    [ $rc -eq 33 ] && rm -f "$f"   # server refused to resume: start over
    sleep 10
  done
  echo "$( [ $rc -eq 0 ] && echo ok || echo "FAIL($rc)" ) $(du -h "$f" 2>/dev/null | cut -f1) $f"
done < files_ordered.tsv
