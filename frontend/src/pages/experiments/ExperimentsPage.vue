<template>
  <div class="page-grid evaluation-workbench">
    <aside class="panel evaluation-sidebar">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">评测集管理</h2>
          <p class="panel-subtitle">按实验维护问题、标准答案、命中文档和引用标签。</p>
        </div>
        <button class="button button-primary" type="button" @click="openCaseForm()">
          新建样本
        </button>
      </div>

      <div class="panel-body stack">
        <div class="evaluation-dashboard">
          <div class="dashboard-metric">
            <span class="metric-label">样本数</span>
            <strong>{{ filteredCases.length }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">启用</span>
            <strong>{{ activeCaseCount }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">已评估</span>
            <strong>{{ recentEvaluations.length }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">平均检索</span>
            <strong>{{ formatScore(summary.averageRetrieval) }}</strong>
          </div>
        </div>

        <label class="form-row">
          <span class="form-label">所属实验</span>
          <select v-model="selectedExperimentId" class="input">
            <option value="">全部实验</option>
            <option v-for="experiment in store.experiments" :key="experiment.id" :value="experiment.id">
              {{ experiment.name }}
            </option>
          </select>
        </label>

        <label class="form-row">
          <span class="form-label">样本状态</span>
          <select v-model="statusFilter" class="input">
            <option value="ACTIVE">只看启用</option>
            <option value="">全部状态</option>
            <option value="ARCHIVED">只看归档</option>
          </select>
        </label>

        <label class="form-row">
          <span class="form-label">关键词</span>
          <input v-model="keyword" class="input" placeholder="搜索样本 ID / 问题 / 备注" />
        </label>

        <div class="button-row">
          <button class="button button-secondary" type="button" @click="reloadAll">刷新数据</button>
          <button class="button button-ghost" type="button" @click="resetFilters">清空筛选</button>
        </div>

        <div class="item-list evaluation-case-list">
          <button
            v-for="evaluationCase in filteredCases"
            :key="evaluationCase.id"
            class="item-card evaluation-case-card"
            :class="{ 'is-active': evaluationCase.id === selectedCase?.id }"
            type="button"
            @click="selectCase(evaluationCase.id)"
          >
            <div class="case-card-topline">
              <h3 class="item-title">{{ evaluationCase.caseId }}</h3>
              <span :class="['status-pill', evaluationCase.status === 'ACTIVE' ? 'status-success' : 'status-muted']">
                {{ statusLabel(evaluationCase.status) }}
              </span>
            </div>
            <div class="item-meta">{{ summarize(evaluationCase.question, 84) }}</div>
            <div class="item-meta">
              {{ experimentName(evaluationCase.experimentId) }}
              · topK {{ evaluationCase.evaluationTopK }}
              · chunk {{ evaluationCase.relevantChunkIds.length }}
            </div>
          </button>
        </div>

        <div v-if="filteredCases.length === 0" class="empty-state">
          当前筛选下没有评测样本。
        </div>
      </div>
    </aside>

    <section class="panel evaluation-main">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">评测样本工作台</h2>
          <p class="panel-subtitle">
            维护人工标注，绑定历史 RAG run，按单样本或批量执行评估。
          </p>
        </div>
        <div class="button-row">
          <button class="button button-secondary" type="button" :disabled="!selectedCase" @click="openCaseForm(selectedCase)">
            编辑样本
          </button>
          <button class="button button-ghost" type="button" :disabled="!selectedCase" @click="archiveSelectedCase">
            {{ selectedCase?.status === "ARCHIVED" ? "启用样本" : "归档样本" }}
          </button>
          <button class="button button-danger" type="button" :disabled="!selectedCase" @click="deleteSelectedCase">
            删除
          </button>
        </div>
      </div>

      <div class="panel-body stack">
        <div v-if="caseFormVisible" class="panel panel-nested">
          <div class="panel-header compact">
            <div>
              <h3 class="section-title">{{ editingCaseId ? "编辑评测样本" : "新建评测样本" }}</h3>
              <p class="panel-subtitle">样本 ID 建议稳定可读，便于后续对比不同策略结果。</p>
            </div>
          </div>

          <div class="panel-body form-grid">
            <label class="form-row">
              <span class="form-label">所属实验</span>
              <select v-model="caseForm.experimentId" class="input">
                <option value="" disabled>请选择实验</option>
                <option v-for="experiment in store.experiments" :key="experiment.id" :value="experiment.id">
                  {{ experiment.name }}
                </option>
              </select>
            </label>

            <div class="form-grid split">
              <label class="form-row">
                <span class="form-label">样本 ID</span>
                <input v-model="caseForm.caseId" class="input" placeholder="advanced-rag-rerank-001" />
              </label>
              <label class="form-row">
                <span class="form-label">状态</span>
                <select v-model="caseForm.status" class="input">
                  <option value="ACTIVE">启用</option>
                  <option value="ARCHIVED">归档</option>
                </select>
              </label>
            </div>

            <label class="form-row">
              <span class="form-label">评测问题</span>
              <textarea v-model="caseForm.question" class="textarea" placeholder="输入这条样本要评测的问题" />
            </label>

            <label class="form-row">
              <span class="form-label">标准答案</span>
              <textarea v-model="caseForm.expectedAnswer" class="textarea" placeholder="人工标注的参考答案，用于 grounded_score / answer quality 判断" />
            </label>

            <div class="form-grid split">
              <label class="form-row">
                <span class="form-label">相关 Chunk IDs</span>
                <textarea v-model="chunkIdsText" class="textarea" placeholder="一行一个 chunkId，或用逗号分隔" />
              </label>
              <label class="form-row">
                <span class="form-label">相关 Document IDs</span>
                <textarea v-model="documentIdsText" class="textarea" placeholder="一行一个 documentId，或用逗号分隔" />
              </label>
            </div>

            <div class="form-grid split">
              <label class="form-row">
                <span class="form-label">期望引用 Chunk IDs</span>
                <textarea v-model="citationIdsText" class="textarea" placeholder="用于 citation_hit 的目标引用 chunkId" />
              </label>
              <label class="form-row">
                <span class="form-label">Top K</span>
                <input v-model.number="caseForm.evaluationTopK" class="input" type="number" min="1" />
              </label>
            </div>

            <label class="form-row">
              <span class="form-label">备注</span>
              <textarea v-model="caseForm.notes" class="textarea" placeholder="样本来源、标注说明、适用策略、失败原因分类" />
            </label>

            <div class="button-row">
              <button class="button button-primary" type="button" :disabled="caseFormSubmitting || !canSubmitCase" @click="submitCaseForm">
                {{ editingCaseId ? "保存样本" : "创建样本" }}
              </button>
              <button class="button button-secondary" type="button" @click="closeCaseForm">取消</button>
            </div>
          </div>
        </div>

        <div v-if="selectedCase" class="evaluation-case-detail">
          <div class="panel-subsection">
            <div class="panel-header compact">
              <div>
                <h3 class="section-title">{{ selectedCase.caseId }}</h3>
                <p class="panel-subtitle">{{ selectedCase.question }}</p>
              </div>
              <span :class="['status-pill', selectedCase.status === 'ACTIVE' ? 'status-success' : 'status-muted']">
                {{ statusLabel(selectedCase.status) }}
              </span>
            </div>

            <div class="metric-list">
              <div class="metric-row">
                <span class="metric-label">所属实验</span>
                <span class="metric-value">{{ experimentName(selectedCase.experimentId) }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">topK</span>
                <span class="metric-value">{{ selectedCase.evaluationTopK }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">标注覆盖</span>
                <span class="metric-value">
                  chunk {{ selectedCase.relevantChunkIds.length }} / doc {{ selectedCase.relevantDocumentIds.length }} / citation {{ selectedCase.expectedCitationChunkIds.length }}
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">更新时间</span>
                <span class="metric-value">{{ formatDate(selectedCase.updatedAt) }}</span>
              </div>
            </div>
          </div>

          <div class="split-columns evaluation-detail-grid">
            <section class="panel panel-nested">
              <div class="panel-header compact">
                <h3 class="section-title">人工标注</h3>
              </div>
              <div class="panel-body stack">
                <div class="label-block">
                  <span class="form-label">标准答案</span>
                  <p class="item-description">{{ selectedCase.expectedAnswer || "未填写标准答案" }}</p>
                </div>
                <div class="label-block">
                  <span class="form-label">相关 Chunk IDs</span>
                  <div class="tag-row">
                    <span v-for="id in selectedCase.relevantChunkIds" :key="id" class="tag">{{ shortId(id) }}</span>
                    <span v-if="selectedCase.relevantChunkIds.length === 0" class="item-meta">未标注</span>
                  </div>
                </div>
                <div class="label-block">
                  <span class="form-label">相关 Document IDs</span>
                  <div class="tag-row">
                    <span v-for="id in selectedCase.relevantDocumentIds" :key="id" class="tag">{{ shortId(id) }}</span>
                    <span v-if="selectedCase.relevantDocumentIds.length === 0" class="item-meta">未标注</span>
                  </div>
                </div>
                <div class="label-block">
                  <span class="form-label">期望引用 Chunk IDs</span>
                  <div class="tag-row">
                    <span v-for="id in selectedCase.expectedCitationChunkIds" :key="id" class="tag">{{ shortId(id) }}</span>
                    <span v-if="selectedCase.expectedCitationChunkIds.length === 0" class="item-meta">未标注</span>
                  </div>
                </div>
                <div class="label-block">
                  <span class="form-label">备注</span>
                  <p class="item-description">{{ selectedCase.notes || "无备注" }}</p>
                </div>
              </div>
            </section>

            <section class="panel panel-nested">
              <div class="panel-header compact">
                <h3 class="section-title">执行评估</h3>
              </div>
              <div class="panel-body stack">
                <label class="form-row">
                  <span class="form-label">选择 RAG Run</span>
                  <select v-model="selectedRunId" class="input">
                    <option value="">请选择历史运行</option>
                    <option v-for="run in runOptionsForSelectedCase" :key="run.id" :value="run.id">
                      {{ runLabel(run) }}
                    </option>
                  </select>
                </label>

                <label class="form-row">
                  <span class="form-label">临时覆盖标准答案</span>
                  <textarea v-model="expectedAnswerOverride" class="textarea" placeholder="留空则使用样本内标准答案" />
                </label>

                <div class="form-grid split">
                  <label class="form-row">
                    <span class="form-label">Preset</span>
                    <select v-model="batchStrategyName" class="input">
                      <option value="basic-rag">basic-rag</option>
                      <option value="hybrid-rerank">hybrid-rerank</option>
                      <option value="metadata-filter">metadata-filter</option>
                      <option value="parent-child">parent-child</option>
                      <option value="advanced-rag">advanced-rag</option>
                      <option value="graph-rag">graph-rag</option>
                    </select>
                  </label>
                  <label class="form-row">
                    <span class="form-label">Batch topK</span>
                    <input v-model.number="batchTopK" class="input" type="number" min="1" />
                  </label>
                </div>

                <div class="button-row">
                  <button class="button button-primary" type="button" :disabled="evaluationPending || !selectedRunId" @click="evaluateSelectedCase">
                    评估当前样本
                  </button>
                  <button class="button button-secondary" type="button" :disabled="evaluationPending || batchCandidateCases.length === 0" @click="evaluateBatch">
                    批量评估 {{ batchCandidateCases.length }} 条
                  </button>
                  <button class="button button-ghost" type="button" :disabled="!selectedRunId" @click="useTopRetrievalAsCase">
                    从首条召回生成样本
                  </button>
                  <button class="button button-primary" type="button" :disabled="evaluationPending || batchCandidateCases.length === 0" @click="runBatchPreset">
                    Run preset {{ batchStrategyName }}
                  </button>
                </div>

                <div v-if="batchStatus" class="empty-state">{{ batchStatus }}</div>
                <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
              </div>
            </section>
          </div>
        </div>

        <div v-else class="empty-state">
          先从左侧选择一个样本，或新建第一条评测样本。
        </div>

        <section class="panel panel-nested">
          <div class="panel-header compact">
            <div>
              <h3 class="section-title">最近评估历史</h3>
              <p class="panel-subtitle">来自 `rag_experiment_evaluations`，用于回看样本、策略和 run 的评测结果。</p>
            </div>
          </div>

          <div v-if="recentEvaluations.length === 0" class="empty-state">
            暂无评估历史。
          </div>
          <div v-else class="history-list">
            <article v-for="evaluation in recentEvaluations" :key="evaluation.id" class="history-row">
              <div class="history-main">
                <span class="history-run">{{ experimentName(evaluation.experimentId) }}</span>
                <span class="item-meta">{{ formatDate(evaluation.createdAt) }}</span>
              </div>
              <div class="history-question">{{ summarize(evaluation.runQuestion) }}</div>
              <div class="item-meta">
                可信度 {{ formatScore(evaluation.groundedScore) }}
                · 检索分 {{ formatScore(evaluation.retrievalScore) }}
                <span v-if="evaluation.runLatencyMs != null"> · {{ evaluation.runLatencyMs }}ms</span>
              </div>
              <div class="item-meta">
                run {{ shortId(evaluation.runId) }}
                <span v-if="evaluation.runRetrieverType"> · {{ evaluation.runRetrieverType }}</span>
                <span v-if="evaluation.runModelName"> · {{ evaluation.runModelName }}</span>
              </div>
              <div v-if="evaluation.notes" class="item-meta">{{ evaluation.notes }}</div>
            </article>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import type {
  CreateEvaluationCaseRequest,
  EvaluationCaseRecord,
  RagRunSummary
} from "../../types";
import { useWorkbenchStore } from "../../stores/workbench";
import {
  createEvaluationCase,
  deleteEvaluationCase,
  evaluateEvaluationCase,
  fetchEvaluationCases,
  runEvaluationCasesBatch,
  updateEvaluationCase
} from "../../api/experiments";

const store = useWorkbenchStore();
const selectedExperimentId = ref("");
const selectedCaseId = ref("");
const selectedRunId = ref("");
const statusFilter = ref("ACTIVE");
const keyword = ref("");
const expectedAnswerOverride = ref("");
const evaluationCases = ref<EvaluationCaseRecord[]>([]);
const caseFormVisible = ref(false);
const editingCaseId = ref<string | null>(null);
const caseFormSubmitting = ref(false);
const evaluationPending = ref(false);
const batchStatus = ref("");
const batchStrategyName = ref("advanced-rag");
const batchTopK = ref(5);

const caseForm = reactive<CreateEvaluationCaseRequest>({
  experimentId: "",
  caseId: "",
  question: "",
  expectedAnswer: "",
  relevantChunkIds: [],
  relevantDocumentIds: [],
  expectedCitationChunkIds: [],
  evaluationTopK: 5,
  notes: "",
  status: "ACTIVE"
});

const chunkIdsText = ref("");
const documentIdsText = ref("");
const citationIdsText = ref("");

const summary = computed(() => store.experimentEvaluationSummary);
const recentEvaluations = computed(() => summary.value.recentEvaluations ?? []);
const activeCaseCount = computed(() => filteredCases.value.filter((item) => item.status === "ACTIVE").length);
const filteredCases = computed(() => {
  const query = keyword.value.trim().toLowerCase();
  return evaluationCases.value.filter((item) => {
    const matchesExperiment = !selectedExperimentId.value || item.experimentId === selectedExperimentId.value;
    const matchesStatus = !statusFilter.value || item.status === statusFilter.value;
    const matchesKeyword =
      !query ||
      item.caseId.toLowerCase().includes(query) ||
      item.question.toLowerCase().includes(query) ||
      (item.notes ?? "").toLowerCase().includes(query);
    return matchesExperiment && matchesStatus && matchesKeyword;
  });
});

const selectedCase = computed(() => {
  if (!selectedCaseId.value) return filteredCases.value[0];
  return filteredCases.value.find((item) => item.id === selectedCaseId.value)
    ?? evaluationCases.value.find((item) => item.id === selectedCaseId.value)
    ?? null;
});

const runOptionsForSelectedCase = computed(() => {
  if (!selectedCase.value) return store.ragRuns;
  return store.ragRuns.filter((run) => {
    if (!run.knowledgeBaseId) return true;
    const experiment = store.experiments.find((item) => item.id === selectedCase.value?.experimentId);
    return !experiment?.knowledgeBaseId || experiment.knowledgeBaseId === run.knowledgeBaseId;
  });
});

const batchCandidateCases = computed(() => {
  if (!selectedRunId.value) return [];
  return filteredCases.value.filter((item) => item.status === "ACTIVE");
});

const canSubmitCase = computed(() =>
  Boolean(caseForm.experimentId && caseForm.caseId.trim() && caseForm.question.trim())
);

watch(selectedExperimentId, () => {
  selectedCaseId.value = "";
  batchStatus.value = "";
});

watch(selectedCase, (value) => {
  selectedRunId.value = "";
  expectedAnswerOverride.value = value?.expectedAnswer ?? "";
});

function resetFilters(): void {
  selectedExperimentId.value = "";
  statusFilter.value = "ACTIVE";
  keyword.value = "";
}

function reloadAll(): void {
  batchStatus.value = "";
  void Promise.all([
    loadCases(),
    store.loadExperiments(),
    store.loadExperimentEvaluationSummary(50),
    store.loadRagRuns(50)
  ]);
}

async function loadCases(): Promise<void> {
  evaluationCases.value = await fetchEvaluationCases();
  if (!selectedCaseId.value || !evaluationCases.value.some((item) => item.id === selectedCaseId.value)) {
    selectedCaseId.value = filteredCases.value[0]?.id ?? evaluationCases.value[0]?.id ?? "";
  }
}

function selectCase(id: string): void {
  selectedCaseId.value = id;
  const target = evaluationCases.value.find((item) => item.id === id);
  if (target) {
    selectedExperimentId.value = target.experimentId;
    selectedRunId.value = "";
    expectedAnswerOverride.value = target.expectedAnswer ?? "";
  }
}

function openCaseForm(target?: EvaluationCaseRecord | null): void {
  if (target) {
    editingCaseId.value = target.id;
    Object.assign(caseForm, {
      experimentId: target.experimentId,
      caseId: target.caseId,
      question: target.question,
      expectedAnswer: target.expectedAnswer ?? "",
      relevantChunkIds: [...target.relevantChunkIds],
      relevantDocumentIds: [...target.relevantDocumentIds],
      expectedCitationChunkIds: [...target.expectedCitationChunkIds],
      evaluationTopK: target.evaluationTopK,
      notes: target.notes ?? "",
      status: target.status
    });
    chunkIdsText.value = target.relevantChunkIds.join("\n");
    documentIdsText.value = target.relevantDocumentIds.join("\n");
    citationIdsText.value = target.expectedCitationChunkIds.join("\n");
  } else {
    editingCaseId.value = null;
    Object.assign(caseForm, {
      experimentId: selectedExperimentId.value || store.experiments[0]?.id || "",
      caseId: "",
      question: "",
      expectedAnswer: "",
      relevantChunkIds: [],
      relevantDocumentIds: [],
      expectedCitationChunkIds: [],
      evaluationTopK: 5,
      notes: "",
      status: "ACTIVE"
    });
    chunkIdsText.value = "";
    documentIdsText.value = "";
    citationIdsText.value = "";
  }
  caseFormVisible.value = true;
}

function closeCaseForm(): void {
  caseFormVisible.value = false;
  editingCaseId.value = null;
}

async function submitCaseForm(): Promise<void> {
  if (!canSubmitCase.value) return;
  caseFormSubmitting.value = true;
  try {
    const payload = {
      ...caseForm,
      evaluationTopK: Math.max(1, Number(caseForm.evaluationTopK) || 5),
      relevantChunkIds: parseIds(chunkIdsText.value),
      relevantDocumentIds: parseIds(documentIdsText.value),
      expectedCitationChunkIds: parseIds(citationIdsText.value)
    };
    const record = editingCaseId.value
      ? await updateEvaluationCase(editingCaseId.value, payload)
      : await createEvaluationCase(payload);
    await loadCases();
    selectedCaseId.value = record.id;
    selectedExperimentId.value = record.experimentId;
    closeCaseForm();
  } finally {
    caseFormSubmitting.value = false;
  }
}

async function archiveSelectedCase(): Promise<void> {
  if (!selectedCase.value) return;
  const nextStatus = selectedCase.value.status === "ARCHIVED" ? "ACTIVE" : "ARCHIVED";
  const updated = await updateEvaluationCase(selectedCase.value.id, { status: nextStatus });
  evaluationCases.value = evaluationCases.value.map((item) => (item.id === updated.id ? updated : item));
  selectedCaseId.value = updated.id;
}

async function deleteSelectedCase(): Promise<void> {
  if (!selectedCase.value) return;
  await handleDeleteCase(selectedCase.value.id);
}

async function handleDeleteCase(id: string): Promise<void> {
  const target = evaluationCases.value.find((item) => item.id === id);
  if (!target) return;
  if (!confirm(`确认删除评测样本 ${target.caseId} 吗？`)) return;
  await deleteEvaluationCase(id);
  evaluationCases.value = evaluationCases.value.filter((item) => item.id !== id);
  selectedCaseId.value = filteredCases.value[0]?.id ?? evaluationCases.value[0]?.id ?? "";
}

async function evaluateSelectedCase(): Promise<void> {
  if (!selectedCase.value || !selectedRunId.value) return;
  evaluationPending.value = true;
  batchStatus.value = "";
  try {
    await evaluateEvaluationCase(selectedCase.value.id, {
      runId: selectedRunId.value,
      expectedAnswer: expectedAnswerOverride.value.trim() || undefined
    });
    await Promise.all([
      store.loadExperiments(),
      store.loadExperimentEvaluationSummary(50)
    ]);
    batchStatus.value = `已完成样本 ${selectedCase.value.caseId} 的评估。`;
  } finally {
    evaluationPending.value = false;
  }
}

async function evaluateBatch(): Promise<void> {
  if (!selectedRunId.value || batchCandidateCases.value.length === 0) return;
  evaluationPending.value = true;
  batchStatus.value = `开始批量评估 ${batchCandidateCases.value.length} 条样本...`;
  try {
    let completed = 0;
    for (const evaluationCase of batchCandidateCases.value) {
      await evaluateEvaluationCase(evaluationCase.id, { runId: selectedRunId.value });
      completed += 1;
      batchStatus.value = `批量评估进度：${completed}/${batchCandidateCases.value.length}`;
    }
    await Promise.all([
      store.loadExperiments(),
      store.loadExperimentEvaluationSummary(50)
    ]);
    batchStatus.value = `批量评估完成：${completed}/${batchCandidateCases.value.length}`;
  } finally {
    evaluationPending.value = false;
  }
}

async function runBatchPreset(): Promise<void> {
  if (!selectedExperimentId.value || batchCandidateCases.value.length === 0) return;
  evaluationPending.value = true;
  batchStatus.value = `Running ${batchStrategyName.value} for ${batchCandidateCases.value.length} cases...`;
  try {
    const result = await runEvaluationCasesBatch({
      experimentId: selectedExperimentId.value,
      caseIds: batchCandidateCases.value.map((item) => item.id),
      strategyName: batchStrategyName.value,
      retrieverType: "hybrid",
      topK: Math.max(1, Number(batchTopK.value) || 5)
    });
    await Promise.all([
      store.loadExperiments(),
      store.loadExperimentEvaluationSummary(50),
      store.loadRagRuns(50)
    ]);
    batchStatus.value = `Preset ${result.strategyName ?? batchStrategyName.value} completed: ${result.completedCount}/${result.requestedCount}, failed ${result.failedCount}.`;
  } finally {
    evaluationPending.value = false;
  }
}

async function useTopRetrievalAsCase(): Promise<void> {
  if (!selectedRunId.value) return;
  const detail = await store.loadRagRunDetail(selectedRunId.value);
  const topResult = detail?.retrievalResults?.[0];
  if (!topResult?.chunkId) {
    store.lastError = "所选 RAG run 没有可用于生成样本的首条召回片段。";
    return;
  }
  openCaseForm();
  caseForm.caseId = `auto-${shortId(selectedRunId.value)}`;
  caseForm.question = detail?.question ?? "";
  caseForm.expectedAnswer = detail?.answer ?? "";
  caseForm.relevantChunkIds = [topResult.chunkId];
  caseForm.relevantDocumentIds = topResult.documentId ? [topResult.documentId] : [];
  caseForm.expectedCitationChunkIds = [topResult.chunkId];
  caseForm.evaluationTopK = 1;
  chunkIdsText.value = topResult.chunkId;
  documentIdsText.value = topResult.documentId ?? "";
  citationIdsText.value = topResult.chunkId;
}

function parseIds(value: string): string[] {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function experimentName(id?: string | null): string {
  if (!id) return "未知实验";
  return store.experiments.find((experiment) => experiment.id === id)?.name ?? shortId(id);
}

function formatScore(value?: number | null): string {
  if (value == null) return "待评估";
  return `${Math.round(value * 100)}%`;
}

function summarize(value?: string | null, maxLength = 72): string {
  if (!value) return "暂无内容";
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function shortId(value?: string | null): string {
  if (!value) return "-";
  return value.slice(0, 8);
}

function formatDate(value?: string | null): string {
  if (!value) return "-";
  return value.replace("T", " ").slice(0, 16);
}

function runLabel(run: RagRunSummary): string {
  return `${run.strategyName ?? "未知策略"} · ${run.status} · ${summarize(run.question, 44)}`;
}

function statusLabel(value?: string | null): string {
  return value === "ARCHIVED" ? "归档" : "启用";
}

onMounted(() => {
  void Promise.all([
    store.loadExperiments(),
    store.loadExperimentEvaluationSummary(50),
    store.loadRagRuns(50)
  ]).then(() => loadCases());
});
</script>
