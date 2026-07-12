import { useState, type FormEvent } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";

interface Message {
  role: "user" | "assistant";
  contenu: string;
}

const QUESTIONS_SUGGEREES = [
  "Quelle est ma trésorerie prévue dans 90 jours ?",
  "Pourquoi mon bénéfice baisse ?",
  "Quels clients sont les moins rentables ?",
  "Quelles dépenses puis-je réduire ?",
];

export function Assistant() {
  const { selectedClientId, selectedExerciceId } = useClient();
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function envoyer(texte: string) {
    if (!selectedClientId || !selectedExerciceId || !texte.trim()) return;
    setError(null);
    setMessages((prev) => [...prev, { role: "user", contenu: texte }]);
    setQuestion("");
    setLoading(true);
    try {
      const res = await api.post<{ reponse: string }>(
        `/api/v1/clients/${selectedClientId}/assistant/ask?exercice_id=${selectedExerciceId}`,
        { question: texte },
      );
      setMessages((prev) => [...prev, { role: "assistant", contenu: res.reponse }]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "L'assistant n'a pas pu répondre");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    envoyer(question);
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Assistant financier</h1>
      <p className="text-ink-soft mb-6">
        Posez une question sur la santé financière du dossier — l'assistant va chercher les vraies données avant de répondre.
      </p>

      <ClientPicker requireExercice />

      {!selectedClientId || !selectedExerciceId ? (
        <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
          Sélectionnez un dossier client et un exercice pour discuter avec l'assistant.
        </div>
      ) : (
        <div className="border border-rule-strong rounded bg-white flex flex-col h-[520px]">
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-wrap gap-2">
                {QUESTIONS_SUGGEREES.map((q) => (
                  <button
                    key={q}
                    onClick={() => envoyer(q)}
                    className="text-sm border border-rule-strong rounded-full px-3 py-1.5 hover:bg-paper-dim"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] rounded px-4 py-2 text-sm ${
                    m.role === "user" ? "bg-forest text-paper" : "bg-paper-dim text-ink"
                  }`}
                >
                  {m.contenu}
                </div>
              </div>
            ))}
            {loading && <div className="text-sm text-ink-soft">L'assistant réfléchit...</div>}
            {error && <div className="text-sm text-red">{error}</div>}
          </div>

          <form onSubmit={handleSubmit} className="border-t border-rule p-3 flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Posez votre question..."
              className="flex-1 border border-rule-strong rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="bg-forest text-paper font-semibold px-4 py-2 rounded text-sm hover:bg-[#233f28] disabled:opacity-50"
            >
              Envoyer
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
