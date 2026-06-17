export function formatDateTime(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function formatNumber(value?: number | null): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "0";
  return new Intl.NumberFormat("zh-CN").format(value);
}
