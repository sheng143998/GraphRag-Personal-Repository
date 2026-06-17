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
          title: "RAG Workbench",
          subtitle: "Session: Local Knowledge Analysis",
          searchPlaceholder: "Search sessions or citations..."
        }
      },
      {
        path: "/documents",
        element: <DocumentsPage />,
        handle: {
          title: "Document Center",
          subtitle: "Ingest files, folders, parsing status and document types.",
          searchPlaceholder: "Search documents..."
        }
      },
      {
        path: "/knowledge-base",
        element: <KnowledgeBasePage />,
        handle: {
          title: "Knowledge Base",
          subtitle: "Manage, index and optimize vector knowledge pipelines.",
          searchPlaceholder: "Search knowledge bases..."
        }
      },
      {
        path: "/experiments",
        element: <ExperimentsPage />,
        handle: {
          title: "Experiment Evaluation",
          subtitle: "Import datasets and automatically run the full RAG evaluation chain.",
          searchPlaceholder: "Search caseId, question, notes..."
        }
      },
      {
        path: "/experiments/comparison",
        element: <ExperimentComparisonPage />,
        handle: { title: "RAG Evaluation Compare", subtitle: "Compare strategies, metrics and run cost." }
      },
      {
        path: "/feedback",
        element: <FeedbackPage />,
        handle: { title: "Feedback", subtitle: "Link feedback to runs, sessions and messages." }
      },
      {
        path: "/graph",
        element: <GraphPage />,
        handle: {
          title: "Knowledge Graph",
          subtitle: "Explore GraphRAG entities, relationships and source evidence.",
          searchPlaceholder: "Search graph entities...",
          fullBleed: true
        }
      },
      {
        path: "/settings",
        element: <SettingsPage />,
        handle: { title: "Settings", subtitle: "Configure Spring API base URL and local workspace defaults." }
      }
    ]
  }
]);
