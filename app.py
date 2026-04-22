import streamlit as st
import joblib
import pandas as pd

# Load the pre-trained model
model = joblib.load("crop_yield_model.pkl")

# Extract available areas and items from model features
all_features = list(model.feature_names_in_)
areas = [f.replace("Area_", "") for f in all_features if f.startswith("Area_")]
items = [f.replace("Item_", "") for f in all_features if f.startswith("Item_")]

# Page configuration
st.set_page_config(page_title="Crop Yield Prediction", page_icon="🌱")

# Title and description
st.title("🌱 Crop Yield Prediction App")
st.write("Predict crop yield using machine learning based on environmental factors.")

# Sidebar for inputs
st.sidebar.header("Environmental Parameters")
rainfall = st.sidebar.number_input(
    "Rainfall (mm per year)", 
    value=1000.0, 
    min_value=0.0,
    help="Annual rainfall in millimeters"
)
temperature = st.sidebar.number_input(
    "Average Temperature (°C)", 
    value=25.0,
    help="Average annual temperature in Celsius"
)
pesticides = st.sidebar.number_input(
    "Pesticides (tonnes)", 
    value=10.0,
    min_value=0.0,
    help="Amount of pesticides used in tonnes"
)

st.sidebar.markdown("---")
st.sidebar.header("Location & Crop")

# Year selection
year = st.sidebar.slider(
    "Year",
    min_value=1990,
    max_value=2040,
    value=2025,
    help="Year for prediction (historical and future projections)"
)

# Area (Country) selection
selected_area = st.sidebar.selectbox(
    "Country/Region",
    options=areas,
    index=areas.index("India") if "India" in areas else 0,
    help="Select the country or region"
)

# Item (Crop) selection
selected_item = st.sidebar.selectbox(
    "Crop Type",
    options=items,
    index=items.index("Wheat") if "Wheat" in items else 0,
    help="Select the crop type"
)

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Summary")
    st.metric("Rainfall", f"{rainfall:.1f} mm/year")
    st.metric("Temperature", f"{temperature:.1f} °C")
    st.metric("Pesticides", f"{pesticides:.1f} tonnes")
    st.metric("Year", str(year))
    st.metric("Country", selected_area)
    st.metric("Crop", selected_item)

with col2:
    st.subheader("Prediction")
    if st.button("🔮 Predict Yield", use_container_width=True):
        try:
            # Create feature dictionary with all expected features
            feature_dict = {name: 0.0 for name in model.feature_names_in_}
            
            # Set the input values
            feature_dict['Year'] = year
            feature_dict['average_rain_fall_mm_per_year'] = rainfall
            feature_dict['pesticides_tonnes'] = pesticides
            feature_dict['avg_temp'] = temperature
            
            # Set selected Area and Item (one-hot encoding)
            feature_dict[f'Area_{selected_area}'] = 1.0
            feature_dict[f'Item_{selected_item}'] = 1.0
            
            # Create DataFrame and predict
            features = pd.DataFrame([feature_dict])
            prediction = model.predict(features)
            
            # Display result
            st.success(f"### Predicted Crop Yield: {prediction[0]:,.0f} hg/ha")
            
            # Additional info
            st.info(f"📊 Prediction for {selected_item} in {selected_area} ({year})")
            
        except Exception as e:
            st.error(f"Error during prediction: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    f"""
    **About this app:**
    - Uses a RandomForestRegressor model trained on agricultural data
    - Supports {len(areas)} countries/regions and {len(items)} crop types
    - Considers rainfall, temperature, pesticide usage, location, and year
    """
)
