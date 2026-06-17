import type { ButtonHTMLAttributes, ReactNode } from "react";
import "./primitives.css";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: ReactNode;
  variant?: ButtonVariant;
}

export function Button({ children, className = "", icon, variant = "secondary", ...props }: ButtonProps) {
  return (
    <button className={`ui-button ui-button--${variant} ${className}`.trim()} type="button" {...props}>
      {icon}
      {children ? <span>{children}</span> : null}
    </button>
  );
}
