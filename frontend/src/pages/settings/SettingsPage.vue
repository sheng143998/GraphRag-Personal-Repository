<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">系统设置</h2>
        <p class="panel-subtitle">本地配置项保存于浏览器本地存储，无需后端持久化接口。</p>
      </div>
      <div class="panel-body">
        <div class="form-grid">
          <label class="form-row">
            <span class="form-label">API Base URL</span>
            <input v-model="local.apiBaseUrl" class="input" placeholder="/api" />
          </label>
          <label class="form-row">
            <span class="form-label">AI Service Base URL</span>
            <input v-model="local.aiServiceBaseUrl" class="input" placeholder="http://localhost:8001" />
          </label>
          <label class="form-row">
            <span class="form-label">默认知识库</span>
            <select v-model="local.defaultKnowledgeBaseId" class="input">
              <option value="">— 未选择 —</option>
              <option v-for="kb in store.knowledgeBases" :key="kb.id" :value="kb.id">
                {{ kb.name }}
              </option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">请求超时 (ms)</span>
            <input v-model.number="local.timeoutMs" class="input" type="number" min="1000" max="60000" step="1000" />
          </label>
          <label class="form-row" style="flex-direction: row; align-items: center; gap: 0.75rem;">
            <input v-model="local.includeTraceHeader" type="checkbox" />
            <span class="form-label">附带 X-Trace-Id 请求头</span>
          </label>
          <div class="tag-row">
            <span class="tag">统一 API Client</span>
            <span class="tag">Trace Header</span>
            <span class="tag">本地持久化</span>
          </div>
          <div class="button-row">
            <button class="button button-primary" type="button" @click="saveSettings">
              保存设置
            </button>
            <span v-if="saved" class="item-meta" style="margin-left: 0.75rem;">已保存</span>
          </div>
          <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { useWorkbenchStore } from "../../stores/workbench";

const STORAGE_KEY = "agent-knowledge-settings";

const store = useWorkbenchStore();
const saved = ref(false);

const local = reactive({
  apiBaseUrl: store.settings.apiBaseUrl,
  aiServiceBaseUrl: store.settings.aiServiceBaseUrl,
  defaultKnowledgeBaseId: store.settings.defaultKnowledgeBaseId,
  timeoutMs: store.settings.timeoutMs,
  includeTraceHeader: store.settings.includeTraceHeader,
});

// 拉取到新 settings 时同步到本地表单
watch(() => store.settings, (s) => {
  local.apiBaseUrl = s.apiBaseUrl;
  local.aiServiceBaseUrl = s.aiServiceBaseUrl;
  local.defaultKnowledgeBaseId = s.defaultKnowledgeBaseId;
  local.timeoutMs = s.timeoutMs;
  local.includeTraceHeader = s.includeTraceHeader;
}, { deep: true });

function saveSettings(): void {
  const payload = {
    apiBaseUrl: local.apiBaseUrl,
    aiServiceBaseUrl: local.aiServiceBaseUrl,
    defaultKnowledgeBaseId: local.defaultKnowledgeBaseId,
    timeoutMs: local.timeoutMs,
    includeTraceHeader: local.includeTraceHeader,
  };
  store.settings.apiBaseUrl = payload.apiBaseUrl;
  store.settings.aiServiceBaseUrl = payload.aiServiceBaseUrl;
  store.settings.defaultKnowledgeBaseId = payload.defaultKnowledgeBaseId;
  store.settings.timeoutMs = payload.timeoutMs;
  store.settings.includeTraceHeader = payload.includeTraceHeader;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  saved.value = true;
  setTimeout(() => { saved.value = false; }, 2000);
}
</script>
