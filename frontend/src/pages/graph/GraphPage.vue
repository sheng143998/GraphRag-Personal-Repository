<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">图谱事实</h2>
          <p class="panel-subtitle">查看 AI 服务从文档切片中沉淀的实体与关系，辅助 GraphRAG 检索调试。</p>
        </div>
      </div>

      <div class="panel-body stack">
        <div class="form-grid">
          <label class="form-row">
            <span class="form-label">知识库</span>
            <select v-model="selectedKnowledgeBaseId" class="input">
              <option v-for="kb in store.knowledgeBases" :key="kb.id" :value="kb.id">
                {{ kb.name }}
              </option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">实体过滤</span>
            <input v-model="entityFilter" class="input" placeholder="例如 GraphRAG、RAG、实体名" @keyup.enter="loadFacts" />
          </label>
          <div class="button-row">
            <button class="button button-primary" type="button" :disabled="loading || !selectedKnowledgeBaseId" @click="loadFacts">
              {{ loading ? "加载中..." : "刷新图谱" }}
            </button>
            <button class="button button-secondary" type="button" @click="clearFilter">清空过滤</button>
          </div>
        </div>

        <div v-if="error" class="empty-state">{{ error }}</div>

        <div v-if="facts" class="metric-list">
          <div class="metric-row">
            <span class="metric-label">实体数量</span>
            <span class="metric-value">{{ facts.entityCount }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">关系数量</span>
            <span class="metric-value">{{ facts.relationshipCount }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">过滤条件</span>
            <span class="metric-value">{{ facts.entity || "全部" }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">实体</h2>
          <p class="panel-subtitle">按入库时间展示最近 100 个图谱实体。</p>
        </div>
      </div>
      <div class="panel-body stack">
        <div v-if="!facts || facts.entities.length === 0" class="empty-state">暂无实体事实。</div>
        <div v-else class="item-list">
          <article v-for="entity in facts.entities" :key="entity.id" class="item-card">
            <h3 class="item-title">{{ entity.name }}</h3>
            <div class="item-meta">{{ entity.entityType }} · {{ entity.normalizedName }}</div>
            <div class="item-meta">
              文档 {{ shortId(entity.documentId) }} · Chunk {{ shortId(entity.chunkId) }}
            </div>
            <div v-if="formatAliases(entity.aliases)" class="item-meta">
              aliases: {{ formatAliases(entity.aliases) }}
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">关系</h2>
          <p class="panel-subtitle">按入库时间展示最近 100 条实体关系。</p>
        </div>
      </div>
      <div class="panel-body stack">
        <div v-if="!facts || facts.relationships.length === 0" class="empty-state">暂无关系事实。</div>
        <div v-else class="item-list">
          <article v-for="relationship in facts.relationships" :key="relationship.id" class="item-card">
            <h3 class="item-title">{{ relationship.sourceName }} → {{ relationship.targetName }}</h3>
            <div class="item-meta">{{ relationship.relationType }} · confidence {{ formatConfidence(relationship.confidence) }}</div>
            <div class="item-meta">
              文档 {{ shortId(relationship.documentId) }} · Chunk {{ shortId(relationship.chunkId) }}
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { fetchGraphFacts } from "../../api";
import { useWorkbenchStore } from "../../stores/workbench";
import type { GraphFactsResponse } from "../../types";

const store = useWorkbenchStore();

const selectedKnowledgeBaseId = ref("");
const entityFilter = ref("");
const facts = ref<GraphFactsResponse | null>(null);
const loading = ref(false);
const error = ref("");

watch(
  () => store.selectedKnowledgeBase?.id,
  (id) => {
    if (!selectedKnowledgeBaseId.value && id) {
      selectedKnowledgeBaseId.value = id;
      void loadFacts();
    }
  },
  { immediate: true }
);

onMounted(async () => {
  if (store.knowledgeBases.length === 0) {
    await store.hydrate();
  }
  selectedKnowledgeBaseId.value = selectedKnowledgeBaseId.value || store.selectedKnowledgeBase?.id || store.knowledgeBases[0]?.id || "";
  if (selectedKnowledgeBaseId.value) {
    await loadFacts();
  }
});

async function loadFacts(): Promise<void> {
  if (!selectedKnowledgeBaseId.value) {
    error.value = "请先选择知识库。";
    return;
  }

  loading.value = true;
  error.value = "";
  try {
    facts.value = await fetchGraphFacts(selectedKnowledgeBaseId.value, entityFilter.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载图谱事实失败。";
  } finally {
    loading.value = false;
  }
}

function clearFilter(): void {
  entityFilter.value = "";
  void loadFacts();
}

function shortId(value?: string | null): string {
  if (!value) return "-";
  return value.slice(0, 8);
}

function formatConfidence(value?: number): string {
  if (value == null) return "-";
  return value.toFixed(2);
}

function formatAliases(value: unknown): string {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "string") {
    return value;
  }
  return "";
}
</script>
