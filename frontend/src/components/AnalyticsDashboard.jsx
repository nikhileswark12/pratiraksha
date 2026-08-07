import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, Building2, TrendingUp, Users, ArrowLeft, Download, FileText, Loader2 } from 'lucide-react';
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
  const [hospitals, setHospitals] = useState([]);
  const [selectedHospitals, setSelectedHospitals] = useState([]);
  const [compareData, setCompareData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [groupBy, setGroupBy] = useState('day');
  const [selectedMetric, setSelectedMetric] = useState('prediction_count');
  const navigate = useNavigate();

  const [reportStatus, setReportStatus] = useState(null);
  const [reportId, setReportId] = useState(null);
  const [reportUrl, setReportUrl] = useState(null);
  const [reportError, setReportError] = useState(null);

  const handleGenerateReport = async () => {
    try {
      setReportStatus('queued');
      setReportError(null);
      setReportUrl(null);
      const res = await fetch('http://localhost:8000/api/v1/analytics/report/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          hospital_ids: selectedHospitals.join(','),
          groupBy
        })
      });
      const data = await res.json();
      if (res.ok) {
        setReportId(data.report_id);
      } else {
        setReportStatus('failed');
        setReportError(data.error || 'Failed to queue report');
      }
    } catch (err) {
      setReportStatus('failed');
      setReportError(err.message);
    }
  };

  useEffect(() => {
    let intervalId;
    if (reportId && (reportStatus === 'queued' || reportStatus === 'processing')) {
      intervalId = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/v1/analytics/report/${reportId}/`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          const data = await res.json();
          if (res.ok) {
            setReportStatus(data.status);
            if (data.status === 'ready') {
              setReportUrl(data.download_url);
              clearInterval(intervalId);
            } else if (data.status === 'failed') {
              setReportError(data.error_message || 'Report generation failed');
              clearInterval(intervalId);
            }
          }
        } catch (err) {
          console.error("Error polling report status:", err);
        }
      }, 3000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [reportId, reportStatus, token]);

  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [overviewRes, trendsRes, hospRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/analytics/overview/', {
            headers: { 'Authorization': `Bearer ${token}` }
          }),
          fetch(`http://localhost:8000/api/v1/analytics/trends/?metric=prediction-count&groupBy=${groupBy}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          }),
          fetch('http://localhost:8000/api/v1/hospitals/', {
            headers: { 'Authorization': `Bearer ${token}` }
          })
        ]);

        if (overviewRes.ok) setOverviewData(await overviewRes.json());
        if (trendsRes.ok) {
           const trends = await trendsRes.json();
           setTrendsData(trends.results || []);
        }
        if (hospRes.ok) {
           const hospData = await hospRes.json();
           const hospList = hospData.results || hospData;
           setHospitals(hospList);
           // Default to first two for comparison if empty
           if (selectedHospitals.length === 0 && hospList.length > 0) {
             setSelectedHospitals(hospList.slice(0, 2).map(h => h.id));
           }
        }
      } catch (err) {
        console.error('Failed to fetch analytics data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token, groupBy]); // selectedHospitals removed to prevent infinite loop on first fetch

  useEffect(() => {
    const fetchCompareData = async () => {
      if (selectedHospitals.length === 0) {
        setCompareData([]);
        return;
      }
      try {
        const res = await fetch(`http://localhost:8000/api/v1/analytics/compare/?groupBy=${groupBy}&hospital_ids=${selectedHospitals.join(',')}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setCompareData(data.results || []);
        }
      } catch (err) {
        console.error('Failed to fetch compare data:', err);
      }
    };
    fetchCompareData();
  }, [token, groupBy, selectedHospitals]);

  const handleHospitalToggle = (hospitalId) => {
    setSelectedHospitals(prev => 
      prev.includes(hospitalId)
        ? prev.filter(id => id !== hospitalId)
        : [...prev, hospitalId]
    );
  };

  const transformCompareData = () => {
    if (!compareData || compareData.length === 0) return [];
    const periods = compareData[0]?.series?.map(s => s.period) || [];
    
    return periods.map(period => {
      const dataPoint = { period };
      compareData.forEach(hosp => {
        const point = hosp.series.find(s => s.period === period);
        if (point) {
          dataPoint[hosp.name] = point[selectedMetric];
        }
      });
      return dataPoint;
    });
  };

  const chartData = transformCompareData();

  if (loading || !overviewData) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading analytics...</div>;
  }

  return (
    <div className="bg-slate-50 min-h-screen text-slate-900 font-sans p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div className="flex items-center gap-4">
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
          
          <div className="flex items-center gap-4">
            {reportStatus === 'ready' && reportUrl && (
              <a 
                href={reportUrl} 
                download
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
              >
                <Download className="w-4 h-4" />
                Download Report
              </a>
            )}
            {reportStatus === 'failed' && (
              <span className="text-red-500 text-sm flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" /> {reportError || 'Failed'}
              </span>
            )}
            <button
              onClick={handleGenerateReport}
              disabled={reportStatus === 'queued' || reportStatus === 'processing'}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:bg-blue-400 text-sm font-medium"
            >
              {(reportStatus === 'queued' || reportStatus === 'processing') ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
              ) : (
                <><FileText className="w-4 h-4" /> Generate Report</>
              )}
            </button>
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
            <h2 className="text-lg font-semibold text-slate-900">Overall Prediction Trend</h2>
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

        {/* Comparative Analytics Row */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
            <h2 className="text-lg font-semibold text-slate-900">Facility Comparison</h2>
            
            <div className="flex bg-slate-100 rounded-lg p-1">
              <button
                onClick={() => setSelectedMetric('prediction_count')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  selectedMetric === 'prediction_count'
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                Predictions
              </button>
              <button
                onClick={() => setSelectedMetric('occupancy')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  selectedMetric === 'occupancy'
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                Occupancy %
              </button>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row gap-6">
            {/* Controls */}
            <div className="w-full md:w-64 flex flex-col gap-4">
              <h3 className="text-sm font-medium text-slate-700 border-b border-slate-100 pb-2">Select Facilities</h3>
              <div className="flex flex-col gap-1 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                {hospitals.map(hospital => (
                  <label key={hospital.id} className="flex items-center gap-2 text-sm text-slate-700 p-2 hover:bg-slate-50 rounded cursor-pointer transition-colors">
                    <input 
                      type="checkbox" 
                      checked={selectedHospitals.includes(hospital.id)}
                      onChange={() => handleHospitalToggle(hospital.id)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="truncate flex-1">{hospital.name}</span>
                  </label>
                ))}
              </div>
            </div>
            
            {/* Chart */}
            <div className="flex-1 h-80">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData}
                    margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
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
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#64748b', fontSize: 12 }}
                      dx={-10}
                    />
                    <Tooltip 
                      contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                    {compareData.map((hosp, i) => (
                      <Line 
                        key={hosp.hospital_id}
                        type="monotone" 
                        dataKey={hosp.name} 
                        name={hosp.name} 
                        stroke={colors[i % colors.length]} 
                        strokeWidth={2}
                        dot={{ fill: colors[i % colors.length], r: 4, strokeWidth: 0 }}
                        activeDot={{ r: 6 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-xl">
                  Select at least one facility to compare.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
