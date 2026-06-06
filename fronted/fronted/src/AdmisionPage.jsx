// src/AdmisionPage.jsx
import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import StatsPanel from "./components/StatsPanel";

/**
 * Página principal del asistente CEPRUNSA
 */
export default function AdmisionPage() {
  const [localStats, setLocalStats] = useState({
    total: 0,
    cacheHits: 0,
    cats: {},
  });

  const handleNewMessage = ({ categoria, isCache }) => {
    setLocalStats(prev => ({
      total: prev.total + 1,
      cacheHits: prev.cacheHits + (isCache ? 1 : 0),
      cats: {
        ...prev.cats,
        [categoria]: (prev.cats[categoria] ?? 0) + 1,
      },
    }));
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl h-[700px] bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col">

        {/* Top bar */}
        <div className="flex items-center gap-3 px-6 py-3 bg-[#003087]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center">
              <span className="text-white font-bold text-[11px] tracking-tight">CEP</span>
            </div>
            <span className="text-white font-medium text-sm">CEPRUNSA</span>
          </div>
          <span className="text-white/40 text-xs ml-auto">
            Sistema de consultas — Admisión UNSA
          </span>
        </div>

        {/* Main content */}
        <div className="flex flex-1 overflow-hidden">

          {/* Chat panel */}
          <div className="flex-1 flex flex-col overflow-hidden border-r border-gray-200">
            <ChatPanel onNewMessage={handleNewMessage} />
          </div>

          {/* Stats panel */}
          <div className="w-64 flex-shrink-0 overflow-hidden">
            <StatsPanel localStats={localStats} />
          </div>

        </div>
      </div>
    </div>
  );
}