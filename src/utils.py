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
    """Auto-detect latitude/longitude columns safely."""
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
        "child_age", "childage", "age_child",
        "age_month", "age_in_month", "agemonth", "age_m",
        "kid_age", "kids_age", "ch_age"
    ]

    col = next((c for c in df.columns if any(p in c.lower() for p in age_patterns)), None)

    if col:
        df["child_age_num"] = pd.to_numeric(safe_get(df, col), errors="coerce")

    return df


# -----------------------------
# Normalization helpers
# -----------------------------

def _map_yes_no(series):
    """Normalize Yes/No fields safely."""
    s = series.astype(str).str.strip().str.lower()

    mapping = {
        "yes": "Yes", "y": "Yes", "1": "Yes", "true": "Yes", "t": "Yes",
        "no": "No", "n": "No", "0": "No", "false": "No", "f": "No"
    }

    out = s.map(mapping).replace({np.nan: None})
    return out


def _map_treatment(series):
    """Normalize treatment fields safely."""
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
# Standardization pipeline
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


# -----------------------------
# MAIN ENTRY — used by app.py
# -----------------------------
def prep_uploaded_files(uploaded_files):
    frames = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
        except:
            try:
                df = pd.read_csv(file)
            except:
                continue

        if df.empty:
            continue

        df.columns = [normalize_colname(c) for c in df.columns]
        df["_source_file"] = file.name

        df = standardize_cols(df)
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


# -----------------------------
# Column finder
# -----------------------------
def find_col(df, mapping):
    for key, patterns in mapping.items():
        for col in df.columns:
            if any(p in col.lower() for p in patterns):
                return col
    return None
