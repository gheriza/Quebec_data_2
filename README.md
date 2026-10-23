# Quebec data — part 2

Companion to [gheriza/Quebec_data](https://github.com/gheriza/Quebec_data) and
[gheriza/Quebec_data_1](https://github.com/gheriza/Quebec_data_1).

| Folder | Content |
|---|---|
| [`National Hurricane Center/`](National%20Hurricane%20Center/) | NOAA hurricane data: HURDAT2 storm tracks (Atlantic 1851–2025, Pacific 1949–2025), the storms that reached Quebec, official forecast errors, and the storm reports |
| [`Infestation/`](Infestation/) | Données Québec datasets tagged « Infestation »: spruce budworm (1967–2025), hemlock looper (1991–2015), jack pine budworm (2004–2007) damage areas, plus the original downloads in `raw/` |
| [`scripts/`](scripts/) | The scripts used to download and convert the data |

Each folder has its own README that explains every file and column.

## Split files

GitHub refuses files over 100 MB, so larger files are stored in 90 MB pieces:

- `name.csv.gz.part00`, `part01`, …: a compressed CSV. Rejoin and unzip with
  `cat name.csv.gz.part* | gunzip > name.csv` (Linux/macOS), or on Windows
  `copy /b name.csv.gz.part* name.csv.gz`, then unzip with 7-Zip.
- `name.zip.part00`, `part01`, …: a split zip. Rejoin with `cat name.zip.part* > name.zip`
  (Windows: `copy /b name.zip.part* name.zip`).
