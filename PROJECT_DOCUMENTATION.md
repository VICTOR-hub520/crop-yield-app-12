# Crop Yield Prediction App - Project Documentation

## Project Overview

The Crop Yield Prediction App is a web-based application built with Streamlit that predicts crop yield based on environmental and agricultural factors. The application uses a pre-trained machine learning model (RandomForestRegressor) to provide yield predictions for various crops in different regions.

### Key Features
- User-friendly web interface for inputting prediction parameters
- Real-time crop yield prediction
- Support for multiple environmental factors (rainfall, temperature, pesticides)
- Default region and crop type settings for simplified usage

## Architecture    

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Browser  │────│   Streamlit App │────│   ML Model      │
│                 │    │   (app.py)      │    │   (Pickle)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Dependencies  │
                       │   (requirements)│
                       └─────────────────┘
```

### Component Breakdown

#### 1. Frontend Layer
- **Framework**: Streamlit
- **Purpose**: Provides the web interface for user interaction
- **Components**:
  - Input forms for rainfall, temperature, and pesticides
  - Prediction button
  - Results display

#### 2. Application Logic Layer
- **Language**: Python 3.11
- **Main File**: `app.py`
- **Responsibilities**:
  - Load the pre-trained machine learning model
  - Process user inputs
  - Prepare feature vectors for prediction
  - Execute model prediction
  - Display results to user

#### 3. Machine Learning Layer
- **Model Type**: RandomForestRegressor (Ensemble Learning)
- **Storage**: Pickle file (`crop_yield_model.pkl`)
- **Input Features**: 113 features including:
  - Year (numeric)
  - Average rainfall (mm/year)
  - Pesticides usage (tonnes)
  - Average temperature (°C)
  - One-hot encoded Area (101 countries/regions)
  - One-hot encoded Item (9 crop types)

#### 4. Data Processing Layer
- **Libraries**: NumPy, Pandas
- **Purpose**: Feature engineering and data preparation
- **Key Operations**:
  - Create feature dictionaries with proper naming
  - Handle one-hot encoding for categorical variables
  - Ensure feature vector matches model expectations

### Data Flow
1. User accesses the Streamlit web application
2. User inputs rainfall, temperature, and pesticides values
3. Application creates a complete feature vector (113 features) with defaults for missing inputs
4. Feature vector is passed to the pre-trained RandomForestRegressor model
5. Model generates yield prediction
6. Prediction result is displayed to the user

## Technologies Used

### Core Technologies
- **Python 3.11**: Primary programming language
- **Streamlit**: Web application framework for data science applications
- **Scikit-learn**: Machine learning library for the RandomForestRegressor model
- **Joblib**: Library for loading/saving Python objects (model serialization)

### Supporting Libraries
- **NumPy**: Numerical computing and array operations
- **Pandas**: Data manipulation and DataFrame operations

### Development Environment
- **Dev Container**: Microsoft Dev Containers for consistent development environment
- **VS Code Extensions**: Python, Pylance for enhanced Python development experience

## Installation and Setup

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Git (for cloning the repository)

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/VICTOR-hub520/crop-yield-app-12.git
   cd crop-yield-app-12
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   streamlit run app.py
   ```

4. **Access the Application**
   - Open your web browser
   - Navigate to the local URL provided by Streamlit (typically http://localhost:8501)

### Dev Container Setup (Optional)
If using VS Code with Dev Containers:
1. Open the project in VS Code
2. When prompted, click "Reopen in Container"
3. The dev container will automatically install all dependencies

## Usage

### Basic Usage
1. Open the application in your web browser
2. Enter the following values:
   - **Rainfall (mm per year)**: Annual rainfall in millimeters (default: 1000.0)
   - **Average Temperature (°C)**: Average annual temperature in Celsius (default: 25.0)
   - **Pesticides (tonnes)**: Amount of pesticides used in tonnes (default: 10.0)
3. Click the "Predict Yield" button
4. View the predicted crop yield result

### Understanding the Prediction
- The model currently uses default values for:
  - Year: 2023
  - Area: India
  - Item: Wheat
- The prediction represents the expected crop yield in appropriate units (likely hg/ha or similar)

## Code Structure

### File Organization
```
crop-yield-app-12/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── crop_yield_model.pkl      # Pre-trained ML model
├── .devcontainer/
│   └── devcontainer.json     # Dev container configuration
└── .git/                     # Git repository data
```

### app.py Detailed Breakdown

#### Imports and Setup
```python
import streamlit as st
import joblib
import numpy as np
import pandas as pd

# Load the pre-trained model
model = joblib.load("crop_yield_model.pkl")
```

#### User Interface
```python
st.title("🌱 Crop Yield Prediction App")
st.write("Enter values to predict crop yield")

# Input fields with default values
rainfall = st.number_input("Rainfall (mm per year)", value=1000.0)
temperature = st.number_input("Average Temperature (°C)", value=25.0)
pesticides = st.number_input("Pesticides (tonnes)", value=10.0)
```

#### Prediction Logic
```python
if st.button("Predict Yield"):
    # Create complete feature vector
    feature_dict = {name: 0.0 for name in model.feature_names_in_}
    
    # Map user inputs to correct features
    feature_dict['Year'] = 2023
    feature_dict['average_rain_fall_mm_per_year'] = rainfall
    feature_dict['pesticides_tonnes'] = pesticides
    feature_dict['avg_temp'] = temperature
    
    # Set defaults for categorical features
    feature_dict['Area_India'] = 1.0
    feature_dict['Item_Wheat'] = 1.0
    
    # Create DataFrame and predict
    features = pd.DataFrame([feature_dict])
    prediction = model.predict(features)
    
    # Display result
    st.success(f"Predicted Crop Yield: {prediction[0]:.2f}")
```

## Model Details

### Model Type
- **Algorithm**: RandomForestRegressor
- **Library**: Scikit-learn
- **Ensemble Method**: Bootstrap aggregation (bagging) of decision trees

### Training Data Characteristics
- **Number of Features**: 113
- **Feature Types**:
  - Numerical: Year, rainfall, pesticides, temperature
  - Categorical (one-hot encoded): Area (101 regions), Item (9 crop types)

### Feature List
#### Numerical Features
- `Year`: Year of data collection
- `average_rain_fall_mm_per_year`: Annual rainfall in millimeters
- `pesticides_tonnes`: Pesticides usage in tonnes
- `avg_temp`: Average temperature in Celsius

#### Categorical Features (One-hot Encoded)
- **Area**: 101 different countries/regions including Algeria, Angola, Argentina, etc.
- **Item**: 9 crop types including Maize, Plantains, Potatoes, Rice, Sorghum, Soybeans, Sweet potatoes, Wheat, Yams

### Model Performance
- **Training Framework**: Scikit-learn 1.6.1 (note: current environment uses 1.8.0)
- **Serialization**: Joblib pickle format
- **Prediction Output**: Continuous numerical value representing crop yield

### Model Limitations
- Trained on specific dataset with limited geographical and temporal coverage
- Uses default values for region and crop type in the current app implementation
- May not generalize well to regions/countries not in training data

## Limitations and Future Improvements

### Current Limitations
1. **Simplified Input Interface**: Only 3 input parameters, with hardcoded defaults for region and crop type
2. **Limited User Customization**: No selection options for Area and Item features
3. **Model Version Compatibility**: Potential issues due to scikit-learn version differences
4. **No Data Validation**: Limited input validation and error handling
5. **Single Model**: No model comparison or ensemble methods
6. **No Historical Data**: Cannot show trends or historical predictions

### Future Enhancement Opportunities

#### User Interface Improvements
- Add dropdown menus for Area (country/region) selection
- Add dropdown menus for Item (crop type) selection
- Include input validation and helpful error messages
- Add tooltips and help text for each input field
- Implement responsive design for mobile devices

#### Feature Engineering
- Add more input features (soil type, irrigation methods, etc.)
- Implement dynamic feature importance visualization
- Add confidence intervals for predictions

#### Model Improvements
- Retrain model with current scikit-learn version
- Implement model versioning and A/B testing
- Add multiple model options (XGBoost, Neural Networks)
- Include model interpretability features (SHAP values, feature importance)

#### Application Architecture
- Separate frontend and backend components
- Add REST API for programmatic access
- Implement user authentication and data persistence
- Add batch prediction capabilities
- Integrate with external data sources (weather APIs, soil databases)

#### Data and Analytics
- Add historical data visualization
- Implement prediction history tracking
- Add comparative analysis features
- Integrate with agricultural databases

#### Deployment and Scalability
- Containerize the application (Docker)
- Deploy to cloud platforms (AWS, GCP, Azure)
- Implement CI/CD pipelines
- Add monitoring and logging
- Optimize for high-traffic scenarios

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Production Deployment
For production deployment, consider:
1. Using a WSGI server (Gunicorn) with Streamlit
2. Containerizing with Docker
3. Deploying to cloud platforms with load balancers
4. Setting up monitoring and logging

### Environment Variables
Currently, no environment variables are used. For production:
- Add configuration for different environments
- Secure sensitive data (API keys, database credentials)
- Configure logging levels

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make changes following the existing code style
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Include comments for complex logic

## License

This project is open-source. Please check the repository for license information.

## Contact

For questions or support, please create an issue in the GitHub repository.

---

*This documentation was generated on April 22, 2026, for the Crop Yield Prediction App project.*