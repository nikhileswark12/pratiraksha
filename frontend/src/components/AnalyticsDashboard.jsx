import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, Building2, TrendingUp, Users, ArrowLeft } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { useNavigate } from 'react-router-dom';

export default function AnalyticsDashboard({ token }) {
  const [overviewData, setOverviewData] = useState(null);
  const [trendsData, setTrendsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [groupBy, setGroupBy] = useState('day');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [overviewRes, trendsRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/analytics/overview/', {
            headers: { 'Authorization': `Bearer ${token}` }
          }),
          fetch(`http://localhost:8000/api/v1/analytics/trends/?metric=prediction-count&groupBy=${groupBy}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
        ]);

        if (overviewRes.ok && trendsRes.ok) {
          const overview = await overviewRes.json();
          const trends = await trendsRes.json();
          setOverviewData(overview);
          setTrendsData(trends.results || []);
        }
      } catch (err) {
        console.error('Failed to fetch analytics data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token, groupBy]);

  if (loading || !overviewData) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading analytics...</div>;
  }

  return (
    <div className="bg-slate-50 min-h-screen text-slate-900 font-sans p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center gap-4 border-b border-slate-200 pb-4">
          <button 
            onClick={() => navigate('/')} 
            className="p-2 rounded-lg hover:bg-slate-200 transition-colors text-slate-600"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Analytics Dashboard</h1>
            <p className="text-slate-500 text-sm">Network overview and historical trends</p>
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg"><Building2 className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Total Hospitals</p>
              <h3 className="text-2xl font-bold font-mono">{overviewData.total_hospitals} <span className="text-sm font-normal text-slate-400">Facilities</span></h3>
            </div>
          </div>
          
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-red-50 text-red-600 rounded-lg"><AlertTriangle className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Critical Status</p>
              <h3 className="text-2xl font-bold font-mono text-red-600">{overviewData.status_summary?.CRITICAL || 0} <span className="text-sm font-normal text-slate-400 text-slate-900">Active</span></h3>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg"><Users className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Avg Occupancy</p>
              <h3 className="text-2xl font-bold font-mono">{overviewData.avg_occupancy_percent}% <span className="text-sm font-normal text-slate-400">Capacity</span></h3>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-amber-50 text-amber-600 rounded-lg"><TrendingUp className="h-6 w-6" /></div>
            <div>
              <p className="text-sm font-medium text-slate-500">Predictions Today</p>
              <h3 className="text-2xl font-bold font-mono">{overviewData.predictions_today} <span className="text-sm font-normal text-slate-400">Run</span></h3>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-slate-900">Prediction Trend</h2>
            <div className="flex bg-slate-100 rounded-lg p-1">
              {['day', 'week', 'month'].map(period => (
                <button
                  key={period}
                  onClick={() => setGroupBy(period)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    groupBy === period 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {period.charAt(0).toUpperCase() + period.slice(1)}
                </button>
              ))}
            </div>
          </div>
          
          <div className="h-80 w-full">
            {trendsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={trendsData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis 
                    dataKey="period" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12 }}
                    dy={10}
                  />
                  <YAxis 
                    yAxisId="left"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12 }}
                    dx={-10}
                  />
                  <YAxis 
                    yAxisId="right" 
                    orientation="right" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12 }}
                    dx={10}
                  />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="count" 
                    name="Prediction Count" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', r: 4, strokeWidth: 0 }}
                    activeDot={{ r: 6 }}
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="avg_risk" 
                    name="Avg Risk Score" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    dot={{ fill: '#f59e0b', r: 4, strokeWidth: 0 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400">
                No trend data available for this period.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
