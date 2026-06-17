import type { AppSettings } from "../types";
import { apiRequest } from "./client";

export function fetchSettings(): Promise<AppSettings> {
  return apiRequest<AppSettings>("/settings");
}
