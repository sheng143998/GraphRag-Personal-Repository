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
            <h3 class="item-title">{{ document.name }}</h3>
            <div class="item-meta">
              {{ document.documentType }} · {{ document.fileType }} · {{ document.knowledgeBaseName }} · {{ document.updatedAt }}
            </div>
            <p class="item-description">后续可扩展为切分策略、chunk 数量、解析器版本与失败原因。</p>
            <span class="status-pill" :class="statusClassMap[document.status]">
              {{ statusLabelMap[document.status] }}
            </span>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import UploadEntry from "../../components/UploadEntry.vue";
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();

const statusClassMap = {
  indexed: "status-success",
  processing: "status-warning",
  failed: "status-muted"
} as const;

const statusLabelMap = {
  indexed: "已索引",
  processing: "处理中",
  failed: "失败"
} as const;
</script>
