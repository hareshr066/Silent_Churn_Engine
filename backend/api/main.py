"""
SilentChurn AI - FastAPI Backend Application
Exposes REST API endpoints for the React frontend, interfacing with MongoDB Atlas
(or local JSON fallback) to serve dashboard statistics, customer listings,
real-time churn prediction, and SHAP explainability.
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.database.mongodb import db_manager
from backend.ml.predict import predict_customer
from backend.ml.shap_analysis import explain_prediction
from backend.ml.recommendation_engine import generate_recommendation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SilentChurn AI ML Engine API",
    description="Backend API for customer disengagement detection and churn prediction.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL (e.g., http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas for Input Validation ---

class CustomerInput(BaseModel):
    customerID: Optional[str] = "9999-CUSTOM"
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: str

# --- API Endpoints ---

@app.get("/")
def read_root():
    db = db_manager.get_database()
    is_fallback = getattr(db_manager, "is_fallback", False)
    return {
        "status": "online",
        "service": "SilentChurn AI ML Backend",
        "database_mode": "Local JSON Fallback" if is_fallback else "MongoDB Atlas Cloud"
    }

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Returns aggregated KPIs and distributions for the dashboard widgets."""
    try:
        db = db_manager.get_database()
        cleaned_col = db["cleaned_dataset"]
        predictions_col = db["predictions"]
        
        total_users = cleaned_col.count_documents({})
        if total_users == 0:
            return {
                "total_customers": 0,
                "active_customers": 0,
                "at_risk_customers": 0,
                "silent_churn_customers": 0,
                "avg_churn_risk": 0.0,
                "churn_distribution": {"Low": 0, "Medium": 0, "High": 0}
            }
            
        # Aggregate predictions
        predictions = list(predictions_col.find({}))
        
        at_risk = 0
        silent_churn = 0
        total_prob = 0.0
        
        dist = {"Low": 0, "Medium": 0, "High": 0}
        
        for p in predictions:
            prob = p.get("churn_probability", 0.0)
            pred = p.get("prediction", "No Churn")
            is_silent = p.get("silent_churn_flag", False)
            
            total_prob += prob
            
            if pred == "Churn" or prob >= 0.5:
                at_risk += 1
            if is_silent:
                silent_churn += 1
                
            if prob < 0.3:
                dist["Low"] += 1
            elif prob < 0.6:
                dist["Medium"] += 1
            else:
                dist["High"] += 1
                
        avg_risk = total_prob / len(predictions) if predictions else 0.0
        active = total_users - at_risk
        
        return {
            "total_customers": total_users,
            "active_customers": active,
            "at_risk_customers": at_risk,
            "silent_churn_customers": silent_churn,
            "avg_churn_risk": round(avg_risk, 4),
            "churn_distribution": dist
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users")
def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    search: Optional[str] = None,
    risk_filter: str = Query("All")
):
    """Returns a paginated and filtered list of users with their predictions."""
    try:
        db = db_manager.get_database()
        cleaned_col = db["cleaned_dataset"]
        predictions_col = db["predictions"]
        
        # Build query for search
        query = {}
        if search:
            query["customerID"] = {"$regex": search, "$options": "i"} if not getattr(db_manager, "is_fallback", False) else search
            
        # Handle fallback vs real mongo search behavior
        if getattr(db_manager, "is_fallback", False) and search:
            # Local json regex fallback
            all_records = cleaned_col.find({})
            cleaned_records = [r for r in all_records if search.lower() in str(r.get("customerID", "")).lower()]
        else:
            cleaned_records = list(cleaned_col.find(query))
            
        # Map prediction attributes to cleaned records
        predictions = {p["user_id"]: p for p in predictions_col.find({})}
        
        users_list = []
        for r in cleaned_records:
            cid = r.get("customerID")
            pred = predictions.get(cid, {
                "prediction": "No Churn",
                "churn_probability": 0.0,
                "silent_churn_flag": False
            })
            
            prob = pred.get("churn_probability", 0.0)
            is_silent = pred.get("silent_churn_flag", False)
            
            # Apply risk filter
            if risk_filter == "Low" and prob >= 0.3:
                continue
            elif risk_filter == "Medium" and (prob < 0.3 or prob >= 0.6):
                continue
            elif risk_filter == "High" and prob < 0.6:
                continue
            elif risk_filter == "Silent Churn" and not is_silent:
                continue
            elif risk_filter == "At Risk" and pred.get("prediction") != "Churn":
                continue
                
            users_list.append({
                "customerID": cid,
                "gender": r.get("gender"),
                "tenure": int(r.get("tenure", 0)),
                "Contract": r.get("Contract"),
                "InternetService": r.get("InternetService"),
                "MonthlyCharges": float(r.get("MonthlyCharges", 0.0)),
                "TotalCharges": r.get("TotalCharges"),
                "churn_probability": prob,
                "prediction": pred.get("prediction"),
                "silent_churn_flag": is_silent
            })
            
        # Pagination
        total = len(users_list)
        start = (page - 1) * limit
        end = start + limit
        paginated_users = users_list[start:end]
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "users": paginated_users
        }
    except Exception as e:
        logger.error(f"Error fetching users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}")
def get_user_profile(user_id: str):
    """Returns detailed demographic, usage, predictions, and SHAP drivers for a customer."""
    try:
        db = db_manager.get_database()
        cleaned_col = db["cleaned_dataset"]
        predictions_col = db["predictions"]
        
        user = cleaned_col.find_one({"customerID": user_id})
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
            
        # Remove DB keys
        user_data = dict(user)
        if "_id" in user_data:
            del user_data["_id"]
            
        # Fetch or compute predictions
        pred = predictions_col.find_one({"user_id": user_id})
        if not pred:
            # Compute on the fly
            pred = predict_customer(user_data)
            
        # Compute SHAP explanation dynamically
        shap_explanation = explain_prediction(user_data)
        
        # Fetch active recommendations
        rec_col = db["recommendations"]
        rec = rec_col.find_one({"user_id": user_id})
        if not rec and pred.get("prediction") == "Churn":
            rec = generate_recommendation(user_data, pred)
            
        return {
            "profile": user_data,
            "prediction": {
                "prediction": pred.get("prediction"),
                "churn_probability": pred.get("churn_probability"),
                "silent_churn_flag": pred.get("silent_churn_flag", False)
            },
            "explainability": shap_explanation,
            "recommendation": rec.get("recommendation") if rec else "No active risk-mitigation recommended."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching user profile {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
def get_recommendations(limit: int = Query(20, ge=1)):
    """Returns a list of high-risk customers and their retention plans."""
    try:
        db = db_manager.get_database()
        rec_col = db["recommendations"]
        cleaned_col = db["cleaned_dataset"]
        
        records = list(rec_col.find({}))
        # Sort recommendations by churn probability descending
        records.sort(key=lambda x: x.get("churn_probability", 0.0), reverse=True)
        records = records[:limit]
        
        # Load user contract & monthly charges details
        user_ids = [r["user_id"] for r in records]
        users = {u["customerID"]: u for u in cleaned_col.find({"customerID": {"$in": user_ids}})}
        
        results = []
        for r in records:
            uid = r["user_id"]
            user = users.get(uid, {})
            results.append({
                "user_id": uid,
                "recommendation": r.get("recommendation"),
                "risk_driver": r.get("risk_driver"),
                "churn_probability": r.get("churn_probability"),
                "contract": user.get("Contract", "Unknown"),
                "monthly_charges": user.get("MonthlyCharges", 0.0),
                "tenure": user.get("tenure", 0)
            })
            
        return results
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict")
def run_realtime_prediction(customer: CustomerInput):
    """On-demand prediction endpoint for a new/custom customer input."""
    try:
        data = customer.model_dump()
        result = predict_customer(data)
        
        # Check if high-risk and trigger recommendations
        rec_text = "No action needed."
        risk_drivers = []
        if result.get("prediction") == "Churn":
            shap_res = explain_prediction(data)
            risk_drivers = shap_res.get("top_risk_factors", [])
            rec_doc = generate_recommendation(data, result)
            rec_text = rec_doc.get("recommendation")
            
        return {
            "prediction": result.get("prediction"),
            "churn_probability": result.get("churn_probability"),
            "top_risk_drivers": risk_drivers,
            "recommendation": rec_text
        }
    except Exception as e:
        logger.error(f"Realtime prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
