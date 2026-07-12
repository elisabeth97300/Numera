export type StatutExercice = "non_demarre" | "en_cours" | "cloture" | "archive";
export type OrigineExercice = "nouveau" | "repris";

export interface LigneSolde {
  id: string;
  compte_pcg: string;
  solde_debit: number;
  solde_credit: number;
  source: string;
}

export interface Exercice {
  id: string;
  client_id: string;
  date_debut: string;
  date_fin: string;
  statut: StatutExercice;
  origine: OrigineExercice;
  date_cloture: string | null;
  exercice_precedent_id: string | null;
  soldes_ouverture: LigneSolde[];
}

export interface PropositionIA {
  id: string;
  document_source_id: string;
  compte_propose: string;
  tiers_propose: string;
  montant_ht: number;
  montant_tva: number;
  taux_tva: number;
  score_confiance: number;
  a_verifier_en_priorite: boolean;
  avertissements?: string[] | null;
  statut: "en_attente" | "validee" | "modifiee" | "rejetee";
}

export interface Client {
  id: string;
  organisation_id: string;
  raison_sociale: string;
  siren: string | null;
  regime_tva: string;
  plan_comptable: string;
}

export interface User {
  id: string;
  email: string;
  role: "admin" | "comptable" | "assistant";
  organisation_id: string;
}
