export function formatScore(value?: number | null): string {
  if (value == null) return "待评估";
  return `${Math.round(value * 100)}%`;
}

export function formatDecimal(value?: number | null): string {
  if (value == null) return "-";
  return value.toFixed(3);
}

export function formatCost(value?: number | null): string {
  if (value == null) return "-";
  return `$${value.toFixed(value < 0.01 ? 6 : 4)}`;
}

export function formatDate(value?: string | null): string {
  if (!value) return "-";
  return value.replace("T", " ").slice(0, 16);
}

export function shortId(value?: string | null): string {
  if (!value) return "-";
  return value.slice(0, 8);
}

export function summarize(value?: string | null, maxLength = 88): string {
  if (!value) return "暂无内容";
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

export function scoreWidth(value?: number | null): string {
  if (value == null) return "0%";
  return `${Math.max(0, Math.min(100, Math.round(value * 100)))}%`;
}
