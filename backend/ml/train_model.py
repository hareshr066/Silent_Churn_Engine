"""
SilentChurn AI - Customer Churn Model Training Pipeline
This script runs the data exploration, data cleaning, feature engineering,
model training (Random Forest & XGBoost), evaluation, comparison, and persistence of the best model.
"""

import os
import logging
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

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
    logger.info("XGBoost is installed and available.")
except ImportError:
    XGB_AVAILABLE = False
    logger.warning("XGBoost is not installed. Will train only Random Forest.")

def explore_dataset(df: pd.DataFrame) -> None:
    """Prints and logs basic exploratory statistics of the dataset."""
    logger.info("=== Phase 1: Dataset Exploration ===")
    print("\n--- Dataset Shape ---")
    print(df.shape)
    
    print("\n--- Column Names & Data Types ---")
    print(df.dtypes)
    
    print("\n--- Missing Values count ---")
    print(df.isnull().sum())
    
    print("\n--- Churn Target Distribution ---")
    churn_dist = df['Churn'].value_counts()
    churn_pct = df['Churn'].value_counts(normalize=True) * 100
    for val, count in churn_dist.items():
        print(f"{val}: {count} ({churn_pct[val]:.2f}%)")
        
    print("\n--- Numerical Data Summary ---")
    print(df.describe(include=[np.number]))
    
    # Write summary report to file
    summary_path = os.path.join(BASE_DIR, "datasets", "data_summary_report.txt")
    with open(summary_path, "w") as f:
        f.write("=== SilentChurn AI - Dataset Summary Report ===\n\n")
        f.write(f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n")
        f.write("--- Data Types ---\n")
        f.write(df.dtypes.to_string())
        f.write("\n\n--- Missing Values ---\n")
        f.write(df.isnull().sum().to_string())
        f.write("\n\n--- Churn Distribution ---\n")
        for val, count in churn_dist.items():
            f.write(f"{val}: {count} ({churn_pct[val]:.2f}%)\n")
    logger.info(f"Summary report saved to {summary_path}")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Performs data cleaning steps and saves the cleaned dataset."""
    logger.info("=== Phase 2: Data Cleaning ===")
    
    # 1. Remove duplicate records
    initial_rows = df.shape[0]
    df = df.drop_duplicates()
    dup_removed = initial_rows - df.shape[0]
    if dup_removed > 0:
        logger.info(f"Removed {dup_removed} duplicate records.")
    
    # 2. Convert TotalCharges to numeric
    # Empty strings are replaced by NaN
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'].replace(r'^\s*$', np.nan, regex=True), errors='coerce')
    
    # 3. Handle missing values
    # TotalCharges NaN values occur when tenure is 0. We fill them with 0.0
    total_charges_nans = df['TotalCharges'].isnull().sum()
    if total_charges_nans > 0:
        logger.info(f"Filling {total_charges_nans} missing values in TotalCharges with 0.0")
        df['TotalCharges'] = df['TotalCharges'].fillna(0.0)
        
    # Check for any remaining missing values in the dataframe
    remaining_nans = df.isnull().sum().sum()
    if remaining_nans > 0:
        logger.warning(f"There are still {remaining_nans} missing values in other columns. Dropping them.")
        df = df.dropna()
        
    # 4. Remove unnecessary identifiers
    if 'customerID' in df.columns:
        df = df.drop(columns=['customerID'])
        logger.info("Removed customerID column.")
        
    # 5. Save cleaned dataset
    os.makedirs(os.path.dirname(CLEANED_DATASET_PATH), exist_ok=True)
    df.to_csv(CLEANED_DATASET_PATH, index=False)
    logger.info(f"Cleaned dataset saved to {CLEANED_DATASET_PATH}")
    
    return df

def feature_engineering(df: pd.DataFrame):
    """Splits variables, creates ColumnTransformer, and saves preprocessing artifacts."""
    logger.info("=== Phase 3: Feature Engineering ===")
    
    # Separate features and target
    X = df.drop(columns=['Churn'])
    y = df['Churn'].map({'Yes': 1, 'No': 0})
    
    # Define categorical and numerical features
    numerical_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
    categorical_cols = [
        col for col in X.columns 
        if col not in numerical_cols
    ]
    
    logger.info(f"Numerical features ({len(numerical_cols)}): {numerical_cols}")
    logger.info(f"Categorical features ({len(categorical_cols)}): {categorical_cols}")
    
    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Train set: {X_train.shape[0]} samples, Test set: {X_test.shape[0]} samples")
    
    # Define preprocessing pipeline using ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
        ]
    )
    
    # Fit and transform
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # Get feature names out
    feature_names = preprocessor.get_feature_names_out()
    logger.info(f"Preprocessed features shape: {X_train_processed.shape[1]}")
    
    return X_train_processed, X_test_processed, y_train, y_test, preprocessor, feature_names

def train_and_evaluate(
    X_train, X_test, y_train, y_test, preprocessor, feature_names
) -> None:
    """Trains and compares models, selects the best performer, and saves them."""
    logger.info("=== Phase 4: Model Training & Evaluation ===")
    
    models = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    }
    
    if XGB_AVAILABLE:
        # Scale pos weight helps with imbalance if necessary, but standard XGB works well too
        models["XGBoost"] = xgb.XGBClassifier(
            n_estimators=100, 
            learning_rate=0.05, 
            max_depth=5, 
            random_state=42,
            eval_metric='logloss'
        )
        
    results = {}
    
    for name, model in models.items():
        logger.info(f"Training {name} Classifier...")
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_prob)
        
        results[name] = {
            "model": model,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": roc_auc
        }
        
        logger.info(f"[{name}] Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | AUC: {roc_auc:.4f}")
        
    # Compare and select best model based on F1-score (or ROC AUC)
    best_name = max(results, key=lambda k: results[k]['f1'])
    best_model_data = results[best_name]
    logger.info(f"Best model selected: {best_name} with F1-score of {best_model_data['f1']:.4f}")
    
    # Phase 5: Model Persistence
    logger.info("=== Phase 5: Model Persistence ===")
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    best_model_path = os.path.join(MODELS_DIR, "best_churn_model.pkl")
    preprocessor_path = os.path.join(MODELS_DIR, "preprocessor.pkl")
    
    joblib.dump(best_model_data['model'], best_model_path)
    joblib.dump(preprocessor, preprocessor_path)
    
    logger.info(f"Saved best model to {best_model_path}")
    logger.info(f"Saved preprocessor to {preprocessor_path}")
    
    # Save training report comparison
    report_path = os.path.join(MODELS_DIR, "model_comparison_report.txt")
    with open(report_path, "w") as f:
        f.write("=== Model Comparison Report ===\n\n")
        for name, metrics in results.items():
            f.write(f"--- {name} ---\n")
            f.write(f"Accuracy:  {metrics['accuracy']:.4f}\n")
            f.write(f"Precision: {metrics['precision']:.4f}\n")
            f.write(f"Recall:    {metrics['recall']:.4f}\n")
            f.write(f"F1 Score:  {metrics['f1']:.4f}\n")
            f.write(f"ROC AUC:   {metrics['roc_auc']:.4f}\n\n")
        f.write(f"Selected Best Model: {best_name}\n")
    logger.info(f"Comparison report saved to {report_path}")

def main():
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Could not find dataset at {DATASET_PATH}. Please check folder structure.")
        return
        
    logger.info(f"Dataset located successfully at {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    
    explore_dataset(df)
    cleaned_df = clean_data(df)
    X_train, X_test, y_train, y_test, preprocessor, feature_names = feature_engineering(cleaned_df)
    train_and_evaluate(X_train, X_test, y_train, y_test, preprocessor, feature_names)

if __name__ == "__main__":
    main()
