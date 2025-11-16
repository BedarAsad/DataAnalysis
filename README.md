# ARCED — Data Preview Dashboard (Streamlit)

Compact, reproducible Streamlit dashboard to preview, filter, visualize, map, and download merged father/mother survey data from the ARCED / NYU pilot.

## Live
- Streamlit: https://dataanalysis-arced.streamlit.app/
- GitHub: https://github.com/BedarAsad/DataAnalysis

## Overview
- Upload two files (father + mother, XLSX/XLS/CSV). The app programmatically normalizes, cleans, and merges them using a tolerant column-detection pipeline.
- Primary merge key: survey ID (commonly hhid_final / hhid / key / unique_id). No manual edits or hard-coded column names required.

## Key features
- Automatic detection & normalization: GPS, survey date/month, child age (months), consent, treatment, enumerator, upazila.
- Interactive filters: Enumerator, Upazila / Area, child age range, survey month, consent, treatment, and other detected fields.
- Data preview table with pagination and CSV export of filtered data.
- Field explorer: create bar/count, box, and scatter visualizations by selected fields.
- Summary statistics: N, mean, median, std, min, max for numeric fields; counts and percentages for categorical fields.
- Comparison tables (e.g., average child age by upazila).
- Enumerator summary: top enumerators by consent rate.
- Map: household GPS points colored by treatment status (treatment = 1 → Treatment; 0 → Control).
- Cached processing for faster interactions.

## Repository structure
- src/
  - app.py        — Streamlit app (UI, filters, visuals, download)
  - utils.py      — data reading, normalization, detection, merge/coalesce helpers
- data/ (optional) — sample/test files
- README.md
- requirements.txt

## Data expectations & detection
- Provide two files: father.xxx and mother.xxx (XLSX/XLS/CSV).
- The pipeline tolerates common name variants:
  - Survey ID: hhid_final, hhid, key, unique_id, survey_id
  - Consent: consent_final, consent
  - Treatment: treatment, treat, group
  - GPS: lat, latitude, lon, lng, longitude, gps_x/y
  - Date: date, survey, interview
  - Child age: child_age, age_month, age_m
- Detected columns are normalized (lowercase, non-alphanumerics replaced) and standardized columns are created (e.g., latitude_num, longitude_num, survey_month, child_age_num, consent_norm, treatment_norm).

## Quick start (Windows)
1. Create & activate a virtual env:
   - python -m venv .venv
   - .venv\Scripts\activate
2. Install dependencies:
   - pip install -r requirements.txt
   If no requirements file:
   - pip install streamlit pandas numpy plotly pydeck openpyxl
3. Run:
   - streamlit run src\app.py
4. Upload both father and mother files in the app UI.

## Deployment (Streamlit Cloud)
1. Push the repository to GitHub.
2. Create a new app on Streamlit Cloud and point the start file to `src/app.py`.
3. After deploy, replace the Live Streamlit URL above with the actual shared URL.

## Reproducibility & design notes
- All cleaning/transformations are code-driven in `src/utils.py`; no manual data edits.
- Column detection is heuristic and tolerant. If a column is not recognized, inspect original column names or add patterns in utils.
- Caching (`st.cache_data`) is used to speed repeated operations.

## Troubleshooting
- Merge fails: ensure both uploads contain a survey ID column (common variants listed above).
- Missing plots or map: confirm filtered data contains numeric values and valid GPS coordinates.
- Excel read errors: ensure `openpyxl` is installed.

## Contact / attribution
- Project scaffold for the ARCED Data Analyst test. Repository: https://github.com/BedarAsad/DataAnalysis

## License
- MIT
