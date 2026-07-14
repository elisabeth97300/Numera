import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth";

type Props = { open?: boolean; onClose?: () => void };
type IconName = "dashboard" | "assistant" | "documents" | "validation" | "entries" | "bank" | "balance" | "analysis";

const items: Array<{ to: string; label: string; subtitle: string; icon: IconName }> = [
  { to: "/", label: "Tableau de bord", subtitle: "Vue d’ensemble", icon: "dashboard" },
  { to: "/assistant", label: "Assistant IA", subtitle: "Posez vos questions", icon: "assistant" },
  { to: "/import", label: "Documents", subtitle: "Importer et classer", icon: "documents" },
  { to: "/validation", label: "À valider", subtitle: "Propositions de l’IA", icon: "validation" },
  { to: "/ecritures", label: "Écritures", subtitle: "Journaux comptables", icon: "entries" },
  { to: "/rapprochement", label: "Banque", subtitle: "Rapprochement bancaire", icon: "bank" },
  { to: "/bilan", label: "États financiers", subtitle: "Bilan et résultat", icon: "balance" },
  { to: "/analyse", label: "Analyse", subtitle: "Diagnostic financier", icon: "analysis" },
];

function Icon({ name }: { name: IconName }) {
  const p: Record<IconName, ReactNode> = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
    assistant: <><path d="M12 3a6 6 0 0 0-6 6v2a4 4 0 0 1-2 3.5V17h16v-2.5A4 4 0 0 1 18 11V9a6 6 0 0 0-6-6Z"/><path d="M9 21h6"/></>,
    documents: <><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></>,
    validation: <><path d="M9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></>,
    entries: <><path d="M4 4h16v16H4z"/><path d="M8 8h8M8 12h8M8 16h5"/></>,
    bank: <><path d="m3 10 9-6 9 6"/><path d="M5 10v8M9 10v8M15 10v8M19 10v8"/><path d="M3 21h18"/></>,
    balance: <><path d="M4 5h16"/><path d="M12 5v16"/><path d="m7 9-4 7h8L7 9Z"/><path d="m17 9-4 7h8l-4-7Z"/></>,
    analysis: <><path d="M4 19V9"/><path d="M10 19V5"/><path d="M16 19v-7"/><path d="M22 19V3"/></>,
  };
  return <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{p[name]}</svg>;
}

export function Sidebar({ open = false, onClose }: Props) {
  const { user, logout } = useAuth();

  return (
    <>
      {open && <button onClick={onClose} className="fixed inset-0 z-40 bg-slate-950/45 backdrop-blur-sm lg:hidden" aria-label="Fermer le menu" />}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r border-white/10 bg-[#0c1712] text-white shadow-2xl transition-transform duration-300 lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="px-5 pb-4 pt-5">
          <div className="flex items-center justify-between">
            <NavLink to="/" onClick={onClose} className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-300 to-emerald-500 font-bold text-emerald-950 shadow-lg">N</span>
              <span>
                <span className="block text-lg font-semibold">Numera</span>
                <span className="block text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-200/55">Finance intelligente</span>
              </span>
            </NavLink>
            <button onClick={onClose} className="h-9 w-9 rounded-xl text-white/60 hover:bg-white/10 lg:hidden">×</button>
          </div>

          <div className="mt-5 rounded-2xl border border-emerald-300/10 bg-white/[0.06] p-3">
            <p className="text-xs text-white/40">Espace de démonstration</p>
            <div className="mt-1 flex items-center justify-between">
              <p className="text-sm font-semibold">Cabinet Démo</p>
              <span className="rounded-full bg-emerald-300/15 px-2 py-1 text-[10px] font-bold uppercase text-emerald-200">Bêta</span>
            </div>
          </div>
        </div>

        <nav className="numera-scrollbar flex-1 overflow-y-auto px-3 pb-5">
          <p className="px-3 pb-2 pt-3 text-[10px] font-bold uppercase tracking-[0.18em] text-white/30">Navigation</p>
          <div className="space-y-1">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onClick={onClose}
                className={({ isActive }) =>
                  `group flex items-center gap-3 rounded-2xl px-3 py-3 transition ${
                    isActive ? "bg-emerald-300 text-emerald-950 shadow-lg shadow-black/20" : "text-white/65 hover:bg-white/[0.07] hover:text-white"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${isActive ? "bg-emerald-950/10" : "bg-white/[0.06]"}`}><Icon name={item.icon}/></span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-semibold">{item.label}</span>
                      <span className={`block truncate text-[11px] ${isActive ? "text-emerald-950/60" : "text-white/35"}`}>{item.subtitle}</span>
                    </span>
                    <span className={isActive ? "text-emerald-950/50" : "text-white/20"}>›</span>
                  </>
                )}
              </NavLink>
            ))}
          </div>
        </nav>

        <div className="border-t border-white/10 p-4">
          <div className="flex items-center gap-3 rounded-2xl bg-white/[0.05] p-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 font-bold text-emerald-200">{(user?.email?.[0] ?? "E").toUpperCase()}</span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold">{user?.email ?? "Mode démonstration"}</span>
              <span className="block text-[11px] text-white/35">Administrateur</span>
            </span>
            {user && <button onClick={logout} className="h-9 w-9 rounded-xl text-white/40 hover:bg-red-400/15 hover:text-red-200" aria-label="Se déconnecter">↗</button>}
          </div>
        </div>
      </aside>
    </>
  );
}
