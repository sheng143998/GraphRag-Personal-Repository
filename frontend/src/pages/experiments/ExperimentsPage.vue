<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">RAG 实验</h2>
        <p class="panel-subtitle">创建、对比并评估不同 RAG 策略的运行效果。</p>
        <button class="button button-primary" type="button" @click="openCreate">
          {{ showForm && !editingId ? "关闭表单" : "创建实验" }}
        </button>
      </div>

      <div class="panel-body stack">
        <div v-if="showForm" class="form-grid">
          <label class="form-row">
            <span class="form-label">名称</span>
            <input v-model="formName" class="input" placeholder="混合检索与重排对比" />
          </label>
          <label class="form-row">
            <span class="form-label">描述</span>
            <textarea v-model="formDescription" class="textarea" placeholder="实验目标和观察记录" />
          </label>
          <label class="form-row">
            <span class="form-label">策略</span>
            <select v-model="formStrategy" class="input">
              <option v-for="opt in store.ragStrategyOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">数据集</span>
            <input v-model="formDatasetName" class="input" placeholder="engineering-smoke" />
          </label>
          <label class="form-row">
            <span class="form-label">样本数</span>
            <input v-model.number="formSampleCount" class="input" type="number" min="0" />
          </label>
          <div class="form-row" style="display: flex; gap: 1rem;">
            <label style="flex: 1;">
              <span class="form-label">精确率</span>
              <input v-model.number="formPrecisionScore" class="input" type="number" min="0" max="1" step="0.01" />
            </label>
            <label style="flex: 1;">
              <span class="form-label">召回率</span>
              <input v-model.number="formRecallScore" class="input" type="number" min="0" max="1" step="0.01" />
            </label>
          </div>
          <label class="form-row">
            <span class="form-label">状态</span>
            <select v-model="formStatus" class="input">
              <option value="PLANNED">计划中</option>
              <option value="RUNNING">运行中</option>
              <option value="COMPLETED">已完成</option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">备注</span>
            <textarea v-model="formNotes" class="textarea" placeholder="实验备注" />
          </label>
          <div class="button-row">
            <button
              class="button button-primary"
              type="button"
              :disabled="store.experimentFormPending || !formName.trim()"
              @click="submitForm"
            >
              {{ store.experimentFormPending ? "保存中..." : editingId ? "更新实验" : "创建实验" }}
            </button>
            <button class="button button-secondary" type="button" @click="closeForm">取消</button>
          </div>
          <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        </div>

        <div v-if="store.experiments.length === 0" class="empty-state">
          暂无实验记录。
        </div>
        <div v-else class="evaluation-dashboard">
          <div class="dashboard-metric">
            <span class="metric-label">评估次数</span>
            <strong>{{ evaluationDashboard.evaluationCount }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">平均可信度</span>
            <strong>{{ formatScore(evaluationDashboard.averageGrounded) }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">平均检索分</span>
            <strong>{{ formatScore(evaluationDashboard.averageRetrieval) }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">最新最佳</span>
            <strong>{{ evaluationDashboard.bestExperimentName }}</strong>
          </div>
        </div>

        <div v-if="store.experiments.length > 0" class="item-list">
          <article v-for="experiment in store.experiments" :key="experiment.id" class="item-card">
            <h3 class="item-title">{{ experiment.name }}</h3>
            <div v-if="experiment.description" class="item-meta">{{ experiment.description }}</div>
            <div class="item-meta">
              {{ strategyLabel(experiment.strategy) }}
              <span v-if="experiment.status"> | {{ statusLabel(experiment.status) }}</span>
              <span v-if="experiment.datasetName"> | {{ experiment.datasetName }}</span>
              | 更新于 {{ experiment.updatedAt }}
            </div>

            <div class="metric-list">
              <div class="metric-row">
                <span class="metric-label">精确率</span>
                <span class="metric-value">{{ experiment.precision ?? formatScore(experiment.precisionScore) }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">召回率</span>
                <span class="metric-value">{{ experiment.recall ?? formatScore(experiment.recallScore) }}</span>
              </div>
              <div v-if="experiment.sampleCount != null" class="metric-row">
                <span class="metric-label">样本数</span>
                <span class="metric-value">{{ experiment.sampleCount }}</span>
              </div>
              <div v-if="experimentHistorySummary(experiment).count > 0" class="metric-row">
                <span class="metric-label">历史均值</span>
                <span class="metric-value">
                  {{ formatScore(experimentHistorySummary(experiment).averageGrounded) }}
                  / {{ formatScore(experimentHistorySummary(experiment).averageRetrieval) }}
                </span>
              </div>
              <div v-if="experimentHistorySummary(experiment).trendLabel" class="metric-row">
                <span class="metric-label">最新趋势</span>
                <span class="metric-value">{{ experimentHistorySummary(experiment).trendLabel }}</span>
              </div>
            </div>

            <div v-if="experiment.notes" class="item-meta" style="margin-top: 0.5rem;">{{ experiment.notes }}</div>

            <div v-if="experiment.evaluations?.length" class="history-list">
              <div
                v-for="evaluation in experiment.evaluations"
                :key="evaluation.id"
                class="history-row"
              >
                <div class="history-main">
                  <span class="history-run">{{ strategyLabel(evaluation.runStrategyName ?? experiment.strategy) }}</span>
                  <span class="item-meta">{{ formatDate(evaluation.createdAt) }}</span>
                </div>
                <div class="history-question">{{ summarize(evaluation.runQuestion) }}</div>
                <div class="item-meta">
                  可信度 {{ formatScore(evaluation.groundedScore ?? undefined) }}
                  | 检索分 {{ formatScore(evaluation.retrievalScore ?? undefined) }}
                  <span v-if="evaluationDeltaLabel(experiment, evaluation)">
                    | {{ evaluationDeltaLabel(experiment, evaluation) }}
                  </span>
                  <span v-if="evaluation.runLatencyMs != null"> | {{ evaluation.runLatencyMs }}ms</span>
                </div>
                <div class="item-meta">
                  运行 {{ shortId(evaluation.runId) }}
                  <span v-if="evaluation.runRetrieverType"> | {{ evaluation.runRetrieverType }}</span>
                  <span v-if="evaluation.runModelName"> | {{ evaluation.runModelName }}</span>
                </div>
                <div v-if="evaluation.notes" class="item-meta">{{ evaluation.notes }}</div>
                <div v-if="graphMetricItems(evaluation).length" class="graph-metric-strip">
                  <div v-for="metric in graphMetricItems(evaluation)" :key="metric.label" class="graph-metric">
                    <span>{{ metric.label }}</span>
                    <strong>{{ metric.value }}</strong>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-grid" style="margin-top: 0.75rem;">
              <label class="form-row">
                <span class="form-label">RAG 运行</span>
                <select v-model="selectedRunIds[experiment.id]" class="input">
                  <option value="">选择最近一次运行</option>
                  <option v-for="run in store.ragRuns" :key="run.id" :value="run.id">
                    {{ runLabel(run) }}
                  </option>
                </select>
              </label>
              <label class="form-row">
                <span class="form-label">期望答案</span>
                <textarea
                  v-model="expectedAnswers[experiment.id]"
                  class="textarea"
                  placeholder="可选：提供给评估器的参考答案"
                />
              </label>
              <div class="structured-eval-box">
                <div>
                  <span class="form-label">结构化检索用例</span>
                  <p class="item-meta">
                    {{ structuredCaseLabel(experiment.id) }}
                  </p>
                </div>
                <div class="button-row compact-row">
                  <button
                    class="button button-secondary"
                    type="button"
                    :disabled="store.experimentFormPending || !selectedRunIds[experiment.id]"
                    @click="handleUseStructuredCase(experiment.id)"
                  >
                    使用首条检索结果
                  </button>
                  <button
                    class="button button-ghost"
                    type="button"
                    :disabled="!structuredCaseFor(experiment.id)"
                    @click="clearStructuredCase(experiment.id)"
                  >
                    清除用例
                  </button>
                </div>
              </div>
            </div>

            <div class="button-row" style="margin-top: 0.75rem;">
              <button
                class="button button-primary"
                type="button"
                :disabled="store.experimentFormPending || !selectedRunIds[experiment.id]"
                @click="handleEvaluate(experiment.id)"
              >
                评估
              </button>
              <button class="button button-secondary" type="button" @click="openEdit(experiment)">编辑</button>
              <button class="button button-ghost" type="button" @click="handleDelete(experiment.id)">删除</button>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import type { ExperimentEvaluationHistory, ExperimentRecord, ExperimentEvaluationRequest, RagRunSummary } from "../../types";
import { useWorkbenchStore } from "../../stores/workbench";
import { formatMetricPercent, parseGraphRagMetricNote } from "../../utils/evaluation-notes";

const store = useWorkbenchStore();

const showForm = ref(false);
const editingId = ref<string | null>(null);

const formName = ref("");
const formDescription = ref("");
const formStrategy = ref(store.ragStrategyOptions[0].value);
const formDatasetName = ref("");
const formSampleCount = ref<number | undefined>(undefined);
const formPrecisionScore = ref<number | undefined>(undefined);
const formRecallScore = ref<number | undefined>(undefined);
const formStatus = ref("PLANNED");
const formNotes = ref("");
const selectedRunIds = reactive<Record<string, string>>({});
const expectedAnswers = reactive<Record<string, string>>({});
const structuredCases = reactive<Record<string, StructuredEvaluationCase>>({});
const structuredCaseRunIds = reactive<Record<string, string>>({});

interface StructuredEvaluationCase {
  evaluationCaseId: string;
  relevantChunkIds: string[];
  relevantDocumentIds: string[];
  expectedCitationChunkIds: string[];
  evaluationTopK: number;
}

interface ExperimentHistorySummary {
  count: number;
  averageGrounded?: number;
  averageRetrieval?: number;
  trendLabel?: string;
}

interface EvaluationDashboard {
  evaluationCount: number;
  averageGrounded?: number;
  averageRetrieval?: number;
  bestExperimentName: string;
}

const evaluationDashboard = computed<EvaluationDashboard>(() => {
  const summary = store.experimentEvaluationSummary;
  if (summary.evaluationCount > 0) {
    return {
      evaluationCount: summary.evaluationCount,
      averageGrounded: summary.averageGrounded ?? undefined,
      averageRetrieval: summary.averageRetrieval ?? undefined,
      bestExperimentName: summary.bestExperimentName ?? "待评估"
    };
  }

  const evaluations = store.experiments.flatMap((experiment) =>
    (experiment.evaluations ?? []).map((evaluation) => ({ experiment, evaluation }))
  );

  if (evaluations.length === 0) {
    return {
      evaluationCount: 0,
      bestExperimentName: "待评估"
    };
  }

  const latestByExperiment = store.experiments
    .map((experiment) => ({ experiment, evaluation: sortEvaluations(experiment.evaluations ?? [])[0] }))
    .filter((item): item is { experiment: ExperimentRecord; evaluation: ExperimentEvaluationHistory } =>
      Boolean(item.evaluation)
    );

  const best = latestByExperiment
    .filter(({ evaluation }) => evaluation.groundedScore != null || evaluation.retrievalScore != null)
    .sort((left, right) => evaluationQuality(right.evaluation) - evaluationQuality(left.evaluation))[0];

  return {
    evaluationCount: evaluations.length,
    averageGrounded: averageScore(evaluations.map(({ evaluation }) => evaluation.groundedScore)),
    averageRetrieval: averageScore(evaluations.map(({ evaluation }) => evaluation.retrievalScore)),
    bestExperimentName: best?.experiment.name ?? "待评估"
  };
});

function formatScore(value?: number): string {
  if (value == null) return "待评估";
  return `${Math.round(value * 100)}%`;
}

function averageScore(values: Array<number | null | undefined>): number | undefined {
  const valid = values.filter((value): value is number => value != null);
  if (valid.length === 0) return undefined;
  return valid.reduce((total, value) => total + value, 0) / valid.length;
}

function evaluationQuality(evaluation: ExperimentEvaluationHistory): number {
  return averageScore([evaluation.groundedScore, evaluation.retrievalScore]) ?? 0;
}

function sortEvaluations(evaluations: ExperimentEvaluationHistory[]): ExperimentEvaluationHistory[] {
  return [...evaluations].sort((left, right) => right.createdAt.localeCompare(left.createdAt));
}

function experimentHistorySummary(experiment: ExperimentRecord): ExperimentHistorySummary {
  const evaluations = sortEvaluations(experiment.evaluations ?? []);
  const latest = evaluations[0];
  const previous = evaluations[1];
  const latestQuality = latest ? evaluationQuality(latest) : undefined;
  const previousQuality = previous ? evaluationQuality(previous) : undefined;
  const delta = latestQuality != null && previousQuality != null ? latestQuality - previousQuality : undefined;

  return {
    count: evaluations.length,
    averageGrounded: averageScore(evaluations.map((evaluation) => evaluation.groundedScore)),
    averageRetrieval: averageScore(evaluations.map((evaluation) => evaluation.retrievalScore)),
    trendLabel: formatTrend(delta)
  };
}

function evaluationDeltaLabel(experiment: ExperimentRecord, evaluation: ExperimentEvaluationHistory): string | undefined {
  const evaluations = sortEvaluations(experiment.evaluations ?? []);
  const index = evaluations.findIndex((item) => item.id === evaluation.id);
  if (index < 0 || index >= evaluations.length - 1) return undefined;
  return formatTrend(evaluationQuality(evaluation) - evaluationQuality(evaluations[index + 1]));
}

function graphMetricItems(evaluation: ExperimentEvaluationHistory): Array<{ label: string; value: string }> {
  const metrics = parseGraphRagMetricNote(evaluation.notes);
  if (!metrics) return [];
  return [
    { label: "实体", value: formatMetricPercent(metrics.entityCoverage) },
    { label: "关系", value: formatMetricPercent(metrics.relationshipHit) },
    { label: "扩展", value: formatMetricPercent(metrics.expansionTermHit) }
  ];
}

function formatTrend(value?: number): string | undefined {
  if (value == null) return undefined;
  const sign = value >= 0 ? "+" : "";
  return `${sign}${Math.round(value * 100)} 点`;
}

function runLabel(run: RagRunSummary): string {
  const question = run.question.length > 64 ? `${run.question.slice(0, 64)}...` : run.question;
  return `${strategyLabel(run.strategyName)} | ${statusLabel(run.status)} | ${question}`;
}

function summarize(value?: string | null, maxLength = 92): string {
  if (!value) return "无问题快照";
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function shortId(value: string): string {
  return value.slice(0, 8);
}

function formatDate(value: string): string {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

function structuredCaseFor(experimentId: string): StructuredEvaluationCase | undefined {
  const selectedRunId = selectedRunIds[experimentId];
  if (!selectedRunId || structuredCaseRunIds[experimentId] !== selectedRunId) {
    return undefined;
  }
  return structuredCases[experimentId];
}

function structuredCaseLabel(experimentId: string): string {
  const evaluationCase = structuredCaseFor(experimentId);
  if (!evaluationCase) {
    return "当前使用简单评估路径。添加用例后可按召回率、精确率、MRR 和引用命中率评估检索结果。";
  }
  const chunkId = evaluationCase.relevantChunkIds[0] ?? "待选择";
  return `${evaluationCase.evaluationCaseId} | topK=${evaluationCase.evaluationTopK} | 片段 ${shortId(chunkId)}`;
}

function strategyLabel(value?: string | null): string {
  if (!value) return "未知策略";
  return store.ragStrategyOptions.find((option) => option.value === value)?.label ?? value;
}

function statusLabel(value?: string | null): string {
  const labels: Record<string, string> = {
    PLANNED: "计划中",
    RUNNING: "运行中",
    COMPLETED: "已完成",
    FAILED: "失败",
    SUCCESS: "成功",
    ERROR: "错误"
  };
  return value ? labels[value] ?? value : "未知状态";
}

function resetForm(): void {
  formName.value = "";
  formDescription.value = "";
  formStrategy.value = store.ragStrategyOptions[0].value;
  formDatasetName.value = "";
  formSampleCount.value = undefined;
  formPrecisionScore.value = undefined;
  formRecallScore.value = undefined;
  formStatus.value = "PLANNED";
  formNotes.value = "";
  editingId.value = null;
}

function openCreate(): void {
  if (showForm.value && !editingId.value) {
    showForm.value = false;
    return;
  }
  resetForm();
  showForm.value = true;
}

function openEdit(exp: ExperimentRecord): void {
  formName.value = exp.name;
  formDescription.value = exp.description ?? "";
  formStrategy.value = exp.strategy;
  formDatasetName.value = exp.datasetName ?? "";
  formSampleCount.value = exp.sampleCount;
  formPrecisionScore.value = exp.precisionScore;
  formRecallScore.value = exp.recallScore;
  formStatus.value = exp.status ?? "PLANNED";
  formNotes.value = exp.notes ?? "";
  editingId.value = exp.id;
  showForm.value = true;
}

function closeForm(): void {
  showForm.value = false;
  resetForm();
}

async function submitForm(): Promise<void> {
  const payload = {
    name: formName.value.trim(),
    description: formDescription.value.trim() || undefined,
    strategy: formStrategy.value,
    datasetName: formDatasetName.value.trim() || undefined,
    sampleCount: formSampleCount.value,
    precisionScore: formPrecisionScore.value,
    recallScore: formRecallScore.value,
    status: formStatus.value,
    notes: formNotes.value.trim() || undefined,
  };

  if (editingId.value) {
    await store.updateExp(editingId.value, payload);
  } else {
    await store.createExp(payload);
  }

  if (!store.lastError) {
    closeForm();
  }
}

async function handleEvaluate(id: string): Promise<void> {
  const runId = selectedRunIds[id];
  if (!runId) return;
  const evaluationCase = structuredCaseFor(id);
  const payload: ExperimentEvaluationRequest = {
    runId,
    expectedAnswer: expectedAnswers[id],
    ...(evaluationCase ?? {})
  };
  await store.evaluateExp(id, payload);
}

async function handleUseStructuredCase(id: string): Promise<void> {
  const runId = selectedRunIds[id];
  if (!runId) return;
  const detail = await store.loadRagRunDetail(runId);
  const topResult = detail?.retrievalResults?.[0];
  if (!topResult?.chunkId) {
    store.lastError = "所选 RAG 运行没有可用于结构化评估用例的检索片段。";
    return;
  }
  structuredCases[id] = {
    evaluationCaseId: `ui-${shortId(runId)}-top-retrieval`,
    relevantChunkIds: [topResult.chunkId],
    relevantDocumentIds: topResult.documentId ? [topResult.documentId] : [],
    expectedCitationChunkIds: [topResult.chunkId],
    evaluationTopK: 1
  };
  structuredCaseRunIds[id] = runId;
}

function clearStructuredCase(id: string): void {
  delete structuredCases[id];
  delete structuredCaseRunIds[id];
}

async function handleDelete(id: string): Promise<void> {
  if (!confirm("确定删除这个实验吗？")) return;
  await store.deleteExp(id);
}

onMounted(() => {
  store.loadRagRuns();
  store.loadExperimentEvaluationSummary();
});
</script>
