import type { RagRunDetail, RagRunSummary } from "../types";
import { apiRequest } from "./client";

export function fetchRagRuns(limit = 20): Promise<RagRunSummary[]> {
  return apiRequest<RagRunSummary[]>(`/rag/runs?limit=${limit}`);
}

export function fetchRagRun(id: string): Promise<RagRunDetail> {
  return apiRequest<RagRunDetail>(`/rag/runs/${id}`);
}
