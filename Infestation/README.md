# Infestation — forest insect damage in Quebec (Données Québec)

All datasets tagged **« Infestation »** on Données Québec
(https://www.donneesquebec.ca/recherche/dataset/?tags=Infestation), published by the
Ministère des Ressources naturelles et des Forêts (MRNF). License: CC-BY 4.0.
Downloaded October 2026.

| Dataset (folder) | Insect | Years |
|---|---|---|
| `tordeuse-des-bourgeons-de-lepinette/` | Spruce budworm (*Choristoneura fumiferana*) | 1967 – current year |
| `arpenteuse-de-la-pruche/` | Hemlock looper (*Lambdina fiscellaria*) | 1991 – 2015 |
| `tordeuse-du-pin-gris/` | Jack pine budworm (*Choristoneura pinus*) | 2004 – 2007 |
| *(forest tent caterpillar)* | *Livrée des forêts*, also tagged « Infestation » | Already extracted in [Quebec_data / 2_forest/insect_defoliation_livree](https://github.com/gheriza/Quebec_data/tree/main/2_forest/insect_defoliation_livree) |

The original zip files are in `raw/`. They are excluded from git because of their size.

## What the CSV files contain

Each CSV is one map layer from the source. File names are `<source zip>__<layer>.csv`.

**Damage areas (polygons):** one row per area mapped from aircraft (or, recently, satellite),
with the source columns plus:

- `centroid_lon`, `centroid_lat`: a point inside the area, in decimal degrees (WGS84)
- `geometry_wkt`: the full outline as WKT text (longitude latitude). Open it in QGIS with
  *Layer → Add Delimited Text Layer → Geometry: WKT*.

| Column | Meaning |
|---|---|
| `ANNEE` / `Annee` | Year of the survey |
| `SUPER_HA` / `Super_Ha` | Area in hectares |
| `NIVEAU` / `Niveau` | Damage class (codes below) |
| `Ia` / `Ia25` | Damage class as a number (2007 onward) |
| `SupHaCea` | Area in hectares, computed in an Albers equal-area projection (2014 onward) |
| `Code_RA` | Administrative region code (2019 onward) |
| `SHAPE_Length`, `SHAPE_Area` | Computed automatically by the GIS software, in degrees. Not useful as distances or areas. |

**Damage classes (`NIVEAU`), from the official read-me files:**

| Dataset | Codes |
|---|---|
| Spruce budworm 1967–1991 | 0 = none; 1 = light (1–35 %); 2 = moderate (36–70 %); 3 = severe (71–100 %); in sprayed areas: 4 = light, 5 = severe "tête verte" (36–50 %), 6 = moderate+ (51–70 %), 7 = severe (71–100 %); mortality: 11 = 0–25 %, 12 = 26–50 %, 13 = 51–75 %, 14 = 76–100 %, 15 = 100 % |
| Spruce budworm 1992–2006 | 1 = light (1–35 %), 2 = moderate (36–70 %), 3 = severe (71–100 %) |
| Spruce budworm 2007 onward | `Niveau` as text (Léger / Modéré / Grave / PRESENCE) and `Ia` as a number: 0 = presence detected on Sentinel satellite imagery, 1 = light (top third of the crown of a few trees), 2 = moderate (upper half of the crown of most trees), 3 = severe (whole crown of most trees) |
| Hemlock looper | 1 = light, 2 = moderate, 3 = severe; mortality 54 = 1–25 %, 55 = 26–50 %, 56 = 51–75 %, 57 = 76–100 %; 8 = clear-cut; 99 = damage seen on satellite imagery |

Percentages are the share of the year's new foliage lost.

**High-resolution image centres (`dpf_imagerie_tbe2X_*`, points):** one row per aerial photo taken
for the spruce budworm survey (2023, 2024, 2025). The columns give the photo number, the sector, the camera,
the capture date and time, the position, and `Hyperlien`, a link to the photo itself. The `_Simplifie` layers
are a lighter subset of the same photos.

The official column descriptions (French) are in each folder's `FD_*.xls` (data dictionary) and
`LisezMoi*.txt` (read-me) files, copied from the source zips.

## Things to know

- **Sprayed areas are missing from 1992 on.** Since then, areas treated by aerial spraying (SOPFIM) are not in
  the files, as the read-me files explain.
- **The hemlock looper zip contains the 2013–2015 layer twice** (identical copies). It was converted once.
- **Some old polygons had broken rings.** These were repaired by keeping their valid rings. Polygons with no
  valid ring keep their attributes with an empty geometry.
- Coordinates are decimal longitude/latitude. Layers published in NAD83 are kept in NAD83, which differs from
  WGS84 by less than 2 m. Layers in a projected system would be converted to WGS84.

## Spruce budworm files from 2007 on

| File | Rows | Content |
|---|---|---|
| `TBE_Donnees_2007-2013__TBE_2007_2013.csv` | 54,867 | 2007–2013 |
| `TBE_Donnees_2014-aujourdhui__TBE_2014_2025.csv` | 411,490 | 2014–2025 (5.1 GB, because the outlines are very detailed) |
| `TBE_Donnees_annee_en_cours__TBE_2025.csv` | 55,377 | 2025 only (shapefile version) |
| `TBE_Donnees_annee_en_cours_gdb__TBE_2025.csv` | 55,377 | 2025 only (geodatabase version). Same areas, plus the `SHAPE_Length`/`SHAPE_Area` columns |

The 2025 areas appear in three files: the 2014–today file and the two current-year files. Use only one of them
to avoid counting areas twice.

## Scripts

[`../scripts/fetch_infestation.sh`](../scripts/fetch_infestation.sh) downloads the files (resumable).
[`../scripts/infestation_to_csv.py`](../scripts/infestation_to_csv.py) converts them.
[`../scripts/infestation_after_download.sh`](../scripts/infestation_after_download.sh) runs the conversion
once the download finishes.
