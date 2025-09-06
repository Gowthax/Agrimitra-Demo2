import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from deep_translator import GoogleTranslator
import io

st.set_page_config(page_title="Agrimitra — Crop Recommender", layout="wide")

# ---------- Utility functions ----------

@st.cache_data
def load_csv(path: str):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return None


def try_load_or_upload(filename: str, key: str):
    df = load_csv(filename)
    if df is None:
        uploaded = st.sidebar.file_uploader(f"Upload {filename}", type=["csv"], key=key)
        if uploaded is not None:
            try:
                uploaded.seek(0)
                return pd.read_csv(uploaded)
            except Exception as e:
                st.sidebar.error(f"Failed to read uploaded {filename}: {e}")
                return None
    return df


def contains_any(text, values):
    if pd.isna(text):
        return False
    text = str(text).lower()
    for v in values:
        if str(v).lower() in text:
            return True
    return False


def translate_text(text: str, lang: str):
    try:
        return GoogleTranslator(source="auto", target=lang).translate(text)
    except Exception:
        return text

# ---------- Load datasets ----------

buyers_df = try_load_or_upload("buyers.csv", key="buyers")
crops_df = try_load_or_upload("crops.csv", key="crops")
locations_df = try_load_or_upload("locations.csv", key="locations")

if buyers_df is None or crops_df is None or locations_df is None:
    st.error("Please provide buyers.csv, crops.csv, and locations.csv to continue.")
    st.stop()

# ---------- Farmer Input ----------

st.sidebar.header("Farmer Input")
location = st.sidebar.selectbox("Location", locations_df["Location"].unique())
soil = st.sidebar.text_input("Soil Type")
season = st.sidebar.text_input("Season")
area = st.sidebar.number_input("Cultivable Area (Ha)", min_value=0.0, step=0.1)

# ---------- Crop Recommendation ----------

loc_row = locations_df[locations_df["Location"] == location].iloc[0]
suitable_crops = []

for _, row in crops_df.iterrows():
    if contains_any(row["SuitableSoils"], [soil]) and contains_any(row["SuitableSeasons"], [season]):
        suitable_crops.append(row)

suitable_df = pd.DataFrame(suitable_crops)

if suitable_df.empty:
    st.warning("No suitable crops found for the given conditions.")
    st.stop()

suitable_df["MarketScore"] = suitable_df["BuyerDemand_kg"] / (suitable_df["AvgPrice_INRkg"] + 1)

best_crop = suitable_df.sort_values("MarketScore", ascending=False).iloc[0]
expected_yield = best_crop["Yield_kgHa"] * area
expected_income = expected_yield * best_crop["AvgPrice_INRkg"]

# ---------- Buyer Matching ----------

buyer_matches = buyers_df[buyers_df["Crop"].str.lower() == best_crop["Crop"].lower()]

# ---------- Display ----------

st.subheader("Recommended Crop")
st.write(f"**{best_crop['Crop']}**")
st.write(f"Expected Yield: {expected_yield:.2f} kg")
st.write(f"Expected Income: ₹{expected_income:,.2f}")

st.subheader("Buyer Matches")
st.dataframe(buyer_matches)

# ---------- MoU Generation ----------

if not buyer_matches.empty:
    buyer = buyer_matches.iloc[0]
    mou_text = f"""
    Memorandum of Understanding (MoU)

    Farmer at {location} agrees to cultivate {best_crop['Crop']}.
    Buyer {buyer['BuyerName']} agrees to purchase at ₹{buyer['PriceOffer_INRkg']} per kg.
    Estimated quantity: {expected_yield:.2f} kg.
    """

    st.subheader("MoU Preview")
    st.text(mou_text)

    st.subheader("Translated Versions")
    for lang, label in [("en", "English"), ("hi", "Hindi"), ("ta", "Tamil")]:
        st.markdown(f"**{label}:**")
        st.text(translate_text(mou_text, lang))
