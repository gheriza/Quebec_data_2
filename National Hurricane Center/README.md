# National Hurricane Center (NOAA) — hurricane data

Data from the U.S. National Hurricane Center archive (https://www.nhc.noaa.gov/data/),
downloaded in October 2026. NOAA data is in the public domain.

| Folder | What it is | Years |
|---|---|---|
| `hurdat2/` | **Best tracks**: the official position and strength of every storm every 6 hours, as CSV | Atlantic 1851–2025, NE/central Pacific 1949–2025 |
| `hurdat2/quebec_*` | The Atlantic storms that crossed into Quebec or came within 200 km | 1851–2025 |
| `tropical_cyclone_reports/` | The official report on each storm (PDF, or scanned pages for older storms) | 1958–2026 |
| `forecast_verification/` | Error of every official NHC forecast against what happened, as CSV, plus the annual verification reports | 1968–2025 (CSV from 1989) |

---

## hurdat2/

Source: HURDAT2 (`raw/hurdat2-1851-2025-092326.txt`, `raw/hurdat2-nepac-1949-2025-092926.txt`).
The official format descriptions are in `raw/hurdat2-format-*.pdf`.

| File | Rows | One row = |
|---|---|---|
| `atlantic_1851_2025_storms.csv` | 1,988 | One storm: name, dates, peak wind, lowest pressure, peak category, landfalls |
| `atlantic_1851_2025_track_points.csv` | 55,524 | One storm position (usually every 6 h) |
| `pacific_ne_nc_1949_2025_storms.csv` | 1,262 | Same, eastern and central North Pacific |
| `pacific_ne_nc_1949_2025_track_points.csv` | 32,060 | Same |
| `quebec_atlantic_storms.csv` | 183 | An Atlantic storm whose track came within 200 km of Quebec (98 crossed into Quebec) |
| `quebec_atlantic_track_points.csv` | 596 | A track point within 200 km of Quebec |

**Track point columns:**

| Column | Meaning |
|---|---|
| `storm_id` | e.g. `AL092024` = Atlantic, 9th cyclone of 2024. Joins the two files. |
| `datetime_utc` | Time of the position, in UTC |
| `record_identifier` | `L` = landfall, `I` = intensity peak, `P` = minimum pressure, `R`/`C`/`G`/`T`/`W`/`S` = other special points (see format PDF) |
| `status` | `TD` tropical depression, `TS` tropical storm, `HU` hurricane, `EX` extratropical, `SD`/`SS` subtropical, `LO` low, `WV` wave, `DB` disturbance |
| `latitude`, `longitude` | Decimal degrees; **longitude is negative west of Greenwich** (the source writes `94.8W`) |
| `max_wind_kt` | Maximum sustained (1-minute) wind, knots |
| `min_pressure_mb` | Minimum central pressure, millibars |
| `saffir_simpson_category` | 1–5, computed from the wind for hurricane (`HU`) points only |
| `wind_radius_34kt_NE_nm` … `wind_radius_64kt_NW_nm` | How far winds of 34, 50 and 64 kt reach in each quadrant, nautical miles (from 2004) |
| `radius_max_wind_nm` | Radius of maximum wind, nautical miles, where available (recent storms, and some older storms from the historical reanalysis) |

Empty cells = not recorded (`-999` in the source). Wind radii only exist from 2004 onward.

**Quebec files:** distances are measured to Quebec's boundary (the 17 administrative regions plus the
"Côte-Nord (Tracé de 1927)" zone). The boundary file is in [Quebec_data / 2_forest/forest_cover_change_hansen/boundaries](https://github.com/gheriza/Quebec_data/tree/main/2_forest/forest_cover_change_hansen/boundaries).
`track_entered_quebec = yes` means the line between two consecutive positions crosses into Quebec.
`closest_distance_to_quebec_km` is the track's closest approach. The `*_within` columns describe only the
points within 200 km, and `regions_crossed` lists the regions the track passes over. Most storms that reach
Quebec have already become extratropical (`EX`), but they still bring heavy rain and wind,
e.g. Fiona 2022, Debby 2024.

---

## tropical_cyclone_reports/

Every report listed in NHC's index (`TCR_StormReportsIndex.xml`): 1,540 storms.

- `pdf/YYYY/`: reports published as PDF, mostly from 1995 onward.
- `storm_wallets/YYYY/<storm>/`: older reports, kept as scanned pages (GIF images, one per page).
  For 1958–1967 storms there is no single report. The "storm wallet" holds the scanned working documents
  instead, in subfolders such as `worksht/` (worksheets), `prenhc/` (advisories), `preloc/`, `modelin/`,
  `opltrack/` (operational track) and `marine/`.
- `html/YYYY/`: 3 reports published as web pages (including Hurricane Andrew 1992).
- `index_reports.csv`: one row per storm: year, basin, name, format, where it was saved, and the original URL.
  The `note` column flags the entries that could not be saved because NHC's own index links to a page that
  no longer exists: 8 of 1,540 (Gordon 1994, four 1988–1992 Pacific storms, and three Pacific depressions).

The reports are documents (text, tables, maps). Their tables were not extracted.

---

## forecast_verification/

Source: NHC official forecast error database (`verification/verify7.shtml`).
The format description is `raw/Error_Tabulation_File_Format.pdf`.

| File | Rows | Content |
|---|---|---|
| `official_forecast_errors_atl_track_intensity_1989_2025.csv` | 13,352 | Each official Atlantic forecast: track error (n mi) and intensity error (kt) at 0–168 h |
| `official_forecast_errors_atl_along_cross_track_1989_2025.csv` | 13,352 | Same forecasts: along-track and cross-track position errors (n mi) |
| `official_forecast_errors_epac_*` | 12,802 each | Same, eastern Pacific |
| `reports_pdf/` | 65 PDFs | Annual verification reports 1968–2025, five-year averages, error trends |

**Columns:**
- `init_datetime_utc`, `storm_id`, and the storm's position (`latitude`, `longitude` negative west) and
  `max_wind_kt` when the forecast was issued.
- `OFCL_track_error_nmi_048h`: distance between the forecast position 48 h ahead and the actual position.
- `OFCL_intensity_error_kt_048h`: forecast wind minus actual wind.
- `OFCL_along_track_error_nmi_*`: positive = forecast too fast.
- `OFCL_cross_track_error_nmi_*`: positive = forecast to the right of the track.
- `equivalent_sample_size_*`: weights for statistics, because forecasts 6 h apart are not independent.

Empty = no forecast or no verifying position at that lead time. Extratropical stages and dissipation
forecasts are excluded, as stated in the `#` header lines of each file.

---

## Scripts

In [`../scripts/`](../scripts/): `hurdat2_to_csv.py`, `hurdat2_quebec.py`, `fetch_nhc_reports.py`,
`nhc_errors_to_csv.py`.
