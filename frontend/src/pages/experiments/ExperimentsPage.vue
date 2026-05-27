<template>
  <div class="page-grid">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">RAG 实验记录</h2>
        <p class="panel-subtitle">预留策略对比视图，后续可接评估集、检索日志与运行详情。</p>
      </div>
      <div class="panel-body">
        <div class="item-list">
          <article
            v-for="experiment in store.experiments"
            :key="experiment.id"
            class="item-card"
          >
            <h3 class="item-title">{{ experiment.name }}</h3>
            <div class="item-meta">{{ experiment.strategy }} · 更新于 {{ experiment.updatedAt }}</div>
            <div class="metric-list">
              <div class="metric-row">
                <span class="metric-label">Precision</span>
                <span class="metric-value">{{ experiment.precision }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">Recall</span>
                <span class="metric-value">{{ experiment.recall }}</span>
              </div>
            </div>
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
