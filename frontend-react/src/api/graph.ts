import type { GraphFactsResponse } from "../types";
import { apiRequest } from "./client";

export function fetchGraphFacts(knowledgeBaseId: string, entity?: string): Promise<GraphFactsResponse> {
  const params = new URLSearchParams({ knowledgeBaseId });
  if (entity && entity.trim().length > 0) {
    params.set("entity", entity.trim());
  }

  return apiRequest<GraphFactsResponse>(`/graph/facts?${params.toString()}`);
}
