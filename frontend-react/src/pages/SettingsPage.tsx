import { Save } from "lucide-react";
import { useEffect, useState } from "react";
import { API_RUNTIME_SETTINGS_KEY, fetchSettings } from "../api";
import { Button } from "../components/primitives/Button";
import { Panel } from "../components/primitives/Panel";
import type { AppSettings } from "../types";
import "./pages.css";

const fallbackSettings: AppSettings = {
  apiBaseUrl: "/api",
  aiServiceBaseUrl: "",
  defaultKnowledgeBaseId: "",
  timeoutMs: 15000,
  includeTraceHeader: true
};

function loadLocal(): AppSettings {
  try {
    const raw = window.localStorage.getItem(API_RUNTIME_SETTINGS_KEY);
    return raw ? { ...fallbackSettings, ...JSON.parse(raw) } : fallbackSettings;
  } catch {
    return fallbackSettings;
  }
}

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(loadLocal);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSettings()
      .then((remote) => setSettings((current) => ({ ...current, ...remote })))
      .catch(() => {
        setError("后端设置接口不可用，当前展示本地运行时配置。");
      });
  }, []);

  function update<K extends keyof AppSettings>(key: K, value: AppSettings[K]) {
    setSettings((current) => ({ ...current, [key]: value }));
  }

  function save() {
    window.localStorage.setItem(API_RUNTIME_SETTINGS_KEY, JSON.stringify(settings));
    setMessage("设置已保存到浏览器本地。");
  }

  return (
    <div className="page-canvas page-stack">
      <header className="page-header">
        <div>
          <h2>系统设置</h2>
          <p>这些配置只影响前端运行时请求，浏览器仍通过业务后端进入 AI 服务。</p>
        </div>
      </header>
      {error ? <div className="alert-error">{error}</div> : null}
      {message ? <div className="alert-success">{message}</div> : null}
      <Panel title="运行时接口设置">
        <div className="stacked-form">
          <label><span>业务后端地址</span><input value={settings.apiBaseUrl} onChange={(event) => update("apiBaseUrl", event.target.value)} /></label>
          <label><span>默认知识库编号</span><input value={settings.defaultKnowledgeBaseId} onChange={(event) => update("defaultKnowledgeBaseId", event.target.value)} /></label>
          <label><span>请求超时 ms</span><input type="number" value={settings.timeoutMs} onChange={(event) => update("timeoutMs", Number(event.target.value))} /></label>
          <label className="checkbox-row">
            <input type="checkbox" checked={settings.includeTraceHeader} onChange={(event) => update("includeTraceHeader", event.target.checked)} />
            <span>发送 X-Trace-Id 请求头</span>
          </label>
          <Button icon={<Save />} variant="primary" onClick={save}>保存设置</Button>
        </div>
      </Panel>
    </div>
  );
}
