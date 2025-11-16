import pandas as pd


def load_uploaded_data(file):
    return pd.read_excel(file)


def preprocess_father_data(df):
    df = df.copy()

    rename_map = {
        "Father_Age": "age",
        "Father_Consent": "consent",
        "Father_Upazila": "upazila",
        "Lat": "latitude",
        "Lon": "longitude",
        "Child_Age": "child_age",
    }

    df.rename(columns=rename_map, inplace=True)

    df["consent"] = normalize_consent(df["consent"])
    df["latitude"] = safe_float(df["latitude"])
    df["longitude"] = safe_float(df["longitude"])

    return df


def preprocess_mother_data(df):
    df = df.copy()

    rename_map = {
        "Mother_Age": "age",
        "Mother_Consent": "consent",
        "Mother_Upazila": "upazila",
        "Lat": "latitude",
        "Lon": "longitude",
        "Child_Age": "child_age",
    }

    df.rename(columns=rename_map, inplace=True)

    df["consent"] = normalize_consent(df["consent"])
    df["latitude"] = safe_float(df["latitude"])
    df["longitude"] = safe_float(df["longitude"])

    return df


def normalize_consent(series):
    yes_values = {"yes", "y", "1", "true", True}
    no_values = {"no", "n", "0", "false", False}

    def convert(v):
        if v is None:
            return None
        v_str = str(v).strip().lower()
        if v_str in yes_values:
            return "Yes"
        if v_str in no_values:
            return "No"
        return None

    return series.map(convert)


def safe_float(series):
    return pd.to_numeric(series, errors="coerce")


def compute_summary(father_df, mother_df):
    return pd.DataFrame({
        "Dataset": ["Father", "Mother"],
        "Total Rows": [len(father_df), len(mother_df)],
        "Avg Age": [father_df["age"].mean(), mother_df["age"].mean()],
        "Avg Child Age": [father_df["child_age"].mean(), mother_df["child_age"].mean()],
    })


def compute_comparison(father_df, mother_df, child_age, upazila):
    f = father_df[(father_df["child_age"] == child_age) & (father_df["upazila"] == upazila)]
    m = mother_df[(mother_df["child_age"] == child_age) & (mother_df["upazila"] == upazila)]

    if f.empty and m.empty:
        return None

    return pd.DataFrame({
        "Metric": ["Count", "Avg Age", "Consent Rate"],
        "Father": [
            len(f),
            f["age"].mean() if not f.empty else None,
            f["consent"].eq("Yes").mean() if not f.empty else None
        ],
        "Mother": [
            len(m),
            m["age"].mean() if not m.empty else None,
            m["consent"].eq("Yes").mean() if not m.empty else None
        ],
    })


def filter_by_upazila(father_df, mother_df):
    df = pd.concat([father_df, mother_df], ignore_index=True)
    df = df.dropna(subset=["latitude", "longitude"])
    return df
