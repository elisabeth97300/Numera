import { useClient } from "../lib/client";

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);

const kpis = [
  {
    label: "Chiffre d’affaires",
    value: 425800,
    evolution: "+12,4 %",
    tone: "positive",
    description: "Depuis le début de l’exercice",
  },
  {
    label: "Charges d’exploitation",
    value: 301200,
    evolution: "+6,8 %",
    tone: "neutral",
    description: "Achats, personnel et frais généraux",
  },
  {
    label: "Résultat provisoire",
    value: 68300,
    evolution: "+9,2 %",
    tone: "positive",
    description: "Avant impôt sur les sociétés",
  },
  {
    label: "Trésorerie disponible",
    value: 148000,
    evolution: "2,8 mois",
    tone: "positive",
    description: "Couverture estimée des charges fixes",
  },
];

const activity = [
  {
    title: "Facture fournisseur importée",
    detail: "EDF — 1 284 €",
    time: "Il y a 12 min",
  },
  {
    title: "Écriture validée",
    detail: "Journal achats — pièce FA-2031",
    time: "Il y a 34 min",
  },
  {
    title: "Anomalie détectée",
    detail: "Compte 6251 inhabituellement élevé",
    time: "Il y a 1 h",
  },
  {
    title: "Rapprochement effectué",
    detail: "Banque BNP — 18 opérations",
    time: "Il y a 2 h",
  },
];

const alerts = [
  {
    level: "attention",
    title: "Charges de personnel élevées",
    text: "Elles représentent 46 % du chiffre d’affaires.",
  },
  {
    level: "urgent",
    title: "3 règlements clients en retard",
    text: "Le montant total en attente est de 18 420 €.",
  },
  {
    level: "info",
    title: "TVA à préparer",
    text: "La prochaine échéance est estimée à 13 200 €.",
  },
];

export function Dashboard() {
  const { clients, selectedClientId } = useClient();

  const selectedClient =
    clients.find((client) => client.id === selectedClientId) ?? clients[0];

  return (
    <div className="min-h-screen bg-[#F6F7F9] p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-7">
        <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="mb-2 text-sm font-semibold uppercase tracking-[0.16em] text-forest">
              Vue financière
            </p>

            <h1 className="font-display text-3xl font-semibold text-ink lg:text-4xl">
              Bonjour Elisabeth
            </h1>

            <p className="mt-2 text-sm text-ink-soft">
              Voici la situation du dossier{" "}
              <span className="font-semibold text-ink">
                {selectedClient?.raison_sociale ?? "Cabinet Démo"}
              </span>
              .
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select className="rounded-xl border border-[#D8DDD8] bg-white px-4 py-3 text-sm font-medium text-ink shadow-sm outline-none">
              <option>Exercice 2026</option>
              <option>Exercice 2025</option>
            </select>

            <button className="rounded-xl bg-forest px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-90">
              Importer un document
            </button>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => (
            <article
              key={kpi.label}
              className="rounded-2xl border border-[#E3E7E3] bg-white p-5 shadow-[0_8px_30px_rgba(22,35,28,0.05)]"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-ink-soft">{kpi.label}</p>

                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                    kpi.tone === "positive"
                      ? "bg-[#E8F4EB] text-[#246236]"
                      : "bg-[#F1F2EE] text-ink-soft"
                  }`}
                >
                  {kpi.evolution}
                </span>
              </div>

              <p className="mt-4 text-2xl font-bold tracking-tight text-ink">
                {formatCurrency(kpi.value)}
              </p>

              <p className="mt-2 text-xs leading-5 text-ink-soft">
                {kpi.description}
              </p>
            </article>
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-5">
            <p className="text-sm text-ink-soft">TVA à décaisser</p>
            <p className="mt-3 text-2xl font-bold text-ink">13 200 €</p>
            <p className="mt-2 text-xs text-gold">Échéance dans 18 jours</p>
          </article>

          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-5">
            <p className="text-sm text-ink-soft">Documents à traiter</p>
            <p className="mt-3 text-2xl font-bold text-ink">18</p>
            <p className="mt-2 text-xs text-ink-soft">6 importés aujourd’hui</p>
          </article>

          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-5">
            <p className="text-sm text-ink-soft">Écritures à valider</p>
            <p className="mt-3 text-2xl font-bold text-ink">42</p>
            <p className="mt-2 text-xs text-red">7 à vérifier en priorité</p>
          </article>

          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-5">
            <p className="text-sm text-ink-soft">Taux de rapprochement</p>
            <p className="mt-3 text-2xl font-bold text-ink">97 %</p>
            <p className="mt-2 text-xs text-forest">+4 points ce mois-ci</p>
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-6 shadow-[0_8px_30px_rgba(22,35,28,0.04)]">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-ink">
                  Activité financière
                </h2>
                <p className="mt-1 text-sm text-ink-soft">
                  Évolution du chiffre d’affaires et des charges.
                </p>
              </div>

              <select className="rounded-lg border border-[#D8DDD8] bg-white px-3 py-2 text-xs text-ink">
                <option>12 derniers mois</option>
                <option>6 derniers mois</option>
              </select>
            </div>

            <div className="mt-8 flex h-64 items-end gap-3 border-b border-l border-[#E4E8E4] px-4 pb-3">
              {[42, 54, 49, 61, 68, 73, 65, 76, 81, 78, 88, 94].map(
                (height, index) => (
                  <div
                    key={index}
                    className="group flex flex-1 items-end justify-center"
                  >
                    <div
                      className="w-full max-w-8 rounded-t-md bg-forest/80 transition group-hover:bg-forest"
                      style={{ height: `${height}%` }}
                      title={`${height * 5000} €`}
                    />
                  </div>
                ),
              )}
            </div>

            <div className="mt-4 flex items-center gap-6 text-xs text-ink-soft">
              <span className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-forest" />
                Chiffre d’affaires
              </span>

              <span className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-rule-strong" />
                Charges
              </span>
            </div>
          </article>

          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-6 shadow-[0_8px_30px_rgba(22,35,28,0.04)]">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-ink">Alertes IA</h2>
                <p className="mt-1 text-sm text-ink-soft">
                  Points nécessitant votre attention.
                </p>
              </div>

              <span className="rounded-full bg-[#FFF3DD] px-3 py-1 text-xs font-semibold text-gold">
                3 alertes
              </span>
            </div>

            <div className="mt-5 space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.title}
                  className={`rounded-xl border p-4 ${
                    alert.level === "urgent"
                      ? "border-red/20 bg-red/5"
                      : alert.level === "attention"
                        ? "border-gold/20 bg-gold/5"
                        : "border-rule bg-paper-dim/30"
                  }`}
                >
                  <p className="text-sm font-semibold text-ink">{alert.title}</p>
                  <p className="mt-1 text-xs leading-5 text-ink-soft">
                    {alert.text}
                  </p>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-6">
            <h2 className="text-lg font-semibold text-ink">
              Dernières activités
            </h2>

            <div className="mt-5 divide-y divide-[#EEF0EE]">
              {activity.map((item) => (
                <div
                  key={`${item.title}-${item.time}`}
                  className="flex items-start justify-between gap-5 py-4 first:pt-0"
                >
                  <div>
                    <p className="text-sm font-semibold text-ink">
                      {item.title}
                    </p>
                    <p className="mt-1 text-xs text-ink-soft">{item.detail}</p>
                  </div>

                  <span className="whitespace-nowrap text-xs text-ink-soft">
                    {item.time}
                  </span>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-2xl bg-[#15241B] p-6 text-white">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#AFC9B5]">
              Synthèse IA
            </p>

            <h2 className="mt-3 text-xl font-semibold">
              Une activité en croissance, avec une marge à surveiller.
            </h2>

            <p className="mt-4 text-sm leading-6 text-[#D5DFD7]">
              Le chiffre d’affaires progresse de 12,4 %, mais les charges
              augmentent plus rapidement sur les deux derniers mois. La
              trésorerie reste confortable.
            </p>

            <button className="mt-6 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-[#15241B]">
              Voir l’analyse complète
            </button>
          </article>
        </section>

        <p className="text-center text-xs text-ink-soft">
          Données de démonstration — les indicateurs réels seront calculés
          depuis les écritures validées.
        </p>
      </div>
    </div>
  );
}
