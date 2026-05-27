import type { ChatRequest, ChatResponse, CitationSource } from "../types";
import { apiRequest } from "./client";

interface RagQueryApiResponse {
  runId: string;
  traceId: string;
  status: string;
  answer: string;
  citations: string[];
  strategyName?: string;
  retrieverType?: string;
}

function mapCitation(source: string, index: number, strategy: string): CitationSource {
  return {
    id: `citation-${index + 1}`,
    title: source,
    location: source,
    strategy,
    score: 0,
    snippet: source
  };
}

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const response = await apiRequest<RagQueryApiResponse>("/rag/query", {
    method: "POST",
    body: JSON.stringify({
      question: payload.question,
      strategyName: payload.strategy,
      retrieverType: "hybrid"
    })
  });

  return {
    traceId: response.traceId,
    answer: response.answer,
    sources: (response.citations ?? []).map((item, index) =>
      mapCitation(item, index, response.strategyName ?? payload.strategy)
    )
  };
}
