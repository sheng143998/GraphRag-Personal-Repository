<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand-block">
        <div class="brand-logo">K</div>
        <div class="brand-title">知识库工作台</div>
        <div class="brand-subtitle">Vue 3 + Spring Boot + FastAPI</div>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="nav-link"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <strong>接口约束</strong>
        <span>页面不直接请求后端，统一经由 src/api/。</span>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div>
          <h1 class="page-title">{{ currentTitle }}</h1>
          <p class="page-subtitle">{{ currentSubtitle }}</p>
        </div>
        <div class="topbar-actions">
          <span class="status-pill status-muted">追踪 {{ store.traceId }}</span>
          <span class="status-pill status-success">{{ selectedStrategyLabel }}</span>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import type { NavigationItem } from "../types";
import { useWorkbenchStore } from "../stores/workbench";

const route = useRoute();
const store = useWorkbenchStore();

const navigation: NavigationItem[] = [
  { label: "对话工作台", to: "/chat", description: "问答与引用来源" },
  { label: "文档中心", to: "/documents", description: "上传与处理状态" },
  { label: "知识库", to: "/knowledge-base", description: "知识库概览" },
  { label: "实验评估", to: "/experiments", description: "策略对比" },
  { label: "评估对比", to: "/experiments/comparison", description: "RAG 评估聚合" },
  { label: "图谱事实", to: "/graph", description: "实体与关系" },
  { label: "用户反馈", to: "/feedback", description: "提交与查看反馈" },
  { label: "系统设置", to: "/settings", description: "接口和默认参数" },
];

const currentTitle = computed(() => String(route.meta.title ?? "工作台"));
const currentSubtitle = computed(() => String(route.meta.subtitle ?? "本地知识库问答与文档管理"));
const selectedStrategyLabel = computed(() => {
  const option = store.ragStrategyOptions.find((item) => item.value === store.selectedStrategy);
  return option?.label ?? store.selectedStrategy;
});

onMounted(() => {
  void store.hydrate();
});
</script>
