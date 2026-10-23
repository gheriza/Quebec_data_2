"""Convert NHC forecast error tabulation files (verification/errors/*.txt) to CSV.

Usage: python3 nhc_errors_to_csv.py <errors.txt> <out.csv>
Format reference: verification/pdfs/Error_Tabulation_File_Format.pdf.
Column codes are renamed, e.g. 024hT01 -> OFCL_track_error_nmi_024h; -9999 becomes
empty; longitude (given in degrees W) becomes negative east-positive longitude;
the dd-mm-yyyy/hh:mm:ss time becomes ISO 8601 UTC. The file's header lines are
kept as '#' comments at the top of the CSV.
"""
import csv
import re
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
KIND = {"T": "track_error_nmi", "I": "intensity_error_kt",
        "A": "along_track_error_nmi", "C": "cross_track_error_nmi",
        "X": "x_error_nmi", "Y": "y_error_nmi"}

lines = open(SRC, encoding="latin-1").read().splitlines()
h = next(i for i, l in enumerate(lines) if l.startswith("Date/Time"))
models = lines[1].split(":", 1)[1].split()
cols = lines[h].split()

names = []
for c in cols:
    m = re.fullmatch(r"(\d{3})h([A-Z])(\d+)", c)
    f = re.fullmatch(r"F(\d{3})", c)
    if m:
        names.append(f"{models[int(m.group(3)) - 1]}_{KIND[m.group(2)]}_{m.group(1)}h")
    elif f:
        names.append(f"equivalent_sample_size_{f.group(1)}h")
    else:
        names.append({"Date/Time": "init_datetime_utc", "STMID": "storm_id", "Lat": "latitude",
                      "Lon": "longitude", "WS": "max_wind_kt"}[c])

n = 0
with open(OUT, "w", newline="", encoding="utf-8") as f:
    for l in lines[:h]:
        if l.strip():
            f.write("# " + l.strip() + "\n")
    w = csv.writer(f)
    w.writerow(names)
    for l in lines[h + 1:]:
        v = l.split()
        if not v:
            continue
        assert len(v) == len(cols), l
        d, t = v[0].split("/")
        dd, mm, yyyy = d.split("-")
        row = [f"{yyyy}-{mm}-{dd}T{t[:5]}Z"] + v[1:]
        row = ["" if x in ("-9999", "-9999.0") else x for x in row]
        lon = names.index("longitude")
        if row[lon]:
            row[lon] = f"{-float(row[lon]):g}"
        w.writerow(row)
        n += 1
print(f"{SRC.rsplit('/', 1)[-1]}: {n} forecasts, {len(names)} columns")
