import streamlit as st
import pandas as pd
from googletrans import Translator

# ---------------------------
# Load CSV files (they must be in the same repo)
# ---------------------------
buyers_df = pd.read_csv("buyers.csv")
crops_df = pd.read_csv("crops.csv")
locations_df = pd.read_csv("locations.csv")

translator = Translator()

st.title("🌾 Agrimitra - Crop Recommendation System")
st.markdown("Get the best crop suggestion, expected income, and buyer match.")

# ---------------------------
# Farmer Input (Streamlit UI)
# ---------------------------
st.subheader("👨‍🌾 Farmer Input")

farmer_location = st.text_input("Enter your Location (e.g., Coimbatore)")
farmer_soil = st.text_input("Enter your Soil Type (e.g., Black, Red, Loamy)")
farmer_season = st.text_input("Enter Current Season (Monsoon, Rabi/Winter, Summer)")
farmer_area = st.number_input("Enter your Land Area (hectares)", min_value=0.1, step=0.1)

if st.button("🔍 Get Recommendation"):

    # ---------------------------
    # Step 1: Filter Suitable Crops by Location
    # ---------------------------
    location_info = locations_df[locations_df['Location'].str.lower() == farmer_location.lower()]

    if location_info.empty:
        st.warning("⚠️ Location not found in dataset. Using all crops as fallback.")
        suitable_crops_list = crops_df['Crop'].tolist()
    else:
        location_info = location_info.iloc[0]
        suitable_crops_list = [crop.strip() for crop in location_info['Top3SuitableCrops'].split(',')]

    suitable_crops_df = crops_df[crops_df['Crop'].isin(suitable_crops_list)].copy()

    # ---------------------------
    # Step 2: Compute MarketScore
    # ---------------------------
    max_price = suitable_crops_df['AvgPrice_INRkg'].max()
    max_demand = suitable_crops_df['BuyerDemand_kg'].max()

    def compute_market_score(row):
        norm_price = row['AvgPrice_INRkg'] / max_price if max_price else 0
        norm_demand = row['BuyerDemand_kg'] / max_demand if max_demand else 0
        soil_match = 1 if farmer_soil.lower() in row['SuitableSoils'].lower() else 0
        season_match = 1 if farmer_season.lower() in row['SuitableSeasons'].lower() else 0
        suitability = 0.5 * soil_match + 0.5 * season_match
        return 0.5 * norm_price + 0.3 * norm_demand + 0.2 * suitability

    suitable_crops_df['MarketScore'] = suitable_crops_df.apply(compute_market_score, axis=1)

    # ---------------------------
    # Step 3: Recommend Best Crop
    # ---------------------------
    best_crop_row = suitable_crops_df.loc[suitable_crops_df['MarketScore'].idxmax()]
    best_crop = best_crop_row['Crop']
    expected_income = best_crop_row['Yield_kgHa'] * farmer_area * best_crop_row['AvgPrice_INRkg']

    # ---------------------------
    # Step 4: Match Buyers
    # ---------------------------
    matched_buyers = buyers_df[buyers_df['Crop'].str.lower() == best_crop.lower()]

    # ---------------------------
    # Step 5: Generate MoU Preview
    # ---------------------------
    mou_text = f"""
    Memorandum of Understanding (Demo)

    Farmer at {farmer_location} agrees to sell {int(best_crop_row['Yield_kgHa']*farmer_area)} kg 
    of {best_crop} to {', '.join(matched_buyers['BuyerName'].tolist()) if not matched_buyers.empty else 'N/A'} 
    at INR {best_crop_row['AvgPrice_INRkg']}/kg.
    """

    try:
        mou_hi = translator.translate(mou_text, dest="hi").text
        mou_ta = translator.translate(mou_text, dest="ta").text
    except:
        mou_hi, mou_ta = mou_text, mou_text

    # ---------------------------
    # Step 6: Display Results
    # ---------------------------
    st.subheader("✅ Recommendation")
    st.write(f"**Best Crop:** {best_crop}")
    st.write(f"**Expected Gross Income:** ₹{int(expected_income):,}")

    st.subheader("📦 Matched Buyers")
    if matched_buyers.empty:
        st.warning("No buyers found for this crop in dataset.")
    else:
        st.dataframe(matched_buyers[['BuyerName','PriceOffer_INRkg','MonthlyDemand_kg','Contact','Location']])

    st.subheader("📜 MoU Preview")
    st.write("**English:**")
    st.code(mou_text, language="text")
    st.write("**Hindi:**")
    st.code(mou_hi, language="text")
    st.write("**Tamil:**")
    st.code(mou_ta, language="text")

st.markdown("---")
st.caption("Agrimitra Prototype | Future: add AI/ML models for price forecasting & yield prediction 🚀")
