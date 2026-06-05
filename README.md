# SilentChurn AI – Behavioral Disengagement Detection Platform

SilentChurn AI is an AI-powered SaaS customer retention platform that identifies disengaged users ("silent churn") before they cancel their subscriptions. The system computes user health scores, trains churn prediction models, provides explainable insights via SHAP, and uses LLMs to generate personalized retention outreach recommendations.

---

## 📂 Folder Structure

```
.
├── README.md
├── .gitignore
├── requirements.txt
├── backend/
│   ├── api/
│   │   ├── database/
│   │   │   ├── session.py
│   │   │   └── models.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   ├── users.py
│   │   │   ├── predictions.py
│   │   │   └── recommendations.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── analytics.py
│   │   │   └── recommendation.py
│   │   ├── config.py
│   │   └── main.py
│   └── ml/
│       ├── data_generator.py
│       ├── preprocessing.py
│       ├── engagement_score.py
│       ├── health_score.py
│       ├── silent_churn.py
│       ├── train_model.py
│       ├── predict.py
│       ├── shap_analysis.py
│       └── recommendation_engine.py
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── Navbar.jsx
        │   ├── MetricCard.jsx
        │   ├── ChurnRiskChart.jsx
        │   └── SilentChurnTable.jsx
        ├── pages/
        │   ├── Dashboard.jsx
        │   ├── UserAnalysis.jsx
        │   ├── SilentChurn.jsx
        │   └── Recommendations.jsx
        └── services/
            ├── api.js
            └── auth.js
```

---

## 🗄️ Database Schema (PostgreSQL)

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) NOT NULL, -- "Free", "Growth", "Enterprise"
    status VARCHAR(50) NOT NULL, -- "active", "inactive", "churned"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- User Activity Logs
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL, -- "login", "export", "report_generation", "invite_member"
    timestamp TIMESTAMP NOT NULL,
    session_duration_sec INTEGER NOT NULL
);

-- Daily Engagement & Health Metrics
CREATE TABLE engagement_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    login_count INTEGER DEFAULT 0,
    active_time_seconds INTEGER DEFAULT 0,
    features_used_count INTEGER DEFAULT 0,
    support_tickets_count INTEGER DEFAULT 0,
    engagement_score FLOAT NOT NULL,
    health_score FLOAT NOT NULL
);

-- Churn Predictions & Explainability
CREATE TABLE churn_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    churn_probability FLOAT NOT NULL,
    risk_level VARCHAR(50) NOT NULL, -- "High", "Medium", "Low"
    silent_churn_flag BOOLEAN DEFAULT FALSE,
    shap_values JSONB, -- stores key SHAP contributions
    key_features JSONB -- list of top disengagement drivers
);

-- AI Retention Recommendations
CREATE TABLE retention_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    risk_driver VARCHAR(255) NOT NULL,
    recommendation_text TEXT NOT NULL,
    action_type VARCHAR(100) NOT NULL, -- "email_campaign", "discount_offer", "csm_call"
    status VARCHAR(50) DEFAULT 'pending', -- "pending", "executed", "dismissed"
    source VARCHAR(50) DEFAULT 'groq_llm'
);
```

---

## 📡 REST API Documentation

### Auth Router
- `POST /api/v1/auth/login` -> Logs in the CSM/admin user.

### Dashboard Router
- `GET /api/v1/dashboard/overview` -> High-level stats: Total users, Active, At Risk, Silent Churners, Avg Health Score, Risk Distribution.
- `GET /api/v1/dashboard/trends?days=30` -> Timeline metrics of average scores.

### Users Router
- `GET /api/v1/users` -> Paginated list of users.
- `GET /api/v1/users/{id}` -> Specific user profile.
- `GET /api/v1/users/{id}/metrics` -> Time-series metrics for engagement graphs.

### Predictions Router
- `POST /api/v1/predictions/trigger-run` -> Triggers the ML pipeline to re-predict churn.
- `GET /api/v1/predictions/{user_id}/shap` -> Fetches SHAP explanation for the user.

### Recommendations Router
- `GET /api/v1/recommendations` -> Active retention recommendations.
- `POST /api/v1/recommendations/generate/{user_id}` -> Calls Groq API to generate an LLM recommendation.
- `PATCH /api/v1/recommendations/{id}` -> Updates recommendation status.

---

## 🚀 Development Roadmap

* **Phase 1: Foundations & ML Engine (Days 1–5)**
  * Initialize PostgreSQL DB and write schema definitions in FastAPI.
  * Implement Python activity simulator (`data_generator.py`).
  * Code formulas for engagement and health scoring.
  * Develop XGBoost/Random Forest models (`train_model.py`) and prediction scripts.
* **Phase 2: SHAP Analysis & LLM Integration (Days 6–9)**
  * Generate SHAP graphs and extract key features per user.
  * Integrate Groq API (using Llama 3) for personalized recommendations.
  * Expose ML operations as callable modules.
* **Phase 3: FastAPI Backend Services (Days 10–12)**
  * Implement routers for Auth, Users, Dashboard, and AI Recommendations.
  * Add background tasks for periodic model inference.
* **Phase 4: Frontend Development (Days 13–15)**
  * Build dark-themed Tailwind CSS dashboard in Vite/React.
  * Wire Chart.js / Recharts with backend APIs.
  * Add the Recommendations Workspace page for Customer Success Managers.
