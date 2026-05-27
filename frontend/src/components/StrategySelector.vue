<template>
  <section class="panel">
    <div class="panel-header">
      <h2 class="panel-title">RAG 策略选择</h2>
      <p class="panel-subtitle">为问答链路预留策略切换入口，后续可扩展更多检索与重排参数。</p>
    </div>
    <div class="panel-body stack">
      <label class="form-row">
        <span class="form-label">当前策略</span>
        <select v-model="store.selectedStrategy" class="select">
          <option
            v-for="option in store.ragStrategyOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </label>

      <div class="item-list">
        <article
          v-for="option in store.ragStrategyOptions"
          :key="option.value"
          class="item-card"
        >
          <h3 class="item-title">{{ option.label }}</h3>
          <p class="item-description">{{ option.description }}</p>
          <span
            class="status-pill"
            :class="option.value === store.selectedStrategy ? 'status-success' : 'status-muted'"
          >
            {{ option.value === store.selectedStrategy ? "已选中" : "可切换" }}
          </span>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useWorkbenchStore } from "../stores/workbench";

const store = useWorkbenchStore();
</script>
