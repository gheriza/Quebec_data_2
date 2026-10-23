"""Download every NHC Tropical Cyclone Report listed in TCR_StormReportsIndex.xml.

Usage: python3 fetch_nhc_reports.py <folder containing TCR_StormReportsIndex.xml>

PDF reports go to pdf/<year>/; older reports kept as scanned "storm wallet"
pages (GIF images) go to storm_wallets/<year>/<basin>_<storm>/. Resumable:
files already on disk are skipped. Writes index_reports.csv.
"""
import csv
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

DIR = sys.argv[1]


def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            err = e
        except Exception as e:
            err = e
        time.sleep(2 ** i)
    raise err


def save(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return os.path.getsize(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get(url)
    with open(path + ".tmp", "wb") as f:
        f.write(data)
    os.replace(path + ".tmp", path)
    return len(data)


def wallet_files(url, depth=0):
    """Files in a storm wallet folder; older wallets (1958-1967) keep their
    scanned documents one level down, in subfolders such as worksht/ and prenhc/."""
    html = get(url).decode("utf-8", "replace")
    names = [n for n in re.findall(r'href="([^"?/][^"]*)"', html) if not n.startswith(("http", "mailto"))]
    files = [n for n in names if not n.endswith("/") and "." in n]
    if depth == 0:
        for sub in (n for n in names if n.endswith("/")):
            files += [sub + f for f in wallet_files(urllib.parse.urljoin(url, sub), 1)]
    return files


def fetch(row):
    name, url, year, basin = row["StormName"], row["StormReportURL"], row["Year"], row["Basin"]
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    try:
        if url.lower().endswith(".pdf"):
            rel = os.path.join("pdf", year, os.path.basename(urllib.parse.urlparse(url).path))
            size = save(url, os.path.join(DIR, rel))
            return [year, basin, name, "PDF", url, rel, 1, size, ""]
        if "storm_wallets" in url:
            rel = os.path.join("storm_wallets", year, slug)
            files = wallet_files(url)
            size = sum(save(urllib.parse.urljoin(url, f), os.path.join(DIR, rel, f)) for f in files)
            return [year, basin, name, "Scanned pages (storm wallet)", url, rel, len(files), size, ""]
        if url.lower().endswith((".html", ".htm")):
            rel = os.path.join("html", year, os.path.basename(urllib.parse.urlparse(url).path))
            size = save(url, os.path.join(DIR, rel))
            return [year, basin, name, "HTML", url, rel, 1, size, ""]
        return [year, basin, name, "", url, "", 0, 0, "Broken link in the NHC index"]
    except Exception as e:
        return [year, basin, name, "", url, "", 0, 0, f"Download failed: {e}"]


def main():
    rows = [{c.tag: (c.text or "").strip() for c in r}
            for r in ET.parse(os.path.join(DIR, "TCR_StormReportsIndex.xml")).getroot()]
    out = []
    with ThreadPoolExecutor(6) as ex:
        for i, res in enumerate(ex.map(fetch, rows), 1):
            out.append(res)
            if i % 50 == 0:
                print(f"{i}/{len(rows)}", flush=True)
    out.sort(key=lambda r: (r[0], r[1], r[2]))
    with open(os.path.join(DIR, "index_reports.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "basin", "storm", "format", "source_url", "local_path", "files", "bytes", "note"])
        w.writerows(out)
    print("done:", sum(1 for r in out if r[5]), "reports saved,", sum(1 for r in out if r[8]), "with notes")


if __name__ == "__main__":
    main()
