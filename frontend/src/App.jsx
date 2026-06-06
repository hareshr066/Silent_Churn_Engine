import React from 'react'
import { HashRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import SilentChurn from './pages/SilentChurn'
import UserAnalysis from './pages/UserAnalysis'
import Recommendations from './pages/Recommendations'
import { LayoutDashboard, Users, AlertTriangle, Lightbulb, Activity } from 'lucide-react'

function AppLayout() {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Overview', icon: LayoutDashboard },
    { path: '/silent-churn', label: 'Silent Churn', icon: AlertTriangle },
    { path: '/users', label: 'User Analysis', icon: Users },
    { path: '/recommendations', label: 'Retention Plays', icon: Lightbulb },
  ]
  
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800/80 flex flex-col justify-between">
        <div>
          <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
              SilentChurn AI
            </span>
          </div>
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-250 ${
                    isActive
                      ? 'bg-gradient-to-r from-violet-600/10 to-indigo-600/10 border-l-2 border-violet-500 text-violet-300 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
        
        <div className="p-4 border-t border-slate-800/80">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-950/40 border border-slate-800/50">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></div>
            <div className="text-xs text-slate-400">
              <span className="font-semibold block text-slate-300">ML Engine Local</span>
              <span>Atlas Fallback Active</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-slate-950">
        <header className="h-16 border-b border-slate-800/80 bg-slate-900/30 flex items-center justify-between px-8">
          <h1 className="text-base font-semibold text-slate-200">
            Customer Disengagement Hub
          </h1>
          <div className="text-xs bg-slate-900 border border-slate-800 px-3 py-1 rounded-full text-slate-400">
            Engine Status: <span className="text-emerald-400 font-semibold">Active</span>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/silent-churn" element={<SilentChurn />} />
            <Route path="/users" element={<UserAnalysis />} />
            <Route path="/recommendations" element={<Recommendations />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  )
}

export default App
