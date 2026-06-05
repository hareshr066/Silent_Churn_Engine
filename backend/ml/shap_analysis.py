"""
SilentChurn AI - ML Explainability Module
This module implements SHAP (SHapley Additive exPlanations) to explain individual
customer predictions, identifying and ranking key risk factors.
"""

import os
import logging
import pandas as pd
import numpy as np
import joblib
import shap

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define file paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(BASE_DIR, "models", "best_churn_model.pkl")
PREPROCESSOR_PATH = os.path.join(BASE_DIR, "models", "preprocessor.pkl")

# Global variables for caching model artifacts and explainer
_model = None
_preprocessor = None
_explainer = None
_feature_names = None

def load_artifacts():
    """Lazy loads the model, preprocessor, and initializes the SHAP TreeExplainer."""
    global _model, _preprocessor, _explainer, _feature_names
    if _model is None or _preprocessor is None or _explainer is None:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(PREPROCESSOR_PATH):
            raise FileNotFoundError("Model or preprocessor artifacts not found. Run train_model.py first.")
            
        logger.info("Loading artifacts for SHAP explainer...")
        _model = joblib.load(MODEL_PATH)
        _preprocessor = joblib.load(PREPROCESSOR_PATH)
        
        # Initialize SHAP TreeExplainer (optimized for tree-based models like RF and XGBoost)
        _explainer = shap.TreeExplainer(_model)
        _feature_names = _preprocessor.get_feature_names_out()
        logger.info("SHAP Explainer initialized successfully.")
        
    return _model, _preprocessor, _explainer, _feature_names

def clean_feature_name(name: str) -> str:
    """Formats raw encoded feature names into clean, readable labels for the UI."""
    # Remove standard pipeline prefixes
    name = name.replace("cat__", "").replace("num__", "")
    
    # Check for original categorical column names to format as 'Field: Value'
    categorical_source_cols = [
        'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'PhoneService', 
        'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup', 
        'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies', 
        'Contract', 'PaperlessBilling', 'PaymentMethod'
    ]
    
    for col in categorical_source_cols:
        if name.startswith(col + "_"):
            val = name[len(col) + 1:]
            # format camelCase to title spaces, e.g. PaymentMethod -> Payment Method
            col_display = "".join([(" " + c) if c.isupper() and i > 0 else c for i, c in enumerate(col)]).strip().title()
            return f"{col_display} is '{val}'"
            
    # Format numerical features
    if name == 'tenure':
        return "Short Subscription Duration (Tenure)"
    if name == 'MonthlyCharges':
        return "High Monthly Bill"
    if name == 'TotalCharges':
        return "High Total Spend"
        
    return name.replace("_", " ").title()

def explain_prediction(customer_data: dict) -> dict:
    """
    Computes SHAP values for a single customer and extracts key drivers increasing churn risk.
    
    Args:
        customer_data (dict): Key-value pairs of customer features.
        
    Returns:
        dict: Top risk factors contributing to a churn prediction.
    """
    try:
        model, preprocessor, explainer, feature_names = load_artifacts()
        
        # 1. Convert to DataFrame and preprocess
        df = pd.DataFrame([customer_data])
        
        # Handle TotalCharges missing/blank strings
        if 'TotalCharges' in df.columns:
            df['TotalCharges'] = pd.to_numeric(df['TotalCharges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')
        else:
            tenure = df.get('tenure', pd.Series([0])).iloc[0]
            monthly = df.get('MonthlyCharges', pd.Series([0.0])).iloc[0]
            df['TotalCharges'] = float(tenure) * float(monthly)
            
        df['TotalCharges'] = df['TotalCharges'].fillna(0.0)
        
        # Make sure SeniorCitizen is numeric
        if 'SeniorCitizen' in df.columns:
            df['SeniorCitizen'] = df['SeniorCitizen'].astype(int)
            
        # Ensure all columns required are present
        expected_cols = [
            'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure', 
            'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity', 
            'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 
            'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod', 
            'MonthlyCharges', 'TotalCharges'
        ]
        
        for col in expected_cols:
            if col not in df.columns:
                if col in ['tenure', 'MonthlyCharges', 'TotalCharges']:
                    df[col] = 0.0
                elif col == 'SeniorCitizen':
                    df[col] = 0
                else:
                    df[col] = 'No'
                    
        df = df[expected_cols]
        
        # 2. Transform the input
        processed_features = preprocessor.transform(df)
        
        # 3. Compute SHAP values
        shap_values = explainer.shap_values(processed_features)
        
        # Handle shape differences between XGBoost and RandomForest output
        if isinstance(shap_values, list):
            # RandomForest list of arrays, shap_values[1] is class 1 (churn)
            customer_shap = shap_values[1][0]
        elif len(shap_values.shape) == 3:
            # RandomForest 3D array (samples, features, classes)
            customer_shap = shap_values[0, :, 1]
        elif len(shap_values.shape) == 2:
            # XGBoost 2D array (samples, features)
            customer_shap = shap_values[0]
        else:
            # Fallback flatten
            customer_shap = np.array(shap_values).flatten()
            
        # 4. Map SHAP values to feature names and sort
        features_shap_map = []
        for name, val in zip(feature_names, customer_shap):
            features_shap_map.append({
                "raw_feature": name,
                "clean_feature": clean_feature_name(name),
                "shap_value": float(val)
            })
            
        # Sort features based on their positive contribution to Churn (shap_value > 0)
        # High SHAP value means that feature is actively driving the customer towards churn.
        risk_factors = [
            item["clean_feature"] 
            for item in sorted(features_shap_map, key=lambda x: x["shap_value"], reverse=True)
            if item["shap_value"] > 0.01  # Only return features with significant positive push
        ]
        
        return {
            "top_risk_factors": risk_factors[:5]  # Return top 5 risk factors
        }
        
    except Exception as e:
        logger.error(f"Error during SHAP explanation: {e}", exc_info=True)
        raise e

# Simple tests to run script directly
if __name__ == "__main__":
    test_customer = {
        'gender': 'Female',
        'SeniorCitizen': 0,
        'Partner': 'Yes',
        'Dependents': 'No',
        'tenure': 1,
        'PhoneService': 'No',
        'MultipleLines': 'No phone service',
        'InternetService': 'DSL',
        'OnlineSecurity': 'No',
        'OnlineBackup': 'Yes',
        'DeviceProtection': 'No',
        'TechSupport': 'No',
        'StreamingTV': 'No',
        'StreamingMovies': 'No',
        'Contract': 'Month-to-month',
        'PaperlessBilling': 'Yes',
        'PaymentMethod': 'Electronic check',
        'MonthlyCharges': 29.85,
        'TotalCharges': '29.85'
    }
    
    result = explain_prediction(test_customer)
    print("Test SHAP Output:")
    print(result)
