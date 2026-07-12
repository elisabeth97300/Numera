import { useState, type ChangeEvent, type DragEvent } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";

const TYPES_DOCUMENT = [
  { value: "facture_achat", label: "Facture d'achat" },
  { value: "facture_vente", label: "Facture de vente" },
  { value: "releve_bancaire", label: "Relevé bancaire" },
  { value: "fec", label: "Fichier FEC" },
];

interface StatutFichier {
  nom: string;
  statut: "en_cours" | "succes" | "erreur";
  message?: string;
  doublon?: boolean;
}

export function Import() {
  const { selectedClientId } = useClient();
  const [isDragging, setIsDragging] = useState(false);
  const [typeDocument, setTypeDocument] = useState("facture_achat");
  const [fichiers, setFichiers] = useState<StatutFichier[]>([]);

  async function envoyerFichiers(fileList: FileList) {
    if (!selectedClientId) return;

    for (const fichier of Array.from(fileList)) {
      setFichiers((prev) => [...prev, { nom: fichier.name, statut: "en_cours" }]);

      const formData = new FormData();
      formData.append("fichier", fichier);

      try {
        const res = await api.upload<{ doublon_detecte: boolean }>(
          `/api/v1/clients/${selectedClientId}/documents?type_document=${typeDocument}`,
          formData,
        );
        setFichiers((prev) =>
          prev.map((f) =>
            f.nom === fichier.name && f.statut === "en_cours"
              ? { ...f, statut: "succes", doublon: res.doublon_detecte }
              : f,
          ),
        );
      } catch (err) {
        setFichiers((prev) =>
          prev.map((f) =>
            f.nom === fichier.name && f.statut === "en_cours"
              ? { ...f, statut: "erreur", message: err instanceof ApiError ? err.message : "Échec de l'envoi" }
              : f,
          ),
        );
      }
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    envoyerFichiers(e.dataTransfer.files);
  }

  function handleInputChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) envoyerFichiers(e.target.files);
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Import de documents</h1>
      <p className="text-ink-soft mb-6">PDF, images, Excel, CSV ou fichiers FEC.</p>

      <ClientPicker />

      {!selectedClientId ? (
        <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
          Sélectionnez un dossier client ci-dessus avant d'importer un document.
        </div>
      ) : (
        <>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Type de document</label>
            <select
              value={typeDocument}
              onChange={(e) => setTypeDocument(e.target.value)}
              className="border border-rule-strong rounded px-3 py-2 text-sm bg-white"
            >
              {TYPES_DOCUMENT.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <label
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`block border-2 border-dashed rounded p-16 text-center transition-colors cursor-pointer ${
              isDragging ? "border-forest bg-forest-dim" : "border-rule-strong bg-white"
            }`}
          >
            <p className="font-medium mb-1">Glissez-déposez vos fichiers ici</p>
            <p className="text-sm text-ink-soft">ou cliquez pour parcourir votre ordinateur</p>
            <input type="file" multiple className="hidden" onChange={handleInputChange} />
          </label>

          {fichiers.length > 0 && (
            <div className="mt-6 border border-rule-strong rounded bg-white overflow-hidden">
              {fichiers.map((f, i) => (
                <div key={i} className="px-4 py-3 border-b border-rule last:border-b-0 flex justify-between text-sm">
                  <span>{f.nom}</span>
                  <span
                    className={
                      f.statut === "succes"
                        ? f.doublon
                          ? "text-red font-medium"
                          : "text-forest font-medium"
                        : f.statut === "erreur"
                          ? "text-red font-medium"
                          : "text-ink-soft"
                    }
                  >
                    {f.statut === "en_cours" && "Envoi..."}
                    {f.statut === "succes" && (f.doublon ? "Doublon détecté" : "Envoyé — OCR en cours")}
                    {f.statut === "erreur" && (f.message ?? "Erreur")}
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
