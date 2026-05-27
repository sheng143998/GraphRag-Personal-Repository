export type DocumentProcessStatus = "indexed" | "processing" | "failed";

export interface NavigationItem {
  label: string;
  to: string;
  description: string;
}

export interface KnowledgeBaseSummary {
  id: string;
  name: string;
  description: string;
  documentCount: number;
  chunkCount: number;
  updatedAt: string;
}

export interface DocumentRecord {
  id: string;
  name: string;
  documentType: string;
  fileType: string;
  knowledgeBaseName: string;
  status: DocumentProcessStatus;
  updatedAt: string;
}

export interface CitationSource {
  id: string;
  title: string;
  location: string;
  strategy: string;
  score: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  sources?: CitationSource[];
}

export interface RagStrategyOption {
  value: string;
  label: string;
  description: string;
}

export interface RagSessionSummary {
  selectedStrategy: string;
  traceId: string;
  answerStatus: "ready" | "retrieving" | "idle";
}

export interface ChatRequest {
  sessionId?: string;
  question: string;
  strategy: string;
}

export interface ChatResponse {
  traceId: string;
  answer: string;
  sources: CitationSource[];
}

export interface UploadPayload {
  knowledgeBaseId: string;
  documentType: string;
  notes: string;
  fileNames: string[];
}

export interface UploadResponse {
  accepted: number;
  traceId: string;
}

export interface ExperimentRecord {
  id: string;
  name: string;
  strategy: string;
  precision: string;
  recall: string;
  updatedAt: string;
}

export interface AppSettings {
  apiBaseUrl: string;
  defaultKnowledgeBaseId: string;
  timeoutMs: number;
  includeTraceHeader: boolean;
}

export interface ApiEnvelope<T> {
  data: T;
  traceId?: string;
  message?: string;
}
