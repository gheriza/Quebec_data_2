"""Select the HURDAT2 Atlantic storms that crossed into or passed near Quebec.

Usage: python3 hurdat2_quebec.py <atlantic track_points.csv> <quebec regions geojson> <output prefix> [km]

Distances are computed in Quebec Lambert (EPSG:32198). A storm "entered Quebec"
when a segment between two consecutive best-track points crosses the Quebec
boundary; it is "near" when any point or segment comes within `km` (default 200).
Writes <prefix>_storms.csv and <prefix>_track_points.csv.
"""
import csv
import json
import sys
from collections import defaultdict

from pyproj import Transformer
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

PTS, REGIONS, PREFIX = sys.argv[1], sys.argv[2], sys.argv[3]
KM = float(sys.argv[4]) if len(sys.argv) > 4 else 200.0
to_m = Transformer.from_crs("EPSG:4326", "EPSG:32198", always_xy=True).transform

feats = json.load(open(REGIONS, encoding="utf-8"))["features"]
regions = [(f["properties"]["RES_NM_REG"], transform(to_m, shape(f["geometry"]).buffer(0))) for f in feats]
quebec = unary_union([g for _, g in regions])
near_zone = quebec.buffer(KM * 1000)
tree = STRtree([g for _, g in regions])


def region_at(p):
    for i in tree.query(p):
        if regions[i][1].contains(p):
            return regions[i][0]
    return ""


tracks = defaultdict(list)
with open(PTS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        tracks[r["storm_id"]].append(r)

out_storms, out_points = [], []
for sid, pts in tracks.items():
    xy = [to_m(float(p["longitude"]), float(p["latitude"])) for p in pts]
    line = LineString(xy) if len(xy) > 1 else Point(xy[0])
    if not line.intersects(near_zone):
        continue
    dist_km = round(line.distance(quebec) / 1000, 1)
    entered = line.intersects(quebec)
    near = []
    for p, (x, y) in zip(pts, xy):
        pt = Point(x, y)
        d = pt.distance(quebec) / 1000
        if d <= KM:
            reg = region_at(pt) if d == 0 else ""
            near.append(p)
            out_points.append([p["storm_id"], p["name"], p["year"], p["datetime_utc"], p["status"], p["status_description"],
                               p["latitude"], p["longitude"], p["max_wind_kt"], p["min_pressure_mb"],
                               round(d, 1), "yes" if d == 0 else "no", reg])
    crossed = sorted({regions[i][0] for i in tree.query(line) if regions[i][1].intersects(line)}) if entered else []
    winds = [int(p["max_wind_kt"]) for p in near if p["max_wind_kt"]]
    press = [int(p["min_pressure_mb"]) for p in near if p["min_pressure_mb"]]
    out_storms.append([sid, pts[0]["name"], pts[0]["year"], "yes" if entered else "no", dist_km, len(near),
                       near[0]["datetime_utc"] if near else "", near[-1]["datetime_utc"] if near else "",
                       max(winds) if winds else "", min(press) if press else "",
                       " ".join(sorted({p["status"] for p in near})), "; ".join(crossed)])

out_storms.sort(key=lambda r: r[0][4:8] + r[0][2:4])
with open(f"{PREFIX}_storms.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["storm_id", "name", "year", "track_entered_quebec", "closest_distance_to_quebec_km",
                f"track_points_within_{int(KM)}km", "first_point_within_utc", "last_point_within_utc",
                "max_wind_kt_within", "min_pressure_mb_within", "statuses_within", "regions_crossed"])
    w.writerows(out_storms)
with open(f"{PREFIX}_track_points.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["storm_id", "name", "year", "datetime_utc", "status", "status_description", "latitude", "longitude",
                "max_wind_kt", "min_pressure_mb", "distance_to_quebec_km", "inside_quebec", "region"])
    w.writerows(out_points)
print(f"{len(out_storms)} storms within {KM:g} km ({sum(r[3] == 'yes' for r in out_storms)} entered Quebec), "
      f"{len(out_points)} track points within {KM:g} km")
