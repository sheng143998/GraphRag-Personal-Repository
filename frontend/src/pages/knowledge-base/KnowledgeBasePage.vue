<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">知识库管理</h2>
        <p class="panel-subtitle">通过 Spring API 创建、查看、更新和删除知识库记录。</p>
      </div>
      <div class="panel-body stack">
        <form class="form-grid" @submit.prevent="saveKnowledgeBase">
          <div class="split-columns">
            <label class="form-row">
              <span class="form-label">名称</span>
              <input v-model="form.name" class="input" placeholder="工程笔记" />
            </label>
            <label class="form-row">
              <span class="form-label">默认策略</span>
              <select v-model="form.defaultRagStrategy" class="select">
                <option value="">使用后端默认值</option>
                <option v-for="option in store.ragStrategyOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>

          <label class="form-row">
            <span class="form-label">描述</span>
            <textarea v-model="form.description" class="textarea" placeholder="说明这个知识库收录的内容" />
          </label>

          <div class="button-row">
            <button class="button button-primary" type="submit" :disabled="!form.name.trim()">
              {{ editingId ? "保存修改" : "创建知识库" }}
            </button>
            <button v-if="editingId" class="button button-secondary" type="button" @click="resetForm">
              取消编辑
            </button>
          </div>

          <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        </form>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">知识库列表</h2>
        <p class="panel-subtitle">详情刷新使用 GET /api/knowledge-bases/{id}，编辑和删除使用对应写接口。</p>
      </div>
      <div class="panel-body">
        <div v-if="store.knowledgeBases.length === 0" class="empty-state">
          暂无知识库。
        </div>

        <div v-else class="item-list">
          <article
            v-for="knowledgeBase in store.knowledgeBases"
            :key="knowledgeBase.id"
            class="item-card"
            :class="{ 'item-card-active': knowledgeBase.id === selectedId }"
          >
            <h3 class="item-title">{{ knowledgeBase.name }}</h3>
            <div class="item-meta">
              {{ knowledgeBase.documentCount }} 个文档 · {{ knowledgeBase.chunkCount }} 个片段 · {{ formatDate(knowledgeBase.updatedAt) }}
            </div>
            <p class="item-description">{{ knowledgeBase.description || "暂无描述" }}</p>

            <div class="button-row" style="margin-top: 0.75rem;">
              <button class="button button-secondary" type="button" @click="selectDetail(knowledgeBase.id)">
                详情
              </button>
              <button class="button button-secondary" type="button" @click="startEdit(knowledgeBase)">
                编辑
              </button>
              <button class="button button-secondary" type="button" @click="removeKnowledgeBase(knowledgeBase.id)">
                删除
              </button>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import type { KnowledgeBaseSummary } from "../../types";
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();
const editingId = ref("");
const selectedId = ref("");

const form = reactive({
  name: "",
  description: "",
  defaultRagStrategy: ""
});

function resetForm(): void {
  editingId.value = "";
  form.name = "";
  form.description = "";
  form.defaultRagStrategy = "";
}

async function saveKnowledgeBase(): Promise<void> {
  if (!form.name.trim()) {
    return;
  }

  if (editingId.value) {
    await store.updateKb(editingId.value, {
      name: form.name.trim(),
      description: form.description.trim()
    });
  } else {
    await store.createKb({
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      defaultRagStrategy: form.defaultRagStrategy || undefined
    });
  }

  if (!store.lastError) {
    resetForm();
  }
}

async function selectDetail(id: string): Promise<void> {
  selectedId.value = id;
  await store.loadKbDetail(id);
}

function startEdit(knowledgeBase: KnowledgeBaseSummary): void {
  editingId.value = knowledgeBase.id;
  selectedId.value = knowledgeBase.id;
  form.name = knowledgeBase.name;
  form.description = knowledgeBase.description ?? "";
  form.defaultRagStrategy = "";
}

async function removeKnowledgeBase(id: string): Promise<void> {
  const confirmed = window.confirm("确定删除这个知识库及其关联记录吗？");
  if (!confirmed) {
    return;
  }

  await store.deleteKb(id);
  if (selectedId.value === id) {
    selectedId.value = "";
  }
  if (editingId.value === id) {
    resetForm();
  }
}

function formatDate(value: string): string {
  if (!value) {
    return "未记录";
  }

  return value.replace("T", " ").slice(0, 19);
}
</script>
