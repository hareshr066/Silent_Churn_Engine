"""
SilentChurn AI - Database Precomputation Script
Runs batch predictions on all 7,043 cleaned customers and populates the 
predictions and recommendations collections in MongoDB.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timezone

# Add current directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.database.mongodb import db_manager
from backend.ml.predict import load_artifacts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLEANED_DATASET_PATH = os.path.join(BASE_DIR, "datasets", "cleaned_churn_data.csv")

def precompute():
    try:
        # Load models
        model, preprocessor = load_artifacts()
        
        # Connect to MongoDB
        db = db_manager.get_database()
        cleaned_col = db["cleaned_dataset"]
        predictions_col = db["predictions"]
        recommendations_col = db["recommendations"]
        
        # Fetch all cleaned records
        logger.info("Fetching cleaned dataset from MongoDB...")
        cleaned_records = list(cleaned_col.find({}))
        
        if not cleaned_records:
            logger.info("No cleaned records found in database. Loading fallback from cleaned CSV...")
            if os.path.exists(CLEANED_DATASET_PATH):
                csv_df = pd.read_csv(CLEANED_DATASET_PATH)
                records = csv_df.to_dict('records')
                logger.info(f"Ingesting {len(records)} records from CSV to cleaned_dataset collection...")
                cleaned_col.insert_many(records)
                cleaned_records = list(cleaned_col.find({}))
            else:
                logger.error("No cleaned dataset CSV found. Run train_model.py first.")
                return
            
        logger.info(f"Loaded {len(cleaned_records)} customer records. Preparing batch prediction...")
        
        df = pd.DataFrame(cleaned_records)
        customer_ids = df['customerID'].tolist()
        
        # Prepare features for preprocessing
        features_df = df.copy()
        if 'customerID' in features_df.columns:
            features_df = features_df.drop(columns=['customerID'])
        if '_id' in features_df.columns:
            features_df = features_df.drop(columns=['_id'])
        if 'Churn' in features_df.columns:
            features_df = features_df.drop(columns=['Churn'])
            
        # Reorder features as expected by preprocessor
        expected_cols = [
            'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure', 
            'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity', 
            'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 
            'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod', 
            'MonthlyCharges', 'TotalCharges'
        ]
        features_df = features_df[expected_cols]
        
        # Run preprocessing and prediction in batch
        logger.info("Transforming features...")
        processed_features = preprocessor.transform(features_df)
        
        logger.info("Calculating churn probabilities...")
        probabilities = model.predict_proba(processed_features)[:, 1]
        predictions = model.predict(processed_features)
        
        # Clear existing predictions/recommendations to maintain idempotency
        logger.info("Clearing existing predictions and recommendations...")
        predictions_col.delete_many({})
        recommendations_col.delete_many({})
        
        # Build batch insert arrays
        prediction_docs = []
        recommendation_docs = []
        
        logger.info("Generating predictions and recommendations documents...")
        now = datetime.now(timezone.utc)
        
        for i in range(len(cleaned_records)):
            user_id = str(customer_ids[i])
            prob = float(probabilities[i])
            pred_val = int(predictions[i])
            
            # Map prediction label
            pred_label = "Churn" if pred_val == 1 or prob >= 0.5 else "No Churn"
            
            # Define Silent Churn flag (At Risk + No Tech Support + Month-to-month Contract)
            contract = df.loc[i, 'Contract']
            tech_support = df.loc[i, 'TechSupport']
            
            is_silent_churn = False
            if pred_label == "Churn" and tech_support == "No" and contract == "Month-to-month":
                is_silent_churn = True
                
            prediction_docs.append({
                "user_id": user_id,
                "prediction": pred_label,
                "churn_probability": round(prob, 4),
                "silent_churn_flag": is_silent_churn,
                "created_at": now
            })
            
            # Generate recommendation if high risk or silent churn
            if pred_label == "Churn":
                rec_text = "Schedule proactive outreach call."
                risk_driver = "General Churn Risk"
                
                # Simple rule mapping for batch recommendations
                if contract == "Month-to-month":
                    rec_text = "Target for 1-year contract migration. Offer 15% discount on annual commitment."
                    risk_driver = "Month-to-month contract"
                elif tech_support == "No":
                    rec_text = "Proactively offer premium Tech Support 30-day free trial."
                    risk_driver = "No Tech Support"
                elif df.loc[i, 'PaymentMethod'] == 'Electronic check':
                    rec_text = "Promote automated Bank Transfer / ACH setup to avoid billing failure."
                    risk_driver = "Electronic Check payment"
                elif df.loc[i, 'MonthlyCharges'] > 80.0:
                    rec_text = "Conduct price optimization review. Suggest downgrading to Growth tier."
                    risk_driver = "High Monthly Charges"
                    
                recommendation_docs.append({
                    "user_id": user_id,
                    "recommendation": rec_text,
                    "risk_driver": risk_driver,
                    "churn_probability": round(prob, 4),
                    "created_at": now
                })
                
        logger.info(f"Inserting {len(prediction_docs)} predictions...")
        predictions_col.insert_many(prediction_docs)
        
        logger.info(f"Inserting {len(recommendation_docs)} recommendations...")
        if recommendation_docs:
            recommendations_col.insert_many(recommendation_docs)
            
        logger.info("Precomputation successfully completed!")
        
    except Exception as e:
        logger.error(f"Failed to precompute database collections: {e}", exc_info=True)
    finally:
        db_manager.close()

if __name__ == "__main__":
    precompute()
