// src/components/ChatPanel.jsx
import { useState, useRef, useEffect } from "react";

export default function ChatPanel({ onNewMessage }) {
  const [messages, setMessages] = useState([
    { role: "bot", text: "¡Hola! Soy tu asistente CEPRUNSA. ¿En qué puedo ayudarte hoy?" },
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const suggestionQuestions = [
    "¿Cuándo es el examen?",
    "¿Cuántas vacantes hay?",
    "Temas de Matemáticas",
    "Documentos de inscripción"
  ];

  // Auto-scroll al final cuando cambian los mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const queryText = input;
    setMessages(prev => [...prev, { role: "user", text: queryText }]);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText })
      });

      if (!res.ok) throw new Error("Error en el servidor");
      const data = await res.json();

      const botMsg = {
        role: "bot",
        text: data.answer,
        categoria: data.category,
        fase: data.phase,
        fuentes: data.sources
      };

      setMessages(prev => [...prev, botMsg]);
      onNewMessage({ categoria: botMsg.categoria, isCache: data.cache_hit });

    } catch (err) {
      setMessages(prev => [...prev, { 
        role: "bot", 
        text: "❌ Error: No pude conectar con el servidor. Revisa si el backend está activo." 
      }]);
    }
  };

  return (
    <div className="flex-1 flex flex-col p-4 gap-4 bg-gray-50 h-full">
      {/* Contenedor de mensajes con scroll automático */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white rounded-lg shadow-inner">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] p-3 rounded-2xl shadow-sm break-words ${
              msg.role === "user" ? "bg-[#003087] text-white" : "bg-gray-200 text-gray-800"
            }`}>
              <p className="text-sm">{msg.text}</p>
              {msg.fase && (
                <div className="mt-2 flex gap-2">
                  <span className="text-[10px] bg-red-500 text-white px-2 py-0.5 rounded-full uppercase">{msg.fase}</span>
                  <span className="text-[10px] bg-blue-500 text-white px-2 py-0.5 rounded-full uppercase">{msg.categoria}</span>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Sugerencias y Input */}
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          {suggestionQuestions.map((q, i) => (
            <button key={i} className="bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded text-xs transition" onClick={() => setInput(q)}>
              {q}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            className="flex-1 border rounded-lg px-4 py-2 focus:ring-2 focus:ring-[#003087] outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Escribe tu consulta..."
          />
          <button className="bg-[#003087] text-white px-6 py-2 rounded-lg hover:bg-blue-900 transition" onClick={handleSend}>
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}