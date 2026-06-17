import { createBrowserRouter, Navigate } from "react-router-dom";
import { WorkbenchLayout } from "../layouts/WorkbenchLayout";
import { ChatPage } from "../pages/ChatPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { ExperimentComparisonPage } from "../pages/ExperimentComparisonPage";
import { ExperimentsPage } from "../pages/ExperimentsPage";
import { FeedbackPage } from "../pages/FeedbackPage";
import { GraphPage } from "../pages/GraphPage";
import { KnowledgeBasePage } from "../pages/KnowledgeBasePage";
import { SettingsPage } from "../pages/SettingsPage";

export const router = createBrowserRouter([
  {
    element: <WorkbenchLayout />,
    children: [
      { path: "/", element: <Navigate replace to="/chat" /> },
      {
        path: "/chat",
        element: <ChatPage />,
        handle: {
          title: "支持问答工作台",
          subtitle: "面向售后技术支持的知识检索、引用核查与回答生成",
          searchPlaceholder: "搜索会话、引用来源或故障关键词"
        }
      },
      {
        path: "/documents",
        element: <DocumentsPage />,
        handle: {
          title: "文档入库中心",
          subtitle: "上传手册、故障案例、常见问题与日志说明，跟踪解析和索引状态",
          searchPlaceholder: "搜索文档、路径或解析状态"
        }
      },
      {
        path: "/knowledge-base",
        element: <KnowledgeBasePage />,
        handle: {
          title: "知识库管理",
          subtitle: "维护售后支持知识源、向量索引与默认检索策略",
          searchPlaceholder: "搜索知识库名称或用途"
        }
      },
      {
        path: "/experiments",
        element: <ExperimentsPage />,
        handle: {
          title: "评测实验",
          subtitle: "导入标准问答集并运行 RAG 全链路评估",
          searchPlaceholder: "搜索样本编号、问题或备注"
        }
      },
      {
        path: "/experiments/comparison",
        element: <ExperimentComparisonPage />,
        handle: { title: "策略对比", subtitle: "对比召回质量、引用覆盖、运行成本和耗时" }
      },
      {
        path: "/feedback",
        element: <FeedbackPage />,
        handle: { title: "质检反馈", subtitle: "把人工反馈绑定到运行、会话和消息，沉淀改进线索" }
      },
      {
        path: "/graph",
        element: <GraphPage />,
        handle: {
          title: "图谱事实",
          subtitle: "查看 GraphRAG 实体、关系和证据来源",
          searchPlaceholder: "搜索实体、产品模块或故障现象",
          fullBleed: true
        }
      },
      {
        path: "/settings",
        element: <SettingsPage />,
        handle: { title: "系统设置", subtitle: "配置 Spring Boot API 入口和本地工作台默认值" }
      }
    ]
  }
]);
