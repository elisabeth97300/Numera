import { useClient } from "../lib/client";

const recommendations = [
  {
    title: "Réduire les délais de règlement clients",
    text: "Le délai moyen atteint 54 jours, soit 9 jours de plus que l’objectif.",
    impact: "Impact trésorerie estimé : +24 000 €",
  },
  {
    title: "Surveiller les charges de personnel",
    text: "Elles représentent 46 % du chiffre d’affaires contre 39 % l’an dernier.",
    impact: "Écart annuel estimé : 18 600 €",
  },
  {
    title: "Préparer l’échéance de TVA",
    text: "Le montant estimé à décaisser est de 13 200 € dans 18 jours.",
    impact: "Provision recommandée immédiatement",
  },
];

export function Analyse() {
  const { clients, selectedClientId } = useClient();

  const selectedClient =
    clients.find((client) => client.id === selectedClientId) ?? clients[0];

  return (
    <div className="min-h-screen bg-[#F6F7F9] p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-7">
        <header>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.16em] text-forest">
            Intelligence financière
          </p>

          <h1 className="font-display text-3xl font-semibold text-ink">
            Analyse financière
          </h1>

          <p className="mt-2 text-sm text-ink-soft">
            Diagnostic du dossier{" "}
            <span className="font-semibold text-ink">
              {selectedClient?.raison_sociale ?? "Cabinet Démo"}
            </span>
            .
          </p>
        </header>

        <section className="grid gap-5 lg:grid-cols-[0.8fr_2fr]">
          <article className="rounded-2xl bg-[#15241B] p-6 text-white">
            <p className="text-sm text-[#B9CDBE]">Score de santé financière</p>

            <div className="mt-7 flex items-end gap-2">
              <span className="text-6xl font-bold">78</span>
              <span className="pb-2 text-lg text-[#B9CDBE]">/ 100</span>
            </div>

            <div className="mt-6 h-2 overflow-hidden rounded-full bg-white/15">
              <div className="h-full w-[78%] rounded-full bg-[#8BC49A]" />
            </div>

            <p className="mt-5 text-sm leading-6 text-[#D7E1D9]">
              Situation globalement saine. La croissance est solide, mais les
              charges de personnel et le besoin en fonds de roulement doivent
              être surveillés.
            </p>
          </article>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {[
              ["Marge nette", "16,0 %", "+1,8 point"],
              ["Marge brute", "39,4 %", "-3,2 points"],
              ["BFR", "62 800 €", "+14,6 %"],
              ["Trésorerie", "148 000 €", "2,8 mois"],
              ["Autonomie financière", "54 %", "Niveau satisfaisant"],
              ["Endettement", "31 %", "Risque modéré"],
            ].map(([label, value, note]) => (
              <article
                key={label}
                className="rounded-2xl border border-[#E3E7E3] bg-white p-5"
              >
                <p className="text-sm text-ink-soft">{label}</p>
                <p className="mt-3 text-2xl font-bold text-ink">{value}</p>
                <p className="mt-2 text-xs text-ink-soft">{note}</p>
              </article>
            ))}
          </section>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-6">
            <h2 className="text-lg font-semibold text-ink">Forces détectées</h2>

            <div className="mt-5 space-y-4">
              {[
                "Chiffre d’affaires en progression de 12,4 %",
                "Trésorerie couvrant près de trois mois de charges",
                "Taux de rapprochement bancaire supérieur à 95 %",
                "Endettement maîtrisé",
              ].map((text) => (
                <div key={text} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#E8F4EB] text-xs font-bold text-[#246236]">
                    ✓
                  </span>
                  <p className="text-sm leading-6 text-ink">{text}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-6">
            <h2 className="text-lg font-semibold text-ink">
              Points de vigilance
            </h2>

            <div className="mt-5 space-y-4">
              {[
                "Baisse de la marge brute depuis trois mois",
                "Hausse des charges de personnel",
                "Délai de règlement client supérieur à l’objectif",
                "Trois factures échues non réglées",
              ].map((text) => (
                <div key={text} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#FFF0E8] text-xs font-bold text-[#A64E20]">
                    !
                  </span>
                  <p className="text-sm leading-6 text-ink">{text}</p>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="rounded-2xl border border-[#E3E7E3] bg-white p-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-forest">
              Recommandations IA
            </p>
            <h2 className="mt-2 text-xl font-semibold text-ink">
              Actions prioritaires
            </h2>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            {recommendations.map((item, index) => (
              <article
                key={item.title}
                className="rounded-xl border border-[#E4E8E4] bg-[#FAFBFA] p-5"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest text-sm font-bold text-white">
                  {index + 1}
                </div>

                <h3 className="mt-4 text-sm font-semibold text-ink">
                  {item.title}
                </h3>

                <p className="mt-2 text-xs leading-5 text-ink-soft">
                  {item.text}
                </p>

                <p className="mt-4 text-xs font-semibold text-forest">
                  {item.impact}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-6">
            <h2 className="text-lg font-semibold text-ink">
              Prévision de trésorerie
            </h2>

            <p className="mt-1 text-sm text-ink-soft">
              Projection sur les six prochains mois.
            </p>

            <div className="mt-8 flex h-60 items-end gap-5 border-b border-l border-[#E3E7E3] px-5 pb-3">
              {[68, 73, 64, 79, 87, 92].map((height, index) => (
                <div
                  key={index}
                  className="flex flex-1 flex-col items-center justify-end gap-2"
                >
                  <div
                    className="w-full max-w-12 rounded-t-lg bg-forest"
                    style={{ height: `${height}%` }}
                  />

                  <span className="text-xs text-ink-soft">
                    {["Août", "Sept.", "Oct.", "Nov.", "Déc.", "Janv."][index]}
                  </span>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-2xl border border-[#E3E7E3] bg-white p-6">
            <h2 className="text-lg font-semibold text-ink">
              Résumé pour le dirigeant
            </h2>

            <p className="mt-4 text-sm leading-7 text-ink-soft">
              L’entreprise connaît une croissance soutenue et dispose d’une
              trésorerie confortable. La rentabilité reste positive, mais la
              hausse des charges de personnel et l’allongement des délais
              clients réduisent progressivement la marge.
            </p>

            <button className="mt-6 w-full rounded-xl bg-forest px-4 py-3 text-sm font-semibold text-white">
              Générer une note de synthèse
            </button>
          </article>
        </section>

        <p className="text-center text-xs text-ink-soft">
          Analyse de démonstration — les données réelles seront issues des
          balances, journaux et écritures validées.
        </p>
      </div>
    </div>
  );
}
