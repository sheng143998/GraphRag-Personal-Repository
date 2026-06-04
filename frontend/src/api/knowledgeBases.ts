import type { KnowledgeBaseSummary } from "../types";
import { apiRequest } from "./client";

export function fetchKnowledgeBases(): Promise<KnowledgeBaseSummary[]> {
  return apiRequest<KnowledgeBaseSummary[]>("/knowledge-bases");
}

export function fetchKnowledgeBaseById(id: string): Promise<KnowledgeBaseSummary> {
  return apiRequest<KnowledgeBaseSummary>(`/knowledge-bases/${id}`);
}

export function updateKnowledgeBase(id: string, payload: Partial<KnowledgeBaseSummary>): Promise<KnowledgeBaseSummary> {
  return apiRequest<KnowledgeBaseSummary>(`/knowledge-bases/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteKnowledgeBase(id: string): Promise<void> {
  return apiRequest<void>(`/knowledge-bases/${id}`, { method: "DELETE" });
}