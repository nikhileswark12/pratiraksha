import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import PratirakshaDashboard from './components/PratirakshaDashboard';
import HospitalList from './components/HospitalList';
import HospitalDetail from './components/HospitalDetail';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import EHRIntegration from './components/EHRIntegration';
import CrisisSimulation from './components/CrisisSimulation';
import { Activity, LogOut } from 'lucide-react';

function Layout({ user, token, onLogout, children }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Activity className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg leading-tight">Pratiraksha</h1>
                <p className="text-xs text-slate-500 font-mono capitalize">Role: {user?.role || 'Unknown'}</p>
              </div>
            </Link>
            
            <nav className="hidden md:flex gap-4 ml-6">
              <Link to="/" className="text-sm font-medium text-slate-600 hover:text-blue-600">Dashboard</Link>
              <Link to="/hospitals" className="text-sm font-medium text-slate-600 hover:text-blue-600">Hospitals</Link>
              <Link to="/ehr" className="text-sm font-medium text-slate-600 hover:text-blue-600">EHR Integration</Link>
              <Link to="/analytics" className="text-sm font-medium text-slate-600 hover:text-blue-600">Analytics</Link>
              <Link to="/crisis" className="text-sm font-medium text-slate-600 hover:text-blue-600">Crisis Simulation</Link>
            </nav>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={onLogout} className="text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-2 text-sm font-medium">
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        </div>
      </header>
      <main>
        {children}
      </main>
    </div>
  );
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [user, setUser] = useState(null); // Assuming user state might be needed globally
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/v1/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      let data;
      try {
        data = await res.json();
      } catch (parseErr) {
        throw new Error(`Server returned ${res.status} ${res.statusText}`);
      }
      if (res.ok) {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setToken(data.access);
      } else {
        setError(data.error || data.detail || `Login failed: ${res.status} ${res.statusText}`);
      }
    } catch (err) {
      setError(err.message === 'Failed to fetch' ? 'Connection error - Backend unreachable' : err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 max-w-sm w-full">
          <h1 className="text-2xl font-bold text-slate-900 mb-6 text-center">Pratiraksha Login</h1>
          {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">{error}</div>}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white font-medium py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Sign In
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Layout user={user} token={token} onLogout={handleLogout}>
        <Routes>
          <Route path="/" element={<PratirakshaDashboard token={token} onLogout={handleLogout} onUserLoaded={setUser} />} />
          <Route path="/hospitals" element={<HospitalList token={token} />} />
          <Route path="/hospitals/:id" element={<HospitalDetail token={token} />} />
          <Route path="/analytics" element={<AnalyticsDashboard token={token} />} />
          <Route path="/ehr" element={<EHRIntegration token={token} />} />
          <Route path="/crisis" element={<CrisisSimulation token={token} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
