"""Convert the Données Québec "Infestation" downloads (shapefiles and file
geodatabases inside zip files) to CSV.

Usage: python3 infestation_to_csv.py <raw folder> <output folder>

For every complete zip in <raw>/<dataset>/, each vector layer becomes
<output>/<dataset>/<zip name>__<layer>.csv with all attribute columns plus
centroid_lon, centroid_lat and geometry_wkt, all in WGS84 longitude/latitude.
Incomplete zips (still downloading) are skipped and listed. Existing CSVs are
not rebuilt, so the script can be re-run as downloads finish.
"""
import csv
import glob
import os
import shutil
import sys
import tempfile
import zipfile

import numpy as np
import pyogrio
import shapefile
import shapely
import shapely.geometry
from pyproj import Transformer

RAW, OUT = sys.argv[1], sys.argv[2]
csv.field_size_limit(sys.maxsize)


def layers_in(folder):
    found = []
    for path in glob.glob(os.path.join(folder, "**", "*"), recursive=True):
        if path.lower().endswith(".shp") or (path.lower().endswith(".gdb") and os.path.isdir(path)):
            for name, gtype in pyogrio.list_layers(path):
                found.append((path, name, gtype))
    return found


def to_text(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v)


def to_geom(shp):
    """Shapely geometry from a pyshp shape. Degenerate rings (< 4 points) are
    dropped and the polygon rebuilt from the valid rings: shapefile outer rings
    are clockwise, holes counter-clockwise."""
    if not shp.points:
        return None
    try:
        return shapely.geometry.shape(shp.__geo_interface__)
    except (ValueError, shapefile.ShapefileException, shapefile.RingSamplingError):
        bounds = list(shp.parts) + [len(shp.points)]
        outers, holes = [], []
        for s, e in zip(bounds[:-1], bounds[1:]):
            ring = shp.points[s:e]
            if len(ring) >= 4:
                poly = shapely.geometry.Polygon(ring).buffer(0)
                (holes if shapely.geometry.LinearRing(ring).is_ccw else outers).append(poly)
        if not outers:
            return None
        g = shapely.union_all(outers)
        return g.difference(shapely.union_all(holes)) if holes else g


def read_shapefile(path):
    """pyshp reader with an encoding fallback: some older shapefiles store
    accents in Latin-1 while GDAL insists on UTF-8."""
    for enc in ("utf-8", "latin-1"):
        try:
            r = shapefile.Reader(path, encoding=enc)
            recs = r.shapeRecords()
            break
        except (UnicodeDecodeError, shapefile.ShapefileException):
            continue
    names = [f[0] for f in r.fields[1:]]
    fields = [[rec.record[j] for rec in recs] for j in range(len(names))]
    geo = np.array([to_geom(rec.shape) for rec in recs], dtype=object)
    prj = path[:-4] + ".prj"
    crs = open(prj).read() if os.path.exists(prj) else None
    return names, fields, geo, crs, len(recs)


def convert(path, layer, out_csv):
    if path.lower().endswith(".shp"):
        names, fields, geo, crs, n = read_shapefile(path)
    else:
        meta, _, geoms, fields = pyogrio.raw.read(path, layer=layer)
        names, crs = list(meta["fields"]), meta.get("crs")
        geo = shapely.from_wkb(geoms) if geoms is not None else None
        n = len(geo) if geo is not None else len(fields[0])
    if geo is not None and crs and "4326" not in str(crs) and "4269" not in str(crs) and "GCS_North_American_1983" not in str(crs):
        tr = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        geo = shapely.transform(geo, lambda xy: np.column_stack(tr.transform(xy[:, 0], xy[:, 1])))
    if geo is not None:
        cent = [shapely.point_on_surface(shapely.make_valid(g)) if g is not None and not shapely.is_empty(g) else None
                for g in geo]
    with open(out_csv + ".tmp", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(names + (["centroid_lon", "centroid_lat", "geometry_wkt"] if geo is not None else []))
        for i in range(n):
            row = [to_text(col[i]) for col in fields]
            if geo is not None:
                g = geo[i]
                if g is None or shapely.is_empty(g):
                    row += ["", "", ""]
                else:
                    c = cent[i]
                    row += [round(shapely.get_x(c), 6), round(shapely.get_y(c), 6), shapely.to_wkt(g, rounding_precision=6)]
            w.writerow(row)
    os.replace(out_csv + ".tmp", out_csv)
    return n, names, crs


def main():
    skipped = []
    for z in sorted(glob.glob(os.path.join(RAW, "*", "*.zip"))):
        ds = os.path.basename(os.path.dirname(z))
        base = os.path.basename(z)[:-4]
        try:
            with zipfile.ZipFile(z) as zf:
                if zf.testzip() is not None:
                    raise zipfile.BadZipFile("corrupt member")
                with tempfile.TemporaryDirectory() as tmp:
                    zf.extractall(tmp)
                    os.makedirs(os.path.join(OUT, ds), exist_ok=True)
                    for doc in glob.glob(os.path.join(tmp, "**", "*"), recursive=True):
                        if os.path.basename(doc).startswith(("LisezMoi", "FD_")):
                            shutil.copy(doc, os.path.join(OUT, ds, os.path.basename(doc)))
                    seen = {}
                    for path, layer, gtype in layers_in(tmp):
                        sig = (layer, os.path.getsize(path) if os.path.isfile(path) else path)
                        if sig in seen:      # identical copy of a layer already converted from this zip
                            print(f"dup     {ds}/{os.path.relpath(path, tmp)} = {seen[sig]} (identical, skipped)")
                            continue
                        seen[sig] = os.path.relpath(path, tmp)
                        out_csv = os.path.join(OUT, ds, f"{base}__{layer}.csv")
                        if layer in {k[0] for k in list(seen)[:-1]}:   # same name, different content
                            out_csv = out_csv[:-4] + f"__{len(seen)}.csv"
                        if os.path.exists(out_csv):
                            print(f"exists  {ds}/{os.path.basename(out_csv)}")
                            continue
                        n, names, crs = convert(path, layer, out_csv)
                        print(f"wrote   {ds}/{os.path.basename(out_csv)}: {n:,} features ({gtype}), "
                              f"{len(names)} columns, source CRS {str(crs)[:40]}", flush=True)
        except (zipfile.BadZipFile, EOFError, OSError) as e:
            skipped.append(f"{ds}/{os.path.basename(z)} ({e.__class__.__name__}: not complete yet)")
    for s in skipped:
        print("skipped", s)


if __name__ == "__main__":
    main()
