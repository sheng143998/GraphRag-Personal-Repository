<template>
  <section class="panel">
    <div class="panel-header">
      <h2 class="panel-title">引用来源</h2>
      <p class="panel-subtitle">展示文档来源、命中位置与片段摘要，供后续接入真实检索结果。</p>
    </div>
    <div class="panel-body">
      <div v-if="sources.length" class="source-list">
        <article
          v-for="source in sources"
          :key="source.id"
          class="source-item"
        >
          <h3 class="source-title">{{ source.title }}</h3>
          <div class="source-meta">{{ source.location }} · {{ source.strategy }} · 得分 {{ source.score }}</div>
          <p class="source-snippet">{{ source.snippet }}</p>
        </article>
      </div>
      <div v-else class="empty-state">
        还没有检索来源。后端返回 `sources` 后，这里会直接按统一类型渲染。
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { CitationSource } from "../types";

defineProps<{
  sources: CitationSource[];
}>();
</script>
