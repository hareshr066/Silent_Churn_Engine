import React, { useState, useEffect } from 'react'
import { Lightbulb, Calendar, ArrowUpRight, DollarSign, Mail, CheckCircle2, UserCheck } from 'lucide-react'

const API_BASE = 'http://localhost:8000/api'

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [completedPlays, setCompletedPlays] = useState(new Set())

  useEffect(() => {
    fetch(`${API_BASE}/recommendations?limit=30`)
      .then((res) => {
        if (!res.ok) throw new Error('API server unreachable')
        return res.json()
      })
      .then((data) => {
        setRecommendations(data || [])
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        // High quality mock recommendations on connection failure
        setRecommendations([
          { user_id: '9237-HQITU', recommendation: 'Target for 1-year contract migration. Offer 15% discount on annual commitment.', risk_driver: "Contract is 'Month-to-month'", churn_probability: 0.7354, contract: 'Month-to-month', monthly_charges: 70.70, tenure: 2 },
          { user_id: '9305-CDSKC', recommendation: 'Conduct price optimization review. Suggest downgrading to Growth tier.', risk_driver: 'High Monthly Charges', churn_probability: 0.8251, contract: 'Month-to-month', monthly_charges: 99.65, tenure: 8 },
          { user_id: '7590-VHVEG', recommendation: 'Target for 1-year contract migration. Offer 15% discount on annual commitment.', risk_driver: "Contract is 'Month-to-month'", churn_probability: 0.6428, contract: 'Month-to-month', monthly_charges: 29.85, tenure: 1 },
          { user_id: '7892-POOKP', recommendation: 'Proactively offer premium Tech Support 30-day free trial.', risk_driver: 'No Tech Support', churn_probability: 0.6120, contract: 'Month-to-month', monthly_charges: 104.80, tenure: 28 },
          { user_id: '5375-MGPIS', recommendation: 'Conduct price optimization review. Suggest downgrading to Growth tier.', risk_driver: 'High Monthly Charges', churn_probability: 0.7612, contract: 'Month-to-month', monthly_charges: 80.85, tenure: 4 }
        ])
        setLoading(false)
      })
  }, [])

  const triggerOutreach = (userId) => {
    // Optimistically toggle action complete
    setCompletedPlays(prev => {
      const next = new Set(prev)
      if (next.has(userId)) {
        next.delete(userId)
      } else {
        next.add(userId)
      }
      return next
    })
  }

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-violet-400" />
          Proactive Retention Plays
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Personalized Customer Success playbooks generated dynamically from customer SHAP disengagement risk profiles.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {recommendations.map((rec) => {
          const isDone = completedPlays.has(rec.user_id)
          return (
            <div
              key={rec.user_id}
              className={`p-6 bg-slate-900 border rounded-2xl flex flex-col justify-between space-y-4 hover:border-slate-700 transition-all ${
                isDone ? 'border-emerald-500/30 bg-emerald-950/5' : 'border-slate-800'
              }`}
            >
              {/* Card Header */}
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500">Account ID</span>
                  <h3 className="text-sm font-bold text-slate-200">{rec.user_id}</h3>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${
                  rec.churn_probability >= 0.6
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                }`}>
                  {(rec.churn_probability * 100).toFixed(0)}% Risk
                </span>
              </div>

              {/* Account Quick Stats */}
              <div className="grid grid-cols-3 gap-2 py-2 bg-slate-950/40 border border-slate-800/50 rounded-xl text-center text-xs">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Tenure</span>
                  <span className="text-slate-300 font-medium">{rec.tenure} months</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Charges</span>
                  <span className="text-slate-300 font-medium">${rec.monthly_charges.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Plan</span>
                  <span className="text-slate-300 font-medium truncate max-w-[80px] block mx-auto">
                    {rec.contract}
                  </span>
                </div>
              </div>

              {/* Driver & Action */}
              <div className="space-y-2">
                <div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase block">Identified Driver</span>
                  <span className="text-xs text-rose-400 font-medium bg-rose-950/10 border border-rose-500/10 px-2 py-1 rounded-md mt-1 inline-block">
                    {rec.risk_driver}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase block">CSM Action Strategy</span>
                  <p className="text-xs text-slate-300 font-medium mt-1 leading-relaxed">
                    {rec.recommendation}
                  </p>
                </div>
              </div>

              {/* Actions Footer */}
              <div className="flex gap-4 pt-2 border-t border-slate-800/50">
                {isDone ? (
                  <button
                    onClick={() => triggerOutreach(rec.user_id)}
                    className="w-full flex items-center justify-center gap-2 bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold py-2.5 px-4 rounded-xl transition-colors"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Playbook Action Triggered
                  </button>
                ) : (
                  <button
                    onClick={() => triggerOutreach(rec.user_id)}
                    className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold py-2.5 px-4 rounded-xl transition-colors shadow-md shadow-violet-500/10"
                  >
                    <Mail className="w-4 h-4" />
                    Trigger Outreach
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
