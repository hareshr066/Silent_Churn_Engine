"""
SilentChurn AI - Customer Churn Prediction Module (MongoDB Integrated)
This module handles loading the trained model and preprocessor to perform
real-time churn probability prediction for a single customer and logs predictions
to MongoDB Atlas.
"""

import os
import logging
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timezone

# Import MongoDB connection layer
from backend.database.mongodb import db_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
    Predicts the churn risk for a single customer, stores the prediction in MongoDB,
    and returns probability and label.
    
    Args:
        input_data (dict): Key-value pairs of customer features.
        
    Returns:
        dict: Churn probability (float) and prediction ('Churn' or 'No Churn').
    """
    try:
        model, preprocessor = load_artifacts()
        
        # Extract user_id/customerID if available
        user_id = str(input_data.get("user_id", input_data.get("customerID", "unknown")))
        
        # 1. Convert dictionary to DataFrame
        df = pd.DataFrame([input_data])
        
        # Remove customerID / user_id from features if they exist
        features_df = df.copy()
        if 'customerID' in features_df.columns:
            features_df = features_df.drop(columns=['customerID'])
        if 'user_id' in features_df.columns:
            features_df = features_df.drop(columns=['user_id'])
            
        # 2. Preprocess & Clean Input Features
        if 'TotalCharges' in features_df.columns:
            features_df['TotalCharges'] = pd.to_numeric(features_df['TotalCharges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')
        else:
            tenure = features_df.get('tenure', pd.Series([0])).iloc[0]
            monthly = features_df.get('MonthlyCharges', pd.Series([0.0])).iloc[0]
            features_df['TotalCharges'] = float(tenure) * float(monthly)
            
        features_df['TotalCharges'] = features_df['TotalCharges'].fillna(0.0)
        
        if 'SeniorCitizen' in features_df.columns:
            features_df['SeniorCitizen'] = features_df['SeniorCitizen'].astype(int)
            
        # Ensure all columns expected by preprocessor are present
        expected_cols = [
            'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure', 
            'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity', 
            'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 
            'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod', 
            'MonthlyCharges', 'TotalCharges'
        ]
        
        for col in expected_cols:
            if col not in features_df.columns:
                if col in ['tenure', 'MonthlyCharges', 'TotalCharges']:
                    features_df[col] = 0.0
                elif col == 'SeniorCitizen':
                    features_df[col] = 0
                else:
                    features_df[col] = 'No'
                    
        features_df = features_df[expected_cols]
        
        # 3. Transform features
        processed_features = preprocessor.transform(features_df)
        
        # 4. Predict
        probability = float(model.predict_proba(processed_features)[0, 1])
        prediction_val = model.predict(processed_features)[0]
        
        prediction_label = "Churn" if prediction_val == 1 or probability >= 0.5 else "No Churn"
        
        # 5. Store prediction in MongoDB 'predictions' collection
        predictions_col = db_manager.get_collection("predictions")
        prediction_doc = {
            "user_id": user_id,
            "prediction": prediction_label,
            "churn_probability": round(probability, 4),
            "created_at": datetime.now(timezone.utc)
        }
        predictions_col.insert_one(prediction_doc)
        logger.info(f"Saved prediction for user '{user_id}' to MongoDB predictions collection.")
        
        return {
            "churn_probability": round(probability, 4),
            "prediction": prediction_label
        }
        
    except Exception as e:
        logger.error(f"Error during customer churn prediction: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    test_customer = {
        'customerID': '9999-TESTID',
        'gender': 'Male',
        'SeniorCitizen': 1,
        'Partner': 'No',
        'Dependents': 'No',
        'tenure': 2,
        'PhoneService': 'Yes',
        'MultipleLines': 'No',
        'InternetService': 'Fiber optic',
        'OnlineSecurity': 'No',
        'OnlineBackup': 'No',
        'DeviceProtection': 'No',
        'TechSupport': 'No',
        'StreamingTV': 'No',
        'StreamingMovies': 'No',
        'Contract': 'Month-to-month',
        'PaperlessBilling': 'Yes',
        'PaymentMethod': 'Electronic check',
        'MonthlyCharges': 70.0,
        'TotalCharges': '140.0'
    }
    
    print("Running customer prediction test...")
    try:
        result = predict_customer(test_customer)
        print("Test Prediction Output:")
        print(result)
    finally:
        db_manager.close()
