import streamlit as st
import joblib
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
from PIL import Image
try:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration, WebRtcMode
except ImportError:
    webrtc_streamer = None

# ========== Model Loading ==========
@st.cache_resource
def load_model():
    """Load the pre-trained crop yield model."""
    try:
        model = joblib.load("crop_yield_model.pkl")
        return model
    except FileNotFoundError:
        st.error("❌ Model file 'crop_yield_model.pkl' not found!")
        return None

model = load_model()

if model is None:
    st.stop()

# Hardcoded feature names in case of loading issues
hardcoded_features = [
    'Year', 'average_rain_fall_mm_per_year', 'pesticides_tonnes', 'avg_temp',
    'Area_Algeria', 'Area_Angola', 'Area_Argentina', 'Area_Armenia', 'Area_Australia', 'Area_Austria',
    'Area_Azerbaijan', 'Area_Bahamas', 'Area_Bahrain', 'Area_Bangladesh', 'Area_Belarus', 'Area_Belgium',
    'Area_Botswana', 'Area_Brazil', 'Area_Bulgaria', 'Area_Burkina Faso', 'Area_Burundi', 'Area_Cameroon',
    'Area_Canada', 'Area_Central African Republic', 'Area_Chile', 'Area_Colombia', 'Area_Croatia', 'Area_Denmark',
    'Area_Dominican Republic', 'Area_Ecuador', 'Area_Egypt', 'Area_El Salvador', 'Area_Eritrea', 'Area_Estonia',
    'Area_Finland', 'Area_France', 'Area_Germany', 'Area_Ghana', 'Area_Greece', 'Area_Guatemala', 'Area_Guinea',
    'Area_Guyana', 'Area_Haiti', 'Area_Honduras', 'Area_Hungary', 'Area_India', 'Area_Indonesia', 'Area_Iraq',
    'Area_Ireland', 'Area_Italy', 'Area_Jamaica', 'Area_Japan', 'Area_Kazakhstan', 'Area_Kenya', 'Area_Latvia',
    'Area_Lebanon', 'Area_Lesotho', 'Area_Libya', 'Area_Lithuania', 'Area_Madagascar', 'Area_Malawi', 'Area_Malaysia',
    'Area_Mali', 'Area_Mauritania', 'Area_Mauritius', 'Area_Mexico', 'Area_Montenegro', 'Area_Morocco', 'Area_Mozambique',
    'Area_Namibia', 'Area_Nepal', 'Area_Netherlands', 'Area_New Zealand', 'Area_Nicaragua', 'Area_Niger', 'Area_Norway',
    'Area_Pakistan', 'Area_Papua New Guinea', 'Area_Peru', 'Area_Poland', 'Area_Portugal', 'Area_Qatar', 'Area_Romania',
    'Area_Rwanda', 'Area_Saudi Arabia', 'Area_Senegal', 'Area_Slovenia', 'Area_South Africa', 'Area_Spain', 'Area_Sri Lanka',
    'Area_Sudan', 'Area_Suriname', 'Area_Sweden', 'Area_Switzerland', 'Area_Tajikistan', 'Area_Thailand', 'Area_Tunisia',
    'Area_Turkey', 'Area_Uganda', 'Area_Ukraine', 'Area_United Kingdom', 'Area_Uruguay', 'Area_Zambia', 'Area_Zimbabwe',
    'Item_Maize', 'Item_Plantains and others', 'Item_Potatoes', 'Item_Rice, paddy', 'Item_Sorghum', 'Item_Soybeans',
    'Item_Sweet potatoes', 'Item_Wheat', 'Item_Yams'
]

# Use model's feature names if available, else hardcoded
if hasattr(model, 'feature_names_in_'):
    all_features = list(model.feature_names_in_)
else:
    all_features = hardcoded_features

# Extract available areas and items from model features
areas = sorted([f.replace("Area_", "") for f in all_features if f.startswith("Area_")])
items = sorted([f.replace("Item_", "") for f in all_features if f.startswith("Item_")])

# ========== Helper Functions ==========
def predict_yield(rainfall, temperature, pesticides, year, area, item):
    """Predict crop yield for given parameters."""
    try:
        feature_dict = {name: 0.0 for name in all_features}
        feature_dict['Year'] = year
        feature_dict['average_rain_fall_mm_per_year'] = rainfall
        feature_dict['pesticides_tonnes'] = pesticides
        feature_dict['avg_temp'] = temperature
        feature_dict[f'Area_{area}'] = 1.0
        feature_dict[f'Item_{item}'] = 1.0
        
        features = pd.DataFrame([feature_dict])
        prediction = model.predict(features)[0]
        return prediction
    except Exception as e:
        return None

def validate_inputs(rainfall, temperature, pesticides):
    """Validate input parameters."""
    errors = []
    if rainfall < 0 or rainfall > 10000:
        errors.append("Rainfall should be between 0 and 10000 mm/year")
    if temperature < -50 or temperature > 60:
        errors.append("Temperature should be between -50 and 60°C")
    if pesticides < 0 or pesticides > 1000:
        errors.append("Pesticides should be between 0 and 1000 tonnes")
    return errors

# ========== DataFrame Utilities ==========
def merge_duplicate_columns(df):
    """Merge columns with duplicate names by taking the first non-null value."""
    if not df.columns.duplicated().any():
        return df

    merged_df = pd.DataFrame()
    for col in pd.unique(df.columns):
        duplicates = df.loc[:, df.columns == col]
        if duplicates.shape[1] == 1:
            merged_df[col] = duplicates.iloc[:, 0]
        else:
            merged_df[col] = duplicates.bfill(axis=1).iloc[:, 0]
    return merged_df

# ========== Unit Conversion Functions ==========
def hectares_to_acres(hectares):
    """Convert hectares to acres."""
    return hectares * 2.471

def acres_to_hectares(acres):
    """Convert acres to hectares."""
    return acres / 2.471

def hg_per_hectare_to_lbs_per_acre(hg_ha):
    """Convert hg/ha to lbs/acre."""
    # 1 hg = 0.0220462 lbs, 1 hectare = 2.471 acres
    return (hg_ha * 0.0220462) / 2.471

def hg_per_hectare_to_tons_per_acre(hg_ha):
    """Convert hg/ha to short tons/acre."""
    # 1 short ton = 2000 lbs
    lbs_per_acre = hg_per_hectare_to_lbs_per_acre(hg_ha)
    return lbs_per_acre / 2000

# ========== Crop Advisor Knowledge Base ==========
advisor_crops = sorted(set(items + [
    "Barley", "Cotton", "Tomatoes", "Sugarcane", "Coffee", "Cocoa",
    "Bananas", "Peanuts", "Sunflower", "Cassava", "Onion", "Pepper",
    "Lentils", "Chickpeas", "Oats", "Rye", "Sorghum"
]))

issue_categories = [
    "Pests/Diseases",
    "Water Stress",
    "Nutrient Deficiency",
    "Weed Pressure",
    "Weather Stress",
    "Soil Health",
    "Harvest & Storage",
    "Auto-detect from notes"
]

crop_issue_advice = {
    "Wheat": {
        "Pests/Diseases": "Wheat is prone to rust, aphids, and fusarium head blight. Implement crop rotation and use resistant varieties.",
        "Water Stress": "Maintain even soil moisture during tillering and heading. Irrigate during dry spells and mulch when possible.",
        "Nutrient Deficiency": "Wheat responds well to nitrogen and sulfur. Test soil and apply balanced NPK fertilizer.",
        "Weather Stress": "Protect wheat from late frost and heat during grain fill with appropriate planting dates.",
    },
    "Maize": {
        "Pests/Diseases": "Common pests include fall armyworm and borers. Scout regularly and consider biological controls.",
        "Water Stress": "Maize needs consistent rainfall from silking to grain fill. Irrigate early and deeply when dry.",
        "Nutrient Deficiency": "Maize requires high nitrogen and phosphorus. Use soil tests and split fertilizer applications.",
    },
    "Rice, paddy": {
        "Pests/Diseases": "Rice blast and planthoppers can reduce yields. Practice proper water management and resistant varieties.",
        "Water Stress": "Paddy fields need consistent water depth before heading. Avoid drought stress during flowering.",
        "Soil Health": "Maintain pH near 6-7 and add organic matter to improve flooded soil structure.",
    },
    "Potatoes": {
        "Pests/Diseases": "Late blight and tuber rot are major threats. Use clean seed potatoes and fungicide protection.",
        "Water Stress": "Keep soil evenly moist, especially during tuber bulking, but avoid waterlogging.",
    },
    "Soybeans": {
        "Pests/Diseases": "Soybean cyst nematode and sudden death syndrome can lower yields. Rotate with non-host crops.",
        "Nutrient Deficiency": "Soybeans benefit from phosphorus and potassium. Nodulation fixes nitrogen if soil is healthy.",
    },
    "Barley": {
        "Pests/Diseases": "Net blotch and powdery mildew are common. Use certified seed and manage residue.",
        "Water Stress": "Barley is sensitive to drought during flowering. Schedule irrigation carefully.",
    },
    "Tomatoes": {
        "Pests/Diseases": "Tomato blight and nematodes can cause severe damage. Ensure good air circulation and rotate crops.",
        "Nutrient Deficiency": "Tomatoes need calcium to prevent blossom end rot. Apply balanced fertilizer and irrigate consistently.",
    },
    "Sugarcane": {
        "Pests/Diseases": "Ratoon stunting disease and borers are key issues. Use clean planting material and maintain healthy soil.",
        "Water Stress": "Sugarcane requires high water at early growth stages. Provide consistent irrigation where possible.",
    },
}

generic_issue_advice = {
    "Pests/Diseases": "Inspect crops weekly for pests and disease symptoms, rotate crops annually, and use resistant varieties when available.",
    "Water Stress": "Monitor soil moisture and adjust irrigation schedules. Avoid both drought and waterlogging.",
    "Nutrient Deficiency": "Soil test before fertilization and apply balanced nutrients based on crop needs.",
    "Weed Pressure": "Use mulches, cover crops, and timely weeding to reduce competition.",
    "Weather Stress": "Match planting time to climate conditions and protect against extreme heat or frost.",
    "Soil Health": "Add organic matter, avoid compaction, and maintain proper pH for healthy root growth.",
    "Harvest & Storage": "Harvest at the right maturity and store in cool, dry conditions to prevent spoilage.",
}

issue_keywords = {
    "drought": "Water Stress",
    "dry": "Water Stress",
    "wet": "Weather Stress",
    "heat": "Weather Stress",
    "cold": "Weather Stress",
    "yellow": "Nutrient Deficiency",
    "necrosis": "Nutrient Deficiency",
    "pest": "Pests/Diseases",
    "disease": "Pests/Diseases",
    "weed": "Weed Pressure",
    "salinity": "Soil Health",
    "compaction": "Soil Health",
    "rot": "Pests/Diseases",
    "blight": "Pests/Diseases",
}

def infer_issue_type(text):
    lower = text.lower()
    for keyword, issue in issue_keywords.items():
        if keyword in lower:
            return issue
    return None


def get_crop_advice(crop, issue_type, region=None, notes=None):
    crop = crop.title()
    if issue_type == "Auto-detect from notes" and notes:
        detected = infer_issue_type(notes)
        if detected:
            issue_type = detected
        else:
            issue_type = "Pests/Diseases"

    advice = crop_issue_advice.get(crop, {})
    if issue_type in advice:
        text = advice[issue_type]
    else:
        text = generic_issue_advice.get(issue_type, "Review crop health and consult local extension services for more detail.")

    if region:
        text += f" Local conditions in {region.title()} may affect the issue. Consider region-specific resistant varieties and management practices."
    return text

# Page configuration
st.set_page_config(
    page_title="Crop Yield Prediction", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Background slideshow for the app
slideshow_images = [
    "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=1350&q=80",  # wheat field
    "https://images.unsplash.com/photo-1601678065305-e6b45d7d8035?auto=format&fit=crop&w=1350&q=80",  # corn field
    "https://images.unsplash.com/photo-1446975921530-4cfa66fc05d3?auto=format&fit=crop&w=1350&q=80",  # wheat plantation
    "https://images.unsplash.com/photo-1451187330695-3c0e96824387?auto=format&fit=crop&w=1350&q=80"   # corn plantation
]

background_css = f"""
<style>
body {{
    background-color: #0c2d0c;
}}
[data-testid="stAppViewContainer"] {{
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    animation: slideshow 40s infinite;
}}

@keyframes slideshow {{
    0% {{background-image: url('{slideshow_images[0]}');}}
    25% {{background-image: url('{slideshow_images[1]}');}}
    50% {{background-image: url('{slideshow_images[2]}');}}
    75% {{background-image: url('{slideshow_images[3]}');}}
    100% {{background-image: url('{slideshow_images[0]}');}}
}}

[data-testid="stAppViewContainer"]::before {{
    content: "";
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.25);
    pointer-events: none;
}}

.css-1outpf7, .css-18e3th9, .css-k1vhr4 {{
    background: rgba(255, 255, 255, 0.85) !important;
}}
</style>
"""

st.markdown(background_css, unsafe_allow_html=True)

# Title and description
st.title("Crop Yield Prediction App")
st.write("Advanced crop yield prediction using machine learning and environmental data analysis.")

# Sidebar for common inputs
st.sidebar.header("⚙️ Common Parameters")
year = st.sidebar.slider(
    "Year",
    min_value=1990,
    max_value=2040,
    value=2025,
    help="Year for prediction (historical and future projections)"
)

# Unit selection
st.sidebar.markdown("---")
st.sidebar.header("Unit Settings")
yield_unit = st.sidebar.radio(
    "Yield Output Unit:",
    options=["hg/ha (Hectogram/Hectare)", "lbs/acre (Pounds/Acre)", "tons/acre (Short Tons/Acre)"],
    help="Choose your preferred unit for yield predictions"
)

st.sidebar.caption("Choose the output yield unit used throughout the app.")

# Create tabs for different features
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Single Prediction", "Sensitivity Analysis", "Batch Predictions", "Trends & Comparison", "Image Analysis", "Voice Input", "Crop Advisor"]
)

# ========== TAB 1: SINGLE PREDICTION ==========
with tab1:
    st.subheader("Single Crop Yield Prediction")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Environmental Factors**")
        rainfall = st.number_input(
            "Rainfall (mm/year)", 
            value=1000.0, 
            min_value=0.0,
            max_value=10000.0,
            step=100.0,
            help="Annual rainfall in millimeters"
        )
        temperature = st.number_input(
            "Temperature (°C)", 
            value=25.0,
            min_value=-50.0,
            max_value=60.0,
            step=1.0,
            help="Average annual temperature in Celsius"
        )
        pesticides = st.number_input(
            "Pesticides (tonnes)", 
            value=10.0,
            min_value=0.0,
            max_value=1000.0,
            step=5.0,
            help="Amount of pesticides used in tonnes"
        )
    
    with col2:
        st.write("**Location**")
        selected_area = st.selectbox(
            "Country/Region",
            options=areas,
            index=areas.index("India") if "India" in areas else 0,
            help="Select the country or region"
        )
    
    with col3:
        st.write("**Crop Type**")
        selected_item = st.selectbox(
            "Crop Type",
            options=items,
            index=items.index("Wheat") if "Wheat" in items else 0,
            help="Select the crop type"
        )
    
    # Validate inputs
    errors = validate_inputs(rainfall, temperature, pesticides)
    
    if errors:
        for error in errors:
            st.warning(error)
    
    # Predict button
    if st.button("Predict Yield", width='stretch', type="primary"):
        with st.spinner("Predicting yield..."):
            yield_pred = predict_yield(rainfall, temperature, pesticides, year, selected_area, selected_item)
        
        if yield_pred is not None:
            # Convert yield based on selected unit
            if yield_unit == "lbs/acre (Pounds/Acre)":
                converted_yield = hg_per_hectare_to_lbs_per_acre(yield_pred)
                unit_display = "lbs/acre"
            elif yield_unit == "tons/acre (Short Tons/Acre)":
                converted_yield = hg_per_hectare_to_tons_per_acre(yield_pred)
                unit_display = "tons/acre"
            else:
                converted_yield = yield_pred
                unit_display = "hg/ha"
            
            # Display result with formatting
            col_result1, col_result2 = st.columns([1, 1])
            
            with col_result1:
                st.metric(
                    "Predicted Crop Yield",
                    f"{converted_yield:,.2f} {unit_display}",
                    delta=None
                )
            
            with col_result2:
                st.info(f"""
                Prediction Details:
                - Crop: {selected_item}
                - Location: {selected_area}
                - Year: {year}
                - Conditions: {rainfall} mm rain, {temperature}°C, {pesticides} T pesticides
                - Unit: {unit_display}
                """)
            
            # Show conversion reference
            st.divider()
            st.write("**Unit Conversion Reference:**")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                st.metric("In hg/ha", f"{yield_pred:,.2f}")
            with col_c2:
                st.metric("In lbs/acre", f"{hg_per_hectare_to_lbs_per_acre(yield_pred):,.2f}")
            with col_c3:
                st.metric("In tons/acre", f"{hg_per_hectare_to_tons_per_acre(yield_pred):,.4f}")
        else:
            st.error("❌ Error during prediction. Please check your inputs.")

# ========== TAB 2: SENSITIVITY ANALYSIS ==========
with tab2:
    st.subheader("Parameter Sensitivity Analysis")
    st.write("See how each parameter affects the crop yield prediction.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        base_rainfall = st.number_input("Base Rainfall (mm/year)", value=1000.0, min_value=0.0, max_value=10000.0, step=100.0)
        base_temperature = st.number_input("Base Temperature (°C)", value=25.0, min_value=-50.0, max_value=60.0, step=1.0)
        base_pesticides = st.number_input("Base Pesticides (tonnes)", value=10.0, min_value=0.0, max_value=1000.0, step=5.0)
    
    with col2:
        sens_area = st.selectbox("Country (Sensitivity)", options=areas, index=areas.index("India") if "India" in areas else 0, key="sens_area")
    
    with col3:
        sens_item = st.selectbox("Crop (Sensitivity)", options=items, index=items.index("Wheat") if "Wheat" in items else 0, key="sens_item")
    
    if st.button("Run Sensitivity Analysis", width='stretch', type="primary"):
        with st.spinner("Calculating sensitivity curves..."):
            # Calculate sensitivity for different parameters
            rainfall_range = np.linspace(0, 3000, 20)
            temp_range = np.linspace(5, 45, 20)
            pesticide_range = np.linspace(0, 100, 20)
            
            # Rainfall sensitivity
            rainfall_yields = [
                predict_yield(r, base_temperature, base_pesticides, year, sens_area, sens_item)
                for r in rainfall_range
            ]
            
            # Temperature sensitivity
            temp_yields = [
                predict_yield(base_rainfall, t, base_pesticides, year, sens_area, sens_item)
                for t in temp_range
            ]
            
            # Pesticide sensitivity
            pesticide_yields = [
                predict_yield(base_rainfall, base_temperature, p, year, sens_area, sens_item)
                for p in pesticide_range
            ]
        
        # Create visualizations
        # Apply unit conversion
        if yield_unit == "lbs/acre (Pounds/Acre)":
            rainfall_yields_converted = [hg_per_hectare_to_lbs_per_acre(y) for y in rainfall_yields]
            temp_yields_converted = [hg_per_hectare_to_lbs_per_acre(y) for y in temp_yields]
            pesticide_yields_converted = [hg_per_hectare_to_lbs_per_acre(y) for y in pesticide_yields]
            unit_label = "lbs/acre"
        elif yield_unit == "tons/acre (Short Tons/Acre)":
            rainfall_yields_converted = [hg_per_hectare_to_tons_per_acre(y) for y in rainfall_yields]
            temp_yields_converted = [hg_per_hectare_to_tons_per_acre(y) for y in temp_yields]
            pesticide_yields_converted = [hg_per_hectare_to_tons_per_acre(y) for y in pesticide_yields]
            unit_label = "tons/acre"
        else:
            rainfall_yields_converted = rainfall_yields
            temp_yields_converted = temp_yields
            pesticide_yields_converted = pesticide_yields
            unit_label = "hg/ha"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_rain = go.Figure()
            fig_rain.add_trace(go.Scatter(x=rainfall_range, y=rainfall_yields_converted, mode='lines+markers', name='Rainfall effect'))
            fig_rain.update_layout(
                title="Rainfall Impact on Yield",
                xaxis_title="Rainfall (mm/year)",
                yaxis_title=f"Yield ({unit_label})",
                hovermode='x unified'
            )
            st.plotly_chart(fig_rain, width='stretch')
        
        with col2:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(x=temp_range, y=temp_yields_converted, mode='lines+markers', name='Temperature effect'))
            fig_temp.update_layout(
                title="Temperature Impact on Yield",
                xaxis_title="Temperature (°C)",
                yaxis_title=f"Yield ({unit_label})",
                hovermode='x unified'
            )
            st.plotly_chart(fig_temp, width='stretch')
        
        with col3:
            fig_pest = go.Figure()
            fig_pest.add_trace(go.Scatter(x=pesticide_range, y=pesticide_yields_converted, mode='lines+markers', name='Pesticide effect'))
            fig_pest.update_layout(
                title="Pesticide Impact on Yield",
                xaxis_title="Pesticides (tonnes)",
                yaxis_title=f"Yield ({unit_label})",
                hovermode='x unified'
            )
            st.plotly_chart(fig_pest, width='stretch')

# ========== TAB 3: BATCH PREDICTIONS ==========
with tab3:
    st.subheader("Batch Predictions from CSV")
    st.write("Upload a CSV file with columns: `Rainfall`, `Temperature`, `Pesticides`, `Area`, `Item`")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            df = merge_duplicate_columns(df)
            
            # Validate required columns
            required_cols = ['Rainfall', 'Temperature', 'Pesticides', 'Area', 'Item']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing columns: {', '.join(missing_cols)}")
            else:
                st.write(f"Loaded {len(df)} rows. Processing predictions...")
                
                # Add predictions
                predictions = []
                with st.spinner("Running batch predictions..."):
                    for idx, row in df.iterrows():
                        pred = predict_yield(
                            row['Rainfall'],
                            row['Temperature'],
                            row['Pesticides'],
                            year,
                            row['Area'],
                            row['Item']
                        )
                        predictions.append(pred)
                
                df['Predicted_Yield_hg_ha'] = predictions
                
                # Add unit-converted columns
                df['Predicted_Yield_lbs_acre'] = df['Predicted_Yield_hg_ha'].apply(hg_per_hectare_to_lbs_per_acre)
                df['Predicted_Yield_tons_acre'] = df['Predicted_Yield_hg_ha'].apply(hg_per_hectare_to_tons_per_acre)
                
                st.write("**Predictions with All Unit Conversions:**")
                st.dataframe(df, width='stretch')
                
                # Download button - let user choose format
                st.write("**Download Results:**")
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    # Full data with all units
                    csv_buffer = BytesIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    
                    st.download_button(
                        label="Download (All Units)",
                        data=csv_buffer,
                        file_name="crop_yield_predictions_all_units.csv",
                        mime="text/csv",
                        width='stretch'
                    )
                
                with col_dl2:
                    # Simplified data with selected unit
                    df_download = df.copy()
                    if yield_unit == "lbs/acre (Pounds/Acre)":
                        df_download = df_download[['Rainfall', 'Temperature', 'Pesticides', 'Area', 'Item', 'Predicted_Yield_lbs_acre']]
                        df_download = df_download.rename(columns={'Predicted_Yield_lbs_acre': 'Predicted_Yield'})
                        filename = "crop_yield_predictions_lbs_acre.csv"
                    elif yield_unit == "tons/acre (Short Tons/Acre)":
                        df_download = df_download[['Rainfall', 'Temperature', 'Pesticides', 'Area', 'Item', 'Predicted_Yield_tons_acre']]
                        df_download = df_download.rename(columns={'Predicted_Yield_tons_acre': 'Predicted_Yield'})
                        filename = "crop_yield_predictions_tons_acre.csv"
                    else:
                        df_download = df_download[['Rainfall', 'Temperature', 'Pesticides', 'Area', 'Item', 'Predicted_Yield_hg_ha']]
                        df_download = df_download.rename(columns={'Predicted_Yield_hg_ha': 'Predicted_Yield'})
                        filename = "crop_yield_predictions_hg_ha.csv"
                    
                    csv_buffer2 = BytesIO()
                    df_download.to_csv(csv_buffer2, index=False)
                    csv_buffer2.seek(0)
                    
                    st.download_button(
                        label=f"Download ({yield_unit.split('(')[1].rstrip(')')})",
                        data=csv_buffer2,
                        file_name=filename,
                        mime="text/csv",
                        width='stretch'
                )
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")

# ========== TAB 4: TRENDS & COMPARISON ==========
with tab4:
    st.subheader("Multi-Scenario Trends & Comparison")
    st.write("Compare predictions across different years, regions, or crops.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        comparison_type = st.radio(
            "Compare across:",
            options=["Years", "Countries", "Crops"],
            horizontal=True
        )
    
    with col2:
        st.write("**Base Parameters**")
        comp_rainfall = st.number_input("Rainfall (mm/year)##comp", value=1000.0, min_value=0.0, max_value=10000.0, step=100.0)
        comp_temp = st.number_input("Temperature (°C)##comp", value=25.0, min_value=-50.0, max_value=60.0, step=1.0)
        comp_pesticides = st.number_input("Pesticides (tonnes)##comp", value=10.0, min_value=0.0, max_value=1000.0, step=5.0)
    
    if st.button("Generate Comparison Chart", width='stretch', type="primary"):
        results = []
        
        if comparison_type == "Years":
            comp_area = st.selectbox("Select Country", options=areas, key="comp_area1")
            comp_item = st.selectbox("Select Crop", options=items, key="comp_item1")
            
            for y in range(2000, 2041, 5):
                yield_val = predict_yield(comp_rainfall, comp_temp, comp_pesticides, y, comp_area, comp_item)
                results.append({"Year": y, "Yield": yield_val, "Category": comp_area})
        
        elif comparison_type == "Countries":
            comp_item_c = st.selectbox("Select Crop", options=items, key="comp_item2")
            selected_countries = st.multiselect("Select Countries", options=areas, default=[areas[0], areas[10], areas[20]], max_selections=5)
            
            for country in selected_countries:
                yield_val = predict_yield(comp_rainfall, comp_temp, comp_pesticides, year, country, comp_item_c)
                results.append({"Country": country, "Yield": yield_val, "Category": comp_item_c})
        
        else:  # Crops
            comp_area_c = st.selectbox("Select Country", options=areas, key="comp_area2")
            
            for crop in items:
                yield_val = predict_yield(comp_rainfall, comp_temp, comp_pesticides, year, comp_area_c, crop)
                results.append({"Crop": crop, "Yield": yield_val, "Category": comp_area_c})
        
        if results:
            results_df = pd.DataFrame(results)
            results_df = results_df.loc[:, ~results_df.columns.duplicated()]
            
            # Apply unit conversion
            if yield_unit == "lbs/acre (Pounds/Acre)":
                results_df["Yield_Converted"] = results_df["Yield"].apply(hg_per_hectare_to_lbs_per_acre)
                unit_label = "lbs/acre"
            elif yield_unit == "tons/acre (Short Tons/Acre)":
                results_df["Yield_Converted"] = results_df["Yield"].apply(hg_per_hectare_to_tons_per_acre)
                unit_label = "tons/acre"
            else:
                results_df["Yield_Converted"] = results_df["Yield"]
                unit_label = "hg/ha"
            
            if comparison_type == "Years":
                fig = px.line(results_df, x="Year", y="Yield_Converted", markers=True, title=f"Yield Trend: {comp_area} - {comp_item} ({unit_label})")
            elif comparison_type == "Countries":
                fig = px.bar(results_df, x="Country", y="Yield_Converted", title=f"Yield by Country: {comp_item_c} ({unit_label})")
            else:
                fig = px.bar(results_df, x="Crop", y="Yield_Converted", title=f"Yield by Crop: {comp_area_c} ({unit_label})")
            
            fig.update_yaxes(title_text=f"Yield ({unit_label})")
            st.plotly_chart(fig, width='stretch')
            
            # Show statistics with both original and converted values
            st.write("**Results (with unit conversion):**")
            display_df = results_df.copy()
            target_name = f"Yield ({unit_label})"
            if target_name in display_df.columns:
                display_df[target_name] = display_df["Yield_Converted"]
                if "Yield" in display_df.columns:
                    display_df = display_df.drop(columns=["Yield"])
            else:
                display_df = display_df.rename(columns={
                    "Yield": "Yield (hg/ha)",
                    "Yield_Converted": target_name
                })
            display_df = display_df.loc[:, ~display_df.columns.duplicated()]
            st.dataframe(display_df, width='stretch')

# ========== TAB 5: IMAGE ANALYSIS ==========
with tab5:
    st.subheader("Crop Image Analysis")
    st.write("Upload an image of your crop field for visual analysis.")
    
    uploaded_image = st.file_uploader("Choose a crop image", type=["jpg", "jpeg", "png", "bmp", "gif"])
    
    if uploaded_image is not None:
        # Display image
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Crop Image", width='stretch')
        
        # Image information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Image Size", f"{image.size[0]}×{image.size[1]} px")
        with col2:
            st.metric("Format", image.format or "Unknown")
        with col3:
            st.metric("File Size", f"{uploaded_image.size / 1024:.1f} KB")
        
        st.divider()
        
        # Provide prediction inputs based on visual assessment
        st.write("**Assess Your Crop Visually and Make Predictions**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            crop_health = st.radio("Crop Health Assessment", ["Excellent", "Good", "Fair", "Poor"])
            pest_presence = st.checkbox("Pest/Disease Signs Visible")
        
        with col2:
            irrigation_status = st.radio("Irrigation Status", ["Well-watered", "Moderate", "Dry"])
            soil_quality = st.radio("Soil Quality", ["Rich/Dark", "Medium", "Poor/Light"])
        
        if st.button("Get Prediction Based on Visual Assessment", width='stretch', type="primary"):
            # Adjust parameters based on visual assessment
            visual_rainfall = 1500.0 if irrigation_status == "Well-watered" else (1000.0 if irrigation_status == "Moderate" else 500.0)
            visual_temp = 25.0
            visual_pesticides = 5.0 if pest_presence else 15.0
            
            vis_area = st.selectbox("Select Country for Prediction", options=areas, key="vis_area")
            vis_item = st.selectbox("Select Crop Type", options=items, key="vis_item")
            vis_year = st.selectbox("Select Year", options=range(2020, 2041), key="vis_year")
            
            prediction = predict_yield(visual_rainfall, visual_temp, visual_pesticides, vis_year, vis_area, vis_item)
            
            if prediction is not None:
                st.success(f"### Predicted Yield: {prediction:,.0f} hg/ha")
                st.info(f"""
                **Assessment Summary:**
                - Health: {crop_health}
                - Pest Presence: {'Yes' if pest_presence else 'No'}
                - Irrigation: {irrigation_status}
                - Soil Quality: {soil_quality}
                - Estimated Rainfall: {visual_rainfall} mm/year
                """)
    else:
        st.info("Upload a crop image to begin analysis")

# ========== TAB 6: VOICE INPUT ==========
with tab6:
    st.subheader("Voice-Controlled Prediction")
    st.write("Use microphone input to control the prediction system (text-based voice simulation).")
    
    voice_option = st.radio("Select Input Method", ["Manual Voice Simulation", "Microphone Stream"])
    
    if voice_option == "Manual Voice Simulation":
        st.info("This simulates voice input through text. Type your prediction request:")
        st.caption("Example: Predict wheat yield in India for 2025 with 1000mm rain, 25°C, 10 tonnes pesticides")
        voice_input = st.text_area(
            "Voice Input (Simulated)",
            placeholder="Example: Predict wheat yield in India for 2025 with 1000mm rainfall, 25 degrees temperature, and 10 tonnes pesticides",
            height=100
        )
        
        if st.button("Process Voice Command", width='stretch', type="primary"):
            if voice_input:
                st.write("**Parsing Voice Command...**")
                
                # Simple parsing (in production, use NLP)
                try:
                    # Default values
                    voice_rainfall = 1000.0
                    voice_temp = 25.0
                    voice_pesticides = 10.0
                    voice_country = "India"
                    voice_crop = "Wheat"
                    voice_year = 2025
                    
                    # Try to extract numbers
                    import re
                    numbers = re.findall(r'\d+(?:\.\d+)?', voice_input)
                    
                    if len(numbers) >= 1:
                        voice_rainfall = min(float(numbers[0]), 10000.0)
                    if len(numbers) >= 2:
                        voice_temp = min(float(numbers[1]), 60.0)
                    if len(numbers) >= 3:
                        voice_pesticides = min(float(numbers[2]), 1000.0)
                    # Find a year between 1900 and 2100 if present
                    if len(numbers) >= 1:
                        for num in numbers:
                            year_candidate = float(num)
                            if 1900 <= year_candidate <= 2100:
                                voice_year = int(year_candidate)
                                break
                    
                    # Check for country/crop names
                    voice_input_lower = voice_input.lower()
                    for area in areas:
                        if area.lower() in voice_input_lower:
                            voice_country = area
                            break
                    
                    for item in items:
                        if item.lower() in voice_input_lower:
                            voice_crop = item
                            break
                    
                    st.success("Command parsed successfully!")
                    
                    # Display parsed values
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rainfall", f"{voice_rainfall:.0f} mm/year")
                    with col2:
                        st.metric("Temperature", f"{voice_temp:.1f}°C")
                    with col3:
                        st.metric("Pesticides", f"{voice_pesticides:.1f} tonnes")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Country", voice_country)
                    with col2:
                        st.metric("Crop", voice_crop)
                    with col3:
                        st.metric("Year", str(voice_year))
                    
                    # Make prediction
                    voice_prediction = predict_yield(voice_rainfall, voice_temp, voice_pesticides, voice_year, voice_country, voice_crop)
                    
                    if voice_prediction is not None:
                        st.success(f"### Yield Prediction: {voice_prediction:,.0f} hg/ha")
                        st.balloons()
                
                except Exception as e:
                    st.error(f"❌ Error parsing command: {str(e)}")
            else:
                st.warning("Please enter a voice command")
    
    else:  # Microphone Stream
        if webrtc_streamer is not None:
            st.info("Microphone features require additional runtime. Use 'Manual Voice Simulation' for text-based commands.")
            st.write("**Note:** For full microphone streaming in production, use streamlit-webrtc with proper browser support.")
        else:
            st.warning("Microphone streaming not yet available. Use text-based voice input above.")
    
    st.divider()
    st.write("**Voice Command Examples:**")
    st.code("""
Predict wheat yield in India for 2025 with 1000mm rain, 25°C, 10 tonnes pesticides
Get maize prediction for Brazil, 1500mm rainfall, 22 degrees, 15 tonnes pesticides
Calculate rice yield in Egypt, 800mm rain, 28 degrees, 8 tonnes pesticides
    """)

# ========== TAB 7: CROP ADVISOR ==========
with tab7:
    st.subheader("Crop Advisor Bot")
    st.write("Ask about crop issues, pests, diseases and growing conditions.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        advisor_crop = st.selectbox("Crop", options=advisor_crops, index=advisor_crops.index("Wheat") if "Wheat" in advisor_crops else 0)
        advisor_issue = st.selectbox("Problem Type", options=issue_categories)
    with col2:
        advisor_region = st.text_input("Region (optional)", help="Optional region for localized advice")
        advisor_notes = st.text_area("Describe the problem or symptoms", height=120, help="Add details such as yellow leaves, stunted growth, pests, etc.")
    
    if st.button("Get Crop Advice", width='stretch', type="primary"):
        with st.spinner("Analyzing crop issue..."):
            advice_text = get_crop_advice(advisor_crop, advisor_issue, advisor_region, advisor_notes)
        
        st.success("Advice generated")
        st.write(f"**Crop:** {advisor_crop}")
        st.write(f"**Issue Type:** {advisor_issue}")
        if advisor_region:
            st.write(f"**Region:** {advisor_region.title()}")
        if advisor_notes:
            st.write("**Symptoms:**")
            st.write(advisor_notes)
        st.markdown("---")
        st.write(advice_text)
        
        if advisor_crop in items:
            st.info("This crop is also supported by the yield prediction model. Use the Single Prediction tab for yield estimates.")
        else:
            st.info("This crop is advisory-only; yield prediction is not available for this crop in the current model.")

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.markdown(f"""
    **Model Information:**
    - Algorithm: RandomForest Regressor
    - Features: 113
    - Supported Countries: {len(areas)}
    """)

with col_footer2:
    st.markdown(f"""
    **Coverage:**
    - Countries: {len(areas)}
    - Crop Types: {len(items)}
    - Year Range: 1990-2040
    """)

with col_footer3:
    st.markdown("""
    **Tips:**
    - Use Sensitivity Analysis to understand parameter impacts
    - Upload batch CSV for multiple predictions
    - Compare trends across different scenarios
    """)
