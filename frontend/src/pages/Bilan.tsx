import { useEffect, useState } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";

interface Poste {
  compte_pcg: string;
  libelle: string;
  montant: number;
}

interface BilanAPI {
  actif: Poste[];
  passif: Poste[];
  total_actif: number;
  total_passif: number;
  equilibre: boolean;
}

interface CompteResultatAPI {
  charges: Poste[];
  produits: Poste[];
  total_charges: number;
  total_produits: number;
  resultat_net: number;
}

export function Bilan() {
  const { selectedClientId, selectedExerciceId } = useClient();
  const [bilan, setBilan] = useState<BilanAPI | null>(null);
  const [compteResultat, setCompteResultat] = useState<CompteResultatAPI | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedClientId || !selectedExerciceId) return;
    setError(null);
    Promise.all([
      api.get<BilanAPI>(`/api/v1/clients/${selectedClientId}/bilan?exercice_id=${selectedExerciceId}`),
      api.get<CompteResultatAPI>(
        `/api/v1/clients/${selectedClientId}/compte-resultat?exercice_id=${selectedExerciceId}`,
      ),
    ])
      .then(([b, cr]) => {
        setBilan(b);
        setCompteResultat(cr);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erreur de chargement"));
  }, [selectedClientId, selectedExerciceId]);

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Bilan &amp; Compte de résultat</h1>
      <p className="text-ink-soft mb-6">Générés à partir des écritures validées de l'exercice sélectionné.</p>

      <ClientPicker requireExercice />

      {error && <div className="text-sm text-red mb-4">{error}</div>}

      {!selectedClientId || !selectedExerciceId ? (
        <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
          Sélectionnez un dossier client et un exercice.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          <div className="border border-rule-strong rounded bg-white p-6">
            <h2 className="font-display font-semibold mb-4">
              Bilan {bilan && (bilan.equilibre ? <span className="text-forest text-xs font-mono ml-2">équilibré</span> : <span className="text-red text-xs font-mono ml-2">déséquilibré</span>)}
            </h2>
            {bilan && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-mono text-xs text-ink-soft mb-2">ACTIF</div>
                  {bilan.actif.map((p) => (
                    <div key={p.compte_pcg} className="flex justify-between py-1 border-b border-rule">
                      <span className="font-mono text-xs text-gold">{p.compte_pcg}</span>
                      <span className="font-mono">{p.montant}</span>
                    </div>
                  ))}
                  <div className="flex justify-between pt-2 font-semibold">
                    <span>Total</span>
                    <span className="font-mono">{bilan.total_actif}</span>
                  </div>
                </div>
                <div>
                  <div className="font-mono text-xs text-ink-soft mb-2">PASSIF</div>
                  {bilan.passif.map((p) => (
                    <div key={p.compte_pcg} className="flex justify-between py-1 border-b border-rule">
                      <span className="font-mono text-xs text-gold">{p.compte_pcg}</span>
                      <span className="font-mono">{p.montant}</span>
                    </div>
                  ))}
                  <div className="flex justify-between pt-2 font-semibold">
                    <span>Total</span>
                    <span className="font-mono">{bilan.total_passif}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="border border-rule-strong rounded bg-white p-6">
            <h2 className="font-display font-semibold mb-4">Compte de résultat</h2>
            {compteResultat && (
              <div className="text-sm">
                <div className="font-mono text-xs text-ink-soft mb-2">CHARGES</div>
                {compteResultat.charges.map((p) => (
                  <div key={p.compte_pcg} className="flex justify-between py-1 border-b border-rule">
                    <span className="font-mono text-xs text-gold">{p.compte_pcg}</span>
                    <span className="font-mono">{p.montant}</span>
                  </div>
                ))}
                <div className="font-mono text-xs text-ink-soft mb-2 mt-4">PRODUITS</div>
                {compteResultat.produits.map((p) => (
                  <div key={p.compte_pcg} className="flex justify-between py-1 border-b border-rule">
                    <span className="font-mono text-xs text-gold">{p.compte_pcg}</span>
                    <span className="font-mono">{p.montant}</span>
                  </div>
                ))}
                <div className="flex justify-between pt-3 font-semibold">
                  <span>Résultat net</span>
                  <span className={`font-mono ${compteResultat.resultat_net >= 0 ? "text-forest" : "text-red"}`}>
                    {compteResultat.resultat_net}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
