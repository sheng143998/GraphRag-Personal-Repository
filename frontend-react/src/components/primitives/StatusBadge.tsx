import "./primitives.css";

interface StatusBadgeProps {
  status?: string | null;
}

function getTone(status?: string | null) {
  const value = (status ?? "").toUpperCase();
  if (["INDEXED", "COMPLETED", "SUCCESS", "ACTIVE"].includes(value)) return "success";
  if (["PROCESSING", "RUNNING", "UPLOADED", "PENDING"].includes(value)) return "warning";
  if (["FAILED", "ERROR", "ARCHIVED"].includes(value)) return "error";
  return "muted";
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const text = status || "UNKNOWN";
  const tone = getTone(status);
  return (
    <span className={`status-badge status-badge--${tone}`}>
      <span className="status-badge__dot" />
      {text}
    </span>
  );
}
