<template>
  <div class="coze-workbench">
    <aside class="coze-left-rail">
      <section class="coze-panel coze-session-panel">
        <div class="coze-section-heading">
          <div>
            <span class="coze-kicker">Sessions</span>
            <h2>对话</h2>
          </div>
          <button class="icon-button" type="button" title="刷新会话" @click="store.loadSessions()">
            ↻
          </button>
        </div>

        <form class="coze-new-session" @submit.prevent="createNewSession">
          <input v-model="newSessionTitle" class="input" placeholder="新会话标题" />
          <button
            class="button button-primary"
            type="submit"
            :disabled="store.sessionsPending || !newSessionTitle.trim()"
          >
            {{ store.sessionsPending ? "创建中" : "新建" }}
          </button>
        </form>

        <div v-if="store.chatSessions.length === 0" class="coze-empty-compact">
          还没有会话。
        </div>
        <div v-else class="coze-session-list">
          <button
            v-for="session in store.chatSessions"
            :key="session.id"
            class="coze-session-item"
            :class="{ 'is-active': session.id === store.currentSessionId }"
            type="button"
            @click="selectSession(session.id)"
          >
            <strong>{{ session.title }}</strong>
            <span>{{ session.sessionStatus }} · {{ formatDate(session.updatedAt) }}</span>
          </button>
        </div>
      </section>

      <section class="coze-panel coze-context-panel">
        <div class="coze-section-heading">
          <div>
            <span class="coze-kicker">Context</span>
            <h2>知识库</h2>
          </div>
          <span class="status-pill status-success">{{ strategyLabel }}</span>
        </div>

        <div class="coze-stat-list">
          <div class="coze-stat-row">
            <span>当前知识库</span>
            <strong>{{ store.selectedKnowledgeBase?.name ?? "未配置" }}</strong>
          </div>
          <div class="coze-stat-row">
            <span>文档</span>
            <strong>{{ store.indexedDocuments }} / {{ store.totalDocuments }}</strong>
          </div>
          <div class="coze-stat-row">
            <span>实验记录</span>
            <strong>{{ store.experiments.length }}</strong>
          </div>
          <div class="coze-stat-row">
            <span>Trace</span>
            <strong class="coze-trace">{{ store.traceId }}</strong>
          </div>
        </div>
      </section>

      <div class="coze-context-panel">
        <UploadEntry />
      </div>
    </aside>

    <main class="coze-chat-pane">
      <header class="coze-chat-header">
        <div>
          <span class="coze-kicker">Knowledge Agent</span>
          <h2>{{ activeSessionTitle }}</h2>
          <p>{{ chatStatusLabel }} · {{ store.selectedKnowledgeBase?.name ?? "默认知识库" }}</p>
        </div>
        <div class="coze-chat-actions">
          <span class="status-pill" :class="store.pending ? 'status-warning' : 'status-success'">
            {{ store.pending ? "检索中" : "就绪" }}
          </span>
          <button class="button button-secondary" type="button" @click="fillQuestion">
            示例问题
          </button>
        </div>
      </header>

      <section class="coze-message-stream">
        <div v-if="store.messages.length === 0" class="coze-welcome">
          <span>Agent</span>
          <h2>把知识库当成你的复习搭子。</h2>
          <p>选择会话或直接输入问题，我会带上检索策略、引用来源、追问和薄弱点练习一起返回。</p>
          <div class="coze-prompt-grid">
            <button
              class="coze-prompt-card"
              type="button"
              @click="question = '帮我总结 Spring 事务传播行为，并给出面试回答框架。'"
            >
              Spring 事务传播
            </button>
            <button
              class="coze-prompt-card"
              type="button"
              @click="question = '对比 hybrid rerank 和 parent-child retrieval 的适用场景。'"
            >
              Advanced RAG 策略
            </button>
            <button
              class="coze-prompt-card"
              type="button"
              @click="question = '根据我的薄弱点生成一轮复习计划。'"
            >
              生成复习计划
            </button>
          </div>
        </div>

        <article
          v-for="message in store.messages"
          :key="message.id"
          class="coze-message"
          :class="message.role"
        >
          <div class="coze-avatar">
            {{ message.role === "user" ? "你" : "AI" }}
          </div>
          <div class="coze-bubble">
            <div class="coze-message-meta">
              <strong>{{ message.role === "user" ? "你" : "知识库助手" }}</strong>
              <span>{{ message.createdAt }}</span>
            </div>
            <div class="coze-message-content">{{ message.content }}</div>
          </div>
        </article>
      </section>

      <footer class="coze-composer-wrap">
        <div v-if="store.lastError" class="coze-error">{{ store.lastError }}</div>
        <div v-if="store.followUpQuestions.length" class="coze-followups">
          <button
            v-for="item in store.followUpQuestions"
            :key="item"
            class="coze-followup"
            type="button"
            @click="useFollowUp(item)"
          >
            {{ item }}
          </button>
        </div>
        <form class="coze-composer" @submit.prevent="submitQuestion">
          <textarea
            v-model="question"
            class="coze-composer-input"
            placeholder="向本地知识库提问，支持引用、追问、复习卡片和薄弱点练习。"
          />
          <div class="coze-composer-tools">
            <label>
              <span>混合检索</span>
              <select v-model="store.hybridRetrievalPreset" class="select">
                <option value="default">默认</option>
                <option value="balanced">均衡 60/40</option>
                <option value="vector">语义优先</option>
                <option value="keyword">关键词优先</option>
              </select>
            </label>
            <button class="button button-primary" type="submit" :disabled="store.pending || !question.trim()">
              {{ store.pending ? "生成中..." : "发送" }}
            </button>
          </div>
        </form>
      </footer>
    </main>

    <aside class="coze-right-rail">
      <SourceList :sources="store.latestSources" />
      <StrategySelector />

      <section v-if="store.studyPlan" class="coze-panel">
        <div class="coze-section-heading">
          <div>
            <span class="coze-kicker">Study</span>
            <h2>学习计划</h2>
          </div>
        </div>
        <p class="coze-muted">{{ store.studyPlan.summary }}</p>
        <div v-if="store.studyPlan.focusAreas.length" class="tag-row">
          <span v-for="area in store.studyPlan.focusAreas" :key="area" class="tag">
            {{ area }}
          </span>
        </div>
        <div class="coze-compact-list">
          <article v-for="step in store.studyPlan.steps" :key="step" class="coze-compact-item">
            {{ step }}
          </article>
        </div>
      </section>

      <section v-if="store.reviewCards.length" class="coze-panel">
        <div class="coze-section-heading">
          <div>
            <span class="coze-kicker">Cards</span>
            <h2>复习卡片</h2>
          </div>
        </div>
        <div class="coze-compact-list">
          <article v-for="card in store.reviewCards" :key="card.question" class="coze-compact-item">
            <strong>{{ card.question }}</strong>
            <p>{{ card.expectedAnswer }}</p>
            <span>{{ card.difficulty }}<template v-if="card.sourceHint"> · {{ card.sourceHint }}</template></span>
          </article>
        </div>
      </section>

      <section v-if="store.weakPoints.length" class="coze-panel">
        <div class="coze-section-heading">
          <div>
            <span class="coze-kicker">Practice</span>
            <h2>薄弱点</h2>
          </div>
        </div>

        <div v-if="store.weakPointSummary" class="coze-mini-metrics">
          <div>
            <span>待复习</span>
            <strong>{{ store.weakPointSummary.needsReviewCount }}</strong>
          </div>
          <div>
            <span>完成率</span>
            <strong>{{ formatPercent(store.weakPointSummary.completionRate) }}</strong>
          </div>
          <div>
            <span>到期</span>
            <strong>{{ store.weakPointSummary.dueReviewCount ?? 0 }}</strong>
          </div>
        </div>

        <div class="coze-filter-row">
          <button
            v-for="filter in weakPointFilters"
            :key="filter.value"
            class="coze-filter-chip"
            :class="{ 'is-active': weakPointFilter === filter.value }"
            type="button"
            @click="weakPointFilter = filter.value"
          >
            {{ filter.label }} {{ filter.count }}
          </button>
        </div>

        <button
          class="button button-primary coze-full-button"
          type="button"
          :disabled="store.pending || !store.currentSessionId || !nextDueWeakPoint"
          @click="practiceNextDue"
        >
          练习下一个到期项
        </button>

        <div v-if="displayedWeakPoints.length === 0" class="coze-empty-compact">
          当前筛选下暂无薄弱点。
        </div>

        <article v-for="point in displayedWeakPoints" :key="point.id" class="coze-practice-card">
          <div>
            <strong>{{ point.topic }}</strong>
            <p>{{ point.expectedAnswer }}</p>
            <span>
              {{ point.difficulty }} · {{ point.masteryStatus }} · {{ point.reviewCount }} 次
              <template v-if="point.nextReviewAt"> · {{ formatDate(point.nextReviewAt) }}</template>
            </span>
          </div>
          <textarea
            v-model="practiceAnswers[point.id]"
            class="textarea coze-practice-input"
            placeholder="写下你的回忆答案。"
          />
          <div v-if="store.lastWeakPointAssessment && assessedWeakPointId === point.id" class="coze-assessment">
            {{ formatPercent(store.lastWeakPointAssessment.score) }} ·
            {{ store.lastWeakPointAssessment.masteryStatus }} ·
            {{ store.lastWeakPointAssessment.feedback }}
          </div>
          <div class="coze-practice-actions">
            <button class="button button-secondary" type="button" :disabled="store.pending" @click="store.practiceWeakPoint(point.id)">
              出题
            </button>
            <button
              class="button button-secondary"
              type="button"
              :disabled="store.pending || !practiceAnswers[point.id]?.trim()"
              @click="submitPracticeAnswer(point.id)"
            >
              提交
            </button>
            <button class="button button-secondary" type="button" @click="store.assessWeakPoint(point.id, 'NEEDS_REVIEW')">
              复习
            </button>
            <button class="button button-primary" type="button" @click="store.assessWeakPoint(point.id, 'MASTERED')">
              掌握
            </button>
          </div>
        </article>
      </section>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted } from "vue";
import SourceList from "../../components/SourceList.vue";
import StrategySelector from "../../components/StrategySelector.vue";
import UploadEntry from "../../components/UploadEntry.vue";
import { useWorkbenchStore } from "../../stores/workbench";
import type { LearningWeakPoint } from "../../types";

const store = useWorkbenchStore();
const question = ref("");
const newSessionTitle = ref("");
const practiceAnswers = reactive<Record<string, string>>({});
const assessedWeakPointId = ref("");
type WeakPointFilter = "all" | "due" | "needs-review" | "mastered";
const weakPointFilter = ref<WeakPointFilter>("all");

const strategyLabel = computed(() => {
  const item = store.ragStrategyOptions.find((option) => option.value === store.selectedStrategy);
  return item?.label ?? store.selectedStrategy;
});
const activeSessionTitle = computed(() => {
  const active = store.chatSessions.find((session) => session.id === store.currentSessionId);
  return active?.title ?? "知识库对话";
});
const chatStatusLabel = computed(() => {
  if (store.pending) {
    return "正在检索知识库";
  }
  if (store.currentSessionId) {
    return "继续当前会话";
  }
  return "输入问题后自动创建会话";
});

const dueWeakPoints = computed(() => store.weakPoints.filter(isDueReview));
const needsReviewWeakPoints = computed(() =>
  store.weakPoints.filter((point) => normalizeMasteryStatus(point.masteryStatus) === "NEEDS_REVIEW")
);
const masteredWeakPoints = computed(() =>
  store.weakPoints.filter((point) => normalizeMasteryStatus(point.masteryStatus) === "MASTERED")
);
const nextDueWeakPoint = computed(() => dueWeakPoints.value[0] ?? null);
const displayedWeakPoints = computed(() => {
  if (weakPointFilter.value === "due") {
    return dueWeakPoints.value;
  }
  if (weakPointFilter.value === "needs-review") {
    return needsReviewWeakPoints.value;
  }
  if (weakPointFilter.value === "mastered") {
    return masteredWeakPoints.value;
  }
  return store.weakPoints;
});
const weakPointFilters = computed(() => [
  { value: "all" as const, label: "全部", count: store.weakPoints.length },
  { value: "due" as const, label: "到期", count: dueWeakPoints.value.length },
  { value: "needs-review" as const, label: "待复习", count: needsReviewWeakPoints.value.length },
  { value: "mastered" as const, label: "已掌握", count: masteredWeakPoints.value.length }
]);

onMounted(() => {
  store.loadSessions();
});

function fillQuestion(): void {
  question.value = "帮我总结 Spring 事务传播行为的核心差异，并给一个面试回答思路。";
}

async function submitQuestion(): Promise<void> {
  await store.askQuestion(question.value);
  question.value = "";
}

function useFollowUp(value: string): void {
  question.value = value;
}

async function createNewSession(): Promise<void> {
  const kbId = store.selectedKnowledgeBase?.id ?? store.knowledgeBases[0]?.id ?? "";
  await store.createSession(kbId, newSessionTitle.value.trim());
  if (!store.lastError) {
    newSessionTitle.value = "";
  }
}

function selectSession(sessionId: string): void {
  store.loadSessionMessages(sessionId);
}

async function submitPracticeAnswer(weakPointId: string): Promise<void> {
  await store.practiceWeakPoint(weakPointId, practiceAnswers[weakPointId]);
  if (!store.lastError) {
    assessedWeakPointId.value = weakPointId;
    practiceAnswers[weakPointId] = "";
  }
}

async function practiceNextDue(): Promise<void> {
  if (!nextDueWeakPoint.value) {
    return;
  }
  assessedWeakPointId.value = "";
  await store.practiceWeakPoint(nextDueWeakPoint.value.id);
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string): string {
  return value.replace("T", " ").slice(0, 16);
}

function isDueReview(point: LearningWeakPoint): boolean {
  if (!point.nextReviewAt) {
    return true;
  }
  const timestamp = Date.parse(point.nextReviewAt);
  return !Number.isNaN(timestamp) && timestamp <= Date.now();
}

function normalizeMasteryStatus(value: string): string {
  return value.trim().toUpperCase();
}
</script>
