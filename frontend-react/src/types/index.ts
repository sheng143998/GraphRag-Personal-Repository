export type DocumentProcessStatus = "INDEXED" | "UPLOADED" | "PROCESSING" | "FAILED";

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error?: { code: string; message: string } | null;
  traceId?: string;
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

export interface BatchUploadFileItem {
  file: File;
  relativePath?: string;
}

export interface BatchUploadPayload {
  knowledgeBaseId: string;
  title?: string;
  documentType: string;
  sourceType?: string;
  files: BatchUploadFileItem[];
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
  status: DocumentProcessStatus | string;
  chunkCount?: number;
}

export interface BatchUploadResponse {
  batchId: string;
  acceptedCount: number;
  documents: UploadResponse[];
}

export interface CitationSource {
  id: string;
  title: string;
  location: string;
  strategy: string;
  score: number;
  snippet: string;
}

export interface ChatRequest {
  knowledgeBaseId?: string;
  sessionId?: string;
  messageId?: string;
  question: string;
  strategy: string;
  retrieverType?: string;
  metadataFilters?: Record<string, unknown>;
  retrievalOptions?: Record<string, unknown>;
  topK?: number;
}

export interface ChatResponse {
  traceId: string;
  answer: string;
  sources: CitationSource[];
  userMessage?: ChatMessageRecord;
  assistantMessage?: ChatMessageRecord;
  questionType?: string;
  selectedStrategyName?: string;
  followUpQuestions?: string[];
  studyPlan?: StudyPlan | null;
  reviewCards?: ReviewCard[];
  weakPoints?: LearningWeakPoint[];
  workflowSteps?: AgentWorkflowStep[];
}

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

export interface StudyPlan {
  summary: string;
  focusAreas: string[];
  steps: string[];
}

export interface ReviewCard {
  question: string;
  expectedAnswer: string;
  sourceHint: string;
  difficulty: string;
}

export interface AgentWorkflowStep {
  name: string;
  detail?: string;
  payload?: Record<string, unknown>;
}

export interface AssistantTurnResponse {
  userMessage: ChatMessageRecord;
  assistantMessage: ChatMessageRecord;
  agentName: string;
  questionType: string;
  selectedStrategyName: string;
  followUpQuestions: string[];
  studyPlan?: StudyPlan | null;
  reviewCards: ReviewCard[];
  weakPoints: LearningWeakPoint[];
  workflowSteps: AgentWorkflowStep[];
  trace?: { traceId?: string; trace_id?: string; attributes?: Record<string, unknown> } | null;
  ragTrace?: { traceId?: string; trace_id?: string; attributes?: Record<string, unknown>; steps?: Record<string, unknown>[] } | null;
}

export interface LearningWeakPoint {
  id: string;
  sessionId: string;
  knowledgeBaseId?: string | null;
  evidenceMessageId?: string | null;
  topic: string;
  expectedAnswer?: string | null;
  sourceHint?: string | null;
  difficulty: string;
  masteryStatus: string;
  reviewCount: number;
  lastSeenAt: string;
  lastAssessedAt?: string | null;
  practiceCount?: number | null;
  lastPracticeScore?: number | null;
  nextReviewAt?: string | null;
  createdAt: string;
}

export interface LearningWeakPointSummary {
  totalCount: number;
  needsReviewCount: number;
  masteredCount: number;
  hardCount: number;
  totalReviewCount: number;
  dueReviewCount?: number;
  completionRate: number;
  nextWeakPoint?: LearningWeakPoint | null;
}

export interface WeakPointPracticeAssessment {
  score: number;
  passed: boolean;
  masteryStatus: string;
  difficulty: string;
  feedback: string;
}

export interface AssistantTurnPracticeSummary {
  weakPoint: LearningWeakPoint;
  updatedWeakPoint?: LearningWeakPoint | null;
  assessment?: WeakPointPracticeAssessment | null;
  summary?: LearningWeakPointSummary | null;
  turn: AssistantTurnResponse;
}

export type WeakPointPracticeTurn = AssistantTurnPracticeSummary;

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

export interface RagRunSummary {
  id: string;
  traceId: string;
  sessionId?: string | null;
  messageId?: string | null;
  knowledgeBaseId?: string | null;
  question: string;
  strategyName: string;
  retrieverType: string;
  modelName?: string | null;
  latencyMs?: number | null;
  status: string;
  createdAt: string;
}

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
  traceAttributes?: Record<string, unknown>;
  traceSteps?: Record<string, unknown>[];
  createdAt: string;
  retrievalResults: RetrievalResult[];
}

export interface RagQueryApiRequest {
  knowledgeBaseId: string;
  sessionId?: string | null;
  messageId?: string | null;
  question: string;
  strategyName?: string;
  retrieverType?: string;
  metadataFilters?: Record<string, unknown>;
  retrievalOptions?: Record<string, unknown>;
  topK?: number;
}

export interface RagQueryApiResponse {
  runId: string;
  traceId: string;
  status: string;
  answer: string;
  citations: string[];
  strategyName?: string;
  retrieverType?: string;
}

export interface AppSettings {
  apiBaseUrl: string;
  aiServiceBaseUrl: string;
  defaultKnowledgeBaseId: string;
  timeoutMs: number;
  includeTraceHeader: boolean;
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
  status?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  evaluations?: ExperimentEvaluationHistory[];
}

export interface ExperimentRequest {
  knowledgeBaseId?: string;
  name: string;
  description?: string;
  strategy: string;
  datasetName?: string;
  sampleCount?: number;
  status?: string;
  notes?: string;
}

export interface ExperimentEvaluationHistory {
  id: string;
  experimentId: string;
  experimentName?: string | null;
  runId: string;
  runQuestion?: string | null;
  runStrategyName?: string | null;
  runRetrieverType?: string | null;
  runModelName?: string | null;
  runLatencyMs?: number | null;
  runCreatedAt?: string | null;
  groundedScore?: number | null;
  retrievalScore?: number | null;
  recallAtK?: number | null;
  precisionAtK?: number | null;
  chunkRecallAtK?: number | null;
  documentRecallAtK?: number | null;
  evidenceRecallAtK?: number | null;
  mrr?: number | null;
  citationHit?: number | null;
  graphEntityCoverage?: number | null;
  graphRelationshipHit?: number | null;
  graphExpansionTermHit?: number | null;
  latencyMs?: number | null;
  totalTokens?: number | null;
  estimatedCost?: number | null;
  embeddingLatencyMs?: number | null;
  retrievalLatencyMs?: number | null;
  rerankLatencyMs?: number | null;
  llmLatencyMs?: number | null;
  expectedAnswer?: string | null;
  generatedAnswer?: string | null;
  notes?: string | null;
  createdAt: string;
}

export interface ExperimentEvaluationSummary {
  evaluationCount: number;
  averageGrounded?: number | null;
  averageRetrieval?: number | null;
  bestExperimentId?: string | null;
  bestExperimentName?: string | null;
  recentEvaluations: ExperimentEvaluationHistory[];
}

export interface EvaluationCaseRecord {
  id: string;
  experimentId: string;
  experimentName?: string | null;
  caseId: string;
  question: string;
  expectedAnswer?: string | null;
  requiredChunkIds: string[];
  supportingChunkIds: string[];
  acceptableChunkIds: string[];
  citationChunkIds: string[];
  relevantChunkIds: string[];
  relevantDocumentIds: string[];
  expectedCitationChunkIds: string[];
  evaluationTopK: number;
  notes?: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface ImportEvaluationCaseItem {
  caseId: string;
  question: string;
  expectedAnswer?: string;
  requiredChunkIds?: string[];
  supportingChunkIds?: string[];
  acceptableChunkIds?: string[];
  citationChunkIds?: string[];
  relevantChunkIds?: string[];
  relevantDocumentIds?: string[];
  expectedCitationChunkIds?: string[];
  evaluationTopK?: number;
  notes?: string;
  status?: string;
}

export interface ImportEvaluationCasesPayload {
  experimentId: string;
  items: ImportEvaluationCaseItem[];
}

export interface ImportEvaluationCasesResponse {
  experimentId: string;
  createdCount: number;
  updatedCount: number;
  failedCount: number;
  items: Array<{ caseId: string; status: string; errorMessage?: string | null }>;
}

export interface RunEvaluationCasesBatchRequest {
  experimentId: string;
  caseIds?: string[];
  strategyName?: string;
  retrieverType?: string;
  topK?: number;
  metadataFilters?: Record<string, unknown>;
  retrievalOptions?: Record<string, unknown>;
}

export interface RunEvaluationCasesBatchItem {
  caseId: string;
  caseKey: string;
  runId?: string | null;
  evaluationId?: string | null;
  groundedScore?: number | null;
  retrievalScore?: number | null;
  recallAtK?: number | null;
  precisionAtK?: number | null;
  chunkRecallAtK?: number | null;
  documentRecallAtK?: number | null;
  evidenceRecallAtK?: number | null;
  mrr?: number | null;
  citationHit?: number | null;
  status: string;
  errorMessage?: string | null;
}

export interface RunEvaluationCasesBatchResponse {
  experimentId: string;
  strategyName?: string | null;
  requestedCount: number;
  completedCount: number;
  failedCount: number;
  items: RunEvaluationCasesBatchItem[];
}
