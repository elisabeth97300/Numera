import { NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth";

const links = [
  { to: "/", label: "Tableau de bord" },
  { to: "/assistant", label: "Assistant IA" },
  { to: "/import", label: "Import" },
  { to: "/validation", label: "Validation" },
  { to: "/ecritures", label: "Écritures" },
  { to: "/rapprochement", label: "Rapprochement bancaire" },
  { to: "/bilan", label: "Bilan" },
  { to: "/analyse", label: "Analyse" },
];

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 shrink-0 border-r border-rule-strong bg-paper-dim flex flex-col justify-between min-h-screen">
      <div>
        <div className="px-6 py-5 border-b border-rule-strong">
          <span className="font-display font-semibold text-lg">ComptaCopilot AI</span>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                `px-3 py-2 rounded text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-forest text-paper"
                    : "text-ink-soft hover:bg-paper hover:text-ink"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="p-4 border-t border-rule-strong text-sm">
        <div className="text-ink-soft mb-2 truncate">{user?.email}</div>
        <button
          onClick={logout}
          className="text-red font-medium hover:underline"
        >
          Se déconnecter
        </button>
      </div>
    </aside>
  );
}
