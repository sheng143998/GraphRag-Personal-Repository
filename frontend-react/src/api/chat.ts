import type {
  ChatMessageRecord,
  ChatMessageRequest,
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionRequest,
  CitationSource,
  AssistantTurnResponse,
  LearningWeakPoint,
  LearningWeakPointSummary,
  WeakPointPracticeTurn
} from "../types";
import { apiRequest } from "./client";

const CHAT_TIMEOUT_MS = 180000;

// --- Chat Session API ---

export function createChatSession(payload: ChatSessionRequest, traceId?: string): Promise<ChatSession> {
  return apiRequest<ChatSession>("/chat/sessions", {
    method: "POST",
    traceId,
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

export function fetchChatMessages(sessionId: string, traceId?: string): Promise<ChatMessageRecord[]> {
  return apiRequest<ChatMessageRecord[]>(`/chat/${sessionId}/messages`, { traceId });
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

export async function sendAssistantTurn(sessionId: string, payload: ChatRequest, traceId?: string): Promise<ChatResponse> {
  const response = await apiRequest<AssistantTurnResponse>(`/chat/${sessionId}/assistant-turn`, {
    method: "POST",
    timeoutMs: CHAT_TIMEOUT_MS,
    traceId,
    body: JSON.stringify({
      userInput: payload.question,
      strategyName: payload.strategy,
      topK: payload.topK ?? 5,
      metadataFilters: payload.metadataFilters,
      retrievalOptions: payload.retrievalOptions,
    })
  });
  return mapAssistantTurnResponse(response, payload.strategy);
}

function mapAssistantTurnResponse(response: AssistantTurnResponse, fallbackStrategy: string): ChatResponse {
  const strategy = response.selectedStrategyName ?? fallbackStrategy;
  const traceId =
    response.trace?.traceId ??
    response.trace?.trace_id ??
    response.ragTrace?.traceId ??
    response.ragTrace?.trace_id ??
    response.assistantMessage.traceId ??
    response.userMessage.traceId ??
    "";
  return {
    traceId,
    answer: response.assistantMessage.content,
    sources: parseAssistantCitations(response.assistantMessage.citations, strategy),
    userMessage: response.userMessage,
    assistantMessage: response.assistantMessage,
    questionType: response.questionType,
    selectedStrategyName: response.selectedStrategyName,
    followUpQuestions: response.followUpQuestions,
    studyPlan: response.studyPlan,
    reviewCards: response.reviewCards,
    weakPoints: response.weakPoints,
    workflowSteps: response.workflowSteps
  };
}

export function fetchWeakPoints(sessionId: string, traceId?: string): Promise<LearningWeakPoint[]> {
  return apiRequest<LearningWeakPoint[]>(`/chat/${sessionId}/weak-points`, { traceId });
}

export function fetchWeakPointSummary(sessionId: string, traceId?: string): Promise<LearningWeakPointSummary> {
  return apiRequest<LearningWeakPointSummary>(`/chat/${sessionId}/weak-points/summary`, { traceId });
}

export async function practiceWeakPointTurn(
  sessionId: string,
  weakPointId: string,
  payload: { strategyName?: string; topK?: number; userAnswer?: string | null },
  traceId?: string
): Promise<WeakPointPracticeTurn> {
  return apiRequest<WeakPointPracticeTurn>(`/chat/${sessionId}/weak-points/${weakPointId}/practice-turn`, {
    method: "POST",
    timeoutMs: CHAT_TIMEOUT_MS,
    traceId,
    body: JSON.stringify(payload),
  });
}

export function updateWeakPoint(
  sessionId: string,
  weakPointId: string,
  masteryStatus: string,
  traceId?: string
): Promise<LearningWeakPoint> {
  return apiRequest<LearningWeakPoint>(`/chat/${sessionId}/weak-points/${weakPointId}`, {
    method: "PATCH",
    traceId,
    body: JSON.stringify({ masteryStatus }),
  });
}

export async function sendChatMessage(payload: ChatRequest, traceId?: string): Promise<ChatResponse> {
  const response = await apiRequest<RagQueryApiResponse>("/rag/query", {
    method: "POST",
    timeoutMs: CHAT_TIMEOUT_MS,
    traceId,
    body: JSON.stringify({
      knowledgeBaseId: payload.knowledgeBaseId,
      sessionId: payload.sessionId,
      messageId: payload.messageId,
      question: payload.question,
      strategyName: payload.strategy,
      retrieverType: payload.retrieverType ?? "hybrid",
      metadataFilters: payload.metadataFilters,
      retrievalOptions: payload.retrievalOptions,
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
