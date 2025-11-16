import os
import re
from datetime import datetime
import pandas as pd
import numpy as np

# -----------------------------
# Safe helper functions
# -----------------------------

def safe_get(df, col):
    """Return df[col] or a Series of NaN if missing."""
    return df[col] if col in df.columns else pd.Series([None] * len(df))

def normalize_colname(name):
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")

def detect_latlon(df):
    lat_patterns = ["lat", "latitude", "gps_lat", "y_coord"]
    lon_patterns = ["lon", "lng", "longitude", "gps_lon", "x_coord"]
    lat_col = next((c for c in df.columns if any(p in c.lower() for p in lat_patterns)), None)
    lon_col = next((c for c in df.columns if any(p in c.lower() for p in lon_patterns)), None)
    if lat_col:
        df["latitude_num"] = pd.to_numeric(safe_get(df, lat_col), errors="coerce")
    if lon_col:
        df["longitude_num"] = pd.to_numeric(safe_get(df, lon_col), errors="coerce")
    return df

def detect_dates(df):
    date_patterns = ["date", "survey", "interview", "day"]
    col = next((c for c in df.columns if any(p in c.lower() for p in date_patterns)), None)
    if col:
        s = safe_get(df, col)
        df["survey_date"] = pd.to_datetime(s, errors="coerce")
        df["survey_month"] = df["survey_date"].dt.to_period("M").astype(str)
    return df

def detect_numeric_child_age(df):
    age_patterns = [
        "child_age", "childage", "age_child", "age_month", "age_in_month",
        "agemonth", "age_m", "kid_age", "kids_age", "ch_age", "minage_month"
    ]
    col = next((c for c in df.columns if any(p in c.lower() for p in age_patterns)), None)
    if col:
        df["child_age_num"] = pd.to_numeric(safe_get(df, col), errors="coerce")
    return df

# -----------------------------
# Normalization helpers
# -----------------------------

def _map_yes_no(series):
    s = series.astype(str).str.strip().str.lower()
    mapping = {
        "yes": "Yes", "y": "Yes", "1": "Yes", "true": "Yes", "t": "Yes",
        "no": "No", "n": "No", "0": "No", "false": "No", "f": "No"
    }
    out = s.map(mapping).replace({np.nan: None})
    return out

def _map_treatment(series):
    s = series.astype(str).str.strip().str.lower()
    mapping = {
        "1": 1, "treatment": 1, "t": 1, "yes": 1, "true": 1,
        "0": 0, "control": 0, "c": 0, "no": 0, "false": 0
    }
    out = s.map(mapping)
    out = pd.to_numeric(out, errors="coerce")
    return out

def detect_categorical_binary(df, patterns, new_name):
    col = next((c for c in df.columns if any(p in c.lower() for p in patterns)), None)
    if not col:
        return df
    series = safe_get(df, col)
    if new_name == "consent_norm":
        df[new_name] = _map_yes_no(series)
    else:
        df[new_name] = _map_treatment(series)
    return df

# -----------------------------
# Standardization pipeline for ONE file
# -----------------------------

def standardize_cols(df):
    df = detect_latlon(df)
    df = detect_dates(df)
    df = detect_numeric_child_age(df)
    df = detect_categorical_binary(
        df, ["consent", "consented", "consent_final"], "consent_norm"
    )
    df = detect_categorical_binary(
        df, ["treat", "treatment", "group"], "treatment_norm"
    )
    return df

# --- MODIFICATION: New function to read/prep a single file ---
def read_and_prep_file(file):
    """Reads one file, normalizes, and standardizes it."""
    try:
        if file.name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        elif file.name.lower().endswith(".csv"):
            df = pd.read_csv(file)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error reading {file.name}: {e}")
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    df.columns = [normalize_colname(c) for c in df.columns]
    df["_source_file"] = file.name
    df = standardize_cols(df)
    return df

# --- MODIFICATION: New MAIN function called by app.py ---
def prep_and_merge_files(uploaded_files):
    father_df = None
    mother_df = None

    # 1. Identify father and mother files
    for file in uploaded_files:
        name = file.name.lower()
        if "father" in name:
            father_df = read_and_prep_file(file)
        elif "mother" in name:
            mother_df = read_and_prep_file(file)

    if father_df is None or mother_df is None:
        return pd.DataFrame() # Return empty if both files aren't present

    # 2. Find the merge key (must be normalized)
    merge_key = "hhid_final"
    if merge_key not in father_df.columns or merge_key not in mother_df.columns:
        return pd.DataFrame() # Can't merge

    # 3. Merge the dataframes
    df_merged = pd.merge(
        father_df,
        mother_df,
        on=merge_key,
        how="outer",
        suffixes=("_father", "_mother")
    )

    # 4. Coalesce (combine) key standardized columns
    std_cols = [
        'latitude_num', 'longitude_num', 'survey_date', 'survey_month',
        'child_age_num', 'consent_norm', 'treatment_norm'
    ]
    for col in std_cols:
        col_f = f"{col}_father"
        col_m = f"{col}_mother"
        # Use father's value, but fill any missing with mother's value
        df_merged[col] = safe_get(df_merged, col_f).fillna(safe_get(df_merged, col_m))

    # 5. Coalesce other important filterable columns
    # Enumerator
    enum_f = find_col(df_merged, {"enum": ["enumid_r_father", "enumerator_father"]})
    enum_m = find_col(df_merged, {"enum": ["enumid_mother", "enumerator_mother"]})
    df_merged["enumerator"] = safe_get(df_merged, enum_f).fillna(safe_get(df_merged, enum_m))
    
    # Upazila
    upa_f = find_col(df_merged, {"upa": ["upazila_father"]})
    upa_m = find_col(df_merged, {"upa": ["upazila_mother"]})
    df_merged["upazila"] = safe_get(df_merged, upa_f).fillna(safe_get(df_merged, upa_m))
    
    # HHID (for tooltip)
    hhid_f = find_col(df_merged, {"hhid": ["unique_id_father", "key_father"]})
    hhid_m = find_col(df_merged, {"hhid": ["unique_id_mother", "key_mother"]})
    df_merged["hhid"] = safe_get(df_merged, hhid_f).fillna(safe_get(df_merged, hhid_m))

    return df_merged


# -----------------------------
# Column finder
# -----------------------------
def find_col(df, mapping):
    for key, patterns in mapping.items():
        for col in df.columns:
            if any(p in col.lower() for p in patterns):
                return col
    return None