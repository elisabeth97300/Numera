import { useEffect, useState, type ChangeEvent } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";

interface LigneReleve {
  id: string;
  date_operation: string;
  libelle: string;
  montant: number;
  statut: "rapproche_automatique" | "rapproche_manuel" | "a_verifier" | "non_rapproche";
  ligne_ecriture_id: string | null;
  code_lettrage: string | null;
  candidats_alternatifs: string[];
}

const LABELS_STATUT: Record<LigneReleve["statut"], string> = {
  rapproche_automatique: "Rapproché",
  rapproche_manuel: "Rapproché (manuel)",
  a_verifier: "À vérifier",
  non_rapproche: "Non rapproché",
};

const COULEURS_STATUT: Record<LigneReleve["statut"], string> = {
  rapproche_automatique: "text-forest",
  rapproche_manuel: "text-forest",
  a_verifier: "text-red",
  non_rapproche: "text-ink-soft",
};

export function Rapprochement() {
  const { selectedClientId } = useClient();
  const [lignes, setLignes] = useState<LigneReleve[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [importEnCours, setImportEnCours] = useState(false);

  function charger() {
    if (!selectedClientId) return;
    api
      .get<LigneReleve[]>(`/api/v1/clients/${selectedClientId}/rapprochement`)
      .then(setLignes)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erreur de chargement"));
  }

  useEffect(charger, [selectedClientId]);

  async function handleImport(e: ChangeEvent<HTMLInputElement>) {
    if (!selectedClientId || !e.target.files?.[0]) return;
    setImportEnCours(true);
    setError(null);
    const formData = new FormData();
    formData.append("fichier", e.target.files[0]);
    try {
      await api.upload(`/api/v1/clients/${selectedClientId}/rapprochement/import`, formData);
      charger();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec de l'import du relevé");
    } finally {
      setImportEnCours(false);
    }
  }

  async function validerManuel(ligneId: string, ligneEcritureId: string) {
    try {
      await api.post(`/api/v1/clients/${selectedClientId}/rapprochement/${ligneId}/valider`, {
        ligne_ecriture_id: ligneEcritureId,
      });
      charger();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec de la validation");
    }
  }

  const nombreRapprochees = lignes.filter((l) => l.statut !== "non_rapproche" && l.statut !== "a_verifier").length;

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Rapprochement bancaire</h1>
      <p className="text-ink-soft mb-6">
        Importez un relevé (CSV) — chaque ligne est comparée aux écritures du compte banque existantes.
      </p>

      <ClientPicker />

      {error && <div className="text-sm text-red bg-red/10 border border-red/30 rounded px-3 py-2 mb-4">{error}</div>}

      {!selectedClientId ? (
        <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
          Sélectionnez un dossier client.
        </div>
      ) : (
        <>
          <label className="inline-block mb-6 border border-rule-strong rounded px-4 py-2 text-sm font-medium bg-white cursor-pointer hover:bg-paper-dim">
            {importEnCours ? "Import en cours..." : "Importer un relevé CSV"}
            <input type="file" accept=".csv" className="hidden" onChange={handleImport} disabled={importEnCours} />
          </label>

          {lignes.length > 0 && (
            <p className="text-sm text-ink-soft mb-4">
              {nombreRapprochees} / {lignes.length} lignes rapprochées
            </p>
          )}

          {lignes.length === 0 ? (
            <div className="border border-rule-strong rounded bg-white p-10 text-center text-ink-soft text-sm">
              Aucun relevé importé pour ce client.
            </div>
          ) : (
            <div className="border border-rule-strong rounded bg-white overflow-hidden">
              <div className="grid grid-cols-[100px_1fr_100px_140px_80px_1fr] gap-3 px-4 py-2 text-xs font-mono uppercase text-ink-soft border-b border-rule bg-paper-dim">
                <span>Date</span>
                <span>Libellé</span>
                <span className="text-right">Montant</span>
                <span>Statut</span>
                <span>Lettrage</span>
                <span>Candidats (si ambigu)</span>
              </div>
              {lignes.map((l) => (
                <div
                  key={l.id}
                  className="grid grid-cols-[100px_1fr_100px_140px_80px_1fr] gap-3 px-4 py-2 border-b border-rule last:border-b-0 text-sm items-center"
                >
                  <span className="font-mono text-xs">{l.date_operation}</span>
                  <span>{l.libelle}</span>
                  <span className="text-right font-mono">{l.montant}</span>
                  <span className={`text-xs font-mono ${COULEURS_STATUT[l.statut]}`}>{LABELS_STATUT[l.statut]}</span>
                  <span className="font-mono text-xs text-gold">{l.code_lettrage ?? ""}</span>
                  <span className="flex gap-2 flex-wrap">
                    {l.statut === "a_verifier" &&
                      l.candidats_alternatifs.map((c) => (
                        <button
                          key={c}
                          onClick={() => validerManuel(l.id, c)}
                          className="text-xs border border-rule-strong rounded px-2 py-1 hover:bg-forest hover:text-paper hover:border-forest"
                        >
                          {c.slice(0, 8)}…
                        </button>
                      ))}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
