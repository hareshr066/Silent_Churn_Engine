"""
SilentChurn AI - Customer Churn Model Training Pipeline (MongoDB Integrated)
This script runs the data loading (to raw_dataset collection), data cleaning (to cleaned_dataset collection),
feature engineering, model training (Random Forest & XGBoost), evaluation (saving to model_metrics),
and persistence of the best model.
"""

import os
import logging
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Import MongoDB connection layer
from backend.database.mongodb import db_manager, init_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define file paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASET_PATH = os.path.join(BASE_DIR, "datasets", "WA_Fn-UseC_-Telco-Customer-Churn.csv")
CLEANED_DATASET_PATH = os.path.join(BASE_DIR, "datasets", "cleaned_churn_data.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Check if XGBoost is available
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
    logger.info("XGBoost is available.")
except ImportError:
    XGB_AVAILABLE = False
    logger.warning("XGBoost is not available.")

def ingest_raw_data(df: pd.DataFrame) -> None:
    """Ingests raw original dataset records into MongoDB 'raw_dataset' collection."""
    logger.info("=== Phase 2: Ingesting Raw Dataset to MongoDB ===")
    try:
        raw_col = db_manager.get_collection("raw_dataset")
        # Clear existing data to maintain idempotency
        logger.info("Clearing existing documents in raw_dataset collection...")
        raw_col.delete_many({})
        
        # Convert DataFrame to records dict
        records = df.to_dict('records')
        logger.info(f"Inserting {len(records)} records into raw_dataset collection...")
        raw_col.insert_many(records)
        logger.info("Raw dataset ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Error during raw dataset ingestion: {e}", exc_info=True)
        raise e

def clean_and_ingest_data(df: pd.DataFrame) -> pd.DataFrame:
    """Performs data cleaning steps, saves CSV, and ingests to MongoDB 'cleaned_dataset' collection."""
    logger.info("=== Phase 3: Data Cleaning & Ingesting Cleaned Dataset ===")
    
    try:
        # 1. Remove duplicate records
        initial_rows = df.shape[0]
        df = df.drop_duplicates()
        dup_removed = initial_rows - df.shape[0]
        if dup_removed > 0:
            logger.info(f"Removed {dup_removed} duplicate records.")
        
        # 2. Convert TotalCharges to numeric
        df['TotalCharges'] = pd.to_numeric(df['TotalCharges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')
        
        # 3. Handle missing values
        total_charges_nans = df['TotalCharges'].isnull().sum()
        if total_charges_nans > 0:
            logger.info(f"Filling {total_charges_nans} missing values in TotalCharges with 0.0")
            df['TotalCharges'] = df['TotalCharges'].fillna(0.0)
            
        remaining_nans = df.isnull().sum().sum()
        if remaining_nans > 0:
            logger.warning(f"There are still {remaining_nans} missing values. Dropping them.")
            df = df.dropna()
            
        # 4. Save cleaned dataframe to local CSV
        os.makedirs(os.path.dirname(CLEANED_DATASET_PATH), exist_ok=True)
        df.to_csv(CLEANED_DATASET_PATH, index=False)
        logger.info(f"Cleaned dataset saved locally to {CLEANED_DATASET_PATH}")
        
        # 5. Ingest cleaned records into MongoDB cleaned_dataset collection
        cleaned_col = db_manager.get_collection("cleaned_dataset")
        logger.info("Clearing existing documents in cleaned_dataset collection...")
        cleaned_col.delete_many({})
        
        cleaned_records = df.to_dict('records')
        logger.info(f"Inserting {len(cleaned_records)} records into cleaned_dataset collection...")
        cleaned_col.insert_many(cleaned_records)
        logger.info("Cleaned dataset ingestion to MongoDB completed successfully.")
        
        # Remove customerID column for downstream ML pipeline (keep it in cleaned_df for model feature split)
        if 'customerID' in df.columns:
            df = df.drop(columns=['customerID'])
            
        return df
    except Exception as e:
        logger.error(f"Error during data cleaning and cleaned dataset ingestion: {e}", exc_info=True)
        raise e

def feature_engineering(df: pd.DataFrame):
    """Prepares features, fits ColumnTransformer, and returns split datasets."""
    # Separate features and target
    X = df.drop(columns=['Churn'])
    y = df['Churn'].map({'Yes': 1, 'No': 0})
    
    numerical_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
    categorical_cols = [col for col in X.columns if col not in numerical_cols]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
        ]
    )
    
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    return X_train_processed, X_test_processed, y_train, y_test, preprocessor

def train_evaluate_save_metrics(X_train, X_test, y_train, y_test, preprocessor) -> None:
    """Trains models, evaluates metrics, and stores results in MongoDB 'model_metrics' collection."""
    logger.info("=== Phase 4: Model Training, Evaluation & Metrics Storage ===")
    
    models = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    }
    
    if XGB_AVAILABLE:
        models["XGBoost"] = xgb.XGBClassifier(
            n_estimators=100, 
            learning_rate=0.05, 
            max_depth=5, 
            random_state=42,
            eval_metric='logloss'
        )
        
    metrics_col = db_manager.get_collection("model_metrics")
    results = {}
    
    for name, model in models.items():
        logger.info(f"Training {name} Classifier...")
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred))
        rec = float(recall_score(y_test, y_pred))
        f1 = float(f1_score(y_test, y_pred))
        roc_auc = float(roc_auc_score(y_test, y_prob))
        
        logger.info(f"[{name}] Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | AUC: {roc_auc:.4f}")
        
        # Save metrics to MongoDB
        metrics_doc = {
            "model_name": name,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "created_at": datetime.now(timezone.utc)
        }
        
        metrics_col.insert_one(metrics_doc)
        logger.info(f"Saved {name} metrics to MongoDB model_metrics collection.")
        
        results[name] = {
            "model": model,
            "f1": f1
        }
        
    # Phase 5: Save Best Model & Preprocessor
    logger.info("=== Phase 5: Saving Best Model & Preprocessor ===")
    best_name = max(results, key=lambda k: results[k]['f1'])
    best_model = results[best_name]['model']
    logger.info(f"Best model selected: {best_name}")
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    best_model_path = os.path.join(MODELS_DIR, "best_churn_model.pkl")
    preprocessor_path = os.path.join(MODELS_DIR, "preprocessor.pkl")
    
    joblib.dump(best_model, best_model_path)
    joblib.dump(preprocessor, preprocessor_path)
    
    logger.info(f"Saved best model to {best_model_path}")
    logger.info(f"Saved preprocessor to {preprocessor_path}")

def main():
    try:
        # Initialize database collections and verify connection
        init_db()
        
        if not os.path.exists(DATASET_PATH):
            logger.error(f"Could not find dataset at {DATASET_PATH}.")
            return
            
        logger.info(f"Dataset located at {DATASET_PATH}")
        df = pd.read_csv(DATASET_PATH)
        
        # Load Raw
        ingest_raw_data(df)
        
        # Clean and Load Cleaned
        cleaned_df = clean_and_ingest_data(df)
        
        # Split features
        X_train, X_test, y_train, y_test, preprocessor = feature_engineering(cleaned_df)
        
        # Train & Evaluate & Save
        train_evaluate_save_metrics(X_train, X_test, y_train, y_test, preprocessor)
        
        logger.info("Full MongoDB integrated model training pipeline execution completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
