<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">RAG 实验记录</h2>
        <p class="panel-subtitle">创建、编辑和对比 RAG 策略实验，记录命中率与召回率变化。</p>
        <button class="button button-primary" type="button" @click="openCreate">
          {{ showForm && !editingId ? "收起表单" : "创建实验" }}
        </button>
      </div>
      <div class="panel-body stack">
        <!-- 实验表单 -->
        <div v-if="showForm" class="form-grid">
          <label class="form-row">
            <span class="form-label">实验名称</span>
            <input v-model="formName" class="input" placeholder="例如：Hybrid + Rerank 对比实验" />
          </label>
          <label class="form-row">
            <span class="form-label">描述</span>
            <textarea v-model="formDescription" class="textarea" placeholder="实验目的和预期收益" />
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
            <span class="form-label">数据集名称</span>
            <input v-model="formDatasetName" class="input" placeholder="例如：engineering-smoke" />
          </label>
          <label class="form-row">
            <span class="form-label">样本数量</span>
            <input v-model.number="formSampleCount" class="input" type="number" min="0" />
          </label>
          <div class="form-row" style="display: flex; gap: 1rem;">
            <label style="flex: 1;">
              <span class="form-label">Precision 分数</span>
              <input v-model.number="formPrecisionScore" class="input" type="number" min="0" max="1" step="0.01" placeholder="0.00 ~ 1.00" />
            </label>
            <label style="flex: 1;">
              <span class="form-label">Recall 分数</span>
              <input v-model.number="formRecallScore" class="input" type="number" min="0" max="1" step="0.01" placeholder="0.00 ~ 1.00" />
            </label>
          </div>
          <label class="form-row">
            <span class="form-label">状态</span>
            <select v-model="formStatus" class="input">
              <option value="PLANNED">PLANNED</option>
              <option value="RUNNING">RUNNING</option>
              <option value="COMPLETED">COMPLETED</option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">备注</span>
            <textarea v-model="formNotes" class="textarea" placeholder="实验观察和总结" />
          </label>
          <div class="button-row">
            <button
              class="button button-primary"
              type="button"
              :disabled="store.experimentFormPending || !formName.trim()"
              @click="submitForm"
            >
              {{ store.experimentFormPending ? "提交中..." : editingId ? "更新实验" : "创建实验" }}
            </button>
            <button class="button button-secondary" type="button" @click="closeForm">取消</button>
          </div>
          <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        </div>

        <!-- 实验列表 -->
        <div v-if="store.experiments.length === 0" class="empty-state">
          暂无实验记录，点击上方按钮创建第一个实验。
        </div>
        <div v-else class="item-list">
          <article
            v-for="experiment in store.experiments"
            :key="experiment.id"
            class="item-card"
          >
            <h3 class="item-title">{{ experiment.name }}</h3>
            <div v-if="experiment.description" class="item-meta">{{ experiment.description }}</div>
            <div class="item-meta">
              {{ experiment.strategy }}
              <span v-if="experiment.status"> · {{ experiment.status }}</span>
              <span v-if="experiment.datasetName"> · {{ experiment.datasetName }}</span>
              · 更新于 {{ experiment.updatedAt }}
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
                <span class="metric-label">样本数</span>
                <span class="metric-value">{{ experiment.sampleCount }}</span>
              </div>
            </div>
            <div v-if="experiment.notes" class="item-meta" style="margin-top: 0.5rem;">{{ experiment.notes }}</div>
            <div class="button-row" style="margin-top: 0.75rem;">
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
import { ref } from "vue";
import type { ExperimentRecord } from "../../types";
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

function formatScore(value?: number): string {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
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

async function handleDelete(id: string): Promise<void> {
  if (!confirm("确认删除这条实验记录？")) return;
  await store.deleteExp(id);
}
</script>
