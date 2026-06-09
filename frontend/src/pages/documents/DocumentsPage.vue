<template>
  <div class="page-grid">
    <UploadEntry />

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">文档列表</h2>
        <p class="panel-subtitle">跟踪处理状态、查看文档详情，并清理不再需要的上传记录。</p>
      </div>
      <div class="panel-body">
        <div v-if="store.documents.length === 0" class="empty-state">
          暂无文档。
        </div>

        <div v-else class="item-list">
          <article
            v-for="document in store.documents"
            :key="document.id"
            class="item-card"
            :class="{ 'item-card-active': selectedDocument?.id === document.id }"
          >
            <h3 class="item-title">{{ document.title }}</h3>
            <div class="item-meta">
              {{ document.documentType }} · {{ document.fileType || "未知类型" }} · {{ document.knowledgeBaseName }} · {{ formatDate(document.updatedAt) }}
            </div>
            <p class="item-description">
              {{ document.fileName }} · {{ document.chunkCount ?? 0 }} 个片段 · {{ parserLabel(document) }}
            </p>
            <span class="status-pill" :class="statusClass(document.status)">
              <span v-if="document.status === 'PROCESSING'" class="processing-spinner"></span>
              {{ statusLabel(document.status) }}
            </span>

            <div class="button-row" style="margin-top: 0.75rem;">
              <button class="button button-secondary" type="button" @click="loadDetail(document.id)">
                详情
              </button>
              <button class="button button-secondary" type="button" @click="deleteSelected(document.id)">
                删除
              </button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section v-if="selectedDocument" class="panel">
      <div class="panel-header">
        <h2 class="panel-title">文档详情</h2>
        <p class="panel-subtitle">{{ selectedDocument.title }}</p>
      </div>
      <div class="panel-body stack">
        <div class="summary-grid">
          <div class="summary-card">
            <span class="summary-label">状态</span>
            <span class="summary-value">{{ statusLabel(selectedDocument.status) }}</span>
            <span class="summary-hint">{{ formatDate(selectedDocument.updatedAt) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">片段</span>
            <span class="summary-value">{{ selectedDocument.chunkCount ?? selectedDocument.chunks?.length ?? 0 }}</span>
            <span class="summary-hint">{{ parserLabel(selectedDocument) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">来源</span>
            <span class="summary-value">{{ selectedDocument.sourceType || "未知来源" }}</span>
            <span class="summary-hint">{{ selectedDocument.sourcePath || selectedDocument.fileName }}</span>
          </div>
        </div>

        <p v-if="selectedDocument.summary" class="item-description">{{ selectedDocument.summary }}</p>
        <pre v-if="selectedDocument.metadata" class="metadata-block">{{ selectedDocument.metadata }}</pre>

        <div v-if="!selectedDocument.chunks?.length" class="empty-state">
          当前文档暂无片段详情。
        </div>

        <div v-else class="item-list">
          <article v-for="chunk in selectedDocument.chunks" :key="chunk.id" class="item-card">
            <h3 class="item-title">片段 {{ chunk.chunkIndex }}{{ chunk.title ? ` · ${chunk.title}` : "" }}</h3>
            <div class="item-meta">
              {{ chunk.chunkStrategy || "未知策略" }}
              <span v-if="chunk.pageNumber"> · 第 {{ chunk.pageNumber }} 页</span>
              <span v-if="chunk.sheetName"> · 工作表 {{ chunk.sheetName }}</span>
              <span v-if="chunk.rowRange"> · 行 {{ chunk.rowRange }}</span>
            </div>
            <p class="item-description">{{ chunk.contentPreview }}</p>
            <pre v-if="chunk.metadata" class="metadata-block">{{ chunk.metadata }}</pre>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import UploadEntry from "../../components/UploadEntry.vue";
import type { DocumentRecord } from "../../types";
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();
const selectedDocument = ref<DocumentRecord | null>(null);

const statusClassMap = {
  INDEXED: "status-success",
  UPLOADED: "status-warning",
  PROCESSING: "status-warning",
  FAILED: "status-muted"
} as const;

const statusLabelMap = {
  INDEXED: "已索引",
  UPLOADED: "已上传",
  PROCESSING: "处理中",
  FAILED: "失败"
} as const;

type StatusKey = keyof typeof statusClassMap;

function isStatusKey(value: string): value is StatusKey {
  return value in statusClassMap;
}

function statusClass(status: string): string {
  return isStatusKey(status) ? statusClassMap[status] : "status-muted";
}

function statusLabel(status: string): string {
  return isStatusKey(status) ? statusLabelMap[status] : status;
}

async function loadDetail(id: string): Promise<void> {
  selectedDocument.value = await store.loadDocumentDetail(id);
}

async function deleteSelected(id: string): Promise<void> {
  const confirmed = window.confirm("确定删除这个文档及其片段吗？");
  if (!confirmed) {
    return;
  }

  await store.removeDocument(id);
  if (selectedDocument.value?.id === id) {
    selectedDocument.value = null;
  }
}

function parserLabel(document: DocumentRecord): string {
  if (!document.parserName) {
    return "未记录解析器";
  }

  return document.parserVersion ? `${document.parserName} ${document.parserVersion}` : document.parserName;
}

function formatDate(value: string): string {
  if (!value) {
    return "未记录";
  }

  return value.replace("T", " ").slice(0, 19);
}
</script>

<style scoped>
.processing-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--bg-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
  vertical-align: middle;
}

.metadata-block {
  margin: 0;
  padding: 0.75rem;
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-muted);
  background: rgba(15, 23, 42, 0.6);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
