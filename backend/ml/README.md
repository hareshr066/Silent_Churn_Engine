# SilentChurn AI – Machine Learning & Prediction Engine

This folder contains the machine learning pipelines for predicting customer churn and generating explainable feature-level justifications (SHAP values).

---

## 📊 Dataset Description
The model uses the **Telco Customer Churn** dataset.
* **Size**: 7,043 rows, 21 columns
* **Target Class**: `Churn` (Yes/No) - indicating whether the customer left within the last month.
* **Class Balance**: 73.46% Active (`No`), 26.54% Churned (`Yes`).

---

## 🧼 Data Cleaning & Preprocessing Steps
1. **Deduplication**: Automatically identified and dropped duplicate customer rows (if any).
2. **Type Correction**: Coerced `TotalCharges` from string/object to numerical data type.
3. **Missing Value Imputation**: Imputed missing `TotalCharges` values (typically corresponding to new users with a `tenure` of `0` months) with `0.0`.
4. **ID Exclusion**: Dropped the unique identifier `customerID` from training features.
5. **Categorical Encoding**: Categorical columns were encoded using Scikit-Learn's `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` to prevent downstream key errors.
6. **Numerical Scaling**: Numerical features (`tenure`, `MonthlyCharges`, `TotalCharges`) were standard scaled using `StandardScaler` to ensure stability in algorithms sensitive to feature magnitudes.

---

## 🛠️ Features Used

### Numerical Features
* `tenure` (Number of months the customer has stayed with the company)
* `MonthlyCharges` (The amount charged to the customer monthly)
* `TotalCharges` (The total amount charged to the customer)

### Categorical Features
* Demographics: `gender`, `SeniorCitizen`, `Partner`, `Dependents`
* Services: `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`
* Account Profile: `Contract` (Month-to-month, One year, Two year), `PaperlessBilling`, `PaymentMethod`

---

## 📈 Model Comparison & Metrics

We compared `RandomForestClassifier` (with class weighting to handle imbalance) and `XGBoostClassifier` using an 80/20 train/test split:

| Metric | RandomForest | XGBoost (Best Model) |
| :--- | :--- | :--- |
| **Accuracy** | 79.06% | **79.70%** |
| **Precision** | 63.96% | **65.07%** |
| **Recall** | 48.40% | **50.80%** |
| **F1 Score** | 0.5510 | **0.5706** |
| **ROC AUC** | 0.8222 | **0.8432** |

* **Selection**: XGBoost was selected as the production model due to superior F1 Score (**0.5706**) and ROC-AUC (**0.8432**).

---

## 🚀 How to Run Training
To execute the data preprocessing, training, model evaluation, and saving steps:
```bash
python backend/ml/train_model.py
```
This script saves the following artifacts:
* Preprocessed data: `datasets/cleaned_churn_data.csv`
* Model comparison summary: `models/model_comparison_report.txt`
* Serialized Model: `models/best_churn_model.pkl`
* Preprocessing Pipeline: `models/preprocessor.pkl`

---

## 🔮 How to Run Predictions
To fetch a churn prediction for a customer:
```python
from backend.ml.predict import predict_customer

customer = {
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

result = predict_customer(customer)
print(result)
# Output: {'churn_probability': 0.6428, 'prediction': 'Churn'}
```

---

## 🔍 How to Run Explainability (SHAP)
To fetch the key features driving the risk of churn for a customer:
```python
from backend.ml.shap_analysis import explain_prediction

result = explain_prediction(customer)
print(result)
# Output: {'top_risk_factors': ["Contract is 'Month-to-month'", 'Short Subscription Duration (Tenure)', 'High Total Spend', "Tech Support is 'No'", "Online Security is 'No'"]}
```
