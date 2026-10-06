import { useCallback, useEffect, useState } from "react";
import ChatPanel from "./components/ChatPanel";
import StatsPanel from "./components/StatsPanel";
import { API_BASE_URL } from "./api";

const DEFAULT_WORKSPACE = "ceprunsa_2027";

async function responsePayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `El servidor respondió ${response.status}.`);
  return payload;
}

export default function AdmisionPage() {
  const [statsRefreshKey, setStatsRefreshKey] = useState(0);
  const [workspaces, setWorkspaces] = useState([]);
  const [workspaceId, setWorkspaceId] = useState(() => localStorage.getItem("active-workspace") || DEFAULT_WORKSPACE);
  const [documents, setDocuments] = useState([]);
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceDescription, setWorkspaceDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [contextConfirmed, setContextConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [textractConsent, setTextractConsent] = useState(false);

  const activeWorkspace = workspaces.find((item) => item.id === workspaceId);
  const isReadOnly = activeWorkspace?.read_only !== false;

  const refreshWorkspaces = useCallback(async () => {
    const payload = await responsePayload(await fetch(`${API_BASE_URL}/workspaces`));
    setWorkspaces(payload.workspaces || []);
    if (!(payload.workspaces || []).some((item) => item.id === workspaceId)) {
      setWorkspaceId(DEFAULT_WORKSPACE);
      localStorage.setItem("active-workspace", DEFAULT_WORKSPACE);
    }
  }, [workspaceId]);

  const refreshDocuments = useCallback(async () => {
    if (workspaceId === DEFAULT_WORKSPACE) {
      setDocuments([]);
      return;
    }
    const payload = await responsePayload(await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/documents`));
    setDocuments(payload.documents || []);
  }, [workspaceId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      refreshWorkspaces().catch((fetchError) => setError(fetchError.message));
    }, 0);
    return () => window.clearTimeout(timeout);
  }, [refreshWorkspaces]);

  useEffect(() => {
    const initialFetch = window.setTimeout(() => {
      refreshDocuments().catch((fetchError) => setError(fetchError.message));
    }, 0);
    const interval = window.setInterval(() => {
      refreshDocuments().catch(() => {});
    }, 4000);
    return () => {
      window.clearTimeout(initialFetch);
      window.clearInterval(interval);
    };
  }, [refreshDocuments]);

  const changeWorkspace = (event) => {
    setWorkspaceId(event.target.value);
    localStorage.setItem("active-workspace", event.target.value);
    setError("");
    setNotice("");
    setContextConfirmed(false);
    setTextractConsent(false);
  };

  const createWorkspace = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const created = await responsePayload(await fetch(`${API_BASE_URL}/workspaces`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: workspaceName, description: workspaceDescription }),
      }));
      await refreshWorkspaces();
      setWorkspaceId(created.id);
      localStorage.setItem("active-workspace", created.id);
      setContextConfirmed(false);
      setTextractConsent(false);
      setWorkspaceName("");
      setWorkspaceDescription("");
      setNotice(`Contexto “${created.name}” creado. Sus documentos se mantendrán separados.`);
    } catch (createError) {
      setError(createError.message);
    } finally {
      setLoading(false);
    }
  };

  const uploadDocument = async (event) => {
    event.preventDefault();
    if (!selectedFile || isReadOnly || loading || !contextConfirmed) return;
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const payload = await responsePayload(await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/documents`, {
        method: "POST", headers: {
          "Content-Type": "application/pdf", "X-Filename": encodeURIComponent(selectedFile.name),
          "X-Context-Confirmed": "true",
        }, body: selectedFile,
      }));
      setNotice(payload.status === "awaiting_ocr_consent"
        ? `“${payload.filename}” contiene ${payload.ocr_pages} página(s) que requieren OCR. El archivo quedó guardado; autoriza Textract abajo si quieres enviarlas a AWS.`
        : payload.status === "ready"
          ? `“${payload.filename}” se guardó y quedó conectado al índice del contexto.`
          : `“${payload.filename}” se guardó; la extracción local y la indexación están en curso. El estado aparecerá en la lista.`);
      setSelectedFile(null);
      setContextConfirmed(false);
      event.target.reset();
      await refreshDocuments();
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setLoading(false);
    }
  };

  const processWithTextract = async (document) => {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await responsePayload(await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/documents/${document.id}/process`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ allow_textract: true }),
      }));
      setNotice(`Se autorizó Textract para “${document.filename}”; el procesamiento está en curso y el estado aparecerá en la lista.`);
      await refreshDocuments();
    } catch (processError) {
      setError(processError.message);
      await refreshDocuments().catch(() => {});
    } finally {
      setLoading(false);
      setTextractConsent(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-100 p-0 sm:p-4">
      <div className="mx-auto flex min-h-[100dvh] w-full max-w-6xl flex-col overflow-hidden bg-white shadow-xl sm:rounded-2xl md:min-h-[700px]">
        <header className="flex shrink-0 items-center gap-3 bg-[#003087] px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/20"><span className="text-[11px] font-bold tracking-tight text-white">CEP</span></div>
            <span className="text-sm font-medium text-white">Multi-RAG</span>
          </div>
          <span className="ml-auto text-right text-xs text-white/75">Consultas aisladas por universidad o contexto</span>
        </header>

        <section className="grid shrink-0 gap-3 border-b bg-white p-3 sm:grid-cols-2 sm:p-4" aria-label="Contexto y documentos">
          <div className="space-y-2">
            <label htmlFor="active-workspace" className="block text-xs font-semibold text-gray-700">Contexto activo</label>
            <select id="active-workspace" value={workspaceId} onChange={changeWorkspace} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm">
              {workspaces.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <p className="text-xs text-gray-500">{activeWorkspace?.description || "Las consultas usan solo la colección seleccionada."}</p>
          </div>

          {isReadOnly ? (
            <form onSubmit={createWorkspace} className="grid gap-2 sm:grid-cols-[1fr_1.5fr_auto] sm:items-end">
              <label className="text-xs font-semibold text-gray-700">Nuevo contexto
                <input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-normal" placeholder="Universidad o tema" maxLength={120} required />
              </label>
              <label className="text-xs font-semibold text-gray-700">Alcance documental
                <input value={workspaceDescription} onChange={(event) => setWorkspaceDescription(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-normal" placeholder="Qué información contiene" maxLength={800} required />
              </label>
              <button type="submit" disabled={loading} className="rounded-lg bg-[#003087] px-3 py-2 text-sm font-medium text-white disabled:opacity-50">Crear</button>
            </form>
          ) : (
            <div className="space-y-2">
              <form onSubmit={uploadDocument} className="flex flex-wrap items-end gap-2">
                <label className="min-w-0 flex-1 text-xs font-semibold text-gray-700">Agregar PDF
                  <input type="file" accept="application/pdf,.pdf" onChange={(event) => setSelectedFile(event.target.files?.[0] || null)} className="mt-1 block w-full text-xs file:mr-2 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-2 file:text-xs file:font-medium file:text-blue-900" />
                </label>
                <button type="submit" disabled={!selectedFile || !contextConfirmed || loading} className="rounded-lg bg-[#003087] px-3 py-2 text-sm font-medium text-white disabled:opacity-50">{loading ? "Procesando…" : "Guardar PDF"}</button>
              </form>
              <label className="flex items-start gap-2 text-[11px] text-gray-600"><input type="checkbox" checked={contextConfirmed} onChange={(event) => setContextConfirmed(event.target.checked)} className="mt-0.5" />Confirmo que este PDF pertenece solo al contexto activo; sus datos no se combinarán con otros contextos.</label>
              <p className="text-[11px] text-gray-500">Primero se intenta extraer texto localmente. Un PDF escaneado queda guardado y espera autorización explícita antes de enviarse a Textract.</p>
            </div>
          )}
        </section>

        {(error || notice) && <p role={error ? "alert" : "status"} className={`px-4 py-2 text-xs ${error ? "bg-red-50 text-red-800" : "bg-emerald-50 text-emerald-800"}`}>{error || notice}</p>}

        {!isReadOnly && (
          <section className="max-h-36 shrink-0 overflow-y-auto border-b bg-gray-50 px-4 py-2" aria-label="Documentos del contexto">
            <div className="flex items-center justify-between"><h2 className="text-xs font-semibold text-gray-700">Documentos de este contexto</h2><span className="text-[11px] text-gray-500">{documents.length} archivo(s)</span></div>
            {documents.length === 0 ? <p className="mt-1 text-xs text-gray-500">Aún no se agregaron documentos.</p> : (
              <ul className="mt-1 divide-y divide-gray-200">
                {documents.map((document) => (
                  <li key={document.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-1.5 text-xs">
                    <span className="font-medium text-gray-800">{document.filename}</span>
                    <span className="text-gray-500">{document.status === "ready" ? `${document.pages} pág. · ${document.segments} fragmentos · ${document.tables} tablas` : document.status}</span>
                    {document.error && <span className="text-red-700">{document.error}</span>}
                    {document.status === "awaiting_ocr_consent" && (
                      <div className="ml-auto flex flex-wrap items-center gap-2">
                        <label className="flex items-center gap-1 text-[11px] text-amber-900"><input type="checkbox" checked={textractConsent} onChange={(event) => setTextractConsent(event.target.checked)} />Autorizo enviar estas páginas escaneadas a AWS Textract; puede generar cargos.</label>
                        <button type="button" disabled={!textractConsent || loading} onClick={() => processWithTextract(document)} className="rounded bg-amber-700 px-2 py-1 text-[11px] font-medium text-white disabled:opacity-50">Procesar con Textract</button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        <div className="flex min-h-[420px] flex-1 flex-col overflow-hidden md:flex-row">
          <ChatPanel key={workspaceId} workspaceId={workspaceId} onNewMessage={() => setStatsRefreshKey((value) => value + 1)} />
          <div className="h-44 shrink-0 md:h-auto md:w-64 md:shrink-0"><StatsPanel refreshKey={statsRefreshKey} workspaceId={workspaceId} /></div>
        </div>
      </div>
    </main>
  );
}
