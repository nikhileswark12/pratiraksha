import React, { useState } from 'react';

export default function CrisisSimulation({ token }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/crisis/simulate/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: 'mass_gathering', parameters: { event_size: 5000, duration: 6 } })
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Crisis Simulation</h1>
      <button onClick={runSimulation} disabled={loading} className="bg-red-600 text-white px-4 py-2 rounded font-medium">
        {loading ? 'Running...' : 'Run Simulation'}
      </button>

      {result && (
        <div className="mt-8 p-6 bg-red-50 border border-red-200 rounded-xl crisis-result-card">
          <h2 className="text-xl font-bold text-red-700">Simulation Result</h2>
          <pre className="mt-4 bg-white p-4 rounded text-sm text-slate-800">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
