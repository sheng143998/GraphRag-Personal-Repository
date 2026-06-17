import type { HTMLAttributes, ReactNode } from "react";
import "./primitives.css";

interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
}

export function Panel({ action, children, className = "", eyebrow, title, ...props }: PanelProps) {
  return (
    <section className={`ui-panel ${className}`.trim()} {...props}>
      {(title || eyebrow || action) && (
        <header className="ui-panel__header">
          <div>
            {eyebrow ? <div className="ui-panel__eyebrow">{eyebrow}</div> : null}
            {title ? <h3>{title}</h3> : null}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}
