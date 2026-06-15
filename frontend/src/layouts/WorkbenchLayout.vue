<template>
  <div class="coze-shell">
    <aside class="coze-global-rail">
      <RouterLink class="coze-logo" to="/chat" title="知识库工作台">
        <span>K</span>
      </RouterLink>

      <nav class="coze-global-nav" aria-label="主导航">
        <RouterLink
          v-for="item in primaryNavigation"
          :key="item.to"
          :to="item.to"
          class="coze-global-nav-item"
          :title="item.label"
        >
          <span>{{ item.icon }}</span>
        </RouterLink>
      </nav>

      <div class="coze-global-footer">
        <RouterLink class="coze-global-nav-item" to="/settings" title="系统设置">
          <span>S</span>
        </RouterLink>
      </div>
    </aside>

    <aside class="coze-sub-sidebar">
      <header class="coze-workspace-switcher">
        <span class="coze-kicker">Workspace</span>
        <strong>本地知识库 Agent</strong>
        <small>{{ store.selectedKnowledgeBase?.name ?? "默认知识库" }}</small>
      </header>

      <nav class="coze-sub-nav" aria-label="页面导航">
        <section v-for="group in navigationGroups" :key="group.name" class="coze-sub-nav-section">
          <div class="coze-sub-nav-title">{{ group.name }}</div>
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="coze-sub-nav-item"
          >
            <span class="coze-nav-mark">{{ item.icon }}</span>
            <span class="coze-nav-text">
              <strong>{{ item.label }}</strong>
              <small>{{ item.description }}</small>
            </span>
          </RouterLink>
        </section>
      </nav>

      <section class="coze-sidebar-summary">
        <div>
          <span>文档</span>
          <strong>{{ store.indexedDocuments }} / {{ store.totalDocuments }}</strong>
        </div>
        <div>
          <span>实验</span>
          <strong>{{ store.experiments.length }}</strong>
        </div>
        <div>
          <span>API</span>
          <strong>/api</strong>
        </div>
      </section>
    </aside>

    <div class="coze-main">
      <header class="coze-topbar">
        <div class="coze-topbar-title">
          <span class="coze-kicker">{{ currentSection }}</span>
          <h1>{{ currentTitle }}</h1>
          <p>{{ currentSubtitle }}</p>
        </div>
        <div class="coze-topbar-actions">
          <span class="status-pill status-muted">Trace {{ shortTraceId }}</span>
          <span class="status-pill status-success">{{ selectedStrategyLabel }}</span>
        </div>
      </header>

      <main class="coze-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import { useWorkbenchStore } from "../stores/workbench";

interface NavigationEntry {
  icon: string;
  label: string;
  to: string;
  description: string;
}

const route = useRoute();
const store = useWorkbenchStore();

const primaryNavigation: NavigationEntry[] = [
  { icon: "C", label: "对话工作台", to: "/chat", description: "Agent 问答" },
  { icon: "D", label: "文档中心", to: "/documents", description: "上传与索引" },
  { icon: "K", label: "知识库", to: "/knowledge-base", description: "空间与文档" },
  { icon: "E", label: "实验评估", to: "/experiments", description: "策略评估" },
  { icon: "G", label: "图谱事实", to: "/graph", description: "实体关系" }
];

const navigationGroups: Array<{ name: string; items: NavigationEntry[] }> = [
  {
    name: "Agent",
    items: [
      { icon: "C", label: "对话工作台", to: "/chat", description: "会话、引用、复习" },
      { icon: "F", label: "用户反馈", to: "/feedback", description: "质量反馈" }
    ]
  },
  {
    name: "Knowledge",
    items: [
      { icon: "D", label: "文档中心", to: "/documents", description: "上传与解析状态" },
      { icon: "K", label: "知识库", to: "/knowledge-base", description: "知识库管理" },
      { icon: "G", label: "图谱事实", to: "/graph", description: "GraphRAG 事实" }
    ]
  },
  {
    name: "Evaluation",
    items: [
      { icon: "E", label: "实验评估", to: "/experiments", description: "实验与 run 评分" },
      { icon: "R", label: "评估对比", to: "/experiments/comparison", description: "策略排行" }
    ]
  },
  {
    name: "System",
    items: [
      { icon: "S", label: "系统设置", to: "/settings", description: "运行配置" }
    ]
  }
];

const currentTitle = computed(() => String(route.meta.title ?? "工作台"));
const currentSubtitle = computed(() => String(route.meta.subtitle ?? "本地知识库问答与文档管理"));
const currentSection = computed(() => {
  const group = navigationGroups.find((item) =>
    item.items.some((nav) => nav.to === route.path)
  );
  return group?.name ?? "Workspace";
});
const shortTraceId = computed(() => {
  const trace = store.traceId || "trace";
  return trace.length > 22 ? `${trace.slice(0, 10)}...${trace.slice(-8)}` : trace;
});
const selectedStrategyLabel = computed(() => {
  const option = store.ragStrategyOptions.find((item) => item.value === store.selectedStrategy);
  return option?.label ?? store.selectedStrategy;
});

onMounted(() => {
  void store.hydrate();
});
</script>
