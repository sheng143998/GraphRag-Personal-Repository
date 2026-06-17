import type { RagQueryApiRequest, RagQueryApiResponse, RagRunDetail, RagRunSummary } from "../types";
import { apiRequest } from "./client";

const RAG_QUERY_TIMEOUT_MS = 180000;

export function runRagQuery(payload: RagQueryApiRequest, traceId?: string): Promise<RagQueryApiResponse> {
  return apiRequest<RagQueryApiResponse>("/rag/query", {
    method: "POST",
    timeoutMs: RAG_QUERY_TIMEOUT_MS,
    traceId,
    body: JSON.stringify(payload)
  });
}

export function fetchRagRuns(limit = 20): Promise<RagRunSummary[]> {
  return apiRequest<RagRunSummary[]>(`/rag/runs?limit=${limit}`);
}

export function fetchRagRun(id: string): Promise<RagRunDetail> {
  return apiRequest<RagRunDetail>(`/rag/runs/${id}`);
}
