import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/chat"
    },
    {
      path: "/chat",
      name: "chat",
      component: () => import("../pages/chat/ChatPage.vue"),
      meta: {
        title: "对话工作台",
        subtitle: "围绕本地知识库进行提问、检索和引用查看。"
      }
    },
    {
      path: "/documents",
      name: "documents",
      component: () => import("../pages/documents/DocumentsPage.vue"),
      meta: {
        title: "文档中心",
        subtitle: "集中管理上传文件、解析状态和文档类型。"
      }
    },
    {
      path: "/knowledge-base",
      name: "knowledge-base",
      component: () => import("../pages/knowledge-base/KnowledgeBasePage.vue"),
      meta: {
        title: "知识库",
        subtitle: "查看知识库概览、文档规模和最近更新。"
      }
    },
    {
      path: "/experiments",
      name: "experiments",
      component: () => import("../pages/experiments/ExperimentsPage.vue"),
      meta: {
        title: "实验评估",
        subtitle: "跟踪不同 RAG 策略的精度、召回和最近一次运行。"
      }
    },
    {
      path: "/feedback",
      name: "feedback",
      component: () => import("../pages/feedback/FeedbackPage.vue"),
      meta: {
        title: "用户反馈",
        subtitle: "提交 RAG 回答质量反馈，帮助持续优化检索策略。"
      }
    },
    {
      path: "/graph",
      name: "graph",
      component: () => import("../pages/graph/GraphPage.vue"),
      meta: {
        title: "图谱事实",
        subtitle: "查看 GraphRAG 入库实体、关系和知识库过滤结果。"
      }
    },
    {
      path: "/settings",
      name: "settings",
      component: () => import("../pages/settings/SettingsPage.vue"),
      meta: {
        title: "系统设置",
        subtitle: "配置 API 基地址、默认知识库和请求超时。"
      }
    }
  ]
});

export default router;
