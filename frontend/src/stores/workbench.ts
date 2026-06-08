import { computed, ref } from "vue";
import { defineStore } from "pinia";
import type {
  AppSettings,
  ChatMessage,
  ChatMessageRecord,
  ChatSession,
  DocumentRecord,
  ExperimentRecord,
  ExperimentRequest,
  ExperimentUpdateRequest,
  FeedbackRecord,
  FeedbackRequest,
  KnowledgeBaseSummary,
  UploadPayload
} from "../types";
import {
  addChatMessage,
  createChatSession,
  createExperiment,
  createFeedback,
  createKnowledgeBase,
  deleteDocument,
  deleteExperiment,
  deleteKnowledgeBase,
  fetchChatMessages,
  fetchChatSessions,
  fetchDocumentById,
  fetchDocuments,
  fetchExperimentById,
  fetchExperiments,
  fetchKnowledgeBaseById,
  fetchKnowledgeBases,
  fetchSettings,
  sendChatMessage,
  updateExperiment,
  updateKnowledgeBase,
  uploadDocuments
} from "../api";
import {
  mockDocuments,
  mockExperiments,
  mockKnowledgeBases,
  mockMessages,
  mockSettings,
  ragStrategyOptions
} from "../utils/mock-data";

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

export const useWorkbenchStore = defineStore("workbench", () => {
  // --- Core state ---
  const knowledgeBases = ref<KnowledgeBaseSummary[]>(mockKnowledgeBases);
  const documents = ref<DocumentRecord[]>(sortByUpdatedAt(mockDocuments));
  const experiments = ref<ExperimentRecord[]>(mockExperiments);
  const messages = ref<ChatMessage[]>(mockMessages);
  const settings = ref<AppSettings>(mockSettings);
  const selectedStrategy = ref(ragStrategyOptions[0].value);
  const traceId = ref("trace-demo-20260525-181600");
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
      fetchSettings().then((data) => { settings.value = data; }),
    ]);

    const failedCount = results.filter((item) => item.status === "rejected").length;

    if (failedCount === results.length) {
      knowledgeBases.value = mockKnowledgeBases;
      documents.value = sortByUpdatedAt(mockDocuments);
      experiments.value = mockExperiments;
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

    messages.value.push({
      id: `msg-user-${Date.now()}`,
      role: "user",
      content: question.trim(),
      createdAt: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
    });

    try {
      const result = await sendChatMessage({
        question: question.trim(),
        strategy: selectedStrategy.value,
        knowledgeBaseId,
        sessionId: currentSessionId.value || undefined,
      });

      traceId.value = result.traceId;
      messages.value.push({
        id: `msg-assistant-${Date.now()}`,
        role: "assistant",
        content: result.answer,
        createdAt: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
        sources: result.sources
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "提问失败，请稍后重试。";
      lastError.value = message;
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
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "加载消息失败。";
    }
  }

  // --- Knowledge bases ---
  async function createKb(payload: { name: string; description?: string }): Promise<void> {
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
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "删除知识库失败。";
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
    lastFeedback,
    // actions
    askQuestion,
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
    // documents
    pollDocumentStatus,
    removeDocument,
    loadDocumentDetail,
    // experiments
    createExp,
    updateExp,
    deleteExp,
    loadExpDetail,
    // feedback
    submitFeedback,
  };
});
