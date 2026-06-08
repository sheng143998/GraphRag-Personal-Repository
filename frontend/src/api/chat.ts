import type {
  ChatMessageRecord,
  ChatMessageRequest,
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionRequest,
  CitationSource
} from "../types";
import { apiRequest } from "./client";

// --- Chat Session API ---

export function createChatSession(payload: ChatSessionRequest): Promise<ChatSession> {
  return apiRequest<ChatSession>("/chat/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchChatSessions(): Promise<ChatSession[]> {
  return apiRequest<ChatSession[]>("/chat/sessions");
}

// --- Chat Message API ---

export function addChatMessage(sessionId: string, payload: ChatMessageRequest): Promise<ChatMessageRecord> {
  return apiRequest<ChatMessageRecord>(`/chat/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchChatMessages(sessionId: string): Promise<ChatMessageRecord[]> {
  return apiRequest<ChatMessageRecord[]>(`/chat/${sessionId}/messages`);
}

// --- RAG Query (legacy chat flow) ---

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
      knowledgeBaseId: payload.knowledgeBaseId,
      sessionId: payload.sessionId,
      messageId: payload.messageId,
      question: payload.question,
      strategyName: payload.strategy,
      retrieverType: payload.retrieverType ?? "hybrid",
      metadataFilters: payload.metadataFilters,
      topK: payload.topK ?? 5
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
