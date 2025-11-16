import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk
import datetime
from utils import auto_detect_and_prep, find_col

st.set_page_config(layout="wide", page_title="ARCED - Data Preview", page_icon="📊")

st.title("ARCED / NYU — Data Preview Dashboard")
st.markdown("Interactive preview and analysis. Data is loaded automatically from the `data/` folder.")

@st.cache_data
def load_data():
    return auto_detect_and_prep("data")

df = load_data()

if df.empty:
    st.warning("No data files found in `data/` folder. Upload `father.xlsx` and `mother.xlsx` (or CSVs) into the `data/` folder and refresh.")
    st.stop()

possible_enumerator = find_col(df, {"enumerator": ["enumerator","enumerator_name","enum"]})
possible_upazila = find_col(df, {"upazila": ["upazila","upazila_code","area","upazila_name"]})
possible_age = find_col(df, {"child_age": ["child_age","age_months","age_in_months","age"]})
possible_date = find_col(df, {"survey_date": ["survey_date","date","interview_date"]})

has_latlon = ("latitude_num" in df.columns) and ("longitude_num" in df.columns)

consent_col = "consent_norm" if "consent_norm" in df.columns else None
treatment_col = "treatment_norm" if "treatment_norm" in df.columns else None

st.sidebar.header("Filters")

if possible_enumerator and possible_enumerator in df.columns:
    enums = list(df[possible_enumerator].dropna().unique())
    selected_enums = st.sidebar.multiselect("Enumerator", options=enums, default=enums)
else:
    selected_enums = None

if possible_upazila and possible_upazila in df.columns:
    upazilas = list(df[possible_upazila].dropna().unique())
    selected_upazilas = st.sidebar.multiselect("Upazila / Area", options=upazilas, default=upazilas)
else:
    selected_upazilas = None

if "child_age_num" in df.columns:
    amin = int(np.nanmin(df["child_age_num"].dropna())) if not df["child_age_num"].dropna().empty else 0
    amax = int(np.nanmax(df["child_age_num"].dropna())) if not df["child_age_num"].dropna().empty else 24
    age_min, age_max = st.sidebar.slider("Child age (months)", min_value=amin, max_value=amax, value=(amin, min(24,amax)))
else:
    age_min, age_max = None, None

if "survey_month" in df.columns:
    months = sorted(df["survey_month"].dropna().unique())
    selected_months = st.sidebar.multiselect("Survey month", options=months, default=months)
else:
    selected_months = None

if consent_col:
    consent_opts = list(df[consent_col].dropna().unique())
    selected_consent = st.sidebar.multiselect("Consent", options=consent_opts, default=consent_opts)
else:
    selected_consent = None

if treatment_col:
    treatment_opts = sorted(df[treatment_col].dropna().unique())
    selected_treatment = st.sidebar.multiselect("Treatment (0=Control,1=Treatment)", options=treatment_opts, default=treatment_opts)
else:
    selected_treatment = None

mask = pd.Series(True, index=df.index)

if selected_enums is not None:
    mask &= df[possible_enumerator].isin(selected_enums)

if selected_upazilas is not None:
    mask &= df[possible_upazila].isin(selected_upazilas)

if age_min is not None and "child_age_num" in df.columns:
    mask &= df["child_age_num"].between(age_min, age_max, inclusive="both")

if selected_months is not None and "survey_month" in df.columns:
    mask &= df["survey_month"].isin(selected_months)

if selected_consent is not None and consent_col:
    mask &= df[consent_col].isin(selected_consent)

if selected_treatment is not None and treatment_col:
    mask &= df[treatment_col].isin(selected_treatment)

filtered = df[mask]

left, right = st.columns([2,1])

with left:
    st.subheader("Data preview")
    st.write(f"Files loaded: {filtered['_source_file'].nunique()} | Rows: {len(filtered)}")
    nrows = st.selectbox("Rows to show", options=[10,25,50,100], index=1)
    st.dataframe(filtered.head(nrows))

    st.markdown("---")
    st.subheader("Field explorer & visualization")

    all_cols = list(filtered.columns)
    x_col = st.selectbox("X / field (for charts & stats)", options=all_cols)
    y_candidates = [c for c in all_cols if pd.api.types.is_numeric_dtype(filtered[c])]
    y_col = st.selectbox("Y / numeric (for charts)", options=y_candidates) if y_candidates else None

    plot_type = st.selectbox("Plot type", options=["Bar / Count", "Histogram", "Box", "Scatter (X vs Y)"])

    if plot_type == "Bar / Count":
        st.plotly_chart(px.histogram(filtered, x=x_col), use_container_width=True)

    elif plot_type == "Histogram" and y_col:
        st.plotly_chart(px.histogram(filtered, x=y_col, nbins=30), use_container_width=True)

    elif plot_type == "Box" and y_col:
        st.plotly_chart(px.box(filtered, x=x_col if filtered[x_col].nunique()<50 else None, y=y_col), use_container_width=True)

    elif plot_type == "Scatter (X vs Y)" and y_col:
        st.plotly_chart(px.scatter(filtered, x=x_col, y=y_col, trendline="ols"), use_container_width=True)

    st.markdown("---")
    st.subheader("Summary statistics for selected field")

    if pd.api.types.is_numeric_dtype(filtered[x_col]):
        series = pd.to_numeric(filtered[x_col], errors="coerce")
        stats = {
            "N": int(series.count()),
            "mean": float(series.mean()) if series.count()>0 else None,
            "median": float(series.median()) if series.count()>0 else None,
            "std": float(series.std()) if series.count()>0 else None,
            "min": float(series.min()) if series.count()>0 else None,
            "max": float(series.max()) if series.count()>0 else None
        }
        st.json(stats)
    else:
        vc = filtered[x_col].value_counts(dropna=False)
        summary = pd.DataFrame({"count": vc, "percent": (vc / vc.sum() * 100).round(2)})
        st.dataframe(summary)

    st.markdown("---")
    st.subheader("Comparison table")

    if "child_age_num" in filtered.columns and possible_upazila in filtered.columns:
        comp = filtered.groupby(possible_upazila)["child_age_num"].agg(["count","mean","median"]).reset_index().sort_values("mean", ascending=False)
        st.dataframe(comp)
    else:
        st.info("Comparison table requires child_age and upazila fields.")

with right:
    st.subheader("Enumerator summary")

    if possible_enumerator in df.columns and consent_col in df.columns:
        enum_tab = filtered.groupby(possible_enumerator).agg(
            total=(consent_col,"count"),
            consent_yes=(consent_col,lambda x: (x=="Yes").sum())
        )
        enum_tab["consent_rate_pct"] = (enum_tab["consent_yes"] / enum_tab["total"] * 100).round(2)
        enum_tab = enum_tab.sort_values("consent_rate_pct", ascending=False)
        st.dataframe(enum_tab.head(20))
        st.table(enum_tab.head(3).reset_index()[[possible_enumerator,"total","consent_yes","consent_rate_pct"]])
    else:
        st.info("Enumerator + consent fields are required for this summary.")

    st.markdown("---")
    st.subheader("Quick stats")

    for c in ["_source_file","survey_month","consent_norm","treatment_norm"]:
        if c in filtered.columns:
            st.write(f"**{c}**")
            st.write(filtered[c].value_counts().head(10))

    st.markdown("---")
    st.subheader("Map of households (by treatment)")

    if has_latlon:
        map_df = filtered.dropna(subset=["latitude_num", "longitude_num"]).copy()

        if not map_df.empty:

            map_df["treatment_norm"] = map_df.get("treatment_norm", np.nan)

            def make_json_safe(v):
                if isinstance(v, (np.integer, np.int64)): return int(v)
                if isinstance(v, (np.floating, np.float64)): return float(v)
                if pd.isna(v): return None
                if isinstance(v, (pd.Timestamp, datetime.datetime, datetime.date)): return v.isoformat()
                return v

            map_df = map_df.applymap(make_json_safe)

            map_df["color_r"] = map_df["treatment_norm"].apply(lambda x: 0 if x == 1 else 220)
            map_df["color_g"] = map_df["treatment_norm"].apply(lambda x: 128 if x == 1 else 20)
            map_df["color_b"] = map_df["treatment_norm"].apply(lambda x: 0 if x == 1 else 60)

            lat_center = float(map_df["latitude_num"].mean())
            lon_center = float(map_df["longitude_num"].mean())

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position=["longitude_num","latitude_num"],
                get_fill_color=["color_r","color_g","color_b"],
                get_radius=70,
                pickable=True
            )

            view_state = pdk.ViewState(
                latitude=lat_center,
                longitude=lon_center,
                zoom=10
            )

            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "treatment: {treatment_norm}\nhhid: {hhid}"}
            )

            st.pydeck_chart(deck)
        else:
            st.info("No GPS coordinates found for the filtered set.")
    else:
        st.info("Latitude/Longitude columns not detected.")

st.markdown("---")
st.header("Download filtered data")

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv, file_name="filtered_data.csv", mime="text/csv")

st.caption("CSV contains the processed standardized columns.")