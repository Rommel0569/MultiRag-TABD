import { useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "../api";

const suggestionQuestions = [
  "¿Cuándo es el examen?",
  "¿Cuántas vacantes hay?",
  "Temas de Matemáticas",
  "Documentos de inscripción",
];

const categoryLabels = {
  CRONOGRAMA: "Cronograma",
  VACANTES: "Vacantes",
  TEMARIO: "Temario",
  REGLAMENTO: "Reglamento",
  FUERA_DE_DOMINIO: "Fuera del dominio",
  CACHE: "Caché",
};

function readableError(payload, fallback) {
  const detail = payload?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).filter(Boolean).join(". ");
  return fallback;
}

export default function ChatPanel({ onNewMessage, workspaceId }) {
  const [messages, setMessages] = useState([
    { role: "bot", text: "¡Hola! Soy tu asistente CEPRUNSA. ¿En qué puedo ayudarte hoy?" },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const handleSend = async (event) => {
    event.preventDefault();
    const queryText = input.trim();
    if (!queryText || isSending) return;

    setMessages((current) => [...current, { role: "user", text: queryText }]);
    setInput("");
    setIsSending(true);

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText, workspace_id: workspaceId }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(readableError(payload, `El servidor respondió ${response.status}.`));
      }

      setMessages((current) => [
        ...current,
        {
          role: "bot",
          text: payload.answer,
          category: payload.category,
          phase: payload.phase,
          latencyMs: payload.latency_ms,
          sources: Array.isArray(payload.sources) ? payload.sources : [],
          cacheHit: Boolean(payload.cache_hit),
        },
      ]);
      onNewMessage?.();
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "bot",
          text: error instanceof Error ? error.message : "No se pudo completar la consulta.",
          error: true,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <section className="flex h-full min-h-0 flex-1 flex-col gap-3 bg-gray-50 p-3 sm:gap-4 sm:p-4" aria-label="Chat CEPRUNSA">
      <div className="flex min-h-0 flex-1 flex-col space-y-4 overflow-y-auto rounded-lg bg-white p-3 shadow-inner sm:p-4" aria-live="polite">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
            <article className={`max-w-[90%] break-words rounded-2xl p-3 shadow-sm sm:max-w-[82%] ${
              message.role === "user"
                ? "bg-[#003087] text-white"
                : message.error
                  ? "border border-red-200 bg-red-50 text-red-900"
                  : "bg-gray-100 text-gray-800"
            }`}>
              <p className="whitespace-pre-wrap text-sm leading-6">{message.text}</p>
              {message.phase && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <span className="rounded-full bg-white/80 px-2 py-1 text-[10px] font-medium text-gray-700">{message.phase}</span>
                  <span className="rounded-full bg-blue-100 px-2 py-1 text-[10px] font-medium text-blue-900">
                    {categoryLabels[message.category] || message.category}
                  </span>
                  {message.cacheHit && <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-medium text-emerald-900">Caché</span>}
                  {Number.isFinite(message.latencyMs) && <span className="rounded-full bg-gray-200 px-2 py-1 text-[10px] text-gray-700">{message.latencyMs < 1000 ? `${Math.round(message.latencyMs)} ms` : `${(message.latencyMs / 1000).toFixed(2)} s`}</span>}
                </div>
              )}
              {message.sources?.length > 0 && (
                <div className="mt-3 border-t border-gray-300 pt-2">
                  <p className="mb-1 text-[11px] font-semibold text-gray-600">Fuentes</p>
                  <ul className="space-y-1">
                    {message.sources.map((source) => <li key={source} className="text-[11px] text-gray-600">{source}</li>)}
                  </ul>
                </div>
              )}
            </article>
          </div>
        ))}
        {isSending && (
          <p className="self-start rounded-full bg-blue-50 px-3 py-2 text-xs text-blue-900" role="status">
            Consultando los documentos…
          </p>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-2" aria-label="Consultas sugeridas">
          {suggestionQuestions.map((question) => (
            <button
              key={question}
              type="button"
              className="rounded-full bg-gray-200 px-3 py-1.5 text-xs transition hover:bg-gray-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#003087]"
              onClick={() => setInput(question)}
              disabled={isSending}
            >
              {question}
            </button>
          ))}
        </div>
        <form className="flex gap-2" onSubmit={handleSend}>
          <label className="sr-only" htmlFor="ceprunsa-query">Escribe tu consulta</label>
          <input
            id="ceprunsa-query"
            className="min-w-0 flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Escribe tu consulta…"
            autoComplete="off"
            disabled={isSending}
          />
          <button
            className="rounded-lg bg-[#003087] px-4 py-2 font-medium text-white transition hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-50 sm:px-6"
            type="submit"
            disabled={!input.trim() || isSending}
          >
            {isSending ? "Enviando…" : "Enviar"}
          </button>
        </form>
      </div>
    </section>
  );
}
