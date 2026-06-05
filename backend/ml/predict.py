"""
SilentChurn AI - Customer Churn Prediction Module
This module handles loading the trained model and preprocessor to perform
real-time churn probability prediction for a single customer.
"""

import os
import logging
import pandas as pd
import numpy as np
import joblib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define file paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(BASE_DIR, "models", "best_churn_model.pkl")
PREPROCESSOR_PATH = os.path.join(BASE_DIR, "models", "preprocessor.pkl")

# Global variables for caching model artifacts
_model = None
_preprocessor = None

def load_artifacts():
    """Lazy loads the model and preprocessor artifacts from disk."""
    global _model, _preprocessor
    if _model is None or _preprocessor is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Best churn model not found at {MODEL_PATH}. Run train_model.py first.")
        if not os.path.exists(PREPROCESSOR_PATH):
            raise FileNotFoundError(f"Preprocessor not found at {PREPROCESSOR_PATH}. Run train_model.py first.")
        
        logger.info("Loading model and preprocessor artifacts...")
        _model = joblib.load(MODEL_PATH)
        _preprocessor = joblib.load(PREPROCESSOR_PATH)
        logger.info("Artifacts loaded successfully.")
    return _model, _preprocessor

def predict_customer(input_data: dict) -> dict:
    """
    Predicts the churn risk for a single customer based on behavioral and transactional data.
    
    Args:
        input_data (dict): Key-value pairs of customer features.
        
    Returns:
        dict: Churn probability (float) and prediction ('Churn' or 'No Churn').
    """
    try:
        model, preprocessor = load_artifacts()
        
        # 1. Convert dictionary to DataFrame
        df = pd.DataFrame([input_data])
        
        # 2. Preprocess & Clean Input Features
        # Ensure TotalCharges is present and numeric
        if 'TotalCharges' in df.columns:
            df['TotalCharges'] = pd.to_numeric(df['TotalCharges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')
        else:
            # Fallback estimation if TotalCharges is omitted but tenure/MonthlyCharges are present
            tenure = df.get('tenure', pd.Series([0])).iloc[0]
            monthly = df.get('MonthlyCharges', pd.Series([0.0])).iloc[0]
            df['TotalCharges'] = float(tenure) * float(monthly)
            
        df['TotalCharges'] = df['TotalCharges'].fillna(0.0)
        
        # Ensure SeniorCitizen is an integer/numeric indicator
        if 'SeniorCitizen' in df.columns:
            df['SeniorCitizen'] = df['SeniorCitizen'].astype(int)
            
        # Ensure all columns expected by preprocessor are present
        # If any categorical column is missing, fill it with a sensible default ('No' or similar)
        # Numerical columns fill with median/zeros
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
                    
        # Select and order columns as expected by the preprocessor
        df = df[expected_cols]
        
        # 3. Transform features
        processed_features = preprocessor.transform(df)
        
        # 4. Predict
        probability = float(model.predict_proba(processed_features)[0, 1])
        prediction_val = model.predict(processed_features)[0]
        
        prediction_label = "Churn" if prediction_val == 1 or probability >= 0.5 else "No Churn"
        
        return {
            "churn_probability": round(probability, 4),
            "prediction": prediction_label
        }
        
    except Exception as e:
        logger.error(f"Error during customer churn prediction: {e}", exc_info=True)
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
    
    result = predict_customer(test_customer)
    print("Test Prediction Output:")
    print(result)
