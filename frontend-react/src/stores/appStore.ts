import { create } from "zustand";
import type { AppSettings, KnowledgeBaseSummary } from "../types";
import { fetchKnowledgeBases, fetchSettings } from "../api";

const defaultSettings: AppSettings = {
  apiBaseUrl: "/api",
  aiServiceBaseUrl: "",
  defaultKnowledgeBaseId: "",
  timeoutMs: 15000,
  includeTraceHeader: true
};

interface AppStore {
  error: string;
  knowledgeBases: KnowledgeBaseSummary[];
  loading: boolean;
  settings: AppSettings;
  hydrate: () => Promise<void>;
  setError: (error: string) => void;
  setSettings: (settings: AppSettings) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  error: "",
  knowledgeBases: [],
  loading: false,
  settings: defaultSettings,
  async hydrate() {
    set({ loading: true, error: "" });
    const results = await Promise.allSettled([fetchKnowledgeBases(), fetchSettings()]);
    const next: Partial<AppStore> = { loading: false };
    if (results[0].status === "fulfilled") {
      next.knowledgeBases = results[0].value;
    }
    if (results[1].status === "fulfilled") {
      next.settings = results[1].value;
    }
    const failed = results.filter((item) => item.status === "rejected").length;
    if (failed > 0) {
      next.error = `基础数据部分加载失败（${failed}/${results.length}），页面将继续展示可用数据。`;
    }
    set(next);
  },
  setError(error) {
    set({ error });
  },
  setSettings(settings) {
    set({ settings });
  }
}));
