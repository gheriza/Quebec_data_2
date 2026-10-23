"""Convert NHC HURDAT2 best-track files to CSV.

Usage: python3 hurdat2_to_csv.py <hurdat2 txt> <output prefix>
Writes <prefix>_track_points.csv (one row per best-track point) and
<prefix>_storms.csv (one row per storm). Missing values (-999) are left empty;
longitudes are negative west of Greenwich. Format reference: the
hurdat2-format-*.pdf files published with the data.
"""
import csv
import sys

SRC, PREFIX = sys.argv[1], sys.argv[2]
RADII = [f"wind_radius_{kt}kt_{q}_nm" for kt in (34, 50, 64) for q in ("NE", "SE", "SW", "NW")]
STATUS = {"TD": "Tropical depression", "TS": "Tropical storm", "HU": "Hurricane", "EX": "Extratropical cyclone",
          "SD": "Subtropical depression", "SS": "Subtropical storm", "LO": "Low", "WV": "Tropical wave",
          "DB": "Disturbance"}


def coord(v):
    v = v.strip()
    x = float(v[:-1])
    return -x if v[-1] in "WS" else x


def num(v):
    v = v.strip()
    return "" if v in ("", "-999", "-99") else int(v)


def category(wind, status):
    """Saffir-Simpson category from 1-min sustained wind (kt), hurricanes only."""
    if status != "HU" or wind == "":
        return ""
    for cat, lo in ((5, 137), (4, 113), (3, 96), (2, 83), (1, 64)):
        if wind >= lo:
            return cat
    return ""


def main():
    points, storms = [], []
    lines = [l for l in open(SRC, encoding="ascii") if l.strip()]
    i = 0
    while i < len(lines):
        head = [x.strip() for x in lines[i].split(",")]
        sid, name, n = head[0], head[1], int(head[2])
        rows = [[x.strip() for x in l.split(",")] for l in lines[i + 1:i + 1 + n]]
        assert len(rows) == n and all(len(r[0]) == 8 for r in rows), f"{sid}: expected {n} rows"
        i += 1 + n
        for r in rows:
            date, hhmm, rec, st = r[0], r[1].zfill(4), r[2], r[3]
            wind, pres = num(r[6]), num(r[7])
            radii = [num(x) for x in r[8:20]]
            rmw = num(r[20]) if len(r) > 20 else ""
            points.append([sid, sid[:2], int(sid[2:4]), int(sid[4:8]), name,
                           f"{date[:4]}-{date[4:6]}-{date[6:]}T{hhmm[:2]}:{hhmm[2:]}Z", date, hhmm, rec, st,
                           STATUS.get(st, st), coord(r[4]), coord(r[5]), wind, pres, category(wind, st)] + radii + [rmw])
        sp = points[-n:]
        winds = [p[13] for p in sp if p[13] != ""]
        press = [p[14] for p in sp if p[14] != ""]
        cats = [p[15] for p in sp if p[15] != ""]
        storms.append([sid, sid[:2], int(sid[2:4]), int(sid[4:8]), name, n, sp[0][5], sp[-1][5],
                       max(winds) if winds else "", min(press) if press else "", max(cats) if cats else "",
                       "yes" if any(p[9] == "HU" for p in sp) else "no",
                       sum(p[8] == "L" for p in sp), " ".join(sorted({p[9] for p in sp}))])
    with open(f"{PREFIX}_track_points.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["storm_id", "basin", "cyclone_number", "year", "name", "datetime_utc", "date", "time_utc",
                    "record_identifier", "status", "status_description", "latitude", "longitude",
                    "max_wind_kt", "min_pressure_mb", "saffir_simpson_category"] + RADII + ["radius_max_wind_nm"])
        w.writerows(points)
    with open(f"{PREFIX}_storms.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["storm_id", "basin", "cyclone_number", "year", "name", "track_points", "first_datetime_utc",
                    "last_datetime_utc", "peak_wind_kt", "lowest_pressure_mb", "peak_saffir_simpson_category",
                    "reached_hurricane", "landfall_points", "statuses"])
        w.writerows(storms)
    print(f"{SRC}: {len(storms)} storms, {len(points)} track points")


if __name__ == "__main__":
    main()
