<template>
  <div class="page-grid">
    <UploadEntry />

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">Documents</h2>
        <p class="panel-subtitle">Track processing state, inspect document detail, and remove stale uploads.</p>
      </div>
      <div class="panel-body">
        <div v-if="store.documents.length === 0" class="empty-state">
          No documents yet.
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
              {{ document.documentType }} · {{ document.fileType || "unknown" }} · {{ document.knowledgeBaseName }} · {{ formatDate(document.updatedAt) }}
            </div>
            <p class="item-description">
              {{ document.fileName }} · {{ document.chunkCount ?? 0 }} chunks · {{ parserLabel(document) }}
            </p>
            <span class="status-pill" :class="statusClassMap[document.status]">
              <span v-if="document.status === 'PROCESSING'" class="processing-spinner"></span>
              {{ statusLabelMap[document.status] ?? document.status }}
            </span>

            <div class="button-row" style="margin-top: 0.75rem;">
              <button class="button button-secondary" type="button" @click="loadDetail(document.id)">
                Detail
              </button>
              <button class="button button-secondary" type="button" @click="deleteSelected(document.id)">
                Delete
              </button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section v-if="selectedDocument" class="panel">
      <div class="panel-header">
        <h2 class="panel-title">Document Detail</h2>
        <p class="panel-subtitle">{{ selectedDocument.title }}</p>
      </div>
      <div class="panel-body stack">
        <div class="summary-grid">
          <div class="summary-card">
            <span class="summary-label">Status</span>
            <span class="summary-value">{{ selectedDocument.status }}</span>
            <span class="summary-hint">{{ formatDate(selectedDocument.updatedAt) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">Chunks</span>
            <span class="summary-value">{{ selectedDocument.chunkCount ?? selectedDocument.chunks?.length ?? 0 }}</span>
            <span class="summary-hint">{{ parserLabel(selectedDocument) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">Source</span>
            <span class="summary-value">{{ selectedDocument.sourceType || "unknown" }}</span>
            <span class="summary-hint">{{ selectedDocument.sourcePath || selectedDocument.fileName }}</span>
          </div>
        </div>

        <p v-if="selectedDocument.summary" class="item-description">{{ selectedDocument.summary }}</p>
        <pre v-if="selectedDocument.metadata" class="metadata-block">{{ selectedDocument.metadata }}</pre>

        <div v-if="!selectedDocument.chunks?.length" class="empty-state">
          No chunk detail returned for this document.
        </div>

        <div v-else class="item-list">
          <article v-for="chunk in selectedDocument.chunks" :key="chunk.id" class="item-card">
            <h3 class="item-title">Chunk {{ chunk.chunkIndex }}{{ chunk.title ? ` · ${chunk.title}` : "" }}</h3>
            <div class="item-meta">
              {{ chunk.chunkStrategy || "strategy unknown" }}
              <span v-if="chunk.pageNumber"> · page {{ chunk.pageNumber }}</span>
              <span v-if="chunk.sheetName"> · sheet {{ chunk.sheetName }}</span>
              <span v-if="chunk.rowRange"> · rows {{ chunk.rowRange }}</span>
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
  INDEXED: "Indexed",
  UPLOADED: "Uploaded",
  PROCESSING: "Processing",
  FAILED: "Failed"
} as const;

async function loadDetail(id: string): Promise<void> {
  selectedDocument.value = await store.loadDocumentDetail(id);
}

async function deleteSelected(id: string): Promise<void> {
  const confirmed = window.confirm("Delete this document and its chunks?");
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
    return "parser not recorded";
  }

  return document.parserVersion ? `${document.parserName} ${document.parserVersion}` : document.parserName;
}

function formatDate(value: string): string {
  if (!value) {
    return "not recorded";
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
