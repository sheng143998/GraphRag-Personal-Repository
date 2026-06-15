<template>
  <div class="page-grid coze-two-column">
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">用户反馈</h2>
        <p class="panel-subtitle">提交 RAG 回答质量反馈，帮助持续优化检索策略与生成质量。</p>
      </div>
      <div class="panel-body">
        <div class="form-grid">
          <label class="form-row">
            <span class="form-label">关联运行 ID</span>
            <input v-model="form.runId" class="input" placeholder="RAG 运行 UUID，可为空" />
          </label>
          <label class="form-row">
            <span class="form-label">关联会话 ID</span>
            <input v-model="form.sessionId" class="input" placeholder="会话 UUID，可为空" />
          </label>
          <label class="form-row">
            <span class="form-label">关联消息 ID</span>
            <input v-model="form.messageId" class="input" placeholder="消息 UUID，可为空" />
          </label>
          <label class="form-row">
            <span class="form-label">评分</span>
            <select v-model.number="form.rating" class="input">
              <option v-for="n in 5" :key="n" :value="n">{{ n }} 分</option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">反馈类型</span>
            <select v-model="form.feedbackType" class="input">
              <option value="answer_quality">回答质量</option>
              <option value="retrieval_relevance">检索相关性</option>
              <option value="citation_accuracy">引用准确性</option>
              <option value="usability">使用体验</option>
            </select>
          </label>
          <label class="form-row">
            <span class="form-label">备注</span>
            <textarea v-model="form.comment" class="textarea" placeholder="可选：补充具体说明或建议" />
          </label>
          <div class="button-row">
            <button
              class="button button-primary"
              type="button"
              :disabled="store.feedbackPending || !form.feedbackType"
              @click="submitForm"
            >
              {{ store.feedbackPending ? "提交中..." : "提交反馈" }}
            </button>
          </div>
          <div v-if="store.lastError" class="empty-state">{{ store.lastError }}</div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">{{ store.lastFeedback ? "最近提交" : "反馈上下文" }}</h2>
      </div>
      <div class="panel-body">
        <article v-if="store.lastFeedback" class="item-card">
          <h3 class="item-title">{{ store.lastFeedback.feedbackType }} · {{ store.lastFeedback.rating }} 分</h3>
          <div class="item-meta">ID: {{ store.lastFeedback.id }} · {{ store.lastFeedback.createdAt }}</div>
          <div v-if="store.lastFeedback.comment" class="item-meta" style="margin-top: 0.5rem;">
            {{ store.lastFeedback.comment }}
          </div>
        </article>
        <div v-else class="metric-list">
          <div class="metric-row">
            <span class="metric-label">默认评分</span>
            <span class="metric-value">{{ form.rating }} 分</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">反馈类型</span>
            <span class="metric-value">{{ form.feedbackType }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Trace</span>
            <span class="metric-value">{{ store.traceId }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue";
import { useWorkbenchStore } from "../../stores/workbench";

const store = useWorkbenchStore();

const form = reactive({
  runId: "",
  sessionId: "",
  messageId: "",
  rating: 4,
  feedbackType: "answer_quality",
  comment: "",
});

async function submitForm(): Promise<void> {
  await store.submitFeedback({
    runId: form.runId.trim() || "",
    sessionId: form.sessionId.trim() || "",
    messageId: form.messageId.trim() || "",
    rating: form.rating,
    feedbackType: form.feedbackType,
    comment: form.comment.trim() || undefined,
  });

  if (!store.lastError) {
    form.runId = "";
    form.sessionId = "";
    form.messageId = "";
    form.comment = "";
  }
}
</script>
