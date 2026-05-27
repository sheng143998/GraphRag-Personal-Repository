<template>
  <div class="page-grid workbench-grid">
    <div class="stack">
      <section class="panel">
        <div class="panel-header">
          <h2 class="panel-title">工作台总览</h2>
          <p class="panel-subtitle">文档上传、策略切换、对话问答与来源引用都收在这一屏里。</p>
        </div>
        <div class="panel-body">
          <div class="summary-grid">
            <div class="summary-card">
              <span class="summary-label">知识库</span>
              <span class="summary-value">{{ store.knowledgeBases.length }}</span>
              <span class="summary-hint">{{ store.selectedKnowledgeBase?.name ?? "未配置" }}</span>
            </div>
            <div class="summary-card">
              <span class="summary-label">文档总数</span>
              <span class="summary-value">{{ store.totalDocuments }}</span>
              <span class="summary-hint">{{ store.indexedDocuments }} 份已完成索引</span>
            </div>
            <div class="summary-card">
              <span class="summary-label">当前策略</span>
              <span class="summary-value">{{ strategyLabel }}</span>
              <span class="summary-hint">支持后续扩展 Hybrid / Parent-Child / Filter</span>
            </div>
            <div class="summary-card">
              <span class="summary-label">实验记录</span>
              <span class="summary-value">{{ store.experiments.length }}</span>
              <span class="summary-hint">用于比较策略命中率与召回率</span>
            </div>
          </div>
        </div>
      </section>

      <UploadEntry />

      <section class="panel">
        <div class="panel-header">
          <h2 class="panel-title">知识库对话</h2>
          <p class="panel-subtitle">围绕已入库资料提问，并查看回答引用的来源片段。</p>
        </div>
        <div class="panel-body stack">
          <div class="chat-thread">
            <article
              v-for="message in store.messages"
              :key="message.id"
              class="message"
              :class="message.role"
            >
              <div class="message-header">
                <strong>{{ message.role === "user" ? "你" : "知识库助手" }}</strong>
                <span>{{ message.createdAt }}</span>
              </div>
              <div class="message-content">{{ message.content }}</div>
            </article>
          </div>

          <form class="form-grid" @submit.prevent="submitQuestion">
            <label class="form-row">
              <span class="form-label">提问内容</span>
              <textarea
                v-model="question"
                class="textarea"
                placeholder="例如：帮我比较 Spring 事务传播行为，并给一个面试回答框架。"
              />
            </label>
            <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
            <div class="button-row">
              <button class="button button-primary" type="submit" :disabled="store.pending">
                {{ store.pending ? "检索中..." : "发送问题" }}
              </button>
              <button class="button button-secondary" type="button" @click="fillQuestion">
                示例问题
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>

    <div class="stack">
      <StrategySelector />
      <SourceList :sources="store.latestSources" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import SourceList from "../../components/SourceList.vue";
import StrategySelector from "../../components/StrategySelector.vue";
import UploadEntry from "../../components/UploadEntry.vue";
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();
const question = ref("");

const strategyLabel = computed(() => {
  const item = store.ragStrategyOptions.find((option) => option.value === store.selectedStrategy);
  return item?.label ?? store.selectedStrategy;
});

function fillQuestion(): void {
  question.value = "帮我总结 Spring 事务传播行为的核心差异，并给一个面试回答思路。";
}

async function submitQuestion(): Promise<void> {
  await store.askQuestion(question.value);
  question.value = "";
}
</script>
