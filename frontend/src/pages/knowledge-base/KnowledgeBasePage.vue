<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">Knowledge Bases</h2>
        <p class="panel-subtitle">Create, inspect, update, and remove knowledge base records through the Spring API.</p>
      </div>
      <div class="panel-body stack">
        <form class="form-grid" @submit.prevent="saveKnowledgeBase">
          <div class="split-columns">
            <label class="form-row">
              <span class="form-label">Name</span>
              <input v-model="form.name" class="input" placeholder="Engineering notes" />
            </label>
            <label class="form-row">
              <span class="form-label">Default strategy</span>
              <select v-model="form.defaultRagStrategy" class="select">
                <option value="">Use backend default</option>
                <option v-for="option in store.ragStrategyOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>

          <label class="form-row">
            <span class="form-label">Description</span>
            <textarea v-model="form.description" class="textarea" placeholder="What this knowledge base contains" />
          </label>

          <div class="button-row">
            <button class="button button-primary" type="submit" :disabled="!form.name.trim()">
              {{ editingId ? "Save changes" : "Create knowledge base" }}
            </button>
            <button v-if="editingId" class="button button-secondary" type="button" @click="resetForm">
              Cancel edit
            </button>
          </div>

          <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        </form>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">Knowledge Base List</h2>
        <p class="panel-subtitle">Detail refresh uses GET /api/knowledge-bases/{id}; edit and delete use the matching write APIs.</p>
      </div>
      <div class="panel-body">
        <div v-if="store.knowledgeBases.length === 0" class="empty-state">
          No knowledge bases yet.
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
              {{ knowledgeBase.documentCount }} documents · {{ knowledgeBase.chunkCount }} chunks · {{ formatDate(knowledgeBase.updatedAt) }}
            </div>
            <p class="item-description">{{ knowledgeBase.description || "No description" }}</p>

            <div class="button-row" style="margin-top: 0.75rem;">
              <button class="button button-secondary" type="button" @click="selectDetail(knowledgeBase.id)">
                Detail
              </button>
              <button class="button button-secondary" type="button" @click="startEdit(knowledgeBase)">
                Edit
              </button>
              <button class="button button-secondary" type="button" @click="removeKnowledgeBase(knowledgeBase.id)">
                Delete
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
  const confirmed = window.confirm("Delete this knowledge base and its related records?");
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
    return "not recorded";
  }

  return value.replace("T", " ").slice(0, 19);
}
</script>
