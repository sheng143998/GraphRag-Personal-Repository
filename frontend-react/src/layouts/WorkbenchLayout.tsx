import { NavLink, Outlet, useMatches } from "react-router-dom";

const navItems = [
  { to: "/chat", label: "支持问答", icon: "support_agent" },
  { to: "/knowledge-base", label: "知识库", icon: "database" },
  { to: "/documents", label: "文档入库", icon: "description" },
  { to: "/experiments", label: "评测实验", icon: "biotech" },
  { to: "/graph", label: "图谱事实", icon: "account_tree" },
  { to: "/feedback", label: "质检反馈", icon: "rate_review" }
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
  const title = current?.title ?? "售后知识库工作台";
  const subtitle = current?.subtitle ?? "企业售后技术支持知识库 Agent";
  const searchPlaceholder = current?.searchPlaceholder ?? "搜索知识库、文档、工单线索或评测记录";

  return (
    <div className="app-shell">
      <aside className="workbench-sidebar">
        <div className="workbench-brand">
          <h1 className="workbench-brand__title">售后知识库 Agent</h1>
          <div className="workbench-brand__meta">技术支持工作台</div>
        </div>
        <NavLink className="pipeline-button" to="/knowledge-base">
          <span className="material-symbols-outlined fill-icon">add</span>
          <span>新建知识库</span>
        </NavLink>
        <nav className="workbench-nav" aria-label="主导航">
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
            <span>系统设置</span>
          </NavLink>
          <div className="sidebar-user">
            <div className="avatar-dot">支</div>
            <div>
              <strong>支持工程师</strong>
              <span>本地联调环境</span>
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
            <span className="system-health"><i /> 接口链路正常</span>
            <button className="topbar-icon" type="button" aria-label="通知">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="topbar-icon" type="button" aria-label="帮助">
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
