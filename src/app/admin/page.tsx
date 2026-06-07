'use client';

import { useState } from 'react';
import { runScript } from './actions';

export default function AdminPage() {
  const [status, setStatus] = useState<Record<string, { loading: boolean; error: string | null; output: string | null }>>({
    fetch: { loading: false, error: null, output: null },
    trends: { loading: false, error: null, output: null },
  });

  const handleRun = async (type: 'fetch' | 'trends') => {
    setStatus((prev) => ({
      ...prev,
      [type]: { loading: true, error: null, output: null },
    }));

    const result = await runScript(type);

    setStatus((prev) => ({
      ...prev,
      [type]: {
        loading: false,
        error: result.success ? null : result.error,
        output: result.success ? result.output : null,
      },
    }));
  };

  return (
    <div className="p-8 font-sans max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
        <p className="text-zinc-600">Manual data pipeline management.</p>
      </header>

      <div className="grid gap-6">
        {/* Fetch Data */}
        <div className="border rounded-xl p-6 bg-white shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-bold">Data Ingestion</h2>
              <p className="text-sm text-zinc-500">Fetch latest matches and team data from Fryzigg.</p>
            </div>
            <button
              onClick={() => handleRun('fetch')}
              disabled={status.fetch.loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                status.fetch.loading 
                  ? 'bg-zinc-100 text-zinc-400 cursor-not-allowed' 
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {status.fetch.loading ? 'Running...' : 'Run Fetcher'}
            </button>
          </div>
          {status.fetch.error && (
            <div className="bg-red-50 text-red-700 p-3 rounded text-sm mt-2 font-mono whitespace-pre-wrap">
              {status.fetch.error}
            </div>
          )}
          {status.fetch.output && (
            <div className="bg-zinc-900 text-zinc-300 p-3 rounded text-sm mt-2 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
              {status.fetch.output}
            </div>
          )}
        </div>

        {/* Calculate Trends */}
        <div className="border rounded-xl p-6 bg-white shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-bold">Trend Engine</h2>
              <p className="text-sm text-zinc-500">Recalculate proprietary team momentum metrics.</p>
            </div>
            <button
              onClick={() => handleRun('trends')}
              disabled={status.trends.loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                status.trends.loading 
                  ? 'bg-zinc-100 text-zinc-400 cursor-not-allowed' 
                  : 'bg-zinc-800 text-white hover:bg-zinc-900'
              }`}
            >
              {status.trends.loading ? 'Running...' : 'Recalculate Trends'}
            </button>
          </div>
          {status.trends.error && (
            <div className="bg-red-50 text-red-700 p-3 rounded text-sm mt-2 font-mono whitespace-pre-wrap">
              {status.trends.error}
            </div>
          )}
          {status.trends.output && (
            <div className="bg-zinc-900 text-zinc-300 p-3 rounded text-sm mt-2 font-mono whitespace-pre-wrap">
              {status.trends.output}
            </div>
          )}
        </div>
      </div>

      <nav className="mt-12 flex gap-4 text-sm">
        <a href="/" className="text-blue-600 hover:underline">Back to Home</a>
        <span className="text-zinc-300">|</span>
        <a href="/teams" className="text-blue-600 hover:underline">View Teams</a>
      </nav>
    </div>
  );
}
