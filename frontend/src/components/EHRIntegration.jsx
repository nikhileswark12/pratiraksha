import React, { useState, useEffect } from 'react';

export default function EHRIntegration({ token }) {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/ehr/patients/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setPatients(data.results || data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPatients();
  }, [token]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">EHR Integration</h1>
      {loading ? (
        <p>Loading EHR records...</p>
      ) : (
        <table className="w-full text-left text-sm whitespace-nowrap bg-white rounded-xl shadow-sm border border-slate-200">
          <thead className="bg-slate-50 border-b text-slate-500">
            <tr>
              <th className="px-6 py-3 font-medium">MRN</th>
              <th className="px-6 py-3 font-medium">Name</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {patients.map(p => (
              <tr key={p.id}>
                <td className="px-6 py-4">{p.mrn}</td>
                <td className="px-6 py-4">{p.name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
