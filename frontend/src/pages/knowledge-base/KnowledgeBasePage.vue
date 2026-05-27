<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">知识库概览</h2>
        <p class="panel-subtitle">用于承接知识库列表、描述、文档规模与最近更新时间。</p>
      </div>
      <div class="panel-body">
        <div class="item-list">
          <article
            v-for="knowledgeBase in store.knowledgeBases"
            :key="knowledgeBase.id"
            class="item-card"
          >
            <h3 class="item-title">{{ knowledgeBase.name }}</h3>
            <div class="item-meta">
              {{ knowledgeBase.documentCount }} 份文档 · {{ knowledgeBase.chunkCount }} 个 chunks · {{ knowledgeBase.updatedAt }}
            </div>
            <p class="item-description">{{ knowledgeBase.description }}</p>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();
</script>
