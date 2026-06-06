import React, { useState, useEffect } from 'react'
import { Search, Filter, ChevronLeft, ChevronRight, User, Sparkles, RefreshCw, X, Play } from 'lucide-react'

const API_BASE = 'http://localhost:8000/api'

export default function UserAnalysis() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('All')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedUser, setSelectedUser] = useState(null)
  const [userDetail, setUserDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  
  // Simulator State
  const [simulatedData, setSimulatedData] = useState(null)
  const [simulating, setSimulating] = useState(false)
  const [simResult, setSimResult] = useState(null)

  useEffect(() => {
    setLoading(true)
    fetch(`${API_BASE}/users?page=${page}&search=${search}&risk_filter=${riskFilter}`)
      .then((res) => {
        if (!res.ok) throw new Error('API server unreachable')
        return res.json()
      })
      .then((data) => {
        setUsers(data.users || [])
        // Mock total calculation if backend returns 0 or fallback total
        const limit = data.limit || 20
        setTotalPages(Math.ceil((data.total || 100) / limit))
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        // Static mock fallback lists
        const mockUsers = [
          { customerID: '7590-VHVEG', gender: 'Female', tenure: 1, Contract: 'Month-to-month', InternetService: 'DSL', MonthlyCharges: 29.85, churn_probability: 0.6428, prediction: 'Churn', silent_churn_flag: true },
          { customerID: '5575-GNKDE', gender: 'Male', tenure: 34, Contract: 'One year', InternetService: 'DSL', MonthlyCharges: 56.95, churn_probability: 0.0412, prediction: 'No Churn', silent_churn_flag: false },
          { customerID: '3668-QPYBK', gender: 'Male', tenure: 2, Contract: 'Month-to-month', InternetService: 'DSL', MonthlyCharges: 53.85, churn_probability: 0.5184, prediction: 'Churn', silent_churn_flag: false },
          { customerID: '7795-CFOCW', gender: 'Male', tenure: 45, Contract: 'One year', InternetService: 'DSL', MonthlyCharges: 42.30, churn_probability: 0.0815, prediction: 'No Churn', silent_churn_flag: false },
          { customerID: '9237-HQITU', gender: 'Female', tenure: 2, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 70.70, churn_probability: 0.7354, prediction: 'Churn', silent_churn_flag: true },
          { customerID: '9305-CDSKC', gender: 'Female', tenure: 8, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 99.65, churn_probability: 0.8251, prediction: 'Churn', silent_churn_flag: true },
          { customerID: '1452-KIOVK', gender: 'Male', tenure: 22, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 89.10, churn_probability: 0.4510, prediction: 'No Churn', silent_churn_flag: false },
          { customerID: '6713-OKOMC', gender: 'Female', tenure: 10, Contract: 'Month-to-month', InternetService: 'DSL', MonthlyCharges: 29.75, churn_probability: 0.2185, prediction: 'No Churn', silent_churn_flag: false },
          { customerID: '7892-POOKP', gender: 'Female', tenure: 28, Contract: 'Month-to-month', InternetService: 'Fiber optic', MonthlyCharges: 104.80, churn_probability: 0.6120, prediction: 'Churn', silent_churn_flag: true }
        ]
        
        let filtered = mockUsers
        if (search) {
          filtered = filtered.filter(u => u.customerID.toLowerCase().includes(search.toLowerCase()))
        }
        if (riskFilter !== 'All') {
          filtered = filtered.filter(u => {
            if (riskFilter === 'Low') return u.churn_probability < 0.3
            if (riskFilter === 'Medium') return u.churn_probability >= 0.3 && u.churn_probability < 0.6
            if (riskFilter === 'High') return u.churn_probability >= 0.6
            if (riskFilter === 'Silent Churn') return u.silent_churn_flag
            return true
          })
        }
        
        setUsers(filtered)
        setTotalPages(1)
        setLoading(false)
      })
  }, [page, search, riskFilter])

  const handleUserSelect = (user) => {
    setSelectedUser(user)
    setDetailLoading(true)
    setSimResult(null)
    
    fetch(`${API_BASE}/users/${user.customerID}`)
      .then((res) => {
        if (!res.ok) throw new Error('API server unreachable')
        return res.json()
      })
      .then((data) => {
        setUserDetail(data)
        setSimulatedData({ ...data.profile })
        setDetailLoading(false)
      })
      .catch((err) => {
        console.error(err)
        // Mock detailed profile fallback
        setTimeout(() => {
          const detail = {
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
              OnlineBackup: 'Yes',
              DeviceProtection: 'No',
              TechSupport: 'No',
              StreamingTV: 'Yes',
              StreamingMovies: 'No',
              Contract: user.Contract,
              PaperlessBilling: 'Yes',
              PaymentMethod: 'Electronic check',
              MonthlyCharges: user.MonthlyCharges,
              TotalCharges: (user.MonthlyCharges * user.tenure).toFixed(2)
            },
            prediction: {
              prediction: user.prediction,
              churn_probability: user.churn_probability,
              silent_churn_flag: user.silent_churn_flag
            },
            explainability: {
              top_risk_factors: [
                `Contract is '${user.Contract}'`,
                "Tech Support is 'No'",
                user.InternetService === 'Fiber optic' ? "Internet Service is 'Fiber optic'" : "Short Subscription Duration (Tenure)",
                "Online Security is 'No'"
              ]
            },
            recommendation: "Offer migration to 1-year contract with free premium tech support trial."
          }
          setUserDetail(detail)
          setSimulatedData({ ...detail.profile })
          setDetailLoading(false)
        }, 300)
      })
  }

  const runSimulation = () => {
    setSimulating(true)
    fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(simulatedData)
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to run simulation')
        return res.json()
      })
      .then((data) => {
        setSimResult(data)
        setSimulating(false)
      })
      .catch((err) => {
        console.error(err)
        // Mock simulation result fallback: calculate simple heuristic
        setTimeout(() => {
          let prob = userDetail.prediction.churn_probability
          
          // Lower probability if contract changed to annual
          if (simulatedData.Contract !== userDetail.profile.Contract) {
            prob -= simulatedData.Contract === 'Two year' ? 0.35 : 0.20
          }
          // Lower probability if tech support or online security activated
          if (simulatedData.TechSupport === 'Yes' && userDetail.profile.TechSupport === 'No') {
            prob -= 0.12
          }
          if (simulatedData.OnlineSecurity === 'Yes' && userDetail.profile.OnlineSecurity === 'No') {
            prob -= 0.10
          }
          
          prob = Math.max(0.02, Math.min(0.98, prob))
          
          setSimResult({
            prediction: prob >= 0.5 ? 'Churn' : 'No Churn',
            churn_probability: prob,
            top_risk_drivers: prob >= 0.5 ? ['Month-to-month contract', 'High charges'] : [],
            recommendation: prob >= 0.5 ? 'Outreach required' : 'Client stabilized'
          })
          setSimulating(false)
        }, 500)
      })
  }

  const handleSimFieldChange = (key, value) => {
    setSimulatedData(prev => ({
      ...prev,
      [key]: value
    }))
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-slate-900 border border-slate-800 p-4 rounded-2xl">
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search customer ID..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-violet-500 transition-colors"
          />
        </div>

        <div className="flex gap-4 w-full md:w-auto justify-end">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={riskFilter}
              onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-violet-500"
            >
              <option value="All">All Severity Levels</option>
              <option value="Low">Low Risk (&lt;30%)</option>
              <option value="Medium">Medium Risk (30-60%)</option>
              <option value="High">High Risk (&gt;60%)</option>
              <option value="Silent Churn">Silent Churn Alerts</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Table List */}
        <div className="xl:col-span-2 space-y-4">
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl overflow-hidden">
            {loading ? (
              <div className="flex py-20 items-center justify-center">
                <div className="w-8 h-8 border-3 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : users.length === 0 ? (
              <div className="py-20 text-center text-slate-500">
                <User className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-xs">No customer records matching search parameters.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-900/40 text-xs text-slate-400 font-medium uppercase tracking-wider">
                      <th className="py-4 px-6">Customer</th>
                      <th className="py-4 px-6">Contract</th>
                      <th className="py-4 px-6">Internet</th>
                      <th className="py-4 px-6">Risk Factor</th>
                      <th className="py-4 px-6">Classification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {users.map((user) => (
                      <tr
                        key={user.customerID}
                        onClick={() => handleUserSelect(user)}
                        className={`hover:bg-slate-800/20 cursor-pointer transition-colors ${
                          selectedUser?.customerID === user.customerID ? 'bg-violet-950/15' : ''
                        }`}
                      >
                        <td className="py-4 px-6 font-medium text-slate-300 flex items-center gap-2">
                          <User className="w-3.5 h-3.5 text-slate-500" />
                          {user.customerID}
                        </td>
                        <td className="py-4 px-6 text-xs text-slate-400">{user.Contract}</td>
                        <td className="py-4 px-6 text-xs text-slate-400">{user.InternetService}</td>
                        <td className="py-4 px-6 text-xs font-semibold text-slate-300">
                          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                            user.churn_probability >= 0.6 ? 'bg-red-500' :
                            user.churn_probability >= 0.3 ? 'bg-amber-500' : 'bg-green-500'
                          }`}></span>
                          {(user.churn_probability * 100).toFixed(1)}%
                        </td>
                        <td className="py-4 px-6">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                            user.prediction === 'Churn' 
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' 
                              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          }`}>
                            {user.prediction}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center bg-slate-900 border border-slate-800 px-4 py-3 rounded-xl">
              <span className="text-xs text-slate-400">Page {page} of {totalPages}</span>
              <div className="flex gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage(prev => Math.max(1, prev - 1))}
                  className="p-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:hover:text-slate-400 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
                  className="p-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:hover:text-slate-400 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Drawer Detail & Simulation Panel */}
        <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-6 h-fit overflow-hidden">
          {!selectedUser ? (
            <div className="text-center py-20 text-slate-500">
              <Sparkles className="w-10 h-10 mx-auto mb-2 opacity-30 text-violet-400" />
              <p className="text-xs">Select a customer profile to launch the AI Disengagement Explainer & Retention Simulator.</p>
            </div>
          ) : detailLoading ? (
            <div className="flex justify-center items-center py-20">
              <div className="w-8 h-8 border-3 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : userDetail && simulatedData ? (
            <div className="space-y-6">
              <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500">Customer Assessment</span>
                  <h3 className="text-base font-bold text-slate-200">{userDetail.profile.customerID}</h3>
                </div>
                <button
                  onClick={() => setSelectedUser(null)}
                  className="p-1 hover:bg-slate-800 rounded-lg text-slate-500 hover:text-slate-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Churn Risk Gauge */}
              <div className="bg-slate-950/40 border border-slate-800/50 p-4 rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 block">Churn Risk Assessment</span>
                  <span className={`text-xl font-bold ${
                    userDetail.prediction.churn_probability >= 0.6 ? 'text-red-400' :
                    userDetail.prediction.churn_probability >= 0.3 ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {(userDetail.prediction.churn_probability * 100).toFixed(1)}% Churn Risk
                  </span>
                </div>
                <div className="text-xs">
                  <span className="text-slate-500 block">Status</span>
                  <span className={`font-semibold ${userDetail.prediction.prediction === 'Churn' ? 'text-red-400' : 'text-emerald-400'}`}>
                    {userDetail.prediction.prediction}
                  </span>
                </div>
              </div>

              {/* SHAP Factors */}
              <div>
                <span className="text-xs font-semibold text-slate-400 block mb-2">Primary Risk Factors (SHAP Analysis)</span>
                <div className="space-y-1.5">
                  {userDetail.explainability.top_risk_factors.map((factor, idx) => (
                    <div key={idx} className="text-xs bg-rose-950/15 border border-rose-500/10 px-3 py-2 rounded-lg text-rose-300">
                      {factor}
                    </div>
                  ))}
                </div>
              </div>

              {/* Interactive Simulator Section */}
              <div className="border-t border-slate-800 pt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-violet-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    Retention Playbook Simulator
                  </span>
                  <button
                    onClick={runSimulation}
                    disabled={simulating}
                    className="flex items-center gap-1 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-800 text-white text-[11px] font-bold py-1 px-2.5 rounded-lg transition-colors"
                  >
                    <Play className="w-3 h-3" />
                    {simulating ? 'Simulating...' : 'Run Prediction'}
                  </button>
                </div>

                <div className="space-y-3 bg-slate-950/50 p-4 rounded-xl border border-slate-800/80 text-xs">
                  {/* Select Contract */}
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Contract Plan</span>
                    <select
                      value={simulatedData.Contract}
                      onChange={(e) => handleSimFieldChange('Contract', e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-300"
                    >
                      <option value="Month-to-month">Month-to-month</option>
                      <option value="One year">One year</option>
                      <option value="Two year">Two year</option>
                    </select>
                  </div>

                  {/* Select Tech Support */}
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Tech Support</span>
                    <select
                      value={simulatedData.TechSupport}
                      onChange={(e) => handleSimFieldChange('TechSupport', e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-300"
                    >
                      <option value="Yes">Yes</option>
                      <option value="No">No</option>
                    </select>
                  </div>

                  {/* Select Online Security */}
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Online Security</span>
                    <select
                      value={simulatedData.OnlineSecurity}
                      onChange={(e) => handleSimFieldChange('OnlineSecurity', e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-300"
                    >
                      <option value="Yes">Yes</option>
                      <option value="No">No</option>
                    </select>
                  </div>
                </div>

                {/* Simulation Output Result */}
                {simResult && (
                  <div className="p-4 bg-slate-950 border border-violet-500/20 rounded-xl space-y-2 text-xs animate-slideDown">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Simulated Churn Risk:</span>
                      <span className={`font-bold ${simResult.churn_probability >= 0.5 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {(simResult.churn_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Classification:</span>
                      <span className={`font-semibold ${simResult.prediction === 'Churn' ? 'text-red-400' : 'text-emerald-400'}`}>
                        {simResult.prediction}
                      </span>
                    </div>
                    {simResult.churn_probability < userDetail.prediction.churn_probability ? (
                      <div className="text-[11px] text-emerald-400 font-medium bg-emerald-950/20 border border-emerald-500/10 px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 mt-2">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Probability reduced by {((userDetail.prediction.churn_probability - simResult.churn_probability) * 100).toFixed(1)}%! Action recommended.
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-400 bg-slate-900 px-2.5 py-1.5 rounded-lg mt-2">
                        No change in risk probability. Customize further fields to reduce risk.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
