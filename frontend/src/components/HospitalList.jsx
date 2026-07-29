import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight, Building2 } from 'lucide-react';

const getStatusColor = (status) => {
  switch (status?.toUpperCase()) {
    case 'CRITICAL': return 'bg-red-100 text-red-700 border-red-200';
    case 'MODERATE': return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'NORMAL': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    default: return 'bg-slate-100 text-slate-700 border-slate-200';
  }
};

const getStatusDot = (status) => {
  switch (status?.toUpperCase()) {
    case 'CRITICAL': return 'bg-red-500';
    case 'MODERATE': return 'bg-amber-500';
    case 'NORMAL': return 'bg-emerald-500';
    default: return 'bg-slate-500';
  }
};

export default function HospitalList({ token }) {
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchHospitals = async () => {
      setLoading(true);
      try {
        let url = `http://localhost:8000/api/v1/hospitals/?page=${page}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;

        const res = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
          const data = await res.json();
          if (data.results) {
            setHospitals(data.results);
            setTotalCount(data.count);
            // Assuming default page size is 10
            setTotalPages(Math.ceil(data.count / 10));
          } else {
            setHospitals(data);
            setTotalCount(data.length);
            setTotalPages(1);
          }
        }
      } catch (err) {
        console.error('Failed to fetch hospitals:', err);
      } finally {
        setLoading(false);
      }
    };

    const delayDebounce = setTimeout(() => {
      fetchHospitals();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [token, page, search, statusFilter]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Hospital Network</h1>
          <p className="text-sm text-slate-500">Manage and monitor facilities ({totalCount} total)</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search hospitals..." 
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-9 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm w-64"
            />
          </div>
          <select 
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-white"
          >
            <option value="">All Statuses</option>
            <option value="CRITICAL">Critical</option>
            <option value="MODERATE">Moderate</option>
            <option value="NORMAL">Normal</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col min-h-[400px]">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-medium">Hospital Name</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Occupancy</th>
                <th className="px-6 py-3 font-medium">Location</th>
                <th className="px-6 py-3 font-medium text-right">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 relative">
              {loading && hospitals.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                    Loading facilities...
                  </td>
                </tr>
              ) : hospitals.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                    No hospitals found matching your criteria.
                  </td>
                </tr>
              ) : (
                hospitals.map(hospital => {
                  const occupancyRatio = hospital.total_capacity > 0 ? (hospital.current_occupancy / hospital.total_capacity) * 100 : 0;
                  
                  return (
                    <tr 
                      key={hospital.id} 
                      onClick={() => navigate(`/hospitals/${hospital.id}`)}
                      className="transition-colors hover:bg-slate-50 cursor-pointer"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                            <Building2 className="h-4 w-4" />
                          </div>
                          <span className="font-medium text-slate-900">{hospital.name}</span>
                        </div>
                      </td>
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
                      <td className="px-6 py-4 text-slate-500 text-xs">
                        {hospital.address || 'N/A'}, {hospital.zip_code || ''}
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-xs text-slate-400">
                        {new Date(hospital.updated_at).toLocaleDateString()} {new Date(hospital.updated_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Showing page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1 rounded border border-slate-300 bg-white text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1 rounded border border-slate-300 bg-white text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
