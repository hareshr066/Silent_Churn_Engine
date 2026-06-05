"""
SilentChurn AI - Recommendation Engine
This module generates personalized retention recommendations for customers 
at risk of churning, using their prediction probabilities and key disengagement drivers (SHAP).
It persists the recommendations in the MongoDB Atlas database.
"""

import os
import logging
from datetime import datetime, timezone

# Import MongoDB connection and ML modules
from backend.database.mongodb import db_manager
from backend.ml.predict import predict_customer
from backend.ml.shap_analysis import explain_prediction

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_recommendation(customer_data: dict, prediction_result: dict = None) -> dict:
    """
    Generates personalized retention actions for a customer based on their churn risk and drivers.
    Persists the recommendation in the MongoDB 'recommendations' collection.
    
    Args:
        customer_data (dict): Raw feature details for the customer.
        prediction_result (dict, optional): Churn prediction results. If not provided, computed on the fly.
        
    Returns:
        dict: Recommendation document stored in the database.
    """
    try:
        user_id = str(customer_data.get("user_id", customer_data.get("customerID", "unknown")))
        
        # 1. Get prediction result if not provided
        if prediction_result is None:
            prediction_result = predict_customer(customer_data)
            
        churn_prob = prediction_result.get("churn_probability", 0.0)
        prediction_label = prediction_result.get("prediction", "No Churn")
        
        # 2. Determine recommendation strategy
        recommendation_text = ""
        risk_driver = "None"
        
        if prediction_label == "Churn" or churn_prob >= 0.5:
            # High-risk customer: Get explainable drivers using SHAP
            shap_result = explain_prediction(customer_data)
            top_drivers = shap_result.get("top_risk_factors", [])
            
            # Map top drivers to recommended retention playbook
            if top_drivers:
                primary_driver = top_drivers[0]
                risk_driver = primary_driver
                
                if "Month-to-month" in primary_driver:
                    recommendation_text = "Target for 1-year or 2-year contract migration. Offer a 15% promotional discount on annual commitment."
                elif "Tenure" in primary_driver:
                    recommendation_text = "New customer onboarding alert. Assign customer success manager to schedule a walkthrough call."
                elif "Tech Support" in primary_driver:
                    recommendation_text = "Proactively offer a free 30-day trial of Premium Tech Support and setup assistance."
                elif "Online Security" in primary_driver:
                    recommendation_text = "Recommend upgrading security options. Highlight free security suite tools included in their plan."
                elif "Fiber optic" in primary_driver:
                    recommendation_text = "Initiate proactive technical health check. Fiber optic users exhibit high relative churn rates; verify service stability."
                elif "Electronic check" in primary_driver:
                    recommendation_text = "Encourage setting up Auto-Pay via ACH bank transfer or credit card to prevent billing-failure churn."
                elif "Monthly Bill" in primary_driver or "Total Spend" in primary_driver:
                    recommendation_text = "Execute pricing optimization review. Offer an entry-level plan tier or cost mitigation option."
                else:
                    recommendation_text = f"Proactive Customer Success outreach to discuss user engagement regarding primary driver: {primary_driver}."
            else:
                # Churning but no significant SHAP drivers found
                recommendation_text = "Schedule standard Customer Success account health checkup."
                risk_driver = "General High Risk"
        else:
            # Low risk customer
            recommendation_text = "Maintain standard automated email marketing sequences and customer check-in intervals."
            risk_driver = "Low Risk"
            
        # 3. Save to MongoDB 'recommendations' collection
        rec_col = db_manager.get_collection("recommendations")
        recommendation_doc = {
            "user_id": user_id,
            "recommendation": recommendation_text,
            "risk_driver": risk_driver,
            "churn_probability": round(churn_prob, 4),
            "created_at": datetime.now(timezone.utc)
        }
        
        rec_col.insert_one(recommendation_doc)
        logger.info(f"Saved retention recommendation for user '{user_id}' to MongoDB recommendations collection.")
        
        # Format the document fields for response (clean ObjectId for serialization)
        if "_id" in recommendation_doc:
            recommendation_doc["_id"] = str(recommendation_doc["_id"])
            
        return recommendation_doc
        
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    # Test customer (month-to-month, fiber optic, no security/support, high billing)
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
        'MonthlyCharges': 85.0,
        'TotalCharges': '170.0'
    }
    
    print("Testing recommendation generation...")
    try:
        result = generate_recommendation(test_customer)
        print("Generated Recommendation Details:")
        if "created_at" in result and isinstance(result["created_at"], datetime):
            result["created_at"] = result["created_at"].isoformat()
        import json
        print(json.dumps(result, indent=2))
    finally:
        db_manager.close()
