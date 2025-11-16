# ARCED — Data Preview Dashboard (Streamlit)

Compact interactive dashboard to preview, filter, visualize, map, and download merged father/mother survey data for the ARCED / NYU pilot.

## Live links
- Streamlit (live): https://dataanalysis-arced.streamlit.app/
- GitHub: https://github.com/BedarAsad/DataAnalysis

## Key features
- Upload father/mother XLSX or CSV; files are merged automatically.
- Auto-detect and normalize: survey ID, GPS, dates, child age, consent, treatment.
- Interactive filters: Enumerator, Upazila, child age range, survey month, consent, treatment.
- Data preview table, charts (count/bar, box, scatter), summary stats, comparison tables.
- Enumerator summary (consent rates) and map of households (by treatment).
- Download filtered data as CSV.
- Fully programmatic, reproducible cleaning — no manual edits or hardcoding.

## Data expectations
- Two files: father.xxx and mother.xxx (XLSX/XLS/CSV).
- Typical column names supported (examples): hhid_final / key / unique_id, consent_final, treatment*, lat/lon, survey_date, child_age.

## Quick start (Windows)
1. python -m venv .venv
2. .venv\Scripts\activate
3. pip install -r requirements.txt
4. streamlit run src\app.py
5. Upload both files in the app UI.

## Deployment
- Works on Streamlit Cloud, Render, etc. Point the service to `src/app.py`.

## Troubleshooting
- If merge fails, confirm both files contain a survey ID column (common variants are supported).
- For Excel: install `openpyxl`.

License: MIT