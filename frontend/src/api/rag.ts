import type { RagRunDetail } from "../types";
import { apiRequest } from "./client";

export function fetchRagRun(id: string): Promise<RagRunDetail> {
  return apiRequest<RagRunDetail>(`/rag/runs/${id}`);
}
