import type {
  ChatMessageRecord,
  ChatMessageRequest,
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionRequest,
  CitationSource,
  AssistantTurnResponse
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

interface AgentCitationMetadata {
  documentId?: string | null;
  chunkId?: string | null;
  title?: string | null;
  sourcePath?: string | null;
  score?: number | null;
  rerankScore?: number | null;
  metadata?: Record<string, unknown> | null;
}

function mapAgentCitation(source: AgentCitationMetadata, index: number, strategy: string): CitationSource {
  const preview = source.metadata?.content_preview;
  const title = source.title || source.sourcePath || source.documentId || `source-${index + 1}`;
  return {
    id: source.chunkId || source.documentId || `agent-citation-${index + 1}`,
    title,
    location: source.sourcePath || source.chunkId || title,
    strategy,
    score: source.rerankScore ?? source.score ?? 0,
    snippet: typeof preview === "string" ? preview : title
  };
}

function parseAssistantCitations(value?: string | null, strategy = "agent"): CitationSource[] {
  if (!value) {
    return [];
  }
  try {
    const parsed = JSON.parse(value) as Array<string | AgentCitationMetadata>;
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.map((item, index) =>
      typeof item === "string" ? mapCitation(item, index, strategy) : mapAgentCitation(item, index, strategy)
    );
  } catch {
    return [mapCitation(value, 0, strategy)];
  }
}

export async function sendAssistantTurn(sessionId: string, payload: ChatRequest): Promise<ChatResponse> {
  const response = await apiRequest<AssistantTurnResponse>(`/chat/${sessionId}/assistant-turn`, {
    method: "POST",
    body: JSON.stringify({
      userInput: payload.question,
      strategyName: payload.strategy,
      topK: payload.topK ?? 5,
      metadataFilters: payload.metadataFilters,
    })
  });
  const strategy = response.selectedStrategyName ?? payload.strategy;

  return {
    traceId: response.trace?.traceId ?? response.assistantMessage.traceId ?? response.userMessage.traceId ?? "",
    answer: response.assistantMessage.content,
    sources: parseAssistantCitations(response.assistantMessage.citations, strategy),
    userMessage: response.userMessage,
    assistantMessage: response.assistantMessage,
    questionType: response.questionType,
    selectedStrategyName: response.selectedStrategyName,
    followUpQuestions: response.followUpQuestions,
    workflowSteps: response.workflowSteps
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
