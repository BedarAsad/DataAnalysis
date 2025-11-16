import os
import re
from datetime import datetime
import pandas as pd
import numpy as np


def read_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if ext == ".csv":
        return pd.read_csv(path)
    return pd.DataFrame()


def normalize_colname(name):
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def detect_latlon(df):
    lat_candidates = ["lat", "latitude", "gps_lat", "y_coord"]
    lon_candidates = ["lon", "lng", "longitude", "gps_lon", "x_coord"]

    lat = next((c for c in df.columns if any(k in c.lower() for k in lat_candidates)), None)
    lon = next((c for c in df.columns if any(k in c.lower() for k in lon_candidates)), None)

    if lat and lon:
        df["latitude_num"] = pd.to_numeric(df[lat], errors="coerce")
        df["longitude_num"] = pd.to_numeric(df[lon], errors="coerce")

    return df


def detect_dates(df):
    date_cols = ["date", "survey", "interview", "day"]
    col = next((c for c in df.columns if any(k in c.lower() for k in date_cols)), None)

    if col:
        df["survey_date"] = pd.to_datetime(df[col], errors="coerce")
        df["survey_month"] = df["survey_date"].dt.to_period("M").astype(str)

    return df


def detect_numeric_child_age(df):
    patterns = [
        "child_age", "childage", "age_child",
        "age_month", "age_in_month", "agemonth", "age_m",
        "kid_age", "kids_age", "ch_age"
    ]

    col = next((c for c in df.columns if any(p in c.lower() for p in patterns)), None)

    if col:
        df["child_age_num"] = pd.to_numeric(df[col], errors="coerce")

    return df


def _map_yes_no(series):
    s = series.astype(str).str.strip().str.lower().replace({"nan": None})

    mapping = {
        "yes": "Yes", "y": "Yes", "1": "Yes", "true": "Yes", "t": "Yes",
        "no": "No", "n": "No", "0": "No", "false": "No", "f": "No"
    }

    out = s.map(mapping)

    if out.isna().all():
        nums = pd.to_numeric(series, errors="coerce")
        out = nums.map({1: "Yes", 0: "No"})

    out = out.where(out.notna(), None)
    return out


def _map_treatment(series):
    s = series.astype(str).str.strip().str.lower().replace({"nan": None})

    mapping = {
        "1": 1, "treatment": 1, "t": 1, "yes": 1, "true": 1, "y": 1,
        "0": 0, "control": 0, "c": 0, "no": 0, "false": 0, "n": 0, "f": 0
    }

    out = s.map(mapping)

    if out.isna().any():
        nums = pd.to_numeric(series, errors="coerce")
        out = out.fillna(nums)

    out = pd.to_numeric(out, errors="coerce")
    return out


def detect_categorical_binary(df, patterns, new_name):
    col = next((c for c in df.columns if any(p in c.lower() for p in patterns)), None)
    if not col:
        return df

    try:
        if new_name == "consent_norm":
            df[new_name] = _map_yes_no(df[col])
        else:
            df[new_name] = _map_treatment(df[col])
    except Exception:
        try:
            if new_name == "consent_norm":
                df[new_name] = _map_yes_no(df[col].astype(str))
            else:
                df[new_name] = _map_treatment(df[col].astype(str))
        except Exception:
            df[new_name] = pd.Series([None] * len(df), index=df.index)

    return df


def standardize_cols(df):
    df = detect_latlon(df)
    df = detect_dates(df)
    df = detect_numeric_child_age(df)

    df = detect_categorical_binary(
        df, patterns=["consent", "consent_final", "consented"], new_name="consent_norm"
    )
    df = detect_categorical_binary(
        df, patterns=["treat", "treatment", "treatment_status", "group"], new_name="treatment_norm"
    )

    return df


def prep_uploaded_files(uploaded_files):
    """
    Streamlit version of auto_detect_and_prep("data").
    Reads uploaded files and applies same preprocessing.
    """
    frames = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
        except Exception:
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


def find_col(df, mapping):
    for key, patterns in mapping.items():
        for col in df.columns:
            name = col.lower()
            if any(p in name for p in patterns):
                return col
    return None
