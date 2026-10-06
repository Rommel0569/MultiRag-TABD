import { useCallback, useEffect, useState } from "react";
import { API_BASE_URL } from "../api";

const categoryLabels = {
  CRONOGRAMA: "Cronograma",
  VACANTES: "Vacantes",
  TEMARIO: "Temario",
  REGLAMENTO: "Reglamento",
};

export default function StatsPanel({ refreshKey, workspaceId }) {
  const [stats, setStats] = useState(null);
  const [connected, setConnected] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/stats?workspace_id=${encodeURIComponent(workspaceId || "ceprunsa_2027")}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setStats(await response.json());
      setConnected(true);
    } catch {
      setConnected(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    const initialFetch = window.setTimeout(fetchStats, 0);
    const interval = window.setInterval(fetchStats, 10000);
    return () => {
      window.clearTimeout(initialFetch);
      window.clearInterval(interval);
    };
  }, [fetchStats, refreshKey]);

  const topQueries = stats?.top_queries || [];
  const maxHits = Math.max(1, ...topQueries.map((item) => Number(item.hits || 0)));

  return (
    <aside className="flex h-full flex-col gap-3 overflow-y-auto border-t bg-gray-50 p-3 md:gap-4 md:border-l md:border-t-0 md:p-4" aria-label="Estadísticas del sistema">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-bold text-gray-800">Uso del sistema</h2>
        <span className={`flex items-center gap-1.5 text-[11px] ${connected ? "text-emerald-700" : connected === false ? "text-red-700" : "text-gray-500"}`} role="status">
          <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-500" : connected === false ? "bg-red-500" : "bg-gray-400"}`} />
          {connected ? "API conectada" : connected === false ? "API sin conexión" : "Conectando…"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg border bg-white p-3 shadow-sm">
          <p className="text-[10px] uppercase tracking-wide text-gray-500">Consultas recibidas</p>
          <p className="text-xl font-bold text-gray-900">{stats?.total_queries ?? "—"}</p>
        </div>
        <div className="rounded-lg border bg-white p-3 shadow-sm">
          <p className="text-[10px] uppercase tracking-wide text-gray-500">Respuestas en caché</p>
          <p className="text-xl font-bold text-gray-900">{stats?.total_entries ?? "—"}</p>
        </div>
        <div className="rounded-lg border bg-white p-3 shadow-sm">
          <p className="text-[10px] uppercase tracking-wide text-gray-500">Usos de caché</p>
          <p className="text-xl font-bold text-gray-900">{stats?.total_hits ?? "—"}</p>
        </div>
        <div className="rounded-lg border bg-white p-3 shadow-sm">
          <p className="text-[10px] uppercase tracking-wide text-gray-500">Tasa de aciertos</p>
          <p className="text-xl font-bold text-gray-900">{stats ? `${(Number(stats.hit_rate || 0) * 100).toFixed(0)}%` : "—"}</p>
        </div>
      </div>

      <section className="flex min-h-0 flex-col gap-3" aria-label="Consultas más reutilizadas">
        <div>
          <h3 className="text-xs font-semibold text-gray-600">Consultas más reutilizadas</h3>
          <p className="mt-1 text-[11px] text-gray-500">Modo de caché: {stats?.mode || "—"}</p>
        </div>
        {topQueries.length ? topQueries.map((item) => (
          <div key={`${item.category}-${item.query}`} className="text-xs">
            <div className="mb-1 flex justify-between gap-2">
              <span className="truncate text-gray-700" title={item.query}>{categoryLabels[item.category] || item.category || "Consulta"}</span>
              <span className="shrink-0 tabular-nums text-gray-500">{item.hits}</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-gray-200" aria-hidden="true">
              <div className="h-1.5 rounded-full bg-[#003087]" style={{ width: `${(Number(item.hits || 0) / maxHits) * 100}%` }} />
            </div>
          </div>
        )) : (
          <p className="text-xs italic text-gray-500">{connected === false ? "Las estadísticas aparecerán al conectar el backend." : "Aún no hay respuestas reutilizadas."}</p>
        )}
      </section>
    </aside>
  );
}
