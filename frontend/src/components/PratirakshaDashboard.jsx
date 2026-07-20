import React, { useState, useEffect, useRef } from 'react';
import { Activity, AlertTriangle, Building2, TrendingUp, Users, LogOut, Wifi, WifiOff } from 'lucide-react';

const getStatusColor = (status) => {
  switch (status?.toUpperCase()) {
    case 'CRITICAL': return 'bg-red-100 text-red-700 border-red-200';
    case 'WARNING': return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'NORMAL': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    default: return 'bg-slate-100 text-slate-700 border-slate-200';
  }
};

const getStatusDot = (status) => {
  switch (status?.toUpperCase()) {
    case 'CRITICAL': return 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]';
    case 'WARNING': return 'bg-amber-500';
    case 'NORMAL': return 'bg-emerald-500';
    default: return 'bg-slate-500';
  }
};

export default function PratirakshaDashboard({ token, onLogout, onUserLoaded }) {
  const [user, setUser] = useState(null);
  const [hospitals, setHospitals] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [flashingRows, setFlashingRows] = useState(new Set());
  const ws = useRef(null);

  useEffect(() => {
    // 1. Fetch User Data
    const fetchUser = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/auth/me/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
          if (onUserLoaded) onUserLoaded(data);
        } else if (res.status === 401) {
          onLogout();
        }
      } catch (err) {
        console.error('Failed to fetch user:', err);
      }
    };
    
    // 2. Fetch Hospitals
    const fetchHospitals = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/hospitals/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          // Handling paginated response as well
          setHospitals(data.results || data);
        }
      } catch (err) {
        console.error('Failed to fetch hospitals:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchUser().then(fetchHospitals);
  }, [token, onLogout, onUserLoaded]);

  // WebSocket Connection
  useEffect(() => {
    let reconnectTimeout;
    const connectWs = () => {
      ws.current = new WebSocket(`ws://localhost:8000/ws/hospitals/?token=${token}`);

      ws.current.onopen = () => {
        setIsConnected(true);
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'hospital.updated' || data.type === 'hospital.critical') {
          setHospitals(prev => {
            const updated = prev.map(h => h.id === data.hospital.id ? data.hospital : h);
            return updated;
          });
          
          // Flash animation
          setFlashingRows(prev => {
            const next = new Set(prev);
            next.add(data.hospital.id);
            return next;
          });
          setTimeout(() => {
            setFlashingRows(prev => {
              const next = new Set(prev);
              next.delete(data.hospital.id);
              return next;
            });
          }, 1000);
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        // Attempt reconnect
        reconnectTimeout = setTimeout(connectWs, 3000);
      };
    };

    connectWs();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [token]);

  // KPIs
  const totalHospitals = hospitals.length;
  const criticalCount = hospitals.filter(h => h.status === 'CRITICAL').length;
  const avgOccupancy = totalHospitals 
    ? Math.round(hospitals.reduce((acc, h) => acc + (h.current_occupancy / (h.total_capacity || 1)), 0) / totalHospitals * 100) 
    : 0;

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading dashboard...</div>;
  }

  return (
    <div className="bg-slate-50 text-slate-900 font-sans">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        
        {/* KPI Row */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-slate-200 shadow-sm">
            {isConnected ? (
              <>
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                <span className="text-sm font-medium text-slate-700">Live Dashboard</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-slate-400" />
                <span className="text-sm font-medium text-slate-500">Disconnected</span>
              </>
            )}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg"><Building2 className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Network Scope</p>
              <h3 className="text-2xl font-bold font-mono">{totalHospitals} <span className="text-sm font-normal text-slate-400">Facilities</span></h3>
            </div>
          </div>
          
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-red-50 text-red-600 rounded-lg"><AlertTriangle className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Critical Alerts</p>
              <h3 className="text-2xl font-bold font-mono text-red-600">{criticalCount} <span className="text-sm font-normal text-slate-400 text-slate-900">Active</span></h3>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg"><Users className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Avg Occupancy</p>
              <h3 className="text-2xl font-bold font-mono">{avgOccupancy}% <span className="text-sm font-normal text-slate-400">Capacity</span></h3>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-amber-50 text-amber-600 rounded-lg"><TrendingUp className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Active Predictions</p>
              {/* TODO: Day 7 - Wire this to the prediction API */}
              <h3 className="text-2xl font-bold font-mono">0 <span className="text-sm font-normal text-slate-400">Surges Expected</span></h3>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Table */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50">
              <h2 className="font-semibold text-slate-900">Live Hospital Status</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="px-6 py-3 font-medium">Hospital</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium">Occupancy</th>
                    <th className="px-6 py-3 font-medium text-right">Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {hospitals.map(hospital => {
                    const occupancyRatio = hospital.total_capacity > 0 ? (hospital.current_occupancy / hospital.total_capacity) * 100 : 0;
                    const isFlashing = flashingRows.has(hospital.id);
                    
                    return (
                      <tr 
                        key={hospital.id} 
                        className={`transition-colors duration-500 ${isFlashing ? 'bg-blue-50/50' : 'hover:bg-slate-50'}`}
                      >
                        <td className="px-6 py-4 font-medium text-slate-900">{hospital.name}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusColor(hospital.status)}`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${getStatusDot(hospital.status)}`}></div>
                            {hospital.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full ${
                                  occupancyRatio >= 90 ? 'bg-red-500' : occupancyRatio >= 75 ? 'bg-amber-500' : 'bg-emerald-500'
                                }`}
                                style={{ width: `${Math.min(occupancyRatio, 100)}%` }}
                              ></div>
                            </div>
                            <span className="font-mono text-xs text-slate-500">
                              {hospital.current_occupancy}/{hospital.total_capacity}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right font-mono text-xs text-slate-400">
                          {new Date(hospital.updated_at).toLocaleTimeString()}
                        </td>
                      </tr>
                    );
                  })}
                  {hospitals.length === 0 && (
                    <tr>
                      <td colSpan="4" className="px-6 py-8 text-center text-slate-500">
                        No hospitals found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Topology Placeholder */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50">
              <h2 className="font-semibold text-slate-900">Network Topology</h2>
            </div>
            <div className="p-6 flex-1 flex flex-col items-center justify-center min-h-[300px] bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px]">
              <div className="relative w-full h-full min-h-[250px] flex items-center justify-center">
                {/* Central Node */}
                <div className="absolute z-10 w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center shadow-lg shadow-blue-600/20 ring-4 ring-blue-50">
                  <Activity className="h-6 w-6 text-white" />
                </div>
                
                {/* Simulated Nodes based on data scope */}
                {hospitals.map((h, i) => {
                  const angle = (i / hospitals.length) * Math.PI * 2;
                  const radius = 90;
                  const x = Math.cos(angle) * radius;
                  const y = Math.sin(angle) * radius;
                  
                  return (
                    <div key={h.id}>
                      {/* Line */}
                      <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
                        <line 
                          x1="50%" y1="50%" 
                          x2={`calc(50% + ${x}px)`} y2={`calc(50% + ${y}px)`} 
                          stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4"
                        />
                      </svg>
                      {/* Node */}
                      <div 
                        className="absolute w-8 h-8 bg-white border-2 rounded-full shadow-sm flex items-center justify-center"
                        style={{
                          transform: `translate(calc(${x}px - 50%), calc(${y}px - 50%))`,
                          left: '50%', top: '50%',
                          borderColor: h.status === 'CRITICAL' ? '#ef4444' : h.status === 'WARNING' ? '#f59e0b' : '#10b981',
                          zIndex: 10
                        }}
                        title={h.name}
                      >
                        <Building2 className="h-3 w-3 text-slate-600" />
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="mt-4 text-xs text-slate-400 text-center">
                Displaying {hospitals.length} active node{hospitals.length !== 1 && 's'} in current scope
              </p>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
