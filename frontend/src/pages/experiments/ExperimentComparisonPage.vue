<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">RAG Evaluation Comparison</h2>
        <p class="panel-subtitle">Rank recent evaluation results by strategy, quality, and run context.</p>
      </div>

      <div class="panel-body stack">
        <div class="evaluation-dashboard">
          <div class="dashboard-metric">
            <span class="metric-label">Evaluations</span>
            <strong>{{ summary.evaluationCount }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">Avg grounded</span>
            <strong>{{ formatScore(summary.averageGrounded) }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">Avg retrieval</span>
            <strong>{{ formatScore(summary.averageRetrieval) }}</strong>
          </div>
          <div class="dashboard-metric">
            <span class="metric-label">Best experiment</span>
            <strong>{{ summary.bestExperimentName ?? "pending" }}</strong>
          </div>
        </div>

        <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        <div v-if="summary.evaluationCount === 0" class="empty-state">
          No persisted RAG evaluations yet. Run an experiment evaluation first.
        </div>

        <div v-if="summary.evaluationCount > 0" class="comparison-filter-bar">
          <label class="form-row">
            <span class="form-label">Strategy</span>
            <select v-model="selectedStrategy" class="input">
              <option value="">All strategies</option>
              <option v-for="strategy in strategyOptions" :key="strategy" :value="strategy">
                {{ strategy }}
              </option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">Experiment</span>
            <select v-model="selectedExperimentId" class="input">
              <option value="">All experiments</option>
              <option v-for="experiment in experimentOptions" :key="experiment.id" :value="experiment.id">
                {{ experiment.name }}
              </option>
            </select>
          </label>
          <button class="button button-secondary" type="button" :disabled="!hasActiveFilters" @click="clearFilters">
            Clear filters
          </button>
        </div>

        <div v-if="summary.evaluationCount > 0 && filteredRows.length === 0" class="empty-state">
          No evaluations match the current filters.
        </div>

        <div v-if="summary.evaluationCount > 0 && filteredRows.length > 0" class="split-columns comparison-columns">
          <section class="comparison-section">
            <h3 class="section-title">Strategy Ranking</h3>
            <div class="comparison-list">
              <article v-for="row in strategyRows" :key="row.strategy" class="comparison-row">
                <div class="comparison-row-main">
                  <strong>{{ row.strategy }}</strong>
                  <span>{{ row.count }} evals</span>
                </div>
                <div class="score-bars">
                  <div class="score-bar">
                    <span>Grounded</span>
                    <div class="score-track">
                      <div class="score-fill" :style="{ width: scoreWidth(row.averageGrounded) }" />
                    </div>
                    <strong>{{ formatScore(row.averageGrounded) }}</strong>
                  </div>
                  <div class="score-bar">
                    <span>Retrieval</span>
                    <div class="score-track">
                      <div class="score-fill score-fill-alt" :style="{ width: scoreWidth(row.averageRetrieval) }" />
                    </div>
                    <strong>{{ formatScore(row.averageRetrieval) }}</strong>
                  </div>
                </div>
                <p class="item-meta">
                  Latest {{ formatDate(row.latestAt) }}
                  <span v-if="row.averageLatencyMs != null"> | avg latency {{ Math.round(row.averageLatencyMs) }}ms</span>
                </p>
              </article>
            </div>
          </section>

          <section class="comparison-section">
            <h3 class="section-title">Experiment Ranking</h3>
            <div class="comparison-list">
              <article v-for="row in experimentRows" :key="row.experimentId" class="comparison-row">
                <div class="comparison-row-main">
                  <strong>{{ row.experimentName }}</strong>
                  <span>{{ row.count }} evals</span>
                </div>
                <div class="metric-list compact-metrics">
                  <div class="metric-row">
                    <span class="metric-label">Quality</span>
                    <span class="metric-value">{{ formatScore(row.quality) }}</span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">Grounded / Retrieval</span>
                    <span class="metric-value">{{ formatScore(row.averageGrounded) }} / {{ formatScore(row.averageRetrieval) }}</span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">Latest run</span>
                    <span class="metric-value">{{ row.latestStrategy }}</span>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </div>

        <section v-if="filteredRows.length" class="comparison-section">
          <h3 class="section-title">Recent Evaluations</h3>
          <div class="comparison-table">
            <div class="comparison-table-head">
              <span>Experiment</span>
              <span>Strategy</span>
              <span>Question</span>
              <span>Scores</span>
              <span>Run</span>
            </div>
            <div v-for="evaluation in filteredRows" :key="evaluation.id" class="comparison-table-row">
              <span>
                <strong>{{ evaluation.experimentName ?? experimentName(evaluation.experimentId) }}</strong>
                <small>{{ formatDate(evaluation.createdAt) }}</small>
              </span>
              <span>
                {{ evaluation.runStrategyName ?? "unknown" }}
                <small>{{ evaluation.runRetrieverType ?? "retriever pending" }}</small>
              </span>
              <span>{{ summarize(evaluation.runQuestion, 110) }}</span>
              <span>
                {{ formatScore(evaluation.groundedScore) }}
                / {{ formatScore(evaluation.retrievalScore) }}
                <small v-if="evaluation.runLatencyMs != null">{{ evaluation.runLatencyMs }}ms</small>
              </span>
              <span>
                {{ shortId(evaluation.runId) }}
                <small>{{ evaluation.runModelName ?? "model pending" }}</small>
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
  latestAt: string;
  latestStrategy: string;
}

const summary = computed(() => store.experimentEvaluationSummary);
const recentRows = computed(() => summary.value.recentEvaluations ?? []);
const filteredRows = computed(() =>
  recentRows.value.filter((evaluation) =>
    (!selectedStrategy.value || (evaluation.runStrategyName ?? "unknown") === selectedStrategy.value)
    && (!selectedExperimentId.value || evaluation.experimentId === selectedExperimentId.value)
  )
);

const hasActiveFilters = computed(() => Boolean(selectedStrategy.value || selectedExperimentId.value));

const strategyOptions = computed(() =>
  [...new Set(recentRows.value.map((evaluation) => evaluation.runStrategyName ?? "unknown"))]
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
  aggregateRows(filteredRows.value, (evaluation) => evaluation.runStrategyName ?? "unknown")
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
      latestAt: latest.createdAt,
      latestStrategy: latest.runStrategyName ?? "unknown"
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
  if (value == null) return "pending";
  return `${Math.round(value * 100)}%`;
}

function scoreWidth(value?: number): string {
  if (value == null) return "0%";
  return `${Math.max(0, Math.min(100, Math.round(value * 100)))}%`;
}

function summarize(value?: string | null, maxLength = 92): string {
  if (!value) return "No question snapshot";
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
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
