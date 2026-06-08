<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">RAG Experiments</h2>
        <p class="panel-subtitle">Create, compare, and evaluate RAG strategy runs.</p>
        <button class="button button-primary" type="button" @click="openCreate">
          {{ showForm && !editingId ? "Close form" : "Create experiment" }}
        </button>
      </div>

      <div class="panel-body stack">
        <div v-if="showForm" class="form-grid">
          <label class="form-row">
            <span class="form-label">Name</span>
            <input v-model="formName" class="input" placeholder="Hybrid + rerank comparison" />
          </label>
          <label class="form-row">
            <span class="form-label">Description</span>
            <textarea v-model="formDescription" class="textarea" placeholder="Experiment goal and observation notes" />
          </label>
          <label class="form-row">
            <span class="form-label">Strategy</span>
            <select v-model="formStrategy" class="input">
              <option v-for="opt in store.ragStrategyOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">Dataset</span>
            <input v-model="formDatasetName" class="input" placeholder="engineering-smoke" />
          </label>
          <label class="form-row">
            <span class="form-label">Samples</span>
            <input v-model.number="formSampleCount" class="input" type="number" min="0" />
          </label>
          <div class="form-row" style="display: flex; gap: 1rem;">
            <label style="flex: 1;">
              <span class="form-label">Precision</span>
              <input v-model.number="formPrecisionScore" class="input" type="number" min="0" max="1" step="0.01" />
            </label>
            <label style="flex: 1;">
              <span class="form-label">Recall</span>
              <input v-model.number="formRecallScore" class="input" type="number" min="0" max="1" step="0.01" />
            </label>
          </div>
          <label class="form-row">
            <span class="form-label">Status</span>
            <select v-model="formStatus" class="input">
              <option value="PLANNED">PLANNED</option>
              <option value="RUNNING">RUNNING</option>
              <option value="COMPLETED">COMPLETED</option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">Notes</span>
            <textarea v-model="formNotes" class="textarea" placeholder="Experiment notes" />
          </label>
          <div class="button-row">
            <button
              class="button button-primary"
              type="button"
              :disabled="store.experimentFormPending || !formName.trim()"
              @click="submitForm"
            >
              {{ store.experimentFormPending ? "Saving..." : editingId ? "Update experiment" : "Create experiment" }}
            </button>
            <button class="button button-secondary" type="button" @click="closeForm">Cancel</button>
          </div>
          <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        </div>

        <div v-if="store.experiments.length === 0" class="empty-state">
          No experiment records yet.
        </div>
        <div v-else class="item-list">
          <article v-for="experiment in store.experiments" :key="experiment.id" class="item-card">
            <h3 class="item-title">{{ experiment.name }}</h3>
            <div v-if="experiment.description" class="item-meta">{{ experiment.description }}</div>
            <div class="item-meta">
              {{ experiment.strategy }}
              <span v-if="experiment.status"> | {{ experiment.status }}</span>
              <span v-if="experiment.datasetName"> | {{ experiment.datasetName }}</span>
              | updated {{ experiment.updatedAt }}
            </div>

            <div class="metric-list">
              <div class="metric-row">
                <span class="metric-label">Precision</span>
                <span class="metric-value">{{ experiment.precision ?? formatScore(experiment.precisionScore) }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">Recall</span>
                <span class="metric-value">{{ experiment.recall ?? formatScore(experiment.recallScore) }}</span>
              </div>
              <div v-if="experiment.sampleCount != null" class="metric-row">
                <span class="metric-label">Samples</span>
                <span class="metric-value">{{ experiment.sampleCount }}</span>
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
                  <span class="history-run">Run {{ shortId(evaluation.runId) }}</span>
                  <span class="item-meta">{{ formatDate(evaluation.createdAt) }}</span>
                </div>
                <div class="item-meta">
                  grounded {{ formatScore(evaluation.groundedScore ?? undefined) }}
                  | retrieval {{ formatScore(evaluation.retrievalScore ?? undefined) }}
                </div>
                <div v-if="evaluation.notes" class="item-meta">{{ evaluation.notes }}</div>
              </div>
            </div>

            <div class="form-grid" style="margin-top: 0.75rem;">
              <label class="form-row">
                <span class="form-label">RAG run</span>
                <select v-model="selectedRunIds[experiment.id]" class="input">
                  <option value="">Select recent run</option>
                  <option v-for="run in store.ragRuns" :key="run.id" :value="run.id">
                    {{ runLabel(run) }}
                  </option>
                </select>
              </label>
              <label class="form-row">
                <span class="form-label">Expected answer</span>
                <textarea
                  v-model="expectedAnswers[experiment.id]"
                  class="textarea"
                  placeholder="Optional reference answer for evaluator"
                />
              </label>
            </div>

            <div class="button-row" style="margin-top: 0.75rem;">
              <button
                class="button button-primary"
                type="button"
                :disabled="store.experimentFormPending || !selectedRunIds[experiment.id]"
                @click="handleEvaluate(experiment.id)"
              >
                Evaluate
              </button>
              <button class="button button-secondary" type="button" @click="openEdit(experiment)">Edit</button>
              <button class="button button-ghost" type="button" @click="handleDelete(experiment.id)">Delete</button>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import type { ExperimentRecord, RagRunSummary } from "../../types";
import { useWorkbenchStore } from "../../stores/workbench";

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

function formatScore(value?: number): string {
  if (value == null) return "pending";
  return `${Math.round(value * 100)}%`;
}

function runLabel(run: RagRunSummary): string {
  const question = run.question.length > 64 ? `${run.question.slice(0, 64)}...` : run.question;
  return `${run.strategyName} | ${run.status} | ${question}`;
}

function shortId(value: string): string {
  return value.slice(0, 8);
}

function formatDate(value: string): string {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
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
  await store.evaluateExp(id, runId, expectedAnswers[id]);
}

async function handleDelete(id: string): Promise<void> {
  if (!confirm("Delete this experiment?")) return;
  await store.deleteExp(id);
}

onMounted(() => {
  store.loadRagRuns();
});
</script>
