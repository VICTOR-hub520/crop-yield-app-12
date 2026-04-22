import streamlit as st
import joblib
import pandas as pd

# Load the pre-trained model
model = joblib.load("crop_yield_model.pkl")

# Page configuration
st.set_page_config(page_title="Crop Yield Prediction", page_icon="🌱")

# Title and description
st.title("🌱 Crop Yield Prediction App")
st.write("Predict crop yield using machine learning based on environmental factors.")

# Sidebar for inputs
st.sidebar.header("Input Parameters")
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

# Additional information
st.sidebar.markdown("---")
st.sidebar.info("**Note:** This model predicts yield for Wheat cultivation in India for the year 2023.")

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Summary")
    st.metric("Rainfall", f"{rainfall:.1f} mm/year")
    st.metric("Temperature", f"{temperature:.1f} °C")
    st.metric("Pesticides", f"{pesticides:.1f} tonnes")

with col2:
    st.subheader("Prediction")
    if st.button("🔮 Predict Yield", use_container_width=True):
        try:
            # Create feature dictionary with all expected features
            feature_dict = {name: 0.0 for name in model.feature_names_in_}
            
            # Set the input values
            feature_dict['Year'] = 2023
            feature_dict['average_rain_fall_mm_per_year'] = rainfall
            feature_dict['pesticides_tonnes'] = pesticides
            feature_dict['avg_temp'] = temperature
            
            # Set default Area and Item
            feature_dict['Area_India'] = 1.0
            feature_dict['Item_Wheat'] = 1.0
            
            # Create DataFrame and predict
            features = pd.DataFrame([feature_dict])
            prediction = model.predict(features)
            
            # Display result
            st.success(f"### Predicted Crop Yield: {prediction[0]:,.0f} hg/ha")
            
        except Exception as e:
            st.error(f"Error during prediction: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    **About this app:**
    - Uses a RandomForestRegressor model trained on agricultural data
    - Currently configured for Wheat cultivation in India
    - Considers rainfall, temperature, and pesticide usage
    """
)
