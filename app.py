import streamlit as st
import joblib
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
from PIL import Image
import time
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

# ========== Enhanced Crop Advisor Knowledge Base ==========
advisor_crops = sorted(set(items + [
    "Barley", "Cotton", "Tomatoes", "Sugarcane", "Coffee", "Cocoa",
    "Bananas", "Peanuts", "Sunflower", "Cassava", "Onion", "Pepper",
    "Lentils", "Chickpeas", "Oats", "Rye", "Sorghum", "Millet",
    "Groundnuts", "Sesame", "Tea", "Rubber", "Coconut", "Palm Oil",
    "Citrus", "Apples", "Grapes", "Mangoes", "Pineapple", "Avocado",
    "Carrots", "Cabbage", "Lettuce", "Spinach", "Broccoli", "Cauliflower",
    "Eggplant", "Cucumber", "Squash", "Melon", "Strawberries", "Blueberries"
]))

issue_categories = [
    "Pests/Diseases",
    "Water Stress",
    "Nutrient Deficiency",
    "Weed Pressure",
    "Weather Stress",
    "Soil Health",
    "Harvest & Storage",
    "Growth Issues",
    "Pest Management",
    "Disease Prevention",
    "Nutrient Management",
    "Irrigation Problems",
    "Climate Adaptation",
    "Auto-detect from notes"
]

severity_levels = {
    "Critical": "Immediate action required - potential crop loss",
    "High": "Urgent attention needed - significant yield impact",
    "Medium": "Monitor closely - moderate impact possible",
    "Low": "Minor issue - watch for progression"
}

# Enhanced crop knowledge base with detailed advice
crop_issue_advice = {
    "Wheat": {
        "Pests/Diseases": {
            "symptoms": ["yellow stripes on leaves", "black sooty mold", "white powdery coating", "brown spots"],
            "causes": ["Aphids", "Rust fungi", "Powdery mildew", "Septoria leaf blotch"],
            "severity": "High",
            "treatment": "Apply systemic insecticides for aphids. Use fungicides for rust and mildew. Rotate crops annually.",
            "prevention": "Plant resistant varieties, maintain field sanitation, avoid overhead irrigation."
        },
        "Water Stress": {
            "symptoms": ["wilting leaves", "stunted growth", "premature ripening", "reduced grain fill"],
            "causes": ["Drought", "Poor irrigation timing", "Shallow root penetration"],
            "severity": "Critical",
            "treatment": "Irrigate immediately during critical growth stages (tillering, heading, grain fill). Apply mulch to conserve moisture.",
            "prevention": "Monitor soil moisture regularly, use drip irrigation, improve soil structure for better water retention."
        },
        "Nutrient Deficiency": {
            "symptoms": ["yellow leaves", "purple stems", "stunted growth", "poor grain development"],
            "causes": ["Nitrogen deficiency", "Phosphorus deficiency", "Potassium deficiency", "Sulfur deficiency"],
            "severity": "High",
            "treatment": "Soil test first. Apply balanced NPK fertilizer. For nitrogen, use urea or ammonium nitrate. Monitor pH levels.",
            "prevention": "Regular soil testing, proper crop rotation, organic matter addition, balanced fertilization program."
        },
        "Weather Stress": {
            "symptoms": ["frost damage", "heat stress", "lodging", "shriveled grains"],
            "causes": ["Late spring frost", "Heat waves", "High winds", "Excessive rainfall"],
            "severity": "Critical",
            "treatment": "For frost: Use frost blankets or sprinkler irrigation. For heat: Provide shade, increase irrigation.",
            "prevention": "Choose appropriate planting dates, select heat-tolerant varieties, use windbreaks."
        }
    },
    "Maize": {
        "Pests/Diseases": {
            "symptoms": ["holes in leaves", "sawdust-like frass", "wilted plants", "ear rot"],
            "causes": ["Fall armyworm", "Corn borer", "Corn rootworm", "Fusarium ear rot"],
            "severity": "Critical",
            "treatment": "Use Bt maize varieties, apply biological controls, remove infected plants, use appropriate pesticides.",
            "prevention": "Crop rotation, field scouting, resistant varieties, proper field sanitation."
        },
        "Water Stress": {
            "symptoms": ["rolled leaves", "silk drying", "poor pollination", "small ears"],
            "causes": ["Drought during tasseling/silking", "Inconsistent irrigation", "Poor soil drainage"],
            "severity": "Critical",
            "treatment": "Irrigate during critical stages, ensure consistent moisture, improve drainage.",
            "prevention": "Use drought-tolerant varieties, monitor weather forecasts, implement irrigation scheduling."
        },
        "Nutrient Deficiency": {
            "symptoms": ["yellow striping", "purple coloration", "stunted growth", "poor root development"],
            "causes": ["Nitrogen deficiency", "Phosphorus deficiency", "Zinc deficiency", "Magnesium deficiency"],
            "severity": "High",
            "treatment": "Foliar applications for quick response, soil amendments, pH adjustment.",
            "prevention": "Soil testing, proper fertilization timing, organic matter management."
        }
    },
    "Rice, paddy": {
        "Pests/Diseases": {
            "symptoms": ["diamond-shaped lesions", "hopper burn", "stunted tillers", "grain discoloration"],
            "causes": ["Rice blast", "Brown planthopper", "Rice tungro virus", "Bacterial blight"],
            "severity": "Critical",
            "treatment": "Systemic fungicides for blast, insecticides for hoppers, remove alternate hosts.",
            "prevention": "Balanced fertilization, proper water management, resistant varieties, synchronous planting."
        },
        "Water Stress": {
            "symptoms": ["cracked soil", "stunted growth", "reduced tillering", "poor grain filling"],
            "causes": ["Inadequate flooding", "Uneven water distribution", "Poor field leveling"],
            "severity": "High",
            "treatment": "Maintain proper water depth (5-10cm), ensure uniform distribution, repair bunds.",
            "prevention": "Proper field preparation, efficient irrigation systems, water management planning."
        },
        "Soil Health": {
            "symptoms": ["nutrient imbalances", "poor drainage", "acidic/alkaline conditions", "compacted layers"],
            "causes": ["Continuous flooding", "Nutrient depletion", "Poor organic matter", "Iron toxicity"],
            "severity": "Medium",
            "treatment": "Lime application for acidity, organic matter addition, proper water management.",
            "prevention": "Crop rotation, green manuring, balanced fertilization, periodic soil testing."
        }
    },
    "Potatoes": {
        "Pests/Diseases": {
            "symptoms": ["dark water-soaked spots", "white fungal growth", "tuber rot", "yellowing leaves"],
            "causes": ["Late blight", "Early blight", "Potato virus Y", "Common scab"],
            "severity": "Critical",
            "treatment": "Fungicide applications, remove infected plants, proper seed treatment.",
            "prevention": "Certified seed potatoes, crop rotation, field sanitation, resistant varieties."
        },
        "Growth Issues": {
            "symptoms": ["small tubers", "green tubers", "cracked skin", "hollow heart"],
            "causes": ["Poor soil conditions", "Temperature stress", "Irrigation issues", "Varietal characteristics"],
            "severity": "Medium",
            "treatment": "Adjust irrigation, ensure proper hilling, temperature management.",
            "prevention": "Proper soil preparation, appropriate planting depth, variety selection."
        }
    },
    "Tomatoes": {
        "Pests/Diseases": {
            "symptoms": ["blossom end rot", "yellow leaves", "fruit cracking", "fungal spots"],
            "causes": ["Calcium deficiency", "Fusarium wilt", "Bacterial spot", "Tomato mosaic virus"],
            "severity": "High",
            "treatment": "Calcium sprays for BER, fungicides for diseases, remove infected plants.",
            "prevention": "Proper calcium management, resistant varieties, good air circulation, crop rotation."
        },
        "Nutrient Deficiency": {
            "symptoms": ["yellowing between veins", "purple stems", "small leaves", "poor fruit set"],
            "causes": ["Magnesium deficiency", "Phosphorus deficiency", "Potassium deficiency", "Iron deficiency"],
            "severity": "Medium",
            "treatment": "Foliar fertilization, soil amendments, pH correction.",
            "prevention": "Regular soil testing, balanced fertilization, organic matter addition."
        }
    },
    "Cotton": {
        "Pests/Diseases": {
            "symptoms": ["boll damage", "leaf curling", "square dropping", "fungal spots"],
            "causes": ["Bollworm", "Aphids", "Whitefly", "Bacterial blight"],
            "severity": "Critical",
            "treatment": "Integrated pest management, biological controls, selective pesticides.",
            "prevention": "Scouting programs, resistant varieties, proper field sanitation."
        },
        "Water Stress": {
            "symptoms": ["premature boll opening", "leaf wilting", "reduced fiber quality", "stunted growth"],
            "causes": ["Drought stress", "Poor irrigation scheduling", "High temperatures"],
            "severity": "High",
            "treatment": "Supplemental irrigation, mulching, shade provision.",
            "prevention": "Drought-tolerant varieties, efficient irrigation systems, soil moisture monitoring."
        }
    },
    "Sugarcane": {
        "Pests/Diseases": {
            "symptoms": ["stunted growth", "yellowing", "borer holes", "red rot"],
            "causes": ["Ratoon stunting disease", "Sugarcane borer", "Red rot", "Smuts"],
            "severity": "High",
            "treatment": "Hot water treatment of seed, systemic insecticides, fungicide applications.",
            "prevention": "Disease-free planting material, proper crop rotation, field sanitation."
        },
        "Nutrient Management": {
            "symptoms": ["chlorosis", "reduced tillering", "poor growth", "low sucrose content"],
            "causes": ["Imbalanced fertilization", "Soil nutrient depletion", "pH imbalances"],
            "severity": "Medium",
            "treatment": "Soil testing, balanced NPK application, micronutrient supplementation.",
            "prevention": "Regular soil analysis, proper manure application, crop residue management."
        }
    },
    "Soybeans": {
        "Pests/Diseases": {
            "symptoms": ["cyst formation", "sudden wilting", "leaf spots", "pod damage"],
            "causes": ["Soybean cyst nematode", "Sudden death syndrome", "Frogeye leaf spot", "Pod borers"],
            "severity": "High",
            "treatment": "Nematicides, fungicide applications, resistant varieties.",
            "prevention": "Crop rotation, soil testing, seed treatment, field scouting."
        },
        "Nutrient Deficiency": {
            "symptoms": ["yellowing leaves", "poor nodulation", "stunted growth", "low protein content"],
            "causes": ["Nitrogen fixation issues", "Phosphorus deficiency", "Iron deficiency"],
            "severity": "Medium",
            "treatment": "Inoculant application, phosphorus fertilizers, micronutrient sprays.",
            "prevention": "Proper inoculation, balanced fertilization, soil pH management."
        }
    }
}

# Enhanced generic advice for issues not crop-specific
generic_issue_advice = {
    "Pests/Diseases": {
        "description": "Pest and disease management requires integrated approaches",
        "immediate_actions": ["Identify the pest/disease correctly", "Isolate affected plants", "Remove severely infected material"],
        "treatment_options": ["Biological controls", "Cultural practices", "Chemical treatments when necessary"],
        "prevention": ["Crop rotation", "Resistant varieties", "Field sanitation", "Regular scouting"]
    },
    "Water Stress": {
        "description": "Water management is critical for crop health and yield",
        "immediate_actions": ["Check soil moisture levels", "Adjust irrigation schedules", "Mulch to conserve moisture"],
        "treatment_options": ["Supplemental irrigation", "Drought-tolerant varieties", "Soil moisture sensors"],
        "prevention": ["Proper irrigation planning", "Rainwater harvesting", "Soil water retention improvements"]
    },
    "Nutrient Deficiency": {
        "description": "Proper nutrition is essential for healthy crop development",
        "immediate_actions": ["Soil testing", "Foliar fertilization for quick response", "pH adjustment if needed"],
        "treatment_options": ["Balanced fertilizers", "Organic amendments", "Micronutrient applications"],
        "prevention": ["Regular soil testing", "Crop rotation", "Organic matter management"]
    },
    "Weed Pressure": {
        "description": "Weeds compete for resources and reduce yields significantly",
        "immediate_actions": ["Identify weed species", "Manual weeding for small areas", "Herbicide application"],
        "treatment_options": ["Pre-emergent herbicides", "Post-emergent treatments", "Mechanical control"],
        "prevention": ["Mulching", "Cover crops", "Proper crop spacing", "Crop rotation"]
    },
    "Weather Stress": {
        "description": "Extreme weather events can severely impact crop production",
        "immediate_actions": ["Protect vulnerable crops", "Adjust management practices", "Monitor weather forecasts"],
        "treatment_options": ["Shade structures", "Windbreaks", "Supplemental irrigation"],
        "prevention": ["Climate-appropriate varieties", "Seasonal planning", "Risk management strategies"]
    },
    "Soil Health": {
        "description": "Healthy soil is the foundation of successful agriculture",
        "immediate_actions": ["Soil testing", "Organic matter addition", "pH correction"],
        "treatment_options": ["Liming/acidification", "Compost application", "Cover cropping"],
        "prevention": ["Conservation tillage", "Crop rotation", "Erosion control", "Regular monitoring"]
    },
    "Harvest & Storage": {
        "description": "Proper harvesting and storage prevents post-harvest losses",
        "immediate_actions": ["Harvest at optimal maturity", "Handle gently", "Dry properly"],
        "treatment_options": ["Temperature control", "Humidity management", "Pest control in storage"],
        "prevention": ["Proper timing", "Clean storage facilities", "Regular inspection"]
    },
    "Growth Issues": {
        "description": "Various factors can affect normal crop development",
        "immediate_actions": ["Identify stress factors", "Adjust management", "Protect young plants"],
        "treatment_options": ["Nutrient adjustments", "Pest control", "Environmental modifications"],
        "prevention": ["Proper planting", "Variety selection", "Site preparation"]
    }
}

# Enhanced keyword detection with more patterns and context
issue_keywords = {
    # Water stress indicators
    "drought": "Water Stress",
    "dry": "Water Stress",
    "wilting": "Water Stress",
    "wilted": "Water Stress",
    "cracked soil": "Water Stress",
    "water stress": "Water Stress",
    "dehydration": "Water Stress",

    # Nutrient deficiencies
    "yellow": "Nutrient Deficiency",
    "yellowing": "Nutrient Deficiency",
    "chlorosis": "Nutrient Deficiency",
    "necrosis": "Nutrient Deficiency",
    "stunted": "Nutrient Deficiency",
    "stunting": "Nutrient Deficiency",
    "purple stems": "Nutrient Deficiency",
    "interveinal chlorosis": "Nutrient Deficiency",

    # Pests and diseases
    "pest": "Pests/Diseases",
    "disease": "Pests/Diseases",
    "infection": "Pests/Diseases",
    "infestation": "Pests/Diseases",
    "spots": "Pests/Diseases",
    "lesions": "Pests/Diseases",
    "mold": "Pests/Diseases",
    "fungus": "Pests/Diseases",
    "rot": "Pests/Diseases",
    "blight": "Pests/Diseases",
    "mildew": "Pests/Diseases",
    "rust": "Pests/Diseases",

    # Weed pressure
    "weed": "Weed Pressure",
    "weeds": "Weed Pressure",
    "competition": "Weed Pressure",

    # Weather stress
    "heat": "Weather Stress",
    "cold": "Weather Stress",
    "frost": "Weather Stress",
    "hail": "Weather Stress",
    "wind": "Weather Stress",
    "storm": "Weather Stress",

    # Soil health
    "salinity": "Soil Health",
    "saline": "Soil Health",
    "compaction": "Soil Health",
    "erosion": "Soil Health",
    "acidic": "Soil Health",
    "alkaline": "Soil Health",

    # Growth issues
    "slow growth": "Growth Issues",
    "poor germination": "Growth Issues",
    "seedling death": "Growth Issues",
    "abnormal growth": "Growth Issues"
}

# Symptom pattern matching for better auto-detection
symptom_patterns = {
    "Water Stress": [
        r"wilting|wilted|drooping|dry.*soil|cracked.*soil",
        r"rolled.*leaves|curled.*leaves|dry.*leaves",
        r"stunted.*growth|slow.*growth|poor.*growth"
    ],
    "Nutrient Deficiency": [
        r"yellow.*leaves|yellowing.*leaves|chlorotic",
        r"purple.*stems|red.*stems|discolored.*stems",
        r"interveinal.*chlorosis|vein.*chlorosis",
        r"stunted.*growth|small.*leaves|poor.*development"
    ],
    "Pests/Diseases": [
        r"holes.*leaves|chewed.*leaves|damaged.*leaves",
        r"spots.*leaves|lesions.*leaves|blotches",
        r"mold|mildew|fungus|rust|blight",
        r"borer.*holes|insect.*damage|pest.*damage"
    ]
}

def analyze_symptoms(text):
    """Advanced symptom analysis using pattern matching"""
    text_lower = text.lower()
    detected_issues = {}

    # Check keyword matches
    for keyword, issue in issue_keywords.items():
        if keyword in text_lower:
            detected_issues[issue] = detected_issues.get(issue, 0) + 1

    # Check pattern matches for more sophisticated detection
    for issue, patterns in symptom_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                detected_issues[issue] = detected_issues.get(issue, 0) + 2  # Weight patterns higher

    # Return the most likely issue
    if detected_issues:
        return max(detected_issues.items(), key=lambda x: x[1])[0]
    return None

def get_crop_advice(crop, issue_type, region=None, notes=None):
    """Enhanced crop advice function with detailed analysis"""
    crop = crop.title()

    # Auto-detect issue type from notes if requested
    if issue_type == "Auto-detect from notes" and notes:
        detected = analyze_symptoms(notes)
        if detected:
            issue_type = detected
        else:
            issue_type = "Pests/Diseases"  # Default fallback

    # Get crop-specific advice
    crop_advice = crop_issue_advice.get(crop, {})

    if issue_type in crop_advice:
        advice_data = crop_advice[issue_type]
        severity = advice_data.get("severity", "Medium")
        severity_desc = severity_levels.get(severity, "")

        response = f"""
### **{issue_type} in {crop}**

**Severity Level:** {severity} - {severity_desc}

**Common Symptoms:**
• {chr(10).join(f"- {symptom}" for symptom in advice_data.get("symptoms", ["Various symptoms possible"]))}

**Likely Causes:**
• {chr(10).join(f"- {cause}" for cause in advice_data.get("causes", ["Multiple factors possible"]))}

**Recommended Treatment:**
{advice_data.get("treatment", "Consult local agricultural extension services.")}

**Prevention Strategies:**
{advice_data.get("prevention", "Implement good agricultural practices and regular monitoring.")}
"""
    else:
        # Use generic advice
        generic_data = generic_issue_advice.get(issue_type, {})
        if generic_data:
            response = f"""
### **{issue_type} Management**

**Description:** {generic_data.get("description", "General agricultural issue.")}

**Immediate Actions:**
• {chr(10).join(f"- {action}" for action in generic_data.get("immediate_actions", ["Monitor closely"]))}

**Treatment Options:**
• {chr(10).join(f"- {option}" for option in generic_data.get("treatment_options", ["Various approaches available"]))}

**Prevention:**
• {chr(10).join(f"- {prevent}" for action in generic_data.get("prevention", ["Regular monitoring and good practices"]))}
"""
        else:
            response = f"**{issue_type}** - Limited specific information available for {crop}. Please consult local agricultural extension services or crop specialists for detailed advice."

    # Add regional considerations
    if region:
        response += f"\n\n**Regional Considerations for {region.title()}:**\n" \
                   f"Local climate, soil conditions, and pest pressures in {region.title()} may require " \
                   f"adjustments to these recommendations. Consider consulting regional agricultural " \
                   f"extension services for location-specific advice."

    # Add general monitoring advice
    response += f"\n\n**General Recommendations:**\n" \
               f"- Monitor crop health regularly and document changes\n" \
               f"- Keep detailed records of treatments and their effectiveness\n" \
               f"- Consider integrated pest/disease management approaches\n" \
               f"- Consult with local agricultural experts for complex issues"

    return response

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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Single Prediction", "Sensitivity Analysis", "Batch Predictions", "Trends & Comparison", "Image Analysis", "Crop Advisor"]
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
            help="Select the country or region",
            key="selected_area"
        )
    
    with col3:
        st.write("**Crop Type**")
        selected_item = st.selectbox(
            "Crop Type",
            options=items,
            index=items.index("Wheat") if "Wheat" in items else 0,
            help="Select the crop type",
            key="selected_item"
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

    batch_year = st.slider("Prediction Year", min_value=1990, max_value=2040, value=2025, step=1)
    yield_unit_batch = st.selectbox(
        "Yield Unit",
        options=["hg/ha", "lbs/acre (Pounds/Acre)", "tons/acre (Short Tons/Acre)"],
        index=0,
        help="Choose the unit for batch predictions",
        key="yield_unit_batch"
    )

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

                with st.spinner("Running batch predictions..."):
                    df['Predicted_Yield_hg_ha'] = df.apply(
                        lambda row: predict_yield(
                            row['Rainfall'],
                            row['Temperature'],
                            row['Pesticides'],
                            batch_year,
                            row['Area']
                        ),
                        axis=1
                    )

                if yield_unit_batch == "lbs/acre (Pounds/Acre)":
                    df['Predicted_Yield'] = df['Predicted_Yield_hg_ha'].apply(hg_per_hectare_to_lbs_per_acre)
                    unit_label = "lbs/acre"
                elif yield_unit_batch == "tons/acre (Short Tons/Acre)":
                    df['Predicted_Yield'] = df['Predicted_Yield_hg_ha'].apply(hg_per_hectare_to_tons_per_acre)
                    unit_label = "tons/acre"
                else:
                    df['Predicted_Yield'] = df['Predicted_Yield_hg_ha']
                    unit_label = "hg/ha"

                st.success("Batch predictions completed!")
                st.dataframe(df[['Rainfall', 'Temperature', 'Pesticides', 'Area', 'Item', 'Predicted_Yield']])

                csv_buffer = BytesIO()
                df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)

                st.download_button(
                    label=f"Download predictions ({unit_label})",
                    data=csv_buffer,
                    file_name=f"batch_predictions_{batch_year}.csv",
                    mime="text/csv"
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

with tab6:
    st.subheader("🧠 Advanced Crop Advisor Bot")
    st.write("Get detailed, AI-enhanced crop advice with symptom analysis and comprehensive recommendations.")

    # Enhanced UI with symptom checklist
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🌾 Crop & Issue Selection")
        advisor_crop = st.selectbox(
            "Select Crop",
            options=advisor_crops,
            index=advisor_crops.index("Wheat") if "Wheat" in advisor_crops else 0,
            help="Choose the crop you're having issues with",
            key="advisor_crop"
        )

        advisor_issue = st.selectbox(
            "Problem Category",
            options=issue_categories,
            help="Select the type of problem or choose auto-detection",
            key="advisor_issue"
        )

        advisor_region = st.text_input(
            "Region/Location (optional)",
            help="Enter your region for location-specific advice"
        )

    with col2:
        st.markdown("### 🔍 Symptom Analysis")
        st.write("Describe symptoms or use the auto-detection feature:")

        # Symptom input area
        advisor_notes = st.text_area(
            "Describe symptoms, observations, or problems",
            height=120,
            placeholder="Example: Yellow leaves with brown spots, stunted growth, holes in leaves, wilting plants...",
            help="Be specific about what you observe - colors, patterns, affected plant parts, timing, etc."
        )

        # Quick symptom checklist
        with st.expander("📋 Quick Symptom Checklist"):
            st.write("Check all that apply:")
            symptom_checks = []
            if st.checkbox("Yellow/chlorotic leaves"): symptom_checks.append("yellow leaves")
            if st.checkbox("Brown spots or lesions"): symptom_checks.append("brown spots on leaves")
            if st.checkbox("Wilting or drooping"): symptom_checks.append("wilting plants")
            if st.checkbox("Holes in leaves"): symptom_checks.append("holes in leaves")
            if st.checkbox("Stunted growth"): symptom_checks.append("stunted growth")
            if st.checkbox("White powdery coating"): symptom_checks.append("white powdery coating")
            if st.checkbox("Curled or distorted leaves"): symptom_checks.append("curled leaves")
            if st.checkbox("Root problems"): symptom_checks.append("root rot or damage")

            if symptom_checks:
                auto_symptoms = ", ".join(symptom_checks)
                if st.button("Add to description"):
                    advisor_notes = auto_symptoms + ("; " + advisor_notes if advisor_notes else "")

    # Analysis and advice generation
    if st.button("🔬 Analyze & Get Advice", type="primary", use_container_width=True):
        if not advisor_notes and advisor_issue == "Auto-detect from notes":
            st.error("Please describe symptoms or select a specific problem category for auto-detection to work.")
        else:
            with st.spinner("🤖 Analyzing symptoms and generating comprehensive advice..."):
                time.sleep(1)  # Simulate processing time
                advice_text = get_crop_advice(advisor_crop, advisor_issue, advisor_region, advisor_notes)

            st.success("✅ Analysis Complete - Detailed advice generated!")

            # Display results in organized sections
            st.markdown("---")

            # Summary card
            col_summary1, col_summary2 = st.columns(2)
            with col_summary1:
                st.metric("Crop", advisor_crop)
                st.metric("Issue Type", advisor_issue)
            with col_summary2:
                if advisor_region:
                    st.metric("Region", advisor_region.title())
                if advisor_notes:
                    st.metric("Symptoms Described", "Yes")

            st.markdown("---")

            # Main advice display
            st.markdown(advice_text)

            # Additional resources section
            with st.expander("📚 Additional Resources & Tips"):
                st.markdown("""
                **Monitoring & Documentation:**
                - Keep a crop health journal with photos and observations
                - Track weather patterns and their correlation with symptoms
                - Record all treatments and their effectiveness

                **Professional Consultation:**
                - Contact local agricultural extension services
                - Consult certified crop advisors or agronomists
                - Join local farming communities for peer advice

                **Preventive Measures:**
                - Regular field scouting (at least weekly)
                - Soil testing every 2-3 years
                - Proper crop rotation planning
                - Integrated Pest Management (IPM) practices
                """)

            # Related crops info
            if advisor_crop in items:
                st.info(f"💡 **Pro Tip:** {advisor_crop} is supported by our yield prediction model. Use the 'Single Prediction' tab to estimate potential yields under different conditions.")
            else:
                st.info(f"💡 **Note:** {advisor_crop} advisory data is available, but yield prediction modeling requires additional crop-specific data.")

    # Quick tips section
    st.markdown("---")
    with st.expander("🚀 Quick Farming Tips"):
        st.markdown("""
        **General Best Practices:**
        - **Scout regularly:** Walk your fields at least once a week to catch problems early
        - **Keep records:** Document everything - weather, treatments, yields, problems
        - **Soil testing:** Test your soil every 2-3 years for optimal nutrient management
        - **Crop rotation:** Rotate crops to break pest and disease cycles
        - **Water management:** Monitor soil moisture and avoid over/under watering
        - **Integrated approaches:** Combine cultural, biological, and chemical methods when needed

        **When to Seek Help:**
        - Symptoms persist despite treatment
        - Unidentified problems or unusual symptoms
        - Significant yield losses
        - New or unfamiliar pest/disease issues
        """)

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
