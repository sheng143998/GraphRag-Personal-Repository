<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">RAG 评估对比</h2>
        <p class="panel-subtitle">按策略、质量和运行上下文对最近的评估结果排序。</p>
      </div>

      <div class="panel-body stack">
        <div class="evaluation-dashboard">
          <div class="dashboard-metric">
            <span class="metric-label">评估次数</span>
            <strong>{{ summary.evaluationCount }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">平均可信度</span>
            <strong>{{ formatScore(summary.averageGrounded) }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">平均检索分</span>
            <strong>{{ formatScore(summary.averageRetrieval) }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">最佳实验</span>
            <strong>{{ summary.bestExperimentName ?? "待评估" }}</strong>
          </div>
        </div>

        <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        <div v-if="summary.evaluationCount === 0" class="empty-state">
          暂无已持久化的 RAG 评估记录。请先运行一次实验评估。
        </div>

        <div v-if="summary.evaluationCount > 0" class="comparison-filter-bar">
          <label class="form-row">
            <span class="form-label">策略</span>
            <select v-model="selectedStrategy" class="input">
              <option value="">全部策略</option>
              <option v-for="strategy in strategyOptions" :key="strategy" :value="strategy">
                {{ strategyLabel(strategy) }}
              </option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">实验</span>
            <select v-model="selectedExperimentId" class="input">
              <option value="">全部实验</option>
              <option v-for="experiment in experimentOptions" :key="experiment.id" :value="experiment.id">
                {{ experiment.name }}
              </option>
            </select>
          </label>
          <button class="button button-secondary" type="button" :disabled="!hasActiveFilters" @click="clearFilters">
            清除筛选
          </button>
        </div>

        <div v-if="summary.evaluationCount > 0 && filteredRows.length === 0" class="empty-state">
          当前筛选条件下没有匹配的评估记录。
        </div>

        <div v-if="summary.evaluationCount > 0 && filteredRows.length > 0" class="split-columns comparison-columns">
          <section class="comparison-section">
            <h3 class="section-title">策略排行</h3>
            <div class="comparison-list">
              <article v-for="row in strategyRows" :key="row.strategy" class="comparison-row">
                <div class="comparison-row-main">
                  <strong>{{ strategyLabel(row.strategy) }}</strong>
                  <span>{{ row.count }} 次评估</span>
                </div>
                <div class="score-bars">
                  <div class="score-bar">
                    <span>可信度</span>
                    <div class="score-track">
                      <div class="score-fill" :style="{ width: scoreWidth(row.averageGrounded) }" />
                    </div>
                    <strong>{{ formatScore(row.averageGrounded) }}</strong>
                  </div>
                  <div class="score-bar">
                    <span>检索分</span>
                    <div class="score-track">
                      <div class="score-fill score-fill-alt" :style="{ width: scoreWidth(row.averageRetrieval) }" />
                    </div>
                    <strong>{{ formatScore(row.averageRetrieval) }}</strong>
                  </div>
                </div>
                <p class="item-meta">
                  最近 {{ formatDate(row.latestAt) }}
                  <span v-if="row.averageLatencyMs != null"> | 平均延迟 {{ Math.round(row.averageLatencyMs) }}ms</span>
                  <span v-if="row.graphMetricCount"> | 图谱指标 {{ row.graphMetricCount }}</span>
                </p>
              </article>
            </div>
          </section>

          <section class="comparison-section">
            <h3 class="section-title">实验排行</h3>
            <div class="comparison-list">
              <article v-for="row in experimentRows" :key="row.experimentId" class="comparison-row">
                <div class="comparison-row-main">
                  <strong>{{ row.experimentName }}</strong>
                  <span>{{ row.count }} 次评估</span>
                </div>
                <div class="metric-list compact-metrics">
                  <div class="metric-row">
                    <span class="metric-label">质量</span>
                    <span class="metric-value">{{ formatScore(row.quality) }}</span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">可信度 / 检索分</span>
                    <span class="metric-value">{{ formatScore(row.averageGrounded) }} / {{ formatScore(row.averageRetrieval) }}</span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">最近运行</span>
                    <span class="metric-value">{{ strategyLabel(row.latestStrategy) }}</span>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </div>

        <section v-if="filteredRows.length" class="comparison-section">
          <h3 class="section-title">最近评估</h3>
          <div class="comparison-table">
            <div class="comparison-table-head">
              <span>实验</span>
              <span>策略</span>
              <span>问题</span>
              <span>分数</span>
              <span>图谱指标</span>
              <span>运行</span>
            </div>
            <div v-for="evaluation in filteredRows" :key="evaluation.id" class="comparison-table-row">
              <span>
                <strong>{{ evaluation.experimentName ?? experimentName(evaluation.experimentId) }}</strong>
                <small>{{ formatDate(evaluation.createdAt) }}</small>
              </span>
              <span>
                {{ strategyLabel(evaluation.runStrategyName) }}
                <small>{{ evaluation.runRetrieverType ?? "检索器待记录" }}</small>
              </span>
              <span>{{ summarize(evaluation.runQuestion, 110) }}</span>
              <span>
                {{ formatScore(evaluation.groundedScore) }}
                / {{ formatScore(evaluation.retrievalScore) }}
                <small v-if="evaluation.runLatencyMs != null">{{ evaluation.runLatencyMs }}ms</small>
              </span>
              <span>
                <template v-if="graphMetricSummary(evaluation)">
                  {{ graphMetricSummary(evaluation) }}
                </template>
                <template v-else>无</template>
              </span>
              <span>
                {{ shortId(evaluation.runId) }}
                <small>{{ evaluation.runModelName ?? "模型待记录" }}</small>
              </span>
            </div>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { ExperimentEvaluationHistory } from "../../types";
import { useWorkbenchStore } from "../../stores/workbench";
import { formatMetricPercent, hasGraphRagMetricNote, parseGraphRagMetricNote } from "../../utils/evaluation-notes";

const store = useWorkbenchStore();
const selectedStrategy = ref("");
const selectedExperimentId = ref("");

interface AggregateRow {
  experimentId: string;
  experimentName: string;
  strategy: string;
  count: number;
  averageGrounded?: number;
  averageRetrieval?: number;
  quality?: number;
  averageLatencyMs?: number;
  graphMetricCount: number;
  latestAt: string;
  latestStrategy: string;
}

const summary = computed(() => store.experimentEvaluationSummary);
const recentRows = computed(() => summary.value.recentEvaluations ?? []);
const filteredRows = computed(() =>
  recentRows.value.filter((evaluation) =>
    (!selectedStrategy.value || (evaluation.runStrategyName ?? "未知策略") === selectedStrategy.value)
    && (!selectedExperimentId.value || evaluation.experimentId === selectedExperimentId.value)
  )
);

const hasActiveFilters = computed(() => Boolean(selectedStrategy.value || selectedExperimentId.value));

const strategyOptions = computed(() =>
  [...new Set(recentRows.value.map((evaluation) => evaluation.runStrategyName ?? "未知策略"))]
    .sort((left, right) => left.localeCompare(right))
);

const experimentOptions = computed(() => {
  const options = new Map<string, string>();
  for (const evaluation of recentRows.value) {
    options.set(evaluation.experimentId, evaluation.experimentName ?? experimentName(evaluation.experimentId));
  }
  return [...options.entries()]
    .map(([id, name]) => ({ id, name }))
    .sort((left, right) => left.name.localeCompare(right.name));
});

const strategyRows = computed(() =>
  aggregateRows(filteredRows.value, (evaluation) => evaluation.runStrategyName ?? "未知策略")
    .sort((left, right) => (right.quality ?? 0) - (left.quality ?? 0))
);

const experimentRows = computed(() =>
  aggregateRows(filteredRows.value, (evaluation) => evaluation.experimentId)
    .sort((left, right) => (right.quality ?? 0) - (left.quality ?? 0))
);

function aggregateRows(
  evaluations: ExperimentEvaluationHistory[],
  keyFor: (evaluation: ExperimentEvaluationHistory) => string
): AggregateRow[] {
  const groups = new Map<string, ExperimentEvaluationHistory[]>();
  for (const evaluation of evaluations) {
    const key = keyFor(evaluation);
    groups.set(key, [...(groups.get(key) ?? []), evaluation]);
  }

  return [...groups.entries()].map(([key, items]) => {
    const sorted = [...items].sort((left, right) => right.createdAt.localeCompare(left.createdAt));
    const latest = sorted[0];
    const averageGrounded = averageScore(items.map((item) => item.groundedScore));
    const averageRetrieval = averageScore(items.map((item) => item.retrievalScore));

    return {
      experimentId: latest.experimentId,
      experimentName: latest.experimentName ?? experimentName(latest.experimentId),
      strategy: key,
      count: items.length,
      averageGrounded,
      averageRetrieval,
      quality: averageScore([averageGrounded, averageRetrieval]),
      averageLatencyMs: averageScore(items.map((item) => item.runLatencyMs)),
      graphMetricCount: items.filter(hasGraphRagMetricNote).length,
      latestAt: latest.createdAt,
      latestStrategy: latest.runStrategyName ?? "未知策略"
    };
  });
}

function averageScore(values: Array<number | null | undefined>): number | undefined {
  const valid = values.filter((value): value is number => value != null);
  if (valid.length === 0) return undefined;
  return valid.reduce((total, value) => total + value, 0) / valid.length;
}

function experimentName(id: string): string {
  return store.experiments.find((experiment) => experiment.id === id)?.name ?? shortId(id);
}

function formatScore(value?: number | null): string {
  if (value == null) return "待评估";
  return `${Math.round(value * 100)}%`;
}

function strategyLabel(value?: string | null): string {
  if (!value) return "未知策略";
  return store.ragStrategyOptions.find((option) => option.value === value)?.label ?? value;
}

function scoreWidth(value?: number): string {
  if (value == null) return "0%";
  return `${Math.max(0, Math.min(100, Math.round(value * 100)))}%`;
}

function summarize(value?: string | null, maxLength = 92): string {
  if (!value) return "无问题快照";
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function graphMetricSummary(evaluation: ExperimentEvaluationHistory): string | undefined {
  const metrics = parseGraphRagMetricNote(evaluation.notes);
  if (!metrics) return undefined;
  return [
    `E ${formatMetricPercent(metrics.entityCoverage)}`,
    `R ${formatMetricPercent(metrics.relationshipHit)}`,
    `X ${formatMetricPercent(metrics.expansionTermHit)}`
  ].join(" / ");
}

function shortId(value: string): string {
  return value.slice(0, 8);
}

function formatDate(value?: string | null): string {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

function clearFilters(): void {
  selectedStrategy.value = "";
  selectedExperimentId.value = "";
}

onMounted(() => {
  void store.loadExperimentEvaluationSummary(50);
});
</script>
