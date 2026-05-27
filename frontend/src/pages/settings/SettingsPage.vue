<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">接口与默认参数</h2>
        <p class="panel-subtitle">集中展示 API client 的关键配置，方便后续接环境变量与认证信息。</p>
      </div>
      <div class="panel-body">
        <div class="form-grid">
          <label class="form-row">
            <span class="form-label">API Base URL</span>
            <input :value="store.settings.apiBaseUrl" class="input" readonly />
          </label>
          <label class="form-row">
            <span class="form-label">默认知识库</span>
            <input :value="store.settings.defaultKnowledgeBaseId" class="input" readonly />
          </label>
          <label class="form-row">
            <span class="form-label">请求超时</span>
            <input :value="`${store.settings.timeoutMs} ms`" class="input" readonly />
          </label>
          <div class="tag-row">
            <span class="tag">统一 API Client</span>
            <span class="tag">Trace Header</span>
            <span class="tag">错误结构预留</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();
</script>
