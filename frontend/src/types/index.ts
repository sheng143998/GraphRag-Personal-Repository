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
  knowledgeBaseId?: string;
  sessionId?: string;
  messageId?: string;
  question: string;
  strategy: string;
  retrieverType?: string;
  metadataFilters?: Record<string, unknown>;
  topK?: number;
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
  knowledgeBaseId?: string;
  name: string;
  description?: string;
  strategy: string;
  datasetName?: string;
  sampleCount?: number;
  precisionScore?: number;
  recallScore?: number;
  precision?: string;
  recall?: string;
  status?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AppSettings {
  apiBaseUrl: string;
  aiServiceBaseUrl: string;
  defaultKnowledgeBaseId: string;
  timeoutMs: number;
  includeTraceHeader: boolean;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error?: { code: string; message: string } | null;
  traceId?: string;
}

// --- Chat Session Types ---

export interface ChatSession {
  id: string;
  knowledgeBaseId: string;
  title: string;
  sessionStatus: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatSessionRequest {
  knowledgeBaseId: string;
  title: string;
}

export interface ChatMessageRecord {
  id: string;
  sessionId: string;
  role: string;
  content: string;
  citations?: string | null;
  traceId?: string;
  createdAt: string;
}

export interface ChatMessageRequest {
  role: string;
  content: string;
  citations?: string;
}

// --- Feedback Types ---

export interface FeedbackRecord {
  id: string;
  runId: string;
  sessionId: string;
  messageId: string;
  rating: number;
  feedbackType: string;
  comment?: string;
  createdAt: string;
}

export interface FeedbackRequest {
  runId: string;
  sessionId: string;
  messageId: string;
  rating: number;
  feedbackType: string;
  comment?: string;
}

// --- RAG Run Detail Types ---

export interface RetrievalResult {
  id: string;
  chunkId: string;
  documentId: string;
  rank: number;
  score: number;
  rerankScore?: number | null;
  retrieverType: string;
  source: string;
  metadata: Record<string, unknown>;
  selectedForContext: boolean;
}

export interface RagRunDetail {
  id: string;
  traceId: string;
  sessionId: string;
  messageId: string;
  knowledgeBaseId: string;
  question: string;
  rewrittenQuery?: string | null;
  strategyName: string;
  retrieverType: string;
  finalContext: string;
  answer: string;
  modelName: string;
  promptName: string;
  promptVersion: string;
  latencyMs: number;
  status: string;
  errorMessage?: string | null;
  createdAt: string;
  retrievalResults: RetrievalResult[];
}

// --- Graph Facts Types ---

export interface GraphEntityFact {
  id: string;
  documentId?: string | null;
  chunkId?: string | null;
  name: string;
  normalizedName: string;
  entityType: string;
  aliases: unknown;
  metadata: Record<string, unknown>;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface GraphRelationshipFact {
  id: string;
  documentId?: string | null;
  chunkId?: string | null;
  sourceEntityId?: string | null;
  targetEntityId?: string | null;
  sourceName: string;
  targetName: string;
  relationType: string;
  confidence: number;
  metadata: Record<string, unknown>;
  createdAt?: string | null;
}

export interface GraphFactsResponse {
  knowledgeBaseId: string;
  entity?: string | null;
  entityCount: number;
  relationshipCount: number;
  entities: GraphEntityFact[];
  relationships: GraphRelationshipFact[];
}

// --- Experiment Request Types ---

export interface ExperimentRequest {
  knowledgeBaseId?: string;
  name: string;
  description?: string;
  strategy: string;
  datasetName?: string;
  sampleCount?: number;
  precisionScore?: number;
  recallScore?: number;
  status?: string;
  notes?: string;
}

export type ExperimentUpdateRequest = Partial<ExperimentRequest>;

// --- Health ---

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
}
