import type { KnowledgeBaseSummary } from "../types";
import { apiRequest } from "./client";

export function fetchKnowledgeBases(): Promise<KnowledgeBaseSummary[]> {
  return apiRequest<KnowledgeBaseSummary[]>("/knowledge-bases");
}
