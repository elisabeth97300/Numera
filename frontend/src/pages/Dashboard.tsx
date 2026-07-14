import { useNavigate } from "react-router-dom";
import { useClient } from "../lib/client";

const money = (value: number) =>
  new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);

const revenue = [28, 34, 31, 42, 47, 51, 49, 58, 63, 61, 70, 76];
const expenses = [21, 23, 24, 27, 30, 33, 32, 35, 39, 38, 42, 45];
const months = ["Aoû", "Sep", "Oct", "Nov", "Déc", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil"];

const tasks = [
  { label: "Documents à traiter", value: 18, detail: "6 reçus aujourd’hui", className: "bg-amber-50 text-amber-700 border-amber-100" },
  { label: "Écritures à valider", value: 42, detail: "7 prioritaires", className: "bg-rose-50 text-rose-700 border-rose-100" },
  { label: "Opérations à rapprocher", value: 13, detail: "Banque principale", className: "bg-sky-50 text-sky-700 border-sky-100" },
  { label: "Alertes IA", value: 3, detail: "Analyse recommandée", className: "bg-violet-50 text-violet-700 border-violet-100" },
];

const alerts = [
  { title: "Marge brute en baisse", detail: "La marge recule de 3,2 points sur les trois derniers mois.", badge: "Priorité haute", tone: "bg-rose-50 text-rose-700" },
  { title: "Encours clients à surveiller", detail: "18 420 € de factures ont dépassé leur date d’échéance.", badge: "À relancer", tone: "bg-amber-50 text-amber-700" },
  { title: "TVA à provisionner", detail: "Le prochain décaissement est estimé à 13 200 €.", badge: "Dans 18 jours", tone: "bg-sky-50 text-sky-700" },
];

const activity = [
  { title: "Facture EDF analysée", detail: "Achat • 1 284 €", time: "Il y a 12 min" },
  { title: "18 opérations rapprochées", detail: "Banque BNP", time: "Il y a 34 min" },
  { title: "Écriture FA-2031 validée", detail: "Journal achats", time: "Il y a 1 h" },
  { title: "Prévision de TVA mise à jour", detail: "Juillet 2026", time: "Il y a 2 h" },
];

function Sparkline({ values }: { values: number[] }) {
  const max = Math.max(...values);
  const min = Math.min(...values);
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * 120;
      const y = 42 - ((value - min) / Math.max(max - min, 1)) * 34;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 120 48" className="h-12 w-28 overflow-visible">
      <polyline points={points} fill="none" stroke="#059669" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Dashboard() {
  const navigate = useNavigate();
  const { clients, selectedClientId } = useClient();
  const client = clients.find((item) => item.id === selectedClientId) ?? clients[0];

  return (
    <div className="min-h-screen bg-[#f5f7f6] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
      <div className="mx-auto max-w-[1500px] space-y-6">
        <header className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-emerald-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_0_5px_rgba(16,185,129,.12)]" />
              Activité mise à jour à l’instant
            </div>
            <h1 className="font-['Manrope'] text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Bonjour Elisabeth</h1>
            <p className="mt-2 text-sm text-slate-500">
              Voici l’essentiel pour <span className="font-semibold text-slate-800">{client?.raison_sociale ?? "Cabinet Démo"}</span>.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button onClick={() => navigate("/assistant")} className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
              ✦ Demander à Numera AI
            </button>
            <button onClick={() => navigate("/import")} className="rounded-xl bg-emerald-950 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-950/15 transition hover:-translate-y-0.5 hover:bg-emerald-900">
              ＋ Ajouter un document
            </button>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            { label: "Chiffre d’affaires", value: money(425800), trend: "+12,4 %", note: "vs exercice précédent", values: [21,24,23,29,31,35,34,39,44,42,49,54] },
            { label: "Charges d’exploitation", value: money(301200), trend: "+6,8 %", note: "vs exercice précédent", values: [18,19,20,21,24,23,25,27,29,30,31,34] },
            { label: "Résultat provisoire", value: money(68300), trend: "+9,2 %", note: "avant impôt", values: [10,12,9,14,16,15,18,17,21,22,24,27] },
            { label: "Trésorerie disponible", value: money(148000), trend: "2,8 mois", note: "de charges couvertes", values: [32,31,34,35,37,36,39,41,40,43,46,48] },
          ].map((kpi) => (
            <article key={kpi.label} className="group rounded-3xl border border-slate-200/80 bg-white p-5 shadow-[0_10px_35px_rgba(15,23,42,.045)] transition hover:-translate-y-1 hover:shadow-[0_20px_45px_rgba(15,23,42,.08)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">{kpi.label}</p>
                  <p className="mt-3 text-2xl font-bold tracking-tight text-slate-950">{kpi.value}</p>
                  <div className="mt-3 flex items-center gap-2 text-xs">
                    <span className="rounded-full bg-emerald-50 px-2 py-1 font-bold text-emerald-700">↗ {kpi.trend}</span>
                    <span className="text-slate-400">{kpi.note}</span>
                  </div>
                </div>
                <Sparkline values={kpi.values} />
              </div>
            </article>
          ))}
        </section>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {tasks.map((task) => (
            <button key={task.label} className="flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
              <span className={`flex h-12 w-12 items-center justify-center rounded-2xl border text-lg font-bold ${task.className}`}>{task.value}</span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold text-slate-900">{task.label}</span>
                <span className="mt-1 block text-xs text-slate-400">{task.detail}</span>
              </span>
              <span className="ml-auto text-slate-300">›</span>
            </button>
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.55fr_.85fr]">
          <article className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-[0_10px_35px_rgba(15,23,42,.045)] sm:p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-['Manrope'] text-lg font-bold text-slate-950">Performance financière</h2>
                <p className="mt-1 text-sm text-slate-500">Évolution mensuelle du chiffre d’affaires et des charges.</p>
              </div>
              <select className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 outline-none">
                <option>12 derniers mois</option>
                <option>6 derniers mois</option>
              </select>
            </div>

            <div className="mt-8 grid h-72 grid-cols-12 items-end gap-2 sm:gap-3">
              {revenue.map((value, index) => (
                <div key={months[index]} className="flex h-full flex-col justify-end gap-2">
                  <div className="flex flex-1 items-end justify-center gap-1">
                    <div className="w-2.5 rounded-t-md bg-emerald-700 hover:bg-emerald-600 sm:w-4" style={{ height: `${value}%` }} />
                    <div className="w-2.5 rounded-t-md bg-slate-200 hover:bg-slate-300 sm:w-4" style={{ height: `${expenses[index]}%` }} />
                  </div>
                  <span className="text-center text-[10px] font-medium text-slate-400 sm:text-xs">{months[index]}</span>
                </div>
              ))}
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-5 border-t border-slate-100 pt-4 text-xs font-medium text-slate-500">
              <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-emerald-700" /> Chiffre d’affaires</span>
              <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-slate-300" /> Charges</span>
              <span className="ml-auto font-semibold text-emerald-700">Marge actuelle : 16,0 %</span>
            </div>
          </article>

          <article className="relative overflow-hidden rounded-3xl bg-[#102019] p-6 text-white shadow-xl shadow-emerald-950/15">
            <div className="absolute -right-16 -top-16 h-52 w-52 rounded-full bg-emerald-300/10 blur-2xl" />
            <div className="relative">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs font-bold text-emerald-200">✦ Numera AI</span>
                <span className="text-xs text-white/35">Analyse du jour</span>
              </div>
              <h2 className="mt-6 font-['Manrope'] text-2xl font-bold leading-tight">La croissance reste solide, mais votre marge mérite une attention particulière.</h2>
              <p className="mt-4 text-sm leading-6 text-white/65">Le chiffre d’affaires progresse de 12,4 %. Les charges augmentent toutefois plus vite depuis trois mois.</p>
              <div className="mt-6 space-y-3">
                {["Relancer 3 factures échues", "Analyser les charges de personnel", "Provisionner la TVA de juillet"].map((item) => (
                  <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.06] p-3">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-300 text-xs font-bold text-emerald-950">✓</span>
                    <span className="text-sm font-medium text-white/85">{item}</span>
                  </div>
                ))}
              </div>
              <button onClick={() => navigate("/analyse")} className="mt-6 w-full rounded-xl bg-white px-4 py-3 text-sm font-bold text-emerald-950 transition hover:-translate-y-0.5 hover:bg-emerald-50">Ouvrir l’analyse complète</button>
            </div>
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <article className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-['Manrope'] text-lg font-bold text-slate-950">Alertes à traiter</h2>
                <p className="mt-1 text-sm text-slate-500">Priorités détectées automatiquement.</p>
              </div>
              <span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-bold text-rose-700">3 alertes</span>
            </div>
            <div className="mt-5 space-y-3">
              {alerts.map((alert) => (
                <div key={alert.title} className="flex gap-4 rounded-2xl border border-slate-100 p-4 transition hover:bg-slate-50">
                  <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl font-bold ${alert.tone}`}>!</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-semibold text-slate-900">{alert.title}</p>
                      <span className="text-xs font-semibold text-slate-400">{alert.badge}</span>
                    </div>
                    <p className="mt-1 text-sm leading-6 text-slate-500">{alert.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-['Manrope'] text-lg font-bold text-slate-950">Activité récente</h2>
                <p className="mt-1 text-sm text-slate-500">Ce que Numera a traité pour vous.</p>
              </div>
              <button className="text-sm font-semibold text-emerald-700 hover:text-emerald-800">Tout voir</button>
            </div>
            <div className="mt-5 divide-y divide-slate-100">
              {activity.map((item) => (
                <div key={item.title} className="flex items-start gap-4 py-4 first:pt-0 last:pb-0">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-sm font-bold text-emerald-700">✓</span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                    <p className="mt-1 text-xs text-slate-400">{item.detail}</p>
                  </div>
                  <span className="whitespace-nowrap text-xs text-slate-400">{item.time}</span>
                </div>
              ))}
            </div>
          </article>
        </section>

        <footer className="flex flex-col gap-2 border-t border-slate-200/70 py-4 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <span>Données de démonstration • Connexion aux écritures réelles à venir</span>
          <span>Dernière synchronisation : aujourd’hui à 09:48</span>
        </footer>
      </div>
    </div>
  );
}
