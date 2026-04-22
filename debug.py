import streamlit as st
import joblib
import pandas as pd

# Load the pre-trained model
model = joblib.load("crop_yield_model.pkl")

print(f"Has feature_names_in_: {hasattr(model, 'feature_names_in_')}")
if hasattr(model, 'feature_names_in_'):
    print(f"Length: {len(model.feature_names_in_)}")
else:
    print("No feature_names_in_")

# Extract available areas and items from model features
all_features = list(model.feature_names_in_)
areas = [f.replace("Area_", "") for f in all_features if f.startswith("Area_")]
items = [f.replace("Item_", "") for f in all_features if f.startswith("Item_")]

print(f"Model features: {len(all_features)}")
print(f"Type of all_features: {type(all_features)}")
print(f"Type of model.feature_names_in_: {type(model.feature_names_in_)}")
print(f"Areas: {len(areas)}")
print(f"Items: {len(items)}")

# Simulate the prediction
selected_area = 'India'
selected_item = 'Wheat'
year = 2025
rainfall = 1000.0
pesticides = 10.0
temperature = 25.0

feature_dict = {name: 0.0 for name in model.feature_names_in_}
print(f"feature_dict keys: {len(feature_dict)}")

feature_dict['Year'] = year
feature_dict['average_rain_fall_mm_per_year'] = rainfall
feature_dict['pesticides_tonnes'] = pesticides
feature_dict['avg_temp'] = temperature

feature_dict[f'Area_{selected_area}'] = 1.0
feature_dict[f'Item_{selected_item}'] = 1.0

features = pd.DataFrame([feature_dict])
print(f"DataFrame shape: {features.shape}")
print(f"DataFrame columns: {len(features.columns)}")

prediction = model.predict(features)
print(f"Prediction: {prediction}")