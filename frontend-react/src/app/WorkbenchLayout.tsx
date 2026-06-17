import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/chat", label: "Chat", icon: "chat" },
  { to: "/knowledge-base", label: "Knowledge Base", icon: "database" },
  { to: "/documents", label: "Documents", icon: "description" },
  { to: "/experiments", label: "Experiments", icon: "science" },
  { to: "/graph", label: "Graph", icon: "account_tree" },
  { to: "/feedback", label: "Feedback", icon: "rate_review" },
  { to: "/settings", label: "Settings", icon: "settings" }
];

export function WorkbenchLayout(): JSX.Element {
  return (
    <div className="workbench-shell">
      <aside className="side-nav">
        <div className="brand-block">
          <strong>Workbench</strong>
          <span>React rebuild</span>
        </div>
        <nav>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `side-nav-link${isActive ? " is-active" : ""}`}
            >
              <span className="material-symbols">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="workbench-main">
        <header className="top-bar">
          <div>
            <strong>RAG Workbench</strong>
            <span>Experiment Explorer</span>
          </div>
          <NavLink className="comparison-link" to="/experiments/comparison">
            策略对比
          </NavLink>
        </header>
        <main className="content-scroll">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
