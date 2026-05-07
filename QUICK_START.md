# 🌱 Quick Start Guide - Crop Yield Prediction App v2.0

## 🚀 Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Running the App
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📚 Feature Guide

### Tab 1: 🔮 Single Prediction
**Best for:** Quick predictions for a specific scenario

**How to use:**
1. Set **Year** in the sidebar (1990-2040)
2. Enter **Environmental Factors**:
   - Rainfall: 0-10,000 mm/year
   - Temperature: -50 to 60°C
   - Pesticides: 0-1,000 tonnes
3. Select **Country/Region** and **Crop Type**
4. Click **🔮 Predict Yield**

**Output:** Single yield prediction in hg/ha (hectograms per hectare)

---

### Tab 2: 📊 Sensitivity Analysis
**Best for:** Understanding which factors impact yield the most

**How to use:**
1. Set **Base Parameters**: rainfall, temperature, pesticides
2. Choose target **Country** and **Crop**
3. Click **📊 Run Sensitivity Analysis**

**Output:** 3 interactive charts showing:
- How rainfall affects yield
- How temperature affects yield
- How pesticide usage affects yield

**Interpretation:**
- Steep curves = high impact
- Flat curves = low impact

---

### Tab 3: 📤 Batch Predictions
**Best for:** Processing multiple predictions at once

**How to use:**
1. Prepare CSV file with columns:
   - `Rainfall` (mm/year)
   - `Temperature` (°C)
   - `Pesticides` (tonnes)
   - `Area` (country name)
   - `Item` (crop name)
2. Upload CSV file
3. Review predictions in table
4. Click **📥 Download Results as CSV**

**Example CSV Format:**
```
Rainfall,Temperature,Pesticides,Area,Item
1000,25,10,India,Wheat
1200,22,15,Brazil,Maize
1500,20,12,France,Potatoes
```

**Sample File:** See `sample_predictions.csv`

---

### Tab 4: 📈 Trends & Comparison
**Best for:** Comparing across years, countries, or crops

#### Compare Across Years
1. Select **Countries** and **Crops** to compare
2. Set **Base Parameters**
3. View yield trend from 2000 to 2040
4. Identify growth or decline patterns

#### Compare Across Countries
1. Select target **Crop**
2. Choose up to 5 **Countries** to compare
3. View bar chart of yields by country
4. Identify best-performing regions

#### Compare Across Crops
1. Select target **Country**
2. View yield predictions for all available crops
3. Find best crop for the region

---

## 📊 Supported Countries/Regions

The model supports 101 countries/regions including:

**Americas:** Argentina, Brazil, Canada, Chile, Colombia, Ecuador, El Salvador, Guatemala, Guyana, Haiti, Honduras, Jamaica, Mexico, Nicaragua, Peru, Suriname, United States, Uruguay

**Europe:** Austria, Belarus, Belgium, Bulgaria, Croatia, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Ireland, Italy, Latvia, Lithuania, Netherlands, Poland, Portugal, Romania, Slovenia, Spain, Sweden, Switzerland, Turkey, Ukraine, United Kingdom

**Africa:** Algeria, Angola, Botswana, Burkina Faso, Burundi, Cameroon, Central African Republic, Egypt, Eritrea, Ghana, Guinea, Kenya, Lesotho, Libya, Madagascar, Malawi, Mali, Mauritania, Mauritius, Morocco, Mozambique, Namibia, Niger, Rwanda, Senegal, South Africa, Sudan, Tunisia, Uganda, Zambia, Zimbabwe

**Asia:** Armenia, Azerbaijan, Bahrain, Bangladesh, India, Indonesia, Iraq, Japan, Kazakhstan, Lebanon, Malaysia, Nepal, Pakistan, Papua New Guinea, Qatar, Saudi Arabia, Sri Lanka, Tajikistan, Thailand

**Oceania:** Australia, New Zealand

---

## 🌾 Supported Crops

The model can predict yields for:
- Maize
- Plantains and others
- Potatoes
- Rice, paddy
- Sorghum
- Soybeans
- Sweet potatoes
- Wheat
- Yams

---

## 💡 Usage Tips

### Tip 1: Find Optimal Growing Conditions
Use **Sensitivity Analysis** to find the combination that maximizes yield. Look for peaks in the charts.

### Tip 2: Plan Regional Crop Strategy
Use **Trends & Comparison** → **Countries** to see which regions produce highest yields for your crop.

### Tip 3: Forecast Future Yields
Use **Trends & Comparison** → **Years** to see projected yield changes over time.

### Tip 4: Analyze Multiple Scenarios
Use **Batch Predictions** to quickly process what-if scenarios by uploading a CSV with different parameters.

### Tip 5: Validate Predictions
Use **Single Prediction** to verify specific scenarios before using batch processing.

---

## ⚠️ Input Constraints

| Parameter | Min | Max | Recommended |
|-----------|-----|-----|-------------|
| Rainfall | 0 | 10,000 mm/year | 500-2000 |
| Temperature | -50 | 60 °C | 15-35 |
| Pesticides | 0 | 1,000 tonnes | 5-50 |
| Year | 1990 | 2040 | 2025 |

---

## 🔧 Troubleshooting

### Issue: "Model file 'crop_yield_model.pkl' not found!"
**Solution:** Ensure `crop_yield_model.pkl` is in the same directory as `app.py`

### Issue: CSV upload fails
**Solution:** 
- Check that CSV has required columns: Rainfall, Temperature, Pesticides, Area, Item
- Ensure country/crop names match the supported list
- Verify CSV is properly formatted (no extra spaces)

### Issue: Predictions seem unrealistic
**Solution:** 
- Check input values are within recommended ranges
- Verify country and crop names are correct
- Try Sensitivity Analysis to understand the model's behavior

### Issue: Slow performance when running sensitivity analysis
**Solution:** This is normal - it runs 60 predictions (3 parameters × 20 values). Wait for completion.

---

## 📈 Output Interpretation

### Yield Units
- Output is in **hg/ha** (hectograms per hectare)
- 1 hg/ha = 0.1 kg/ha = 0.1 mg/cm²

### What's a Good Yield?
Varies by crop and region, but typical ranges:
- **Wheat:** 3,000-9,000 hg/ha
- **Maize:** 4,000-12,000 hg/ha
- **Rice:** 4,000-10,000 hg/ha
- **Potatoes:** 20,000-50,000 hg/ha

---

## 🎓 About the Model

- **Algorithm:** Random Forest Regressor
- **Features:** 113 (includes year, climate, location, crop type)
- **Training Data:** Agricultural yield records
- **Accuracy:** Trained on historical data to predict future yields
- **Bias:** Based on available historical data by region

---

## 📞 Support

For issues or suggestions:
1. Check the IMPROVEMENTS.md file for detailed technical information
2. Review the PROJECT_DOCUMENTATION.md for architecture details
3. Ensure all requirements from requirements.txt are installed

---

**Last Updated:** May 2026  
**App Version:** 2.0  
**Model Type:** RandomForestRegressor
