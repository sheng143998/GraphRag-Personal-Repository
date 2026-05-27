import type { ExperimentRecord } from "../types";
import { apiRequest } from "./client";

export function fetchExperiments(): Promise<ExperimentRecord[]> {
  return apiRequest<ExperimentRecord[]>("/rag/experiments");
}
