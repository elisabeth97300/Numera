import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { ApiError } from "../lib/api";

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [organisationNom, setOrganisationNom] = useState("");
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(organisationNom, email, motDePasse);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de créer le cabinet");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-white border border-rule-strong rounded p-8">
        <h1 className="font-display text-2xl font-semibold mb-1">Créer votre cabinet</h1>
        <p className="text-ink-soft text-sm mb-6">Vous serez administrateur du cabinet.</p>

        {error && (
          <div className="mb-4 text-sm text-red bg-red/10 border border-red/30 rounded px-3 py-2">
            {error}
          </div>
        )}

        <label className="block text-sm font-medium mb-1" htmlFor="organisation">
          Nom du cabinet
        </label>
        <input
          id="organisation"
          type="text"
          required
          value={organisationNom}
          onChange={(e) => setOrganisationNom(e.target.value)}
          className="w-full mb-4 px-3 py-2 border border-rule-strong rounded focus:outline-none focus:ring-2 focus:ring-forest"
        />

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
          minLength={10}
          value={motDePasse}
          onChange={(e) => setMotDePasse(e.target.value)}
          className="w-full mb-1 px-3 py-2 border border-rule-strong rounded focus:outline-none focus:ring-2 focus:ring-forest"
        />
        <p className="text-xs text-ink-soft mb-6">Au moins 10 caractères, une lettre et un chiffre.</p>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-forest text-paper font-semibold py-2 rounded hover:bg-[#233f28] disabled:opacity-60"
        >
          {loading ? "Création..." : "Créer le cabinet"}
        </button>

        <p className="text-sm text-ink-soft mt-4 text-center">
          Déjà un compte ?{" "}
          <Link to="/login" className="text-forest font-medium hover:underline">
            Se connecter
          </Link>
        </p>
      </form>
    </div>
  );
}
