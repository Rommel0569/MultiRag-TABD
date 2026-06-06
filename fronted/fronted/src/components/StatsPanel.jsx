// src/components/StatsPanel.jsx
import { useEffect, useState } from "react";

export default function StatsPanel({ localStats }) {
  const [stats, setStats] = useState(localStats);

  const fetchStats = async () => {
    try {
      const res = await fetch("http://localhost:8000/stats");
      if (!res.ok) return;
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error("Error al obtener stats");
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // 10 seg
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-4 p-4 bg-gray-50 h-full border-l">
      <h2 className="font-bold text-gray-700">Panel de Control</h2>
      
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-white p-3 rounded shadow-sm border">
          <p className="text-[10px] text-gray-500 uppercase">Consultas</p>
          <p className="text-lg font-bold">{stats.total_entries || 0}</p>
        </div>
        <div className="bg-white p-3 rounded shadow-sm border">
          <p className="text-[10px] text-gray-500 uppercase">Hits Caché</p>
          <p className="text-lg font-bold">{stats.total_hits || 0}</p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <p className="text-xs font-semibold text-gray-500">Popularidad por Categoria</p>
        {stats.top_queries && stats.top_queries.length > 0 ? (
          stats.top_queries.map((q, i) => (
            <div key={i} className="text-xs">
              <div className="flex justify-between mb-1">
                <span>{q.category}</span>
                <span>{q.hits}</span>
              </div>
              <div className="w-full bg-gray-200 h-1.5 rounded-full">
                <div className="bg-[#003087] h-1.5 rounded-full" style={{ width: '60%' }}></div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-xs text-gray-400 italic">Esperando datos...</p>
        )}
      </div>
    </div>
  );
}