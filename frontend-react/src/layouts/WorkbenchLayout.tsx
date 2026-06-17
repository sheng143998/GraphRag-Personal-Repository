import { NavLink, Outlet, useMatches } from "react-router-dom";

const navItems = [
  { to: "/chat", label: "Chat", icon: "chat" },
  { to: "/knowledge-base", label: "Knowledge Base", icon: "database" },
  { to: "/documents", label: "Documents", icon: "description" },
  { to: "/experiments", label: "Experiments", icon: "biotech" },
  { to: "/graph", label: "Graph", icon: "account_tree" },
  { to: "/feedback", label: "Feedback", icon: "rate_review" }
];

interface RouteHandle {
  title?: string;
  subtitle?: string;
  searchPlaceholder?: string;
  fullBleed?: boolean;
}

export function WorkbenchLayout() {
  const matches = useMatches();
  const current = [...matches].reverse().find((match) => Boolean(match.handle))?.handle as RouteHandle | undefined;
  const title = current?.title ?? "RAG Workbench";
  const subtitle = current?.subtitle ?? "Knowledge studio";
  const searchPlaceholder = current?.searchPlaceholder ?? "Search knowledge, documents, runs...";

  return (
    <div className="app-shell">
      <aside className="workbench-sidebar">
        <div className="workbench-brand">
          <h1 className="workbench-brand__title">RAG Workbench</h1>
          <div className="workbench-brand__meta">v2.4.0-stable</div>
        </div>
        <NavLink className="pipeline-button" to="/knowledge-base">
          <span className="material-symbols-outlined fill-icon">add</span>
          <span>New Pipeline</span>
        </NavLink>
        <nav className="workbench-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              className={({ isActive }) => `workbench-nav__link${isActive ? " is-active" : ""}`}
              key={item.to}
              to={item.to}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="workbench-nav__footer">
          <NavLink className={({ isActive }) => `workbench-nav__link${isActive ? " is-active" : ""}`} to="/settings">
            <span className="material-symbols-outlined">settings</span>
            <span>Settings</span>
          </NavLink>
          <div className="sidebar-user">
            <div className="avatar-dot">A</div>
            <div>
              <strong>Admin Dev</strong>
              <span>Standard Tier</span>
            </div>
          </div>
        </div>
      </aside>
      <div className="workbench-main">
        <header className="workbench-topbar">
          <div className="workbench-topbar__left">
            <span className="material-symbols-outlined topbar-mark">hub</span>
            <h2 className="workbench-title">{title}</h2>
            <span className="topbar-divider" />
            <span className="workbench-subtitle">{subtitle}</span>
          </div>
          <div className="workbench-topbar__right">
            <label className="topbar-search">
              <span className="material-symbols-outlined">search</span>
              <input placeholder={searchPlaceholder} />
            </label>
            <span className="system-health"><i /> System: Healthy</span>
            <button className="topbar-icon" type="button" aria-label="Notifications">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="topbar-icon" type="button" aria-label="Help">
              <span className="material-symbols-outlined">help_outline</span>
            </button>
          </div>
        </header>
        <main className={`workbench-content${current?.fullBleed ? " workbench-content--full" : ""}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
