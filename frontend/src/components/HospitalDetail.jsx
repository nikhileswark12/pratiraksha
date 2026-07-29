import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Building2, MapPin, Phone, ArrowLeft, Activity, Info, Archive, TrendingUp } from 'lucide-react';

const getStatusColor = (status) => {
  switch (status?.toUpperCase()) {
    case 'CRITICAL': return 'bg-red-100 text-red-700 border-red-200';
    case 'MODERATE': return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'NORMAL': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    default: return 'bg-slate-100 text-slate-700 border-slate-200';
  }
};

export default function HospitalDetail({ token }) {
  const { id } = useParams();
  const [hospital, setHospital] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [trend, setTrend] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };
        
        // Fetch hospital detail
        const hRes = await fetch(`http://localhost:8000/api/v1/hospitals/${id}/`, { headers });
        if (!hRes.ok) {
          if (hRes.status === 403 || hRes.status === 404) {
             throw new Error('You do not have permission to view this hospital or it does not exist.');
          }
          throw new Error('Failed to fetch hospital details.');
        }
        const hData = await hRes.json();
        setHospital(hData);

        // Fetch sub-resources in parallel
        const [dRes, eRes, tRes] = await Promise.all([
          fetch(`http://localhost:8000/api/v1/hospitals/${id}/departments/`, { headers }),
          fetch(`http://localhost:8000/api/v1/hospitals/${id}/equipment/`, { headers }),
          fetch(`http://localhost:8000/api/v1/hospitals/${id}/occupancy-trend/`, { headers })
        ]);

        if (dRes.ok) setDepartments(await dRes.json());
        if (eRes.ok) setEquipment(await eRes.json());
        if (tRes.ok) {
            const tData = await tRes.json();
            setTrend(tData.trend || []);
        }

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, token]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading hospital details...</div>;
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="bg-red-50 text-red-600 p-6 rounded-xl border border-red-200">
          <Activity className="h-10 w-10 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-bold mb-2">Access Denied / Error</h2>
          <p>{error}</p>
          <Link to="/hospitals" className="mt-6 inline-flex items-center gap-2 text-blue-600 font-medium hover:underline">
            <ArrowLeft className="h-4 w-4" /> Back to Network
          </Link>
        </div>
      </div>
    );
  }

  if (!hospital) return null;

  const occupancyRatio = hospital.total_capacity > 0 ? (hospital.current_occupancy / hospital.total_capacity) * 100 : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Back nav */}
      <Link to="/hospitals" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-blue-600 transition-colors">
        <ArrowLeft className="h-4 w-4" /> Back to Hospital List
      </Link>

      {/* Hero Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row md:items-start justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
              <Building2 className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{hospital.name}</h1>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border mt-1 ${getStatusColor(hospital.status)}`}>
                {hospital.status}
              </span>
            </div>
          </div>
          <div className="mt-4 flex flex-col gap-2 text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-slate-400" />
              {hospital.address}, {hospital.zip_code}
            </div>
            <div className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-slate-400" />
              {hospital.contact_number || 'No contact provided'}
            </div>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl p-5 border border-slate-100 min-w-[250px]">
          <h3 className="text-sm font-medium text-slate-500 mb-1">Current Occupancy</h3>
          <div className="flex items-end gap-2 mb-3">
            <span className="text-3xl font-bold font-mono text-slate-900">{hospital.current_occupancy}</span>
            <span className="text-sm text-slate-500 font-mono mb-1">/ {hospital.total_capacity} beds</span>
          </div>
          <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full ${
                occupancyRatio >= 90 ? 'bg-red-500' : occupancyRatio >= 75 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(occupancyRatio, 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-400 mt-2 font-mono text-right">{occupancyRatio.toFixed(1)}% Full</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: Info },
            { id: 'departments', name: 'Departments', icon: Building2 },
            { id: 'equipment', name: 'Equipment', icon: Archive },
            { id: 'history', name: 'History & Trends', icon: TrendingUp },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                  ${isActive 
                    ? 'border-blue-600 text-blue-600' 
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}
                `}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[300px]">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Facility Information</h3>
              <dl className="space-y-4 text-sm">
                <div className="grid grid-cols-3 gap-4">
                  <dt className="text-slate-500">ID</dt>
                  <dd className="col-span-2 font-mono text-slate-900">{hospital.id}</dd>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <dt className="text-slate-500">Created</dt>
                  <dd className="col-span-2 text-slate-900">{new Date(hospital.created_at).toLocaleString()}</dd>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <dt className="text-slate-500">Last Updated</dt>
                  <dd className="col-span-2 text-slate-900">{new Date(hospital.updated_at).toLocaleString()}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        {activeTab === 'departments' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-medium">Department Name</th>
                  <th className="px-6 py-3 font-medium">Head</th>
                  <th className="px-6 py-3 font-medium">Capacity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {departments.length === 0 ? (
                  <tr><td colSpan="3" className="px-6 py-8 text-center text-slate-500">No departments recorded.</td></tr>
                ) : (
                  departments.map(dept => (
                    <tr key={dept.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-900">{dept.name}</td>
                      <td className="px-6 py-4 text-slate-600">{dept.head_doctor || 'N/A'}</td>
                      <td className="px-6 py-4 font-mono text-slate-600">{dept.bed_capacity} beds</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'equipment' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-medium">Equipment Type</th>
                  <th className="px-6 py-3 font-medium">Total Quantity</th>
                  <th className="px-6 py-3 font-medium">In Use</th>
                  <th className="px-6 py-3 font-medium">Available</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {equipment.length === 0 ? (
                  <tr><td colSpan="4" className="px-6 py-8 text-center text-slate-500">No equipment recorded.</td></tr>
                ) : (
                  equipment.map(item => (
                    <tr key={item.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-900 capitalize">{item.equipment_type}</td>
                      <td className="px-6 py-4 font-mono text-slate-600">{item.total_quantity}</td>
                      <td className="px-6 py-4 font-mono text-slate-600">{item.in_use_quantity}</td>
                      <td className="px-6 py-4 font-mono text-emerald-600 font-semibold">{item.total_quantity - item.in_use_quantity}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Occupancy Trend (Last 24 Hours)</h3>
            <div className="h-64 flex items-end justify-between gap-2">
              {trend.length === 0 ? (
                <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm">
                  No historical data available.
                </div>
              ) : (
                trend.map((point, idx) => (
                  <div key={idx} className="flex flex-col items-center flex-1 gap-2 group">
                    <div className="w-full bg-slate-100 rounded-t-sm relative h-48 flex items-end justify-center hover:bg-slate-200 transition-colors">
                      <div 
                        className="w-full bg-blue-500 rounded-t-sm opacity-80 group-hover:opacity-100 transition-opacity" 
                        style={{ height: `${point.occupancy}%` }}
                      ></div>
                      <div className="absolute -top-8 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                        {point.occupancy}%
                      </div>
                    </div>
                    <span className="text-xs text-slate-500">{point.time}</span>
                  </div>
                ))
              )}
            </div>
            <p className="text-xs text-slate-400 mt-6 pt-4 border-t border-slate-100">
              Note: This data is aggregated from EHR historical snapshots. Detailed validation arrives in Day 18.
            </p>
          </div>
        )}
      </div>

    </div>
  );
}
