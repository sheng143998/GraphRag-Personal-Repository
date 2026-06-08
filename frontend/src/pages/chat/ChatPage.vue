<template>
  <div class="page-grid workbench-grid">
    <div class="stack">
      <!-- 会话管理 -->
      <section class="panel">
        <div class="panel-header">
          <h2 class="panel-title">对话会话</h2>
          <p class="panel-subtitle">创建会话、切换历史会话，查看消息记录。</p>
        </div>
        <div class="panel-body stack">
          <div class="form-grid">
            <label class="form-row">
              <span class="form-label">会话标题</span>
              <input v-model="newSessionTitle" class="input" placeholder="例如：Spring 面试复习" />
            </label>
            <div class="button-row">
              <button
                class="button button-primary"
                type="button"
                :disabled="store.sessionsPending || !newSessionTitle.trim()"
                @click="createNewSession"
              >
                {{ store.sessionsPending ? "创建中..." : "新建会话" }}
              </button>
              <button class="button button-secondary" type="button" @click="store.loadSessions()">
                刷新列表
              </button>
            </div>
          </div>
          <div v-if="store.chatSessions.length === 0" class="empty-state">
            暂无会话，输入标题创建第一个会话。
          </div>
          <div v-else class="item-list" style="max-height: 200px; overflow-y: auto;">
            <article
              v-for="session in store.chatSessions"
              :key="session.id"
              class="item-card"
              :class="{ 'item-card-active': session.id === store.currentSessionId }"
              style="cursor: pointer;"
              @click="selectSession(session.id)"
            >
              <h3 class="item-title">{{ session.title }}</h3>
              <div class="item-meta">
                {{ session.sessionStatus }} · {{ session.updatedAt }}
              </div>
            </article>
          </div>
        </div>
      </section>

      <!-- 工作台总览 -->
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

      <!-- 知识库对话 -->
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
            <div v-if="store.followUpQuestions.length" class="item-list">
              <button
                v-for="item in store.followUpQuestions"
                :key="item"
                class="button button-ghost"
                type="button"
                @click="useFollowUp(item)"
              >
                {{ item }}
              </button>
            </div>
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
      <section v-if="store.studyPlan" class="panel">
        <div class="panel-header">
          <h2 class="panel-title">Study Plan</h2>
          <p class="panel-subtitle">{{ store.studyPlan.summary }}</p>
        </div>
        <div class="panel-body stack">
          <div v-if="store.studyPlan.focusAreas.length" class="item-list">
            <span v-for="area in store.studyPlan.focusAreas" :key="area" class="button button-ghost">
              {{ area }}
            </span>
          </div>
          <div class="item-list">
            <article v-for="step in store.studyPlan.steps" :key="step" class="item-card">
              {{ step }}
            </article>
          </div>
        </div>
      </section>
      <section v-if="store.reviewCards.length" class="panel">
        <div class="panel-header">
          <h2 class="panel-title">Review Cards</h2>
          <p class="panel-subtitle">Active-recall prompts from the latest answer.</p>
        </div>
        <div class="panel-body stack">
          <article v-for="card in store.reviewCards" :key="card.question" class="item-card">
            <h3 class="item-title">{{ card.question }}</h3>
            <p class="item-description">{{ card.expectedAnswer }}</p>
            <div class="item-meta">
              {{ card.difficulty }}<span v-if="card.sourceHint"> · {{ card.sourceHint }}</span>
            </div>
          </article>
        </div>
      </section>
      <section v-if="store.weakPoints.length" class="panel">
        <div class="panel-header">
          <h2 class="panel-title">Weak Points</h2>
          <p class="panel-subtitle">Session-level topics that need another pass.</p>
        </div>
        <div class="panel-body stack">
          <div v-if="store.weakPointSummary" class="evaluation-dashboard">
            <div class="dashboard-metric">
              <span class="metric-label">Needs review</span>
              <strong>{{ store.weakPointSummary.needsReviewCount }}</strong>
            </div>
            <div class="dashboard-metric">
              <span class="metric-label">Mastered</span>
              <strong>{{ store.weakPointSummary.masteredCount }}</strong>
            </div>
            <div class="dashboard-metric">
              <span class="metric-label">Completion</span>
              <strong>{{ formatPercent(store.weakPointSummary.completionRate) }}</strong>
            </div>
            <div class="dashboard-metric">
              <span class="metric-label">Reviews</span>
              <strong>{{ store.weakPointSummary.totalReviewCount }}</strong>
            </div>
            <div class="dashboard-metric">
              <span class="metric-label">Due</span>
              <strong>{{ store.weakPointSummary.dueReviewCount ?? 0 }}</strong>
            </div>
          </div>
          <div class="button-row compact-row">
            <button
              v-for="filter in weakPointFilters"
              :key="filter.value"
              class="button"
              :class="weakPointFilter === filter.value ? 'button-primary' : 'button-secondary'"
              type="button"
              @click="weakPointFilter = filter.value"
            >
              {{ filter.label }} {{ filter.count }}
            </button>
            <button
              class="button button-primary"
              type="button"
              :disabled="store.pending || !store.currentSessionId || !nextDueWeakPoint"
              @click="practiceNextDue"
            >
              Practice next due
            </button>
          </div>
          <article v-if="store.weakPointSummary?.nextWeakPoint" class="item-card item-card-active">
            <h3 class="item-title">Next practice: {{ store.weakPointSummary.nextWeakPoint.topic }}</h3>
            <div class="item-meta">
              {{ store.weakPointSummary.nextWeakPoint.difficulty }} · {{ store.weakPointSummary.nextWeakPoint.masteryStatus }}
              <span v-if="store.weakPointSummary.nextWeakPoint.nextReviewAt">
                · next {{ formatDate(store.weakPointSummary.nextWeakPoint.nextReviewAt) }}
              </span>
            </div>
          </article>
          <div v-if="displayedWeakPoints.length === 0" class="empty-state">
            No weak points match the current queue filter.
          </div>
          <article v-for="point in displayedWeakPoints" :key="point.id" class="item-card">
            <h3 class="item-title">{{ point.topic }}</h3>
            <p class="item-description">{{ point.expectedAnswer }}</p>
            <div class="item-meta">
              {{ point.difficulty }} · {{ point.masteryStatus }} · seen {{ point.reviewCount }} time{{ point.reviewCount === 1 ? "" : "s" }}
              <span v-if="point.practiceCount != null"> · practiced {{ point.practiceCount }}</span>
              <span v-if="point.lastPracticeScore != null"> · last score {{ formatPercent(point.lastPracticeScore) }}</span>
              <span v-if="point.nextReviewAt"> · next {{ formatDate(point.nextReviewAt) }}</span>
            </div>
            <label class="form-row" style="margin-top: 0.75rem;">
              <span class="form-label">Practice answer</span>
              <textarea
                v-model="practiceAnswers[point.id]"
                class="textarea"
                placeholder="Write your recall answer before asking the assistant to assess it"
              />
            </label>
            <div v-if="store.lastWeakPointAssessment && assessedWeakPointId === point.id" class="item-meta">
              Score {{ formatPercent(store.lastWeakPointAssessment.score) }}
              · {{ store.lastWeakPointAssessment.masteryStatus }}
              · {{ store.lastWeakPointAssessment.feedback }}
            </div>
            <div class="button-row" style="margin-top: 0.75rem;">
              <button class="button button-secondary" type="button" :disabled="store.pending" @click="store.practiceWeakPoint(point.id)">
                Practice
              </button>
              <button
                class="button button-secondary"
                type="button"
                :disabled="store.pending || !practiceAnswers[point.id]?.trim()"
                @click="submitPracticeAnswer(point.id)"
              >
                Submit answer
              </button>
              <button class="button button-secondary" type="button" @click="store.assessWeakPoint(point.id, 'NEEDS_REVIEW')">
                Review again
              </button>
              <button class="button button-primary" type="button" @click="store.assessWeakPoint(point.id, 'MASTERED')">
                Mastered
              </button>
            </div>
          </article>
        </div>
      </section>
      <StrategySelector />
      <SourceList :sources="store.latestSources" />
    </div>
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
  { value: "all" as const, label: "All", count: store.weakPoints.length },
  { value: "due" as const, label: "Due", count: dueWeakPoints.value.length },
  { value: "needs-review" as const, label: "Needs review", count: needsReviewWeakPoints.value.length },
  { value: "mastered" as const, label: "Mastered", count: masteredWeakPoints.value.length }
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
