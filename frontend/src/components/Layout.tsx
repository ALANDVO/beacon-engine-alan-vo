import { Outlet, NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, FileBox, FileCode, Hammer, Settings, LogOut, User, Menu, X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import clsx from "clsx";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "ISOs", href: "/isos", icon: FileBox },
  { name: "Recipes", href: "/recipes", icon: FileCode },
  { name: "Builds", href: "/builds", icon: Hammer },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Layout() {
  const { user, setUser } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = () => {
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen flex">
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 transform transition-transform duration-200 ease-in-out lg:translate-x-0",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Main navigation"
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800">
            <NavLink to="/dashboard" className="flex items-center gap-2" aria-label="beacon-engine home">
              <svg className="w-8 h-8 text-blue-500" viewBox="0 0 32 32" fill="none">
                <rect width="32" height="32" rx="6" fill="#1e293b"/>
                <path d="M16 6L26 16L16 26" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                <path d="M6 16H26" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round"/>
              </svg>
              <span className="text-xl font-bold text-white">beacon-engine</span>
            </NavLink>
            <button
              className="lg:hidden p-2 text-slate-400 hover:text-white"
              onClick={() => setMobileMenuOpen(false)}
              aria-label="Close menu"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Main">
            <ul role="list" className="space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + "/");
                return (
                  <li key={item.name}>
                    <NavLink
                      to={item.href}
                      className={clsx(
                        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                        isActive
                          ? "bg-blue-600/20 text-blue-400"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      )}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                      {item.name}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="p-3 border-t border-slate-800">
            <div className="relative">
              <button
                className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                aria-expanded={userMenuOpen}
                aria-haspopup="true"
              >
                <User className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                <span className="truncate flex-1">{user?.name || "User"}</span>
              </button>
              {userMenuOpen && (
                <div className="absolute bottom-full left-0 right-0 mb-1 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1">
                  <div className="px-3 py-2 text-xs text-slate-400 border-b border-slate-700">{user?.email}</div>
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white"
                  >
                    <LogOut className="w-4 h-4" aria-hidden="true" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </aside>

      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className="flex-1 flex flex-col min-w-0 lg:ml-64">
        <header className="sticky top-0 z-30 flex items-center gap-4 h-16 px-4 bg-slate-900/80 backdrop-blur-sm border-b border-slate-800 lg:px-6">
          <button
            className="lg:hidden p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" />
          </button>
          <h1 className="text-lg font-semibold text-white truncate">
            {navigation.find((n) => location.pathname === n.href || location.pathname.startsWith(n.href + "/"))?.name ||
              "beacon-engine"}
          </h1>
        </header>

        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          <Outlet />
        </main>

        <footer className="px-4 py-3 border-t border-slate-800 text-xs text-slate-500 lg:px-6 lg:ml-64">
          <p>beacon-engine &mdash; Alan Vo | AI & Machine Learning &mdash; alanvo@gmail.com</p>
        </footer>
      </div>
    </div>
  );
}