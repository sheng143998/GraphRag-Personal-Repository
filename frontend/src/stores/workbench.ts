import { computed, ref } from "vue";
import { defineStore } from "pinia";
import type {
  AppSettings,
  ChatMessage,
  DocumentRecord,
  ExperimentRecord,
  KnowledgeBaseSummary,
  UploadPayload
} from "../types";
import {
  fetchDocuments,
  fetchExperiments,
  fetchKnowledgeBases,
  fetchSettings,
  sendChatMessage,
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

  const totalDocuments = computed(() => documents.value.length);
  const indexedDocuments = computed(() => documents.value.filter((item) => item.status === "INDEXED").length);
  const latestSources = computed(() => findLatestSources(messages.value));
  const selectedKnowledgeBase = computed(
    () => knowledgeBases.value.find((item) => item.id === settings.value.defaultKnowledgeBaseId) ?? knowledgeBases.value[0]
  );

  async function hydrate(): Promise<void> {
    lastError.value = "";

    const tasks = [
      fetchKnowledgeBases().then((data) => {
        knowledgeBases.value = data;
      }),
      fetchDocuments().then((data) => {
        documents.value = sortByUpdatedAt(data);
      }),
      fetchExperiments().then((data) => {
        experiments.value = data;
      }),
      fetchSettings().then((data) => {
        settings.value = data;
      })
    ];

    const results = await Promise.allSettled(tasks);
    const hasFailure = results.some((item) => item.status === "rejected");

    if (hasFailure) {
      knowledgeBases.value = mockKnowledgeBases;
      documents.value = sortByUpdatedAt(mockDocuments);
      experiments.value = mockExperiments;
      settings.value = mockSettings;
      lastError.value = "当前使用本地示例数据展示，待后端接口就绪后可直接切换。";
    }
  }

  async function askQuestion(question: string): Promise<void> {
    if (!question.trim()) {
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
        strategy: selectedStrategy.value
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

  async function submitUpload(payload: UploadPayload): Promise<void> {
    uploadPending.value = true;
    lastError.value = "";

    try {
      const result = await uploadDocuments(payload);
      traceId.value = `upload-${result.id}`;
    } catch (error) {
      const message = error instanceof Error ? error.message : "上传失败，请稍后重试。";
      lastError.value = message;
    } finally {
      uploadPending.value = false;
    }
  }

  return {
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
    askQuestion,
    hydrate,
    submitUpload
  };
});
