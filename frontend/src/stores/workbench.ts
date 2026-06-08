import { computed, ref } from "vue";
import { defineStore } from "pinia";
import type {
  AppSettings,
  ChatResponse,
  ChatMessage,
  ChatMessageRecord,
  ChatSession,
  DocumentRecord,
  ExperimentRecord,
  ExperimentEvaluationRequest,
  ExperimentEvaluationSummary,
  ExperimentRequest,
  ExperimentUpdateRequest,
  FeedbackRecord,
  FeedbackRequest,
  CitationSource,
  KnowledgeBaseSummary,
  LearningWeakPointSummary,
  RagRunDetail,
  RagRunSummary,
  UploadPayload
} from "../types";
import {
  API_RUNTIME_SETTINGS_KEY,
  addChatMessage,
  createChatSession,
  createExperiment,
  evaluateExperiment,
  createFeedback,
  createKnowledgeBase,
  deleteDocument,
  deleteExperiment,
  deleteKnowledgeBase,
  fetchChatMessages,
  fetchChatSessions,
  fetchDocumentById,
  fetchDocuments,
  fetchExperimentEvaluationSummary,
  fetchExperimentById,
  fetchExperiments,
  fetchKnowledgeBaseById,
  fetchKnowledgeBases,
  fetchRagRuns,
  fetchRagRun,
  fetchSettings,
  fetchWeakPointSummary,
  fetchWeakPoints,
  practiceWeakPointTurn,
  sendAssistantTurn,
  updateWeakPoint,
  updateExperiment,
  updateKnowledgeBase,
  uploadDocuments
} from "../api";
import {
  mockDocuments,
  mockExperiments,
  mockExperimentEvaluationSummary,
  mockKnowledgeBases,
  mockMessages,
  mockSettings,
  ragStrategyOptions
} from "../utils/mock-data";

function loadPersistedSettings(): AppSettings {
  try {
    const raw = window.localStorage.getItem(API_RUNTIME_SETTINGS_KEY);
    if (!raw) {
      return mockSettings;
    }

    return {
      ...mockSettings,
      ...(JSON.parse(raw) as Partial<AppSettings>)
    };
  } catch {
    return mockSettings;
  }
}

function sortByUpdatedAt<T extends { updatedAt: string }>(items: T[]): T[] {
  return [...items].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function findLatestSources(messages: ChatMessage[]) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].sources?.length) {
      return messages[index].sources ?? [];
    }
  }
  return [];
}

function formatMessageTime(value: string): string {
  if (!value) {
    return new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  }

  if (!value.includes("T")) {
    return value;
  }

  return value.replace("T", " ").slice(11, 16);
}

function parseCitations(value?: string | null): CitationSource[] | undefined {
  if (!value) {
    return undefined;
  }

  try {
    const parsed = JSON.parse(value) as CitationSource[] | string[];
    if (!Array.isArray(parsed)) {
      return undefined;
    }

    return parsed.map((item, index) => {
      if (typeof item === "string") {
        return {
          id: `history-citation-${index + 1}`,
          title: item,
          location: item,
          strategy: "history",
          score: 0,
          snippet: item
        };
      }

      if ("id" in item && "location" in item && "snippet" in item) {
        return item;
      }

      const source = item as {
        documentId?: string | null;
        chunkId?: string | null;
        title?: string | null;
        sourcePath?: string | null;
        score?: number | null;
        rerankScore?: number | null;
        metadata?: Record<string, unknown> | null;
      };
      const preview = source.metadata?.content_preview;
      const title = source.title || source.sourcePath || source.documentId || `source-${index + 1}`;
      return {
        id: source.chunkId || source.documentId || `history-citation-${index + 1}`,
        title,
        location: source.sourcePath || source.chunkId || title,
        strategy: "agent-history",
        score: source.rerankScore ?? source.score ?? 0,
        snippet: typeof preview === "string" ? preview : title
      };
    });
  } catch {
    return [{
      id: "history-citation-1",
      title: value,
      location: value,
      strategy: "history",
      score: 0,
      snippet: value
    }];
  }
}

function mapHistoryMessages(records: ChatMessageRecord[]): ChatMessage[] {
  return records.map((record) => ({
    id: record.id,
    role: record.role === "assistant" ? "assistant" : "user",
    content: record.content,
    createdAt: formatMessageTime(record.createdAt),
    sources: parseCitations(record.citations)
  }));
}

export const useWorkbenchStore = defineStore("workbench", () => {
  // --- Core state ---
  const knowledgeBases = ref<KnowledgeBaseSummary[]>(mockKnowledgeBases);
  const documents = ref<DocumentRecord[]>(sortByUpdatedAt(mockDocuments));
  const experiments = ref<ExperimentRecord[]>(mockExperiments);
  const experimentEvaluationSummary = ref<ExperimentEvaluationSummary>(mockExperimentEvaluationSummary);
  const ragRuns = ref<RagRunSummary[]>([]);
  const ragRunDetails = ref<Record<string, RagRunDetail>>({});
  const messages = ref<ChatMessage[]>(mockMessages);
  const settings = ref<AppSettings>(loadPersistedSettings());
  const selectedStrategy = ref(ragStrategyOptions[0].value);
  const traceId = ref("trace-demo-20260525-181600");
  const followUpQuestions = ref<string[]>([]);
  const studyPlan = ref<ChatResponse["studyPlan"]>(null);
  const reviewCards = ref<NonNullable<ChatResponse["reviewCards"]>>([]);
  const weakPoints = ref<NonNullable<ChatResponse["weakPoints"]>>([]);
  const weakPointSummary = ref<LearningWeakPointSummary | null>(null);
  const pending = ref(false);
  const uploadPending = ref(false);
  const lastError = ref("");

  // --- Chat session state ---
  const chatSessions = ref<ChatSession[]>([]);
  const currentSessionId = ref("");
  const sessionMessages = ref<ChatMessageRecord[]>([]);
  const sessionsPending = ref(false);

  // --- Experiment form state ---
  const experimentFormPending = ref(false);

  // --- Feedback state ---
  const feedbackPending = ref(false);
  const lastFeedback = ref<FeedbackRecord | null>(null);

  const totalDocuments = computed(() => documents.value.length);
  const indexedDocuments = computed(() => documents.value.filter((item) => item.status === "INDEXED").length);
  const latestSources = computed(() => findLatestSources(messages.value));
  const selectedKnowledgeBase = computed(
    () => knowledgeBases.value.find((item) => item.id === settings.value.defaultKnowledgeBaseId) ?? knowledgeBases.value[0]
  );

  // --- Hydrate (partial-failure tolerant) ---
  async function hydrate(): Promise<void> {
    lastError.value = "";

    const results = await Promise.allSettled([
      fetchKnowledgeBases().then((data) => { knowledgeBases.value = data; }),
      fetchDocuments().then((data) => { documents.value = sortByUpdatedAt(data); }),
      fetchExperiments().then((data) => { experiments.value = data; }),
      fetchExperimentEvaluationSummary().then((data) => { experimentEvaluationSummary.value = data; }),
      fetchRagRuns().then((data) => { ragRuns.value = data; }),
      fetchSettings().then((data) => { settings.value = data; }),
    ]);

    const failedCount = results.filter((item) => item.status === "rejected").length;

    if (failedCount === results.length) {
      knowledgeBases.value = mockKnowledgeBases;
      documents.value = sortByUpdatedAt(mockDocuments);
      experiments.value = mockExperiments;
      experimentEvaluationSummary.value = mockExperimentEvaluationSummary;
      ragRuns.value = [];
      settings.value = mockSettings;
      lastError.value = "后端服务未就绪，当前使用本地示例数据展示。";
    } else if (failedCount > 0) {
      lastError.value = `部分数据加载失败（${failedCount}/${results.length}），已展示可用数据。`;
    }
  }

  // --- Chat: RAG query ---
  async function askQuestion(question: string): Promise<void> {
    if (!question.trim()) return;

    const knowledgeBaseId = selectedKnowledgeBase.value?.id || settings.value.defaultKnowledgeBaseId;
    if (!knowledgeBaseId) {
      lastError.value = "请先选择默认知识库，再发起 RAG 提问。";
      return;
    }

    pending.value = true;
    lastError.value = "";

    try {
      let sessionId = currentSessionId.value;
      if (!sessionId) {
        const session = await createChatSession({
          knowledgeBaseId,
          title: question.trim().slice(0, 60)
        });
        chatSessions.value.unshift(session);
        currentSessionId.value = session.id;
        sessionId = session.id;
      }

      const result = await sendAssistantTurn(sessionId, {
        question: question.trim(),
        strategy: selectedStrategy.value,
        knowledgeBaseId,
        sessionId,
      });

      traceId.value = result.traceId;
      selectedStrategy.value = result.selectedStrategyName || selectedStrategy.value;
      followUpQuestions.value = result.followUpQuestions ?? [];
      studyPlan.value = result.studyPlan ?? null;
      reviewCards.value = result.reviewCards ?? [];
      weakPoints.value = result.weakPoints ?? [];
      if (result.userMessage && result.assistantMessage) {
        messages.value.push(...mapHistoryMessages([result.userMessage, result.assistantMessage]));
      } else {
        messages.value.push({
          id: `msg-assistant-${Date.now()}`,
          role: "assistant",
          content: result.answer,
          createdAt: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
          sources: result.sources
        });
      }

      if (currentSessionId.value) {
        try {
          sessionMessages.value = await fetchChatMessages(currentSessionId.value);
          messages.value = mapHistoryMessages(sessionMessages.value);
          weakPoints.value = await fetchWeakPoints(currentSessionId.value);
          weakPointSummary.value = await fetchWeakPointSummary(currentSessionId.value);
        } catch {
          // Keep the optimistic thread visible if session history refresh is unavailable.
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "提问失败，请稍后重试。";
      lastError.value = message;
      followUpQuestions.value = [];
      studyPlan.value = null;
      reviewCards.value = [];
      weakPoints.value = [];
      weakPointSummary.value = null;
      messages.value.push({
        id: `msg-assistant-${Date.now()}`,
        role: "assistant",
        content: "暂时无法获取真实回答。你可以稍后重试，或先继续整理文档和检索策略。",
        createdAt: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
        sources: findLatestSources(messages.value)
      });
    } finally {
      pending.value = false;
    }
  }

  // --- Document status polling ---
  const pollingTimers = new Map<string, ReturnType<typeof setInterval>>();

  function pollDocumentStatus(documentId: string): void {
    const existing = pollingTimers.get(documentId);
    if (existing) clearInterval(existing);

    let attempts = 0;
    const maxAttempts = 30;
    const interval = 2000;

    const timer = setInterval(async () => {
      attempts++;
      try {
        const doc = await fetchDocumentById(documentId);
        if (doc.status === "INDEXED" || doc.status === "FAILED") {
          clearInterval(timer);
          pollingTimers.delete(documentId);
          documents.value = sortByUpdatedAt(await fetchDocuments());
        } else if (attempts >= maxAttempts) {
          clearInterval(timer);
          pollingTimers.delete(documentId);
          documents.value = sortByUpdatedAt(await fetchDocuments());
        } else {
          const idx = documents.value.findIndex((d) => d.id === documentId);
          if (idx >= 0) {
            documents.value[idx] = { ...doc };
          }
        }
      } catch {
        if (attempts >= maxAttempts) {
          clearInterval(timer);
          pollingTimers.delete(documentId);
        }
      }
    }, interval);

    pollingTimers.set(documentId, timer);
  }

  // --- Document upload ---
  async function submitUpload(payload: UploadPayload): Promise<void> {
    uploadPending.value = true;
    lastError.value = "";

    try {
      const result = await uploadDocuments(payload);
      traceId.value = `upload-${result.id}`;
      documents.value = sortByUpdatedAt(await fetchDocuments());
      pollDocumentStatus(result.id);
    } catch (error) {
      const message = error instanceof Error ? error.message : "上传失败，请稍后重试。";
      lastError.value = message;
    } finally {
      uploadPending.value = false;
    }
  }

  // --- Chat sessions ---
  async function createSession(knowledgeBaseId: string, title: string): Promise<void> {
    sessionsPending.value = true;
    lastError.value = "";
    try {
      const session = await createChatSession({ knowledgeBaseId, title });
      chatSessions.value.unshift(session);
      currentSessionId.value = session.id;
      sessionMessages.value = [];
      messages.value = [];
      weakPoints.value = [];
      weakPointSummary.value = null;
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "创建会话失败。";
    } finally {
      sessionsPending.value = false;
    }
  }

  async function loadSessions(): Promise<void> {
    sessionsPending.value = true;
    try {
      chatSessions.value = await fetchChatSessions();
    } catch {
      // 静默失败，会话列表为空
    } finally {
      sessionsPending.value = false;
    }
  }

  async function loadSessionMessages(sessionId: string): Promise<void> {
    lastError.value = "";
    try {
      sessionMessages.value = await fetchChatMessages(sessionId);
      currentSessionId.value = sessionId;
      messages.value = mapHistoryMessages(sessionMessages.value);
      weakPoints.value = await fetchWeakPoints(sessionId);
      weakPointSummary.value = await fetchWeakPointSummary(sessionId);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "加载消息失败。";
    }
  }

  async function assessWeakPoint(weakPointId: string, masteryStatus: string): Promise<void> {
    if (!currentSessionId.value) return;
    const updated = await updateWeakPoint(currentSessionId.value, weakPointId, masteryStatus);
    weakPoints.value = weakPoints.value.map((item) => (item.id === updated.id ? updated : item));
    weakPointSummary.value = await fetchWeakPointSummary(currentSessionId.value);
  }

  async function practiceWeakPoint(weakPointId: string): Promise<void> {
    if (!currentSessionId.value) return;
    pending.value = true;
    lastError.value = "";
    try {
      const result = await practiceWeakPointTurn(currentSessionId.value, weakPointId, {
        strategyName: selectedStrategy.value,
        topK: 5
      });
      traceId.value = result.traceId;
      selectedStrategy.value = result.selectedStrategyName || selectedStrategy.value;
      followUpQuestions.value = result.followUpQuestions ?? [];
      studyPlan.value = result.studyPlan ?? null;
      reviewCards.value = result.reviewCards ?? [];
      weakPoints.value = result.weakPoints ?? [];
      if (result.userMessage && result.assistantMessage) {
        messages.value.push(...mapHistoryMessages([result.userMessage, result.assistantMessage]));
      }
      sessionMessages.value = await fetchChatMessages(currentSessionId.value);
      messages.value = mapHistoryMessages(sessionMessages.value);
      weakPoints.value = await fetchWeakPoints(currentSessionId.value);
      weakPointSummary.value = await fetchWeakPointSummary(currentSessionId.value);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "Unable to start weak point practice.";
    } finally {
      pending.value = false;
    }
  }

  // --- Knowledge bases ---
  async function createKb(payload: {
    name: string;
    description?: string;
    ownerId?: string;
    defaultRagStrategy?: string;
  }): Promise<void> {
    lastError.value = "";
    try {
      const kb = await createKnowledgeBase(payload);
      knowledgeBases.value.unshift(kb);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "创建知识库失败。";
    }
  }

  async function updateKb(id: string, payload: Partial<KnowledgeBaseSummary>): Promise<void> {
    lastError.value = "";
    try {
      const updated = await updateKnowledgeBase(id, payload);
      const idx = knowledgeBases.value.findIndex((k) => k.id === id);
      if (idx >= 0) knowledgeBases.value[idx] = updated;
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "更新知识库失败。";
    }
  }

  async function deleteKb(id: string): Promise<void> {
    lastError.value = "";
    try {
      await deleteKnowledgeBase(id);
      knowledgeBases.value = knowledgeBases.value.filter((k) => k.id !== id);
      if (settings.value.defaultKnowledgeBaseId === id) {
        settings.value.defaultKnowledgeBaseId = knowledgeBases.value[0]?.id ?? "";
      }
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "删除知识库失败。";
    }
  }

  async function loadKbDetail(id: string): Promise<KnowledgeBaseSummary | null> {
    lastError.value = "";
    try {
      const kb = await fetchKnowledgeBaseById(id);
      const idx = knowledgeBases.value.findIndex((item) => item.id === id);
      if (idx >= 0) {
        knowledgeBases.value[idx] = kb;
      }
      return kb;
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "加载知识库详情失败。";
      return null;
    }
  }

  // --- Documents ---
  async function removeDocument(id: string): Promise<void> {
    lastError.value = "";
    try {
      await deleteDocument(id);
      documents.value = documents.value.filter((d) => d.id !== id);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "删除文档失败。";
    }
  }

  async function loadDocumentDetail(id: string): Promise<DocumentRecord | null> {
    lastError.value = "";
    try {
      return await fetchDocumentById(id);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "加载文档详情失败。";
      return null;
    }
  }

  // --- Experiments ---
  async function createExp(payload: ExperimentRequest): Promise<void> {
    experimentFormPending.value = true;
    lastError.value = "";
    try {
      const exp = await createExperiment(payload);
      experiments.value.unshift(exp);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "创建实验失败。";
    } finally {
      experimentFormPending.value = false;
    }
  }

  async function updateExp(id: string, payload: ExperimentUpdateRequest): Promise<void> {
    experimentFormPending.value = true;
    lastError.value = "";
    try {
      const updated = await updateExperiment(id, payload);
      const idx = experiments.value.findIndex((e) => e.id === id);
      if (idx >= 0) experiments.value[idx] = updated;
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "更新实验失败。";
    } finally {
      experimentFormPending.value = false;
    }
  }

  async function deleteExp(id: string): Promise<void> {
    lastError.value = "";
    try {
      await deleteExperiment(id);
      experiments.value = experiments.value.filter((e) => e.id !== id);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "删除实验失败。";
    }
  }

  async function loadExpDetail(id: string): Promise<ExperimentRecord | null> {
    lastError.value = "";
    try {
      return await fetchExperimentById(id);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "加载实验详情失败。";
      return null;
    }
  }

  async function loadExperimentEvaluationSummary(limit = 20): Promise<void> {
    lastError.value = "";
    try {
      experimentEvaluationSummary.value = await fetchExperimentEvaluationSummary(limit);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "Unable to load experiment evaluation summary.";
    }
  }

  async function loadRagRuns(limit = 20): Promise<void> {
    lastError.value = "";
    try {
      ragRuns.value = await fetchRagRuns(limit);
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "Unable to load RAG runs.";
    }
  }

  async function loadRagRunDetail(id: string): Promise<RagRunDetail | null> {
    lastError.value = "";
    try {
      const detail = await fetchRagRun(id);
      ragRunDetails.value = {
        ...ragRunDetails.value,
        [id]: detail
      };
      return detail;
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "Unable to load RAG run detail.";
      return null;
    }
  }

  async function evaluateExp(id: string, payload: ExperimentEvaluationRequest): Promise<void>;
  async function evaluateExp(id: string, runId: string, expectedAnswer?: string): Promise<void>;
  async function evaluateExp(
    id: string,
    runOrPayload: string | ExperimentEvaluationRequest,
    expectedAnswer?: string
  ): Promise<void> {
    experimentFormPending.value = true;
    lastError.value = "";
    try {
      const payload = typeof runOrPayload === "string"
        ? {
            runId: runOrPayload,
            expectedAnswer: expectedAnswer?.trim() || undefined
          }
        : {
            ...runOrPayload,
            expectedAnswer: runOrPayload.expectedAnswer?.trim() || undefined
          };
      const result = await evaluateExperiment(id, payload);
      const idx = experiments.value.findIndex((item) => item.id === id);
      if (idx >= 0) {
        experiments.value[idx] = result.experiment;
      }
      await loadExperimentEvaluationSummary();
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "Unable to evaluate experiment.";
    } finally {
      experimentFormPending.value = false;
    }
  }

  // --- Feedback ---
  async function submitFeedback(payload: FeedbackRequest): Promise<FeedbackRecord | null> {
    feedbackPending.value = true;
    lastError.value = "";
    try {
      const record = await createFeedback(payload);
      lastFeedback.value = record;
      return record;
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "提交反馈失败。";
      return null;
    } finally {
      feedbackPending.value = false;
    }
  }

  return {
    // state
    documents,
    experiments,
    experimentEvaluationSummary,
    ragRunDetails,
    ragRuns,
    indexedDocuments,
    knowledgeBases,
    lastError,
    latestSources,
    messages,
    pending,
    ragStrategyOptions,
    selectedKnowledgeBase,
    selectedStrategy,
    settings,
    totalDocuments,
    traceId,
    uploadPending,
    // chat sessions
    chatSessions,
    currentSessionId,
    sessionMessages,
    sessionsPending,
    // experiments form
    experimentFormPending,
    // feedback
    feedbackPending,
    followUpQuestions,
    studyPlan,
    reviewCards,
    weakPoints,
    weakPointSummary,
    lastFeedback,
    // actions
    askQuestion,
    assessWeakPoint,
    practiceWeakPoint,
    hydrate,
    submitUpload,
    // sessions
    createSession,
    loadSessions,
    loadSessionMessages,
    // knowledge bases
    createKb,
    updateKb,
    deleteKb,
    loadKbDetail,
    // documents
    pollDocumentStatus,
    removeDocument,
    loadDocumentDetail,
    // experiments
    createExp,
    updateExp,
    deleteExp,
    loadExpDetail,
    loadRagRuns,
    loadRagRunDetail,
    loadExperimentEvaluationSummary,
    evaluateExp,
    // feedback
    submitFeedback,
  };
});
