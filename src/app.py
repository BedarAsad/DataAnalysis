import streamlit as st
import pandas as pd
import pydeck as pdk

from utils import (
    preprocess_father_data,
    preprocess_mother_data,
    load_uploaded_data,
    compute_summary,
    compute_comparison,
    filter_by_upazila,
)

st.set_page_config(page_title="Data Explorer", layout="wide")

st.title("Data Explorer — Father & Mother Survey")

st.sidebar.header("Upload Your Excel Files")

uploaded_father = st.sidebar.file_uploader("Upload father.xlsx", type=["xlsx"])
uploaded_mother = st.sidebar.file_uploader("Upload mother.xlsx", type=["xlsx"])

if not uploaded_father or not uploaded_mother:
    st.info("Please upload both father.xlsx and mother.xlsx to continue.")
    st.stop()

father_df = load_uploaded_data(uploaded_father)
mother_df = load_uploaded_data(uploaded_mother)

father_df = preprocess_father_data(father_df)
mother_df = preprocess_mother_data(mother_df)

tab1, tab2, tab3 = st.tabs(["Summary", "Comparison Table", "Map"])

with tab1:
    st.subheader("Summary Statistics")
    summary = compute_summary(father_df, mother_df)
    st.dataframe(summary)

with tab2:
    st.subheader("Comparison Table")

    child_age = st.number_input("Child Age", min_value=0, max_value=20, value=5)
    upazila = st.selectbox("Upazila", sorted(father_df["upazila"].dropna().unique()))

    comparison = compute_comparison(father_df, mother_df, child_age, upazila)

    if comparison is None:
        st.warning("No matching data for the selected filters.")
    else:
        st.dataframe(comparison)

with tab3:
    st.subheader("Location Map")

    map_df = filter_by_upazila(father_df, mother_df)
    if map_df.empty:
        st.warning("No geolocation data available.")
    else:
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[longitude, latitude]",
            get_radius=80,
        )

        deck = pdk.Deck(
            layers=[layer],
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=map_df["latitude"].mean(),
                longitude=map_df["longitude"].mean(),
                zoom=10,
            ),
        )
        st.pydeck_chart(deck)
