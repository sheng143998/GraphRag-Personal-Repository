<template>
  <div class="page-grid">
    <UploadEntry />

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">文档处理状态</h2>
        <p class="panel-subtitle">为解析中、已索引、失败状态预留展示区。</p>
      </div>
      <div class="panel-body">
        <div class="item-list">
          <article
            v-for="document in store.documents"
            :key="document.id"
            class="item-card"
          >
            <h3 class="item-title">{{ document.title }}</h3>
            <div class="item-meta">
              {{ document.documentType }} · {{ document.fileType || "unknown" }} · {{ document.knowledgeBaseName }} · {{ formatDate(document.updatedAt) }}
            </div>
            <p class="item-description">
              {{ document.fileName }} · {{ document.chunkCount ?? 0 }} chunks · {{ parserLabel(document) }}
            </p>
            <span class="status-pill" :class="statusClassMap[document.status]">
              {{ statusLabelMap[document.status] ?? document.status }}
            </span>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import UploadEntry from "../../components/UploadEntry.vue";
import type { DocumentRecord } from "../../types";
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();

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

function parserLabel(document: DocumentRecord): string {
  if (!document.parserName) {
    return "解析器待记录";
  }

  return document.parserVersion ? `${document.parserName} ${document.parserVersion}` : document.parserName;
}

function formatDate(value: string): string {
  if (!value) {
    return "时间待记录";
  }

  return value.replace("T", " ").slice(0, 19);
}
</script>
