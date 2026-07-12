import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { ApiError } from "../lib/api";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de se connecter");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-white border border-rule-strong rounded p-8">
        <h1 className="font-display text-2xl font-semibold mb-1">ComptaCopilot AI</h1>
        <p className="text-ink-soft text-sm mb-6">Connexion à votre cabinet</p>

        {error && (
          <div className="mb-4 text-sm text-red bg-red/10 border border-red/30 rounded px-3 py-2">
            {error}
          </div>
        )}

        <label className="block text-sm font-medium mb-1" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 px-3 py-2 border border-rule-strong rounded focus:outline-none focus:ring-2 focus:ring-forest"
        />

        <label className="block text-sm font-medium mb-1" htmlFor="password">
          Mot de passe
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-6 px-3 py-2 border border-rule-strong rounded focus:outline-none focus:ring-2 focus:ring-forest"
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-forest text-paper font-semibold py-2 rounded hover:bg-[#233f28] disabled:opacity-60"
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>

        <p className="text-sm text-ink-soft mt-4 text-center">
          Pas encore de cabinet ?{" "}
          <Link to="/register" className="text-forest font-medium hover:underline">
            En créer un
          </Link>
        </p>
      </form>
    </div>
  );
}
