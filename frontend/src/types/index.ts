export type DocumentProcessStatus = "INDEXED" | "UPLOADED" | "PROCESSING" | "FAILED";

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
  knowledgeBaseId: string;
  knowledgeBaseName: string;
  title: string;
  documentType: string;
  fileName: string;
  fileType: string;
  mimeType?: string;
  sourceType?: string;
  sourcePath?: string;
  parserName?: string;
  parserVersion?: string;
  status: DocumentProcessStatus;
  summary?: string;
  metadata?: string;
  chunkCount?: number;
  chunks?: DocumentChunkRecord[];
  createdAt: string;
  updatedAt: string;
}

export interface DocumentChunkRecord {
  id: string;
  chunkIndex: number;
  title?: string;
  contentPreview: string;
  chunkStrategy?: string;
  pageNumber?: number;
  sheetName?: string;
  rowRange?: string;
  metadata?: string;
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
  title: string;
  documentType: string;
  fileName: string;
  fileType: string;
  mimeType?: string;
  sourceType?: string;
  sourcePath?: string;
  content?: string;
  file?: File;
  summary?: string;
  metadata?: Record<string, unknown>;
}

export interface UploadResponse {
  id: string;
  knowledgeBaseId: string;
  knowledgeBaseName: string;
  title: string;
  documentType: string;
  fileName: string;
  fileType: string;
  status: string;
  chunkCount?: number;
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
