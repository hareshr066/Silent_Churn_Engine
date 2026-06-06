import React, { useState, useEffect } from 'react'
import { AlertCircle, User, ShieldAlert, ArrowRight, ShieldCheck, Mail } from 'lucide-react'

const API_BASE = 'http://localhost:8000/api'

export default function SilentChurn() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedUser, setSelectedUser] = useState(null)
  const [userDetail, setUserDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/users?risk_filter=Silent Churn&limit=50`)
      .then((res) => {
        if (!res.ok) throw new Error('API server unreachable')
        return res.json()
      })
      .then((data) => {
        setUsers(data.users || [])
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        // Load high-quality mock silent churn users on connection failure
        setUsers([
          { customerID: '7590-VHVEG', gender: 'Female', tenure: 1, Contract: 'Month-to-month', InternetService: 'DSL', MonthlyCharges: 29.85, churn_probability: 0.6428, silent_churn_flag: true },
          { customerID: '5375-MGPIS', gender: 'Male', tenure: 4, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 80.85, churn_probability: 0.7612, silent_churn_flag: true },
          { customerID: '1092-HSHKR', gender: 'Female', tenure: 12, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 95.05, churn_probability: 0.8124, silent_churn_flag: true },
          { customerID: '3192-NQQCA', gender: 'Female', tenure: 2, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 84.15, churn_probability: 0.7258, silent_churn_flag: true },
          { customerID: '9231-LKABW', gender: 'Male', tenure: 3, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 90.35, churn_probability: 0.6942, silent_churn_flag: true }
        ])
        setLoading(false)
      })
  }, [])

  const handleUserClick = (user) => {
    setSelectedUser(user)
    setDetailLoading(true)
    fetch(`${API_BASE}/users/${user.customerID}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch profile')
        return res.json()
      })
      .then((data) => {
        setUserDetail(data)
        setDetailLoading(false)
      })
      .catch((err) => {
        console.error(err)
        // Local mock detail fallback
        setTimeout(() => {
          setUserDetail({
            profile: {
              customerID: user.customerID,
              gender: user.gender,
              SeniorCitizen: 0,
              Partner: 'No',
              Dependents: 'No',
              tenure: user.tenure,
              PhoneService: 'Yes',
              MultipleLines: 'No',
              InternetService: user.InternetService,
              OnlineSecurity: 'No',
              OnlineBackup: 'No',
              DeviceProtection: 'No',
              TechSupport: 'No',
              StreamingTV: 'No',
              StreamingMovies: 'No',
              Contract: user.Contract,
              PaperlessBilling: 'Yes',
              PaymentMethod: 'Electronic check',
              MonthlyCharges: user.MonthlyCharges,
              TotalCharges: (user.MonthlyCharges * user.tenure).toFixed(2)
            },
            prediction: {
              prediction: 'Churn',
              churn_probability: user.churn_probability,
              silent_churn_flag: true
            },
            explainability: {
              top_risk_factors: [
                "Contract is 'Month-to-month'",
                "Tech Support is 'No'",
                user.InternetService === 'Fiber optic' ? "Internet Service is 'Fiber optic'" : "Short Subscription Duration (Tenure)",
                "Online Security is 'No'",
                "Payment Method is 'Electronic check'"
              ]
            },
            recommendation: "Target for 1-year contract migration. Offer 15% discount on annual commitment."
          })
          setDetailLoading(false)
        }, 300)
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
    <div className="space-y-6 animate-fadeIn relative">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-500" />
            Silent Churn Detection
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Accounts displaying high behavioral disengagement: Month-to-month contracts, no security/support additions, and high churn probability.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main List */}
        <div className="lg:col-span-2 space-y-4">
          {users.length === 0 ? (
            <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl text-center">
              <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
              <p className="text-sm text-slate-300 font-semibold">Zero Silent Churn Alerts</p>
              <p className="text-xs text-slate-500 mt-1">All month-to-month users have active engagement metrics.</p>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800/80 rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-900/40 text-xs text-slate-400 font-medium uppercase tracking-wider">
                      <th className="py-4 px-6">Customer ID</th>
                      <th className="py-4 px-6">Tenure</th>
                      <th className="py-4 px-6">Charges</th>
                      <th className="py-4 px-6">Risk Rate</th>
                      <th className="py-4 px-6 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {users.map((user) => (
                      <tr
                        key={user.customerID}
                        onClick={() => handleUserClick(user)}
                        className={`hover:bg-slate-800/20 cursor-pointer transition-colors ${
                          selectedUser?.customerID === user.customerID ? 'bg-violet-900/10' : ''
                        }`}
                      >
                        <td className="py-4 px-6 font-medium text-slate-300 flex items-center gap-2">
                          <User className="w-3.5 h-3.5 text-slate-500" />
                          {user.customerID}
                        </td>
                        <td className="py-4 px-6 text-xs text-slate-400">{user.tenure} months</td>
                        <td className="py-4 px-6 text-xs text-slate-300 font-medium">${user.MonthlyCharges.toFixed(2)}/mo</td>
                        <td className="py-4 px-6">
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            {(user.churn_probability * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <button className="p-1.5 hover:bg-slate-800 rounded-lg text-violet-400 hover:text-violet-300 transition-colors">
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Side Detail Panel / Drawer */}
        <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 h-fit">
          {!selectedUser ? (
            <div className="text-center py-12 text-slate-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-xs">Select a customer profile from the list to display SHAP risk explanations and retention strategies.</p>
            </div>
          ) : detailLoading ? (
            <div className="flex justify-center items-center py-20">
              <div className="w-8 h-8 border-3 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : userDetail ? (
            <div className="space-y-6">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Customer Details</span>
                <h3 className="text-lg font-bold text-slate-200 mt-1">{userDetail.profile.customerID}</h3>
                <div className="grid grid-cols-2 gap-4 mt-3 text-xs bg-slate-950/40 p-3 rounded-xl border border-slate-800/50">
                  <div>
                    <span className="text-slate-500 block">Contract</span>
                    <span className="text-slate-300">{userDetail.profile.Contract}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Internet Service</span>
                    <span className="text-slate-300">{userDetail.profile.InternetService}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Tech Support</span>
                    <span className="text-slate-300">{userDetail.profile.TechSupport}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Monthly charges</span>
                    <span className="text-slate-300">${userDetail.profile.MonthlyCharges}</span>
                  </div>
                </div>
              </div>

              {/* Explainability Section */}
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Disengagement Drivers (SHAP)</span>
                <ul className="space-y-2 mt-2">
                  {userDetail.explainability.top_risk_factors.map((factor, idx) => (
                    <li key={idx} className="text-xs flex items-start gap-2 bg-rose-950/10 border border-rose-500/10 p-2.5 rounded-lg text-rose-300">
                      <span className="font-bold text-rose-400">•</span>
                      <span>{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recommendation Playbook */}
              <div className="p-4 bg-gradient-to-br from-violet-600/15 to-indigo-600/15 border border-violet-500/20 rounded-xl">
                <span className="text-[10px] uppercase font-bold tracking-wider text-violet-400 block mb-1">Recommended Retention Play</span>
                <p className="text-xs text-slate-300 leading-relaxed font-medium">{userDetail.recommendation}</p>
                
                <button className="w-full mt-4 flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold py-2.5 px-4 rounded-lg transition-colors shadow-md shadow-violet-500/10">
                  <Mail className="w-3.5 h-3.5" />
                  Trigger Retention Play
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
