import { useEffect, useMemo, useState } from "react";
import { createKnowledgeBase, deleteKnowledgeBase, fetchKnowledgeBases } from "../api";
import type { KnowledgeBaseSummary } from "../types";
import { formatDateTime, formatNumber } from "../utils/format";
import "./pages.css";

const modelNames = ["text-embedding-3-small", "bge-large-zh-v1.5", "text-embedding-ada-002"];
const chunkStrategies = ["递归切分 512/64", "语义切分", "父子块 1024/128"];

export function KnowledgeBasePage() {
  const [items, setItems] = useState<KnowledgeBaseSummary[]>([]);
  const [pending, setPending] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  const totals = useMemo(
    () => ({
      documents: items.reduce((sum, item) => sum + (item.documentCount ?? 0), 0),
      chunks: items.reduce((sum, item) => sum + (item.chunkCount ?? 0), 0)
    }),
    [items]
  );

  async function load() {
    setPending(true);
    setError("");
    try {
      setItems(await fetchKnowledgeBases());
    } catch (err) {
      setError(err instanceof Error ? err.message : "无法加载知识库。");
    } finally {
      setPending(false);
    }
  }

  async function submit() {
    if (!name.trim()) return;
    setPending(true);
    setError("");
    try {
      const created = await createKnowledgeBase({ name: name.trim(), description: description.trim() || undefined });
      setItems((current) => [created, ...current]);
      setName("");
      setDescription("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建知识库失败。");
    } finally {
      setPending(false);
    }
  }

  async function remove(id: string) {
    const ok = window.confirm("确定删除这个知识库吗？关联文档将无法在前端继续使用。");
    if (!ok) return;
    setPending(true);
    setError("");
    try {
      await deleteKnowledgeBase(id);
      setItems((current) => current.filter((item) => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除知识库失败。");
    } finally {
      setPending(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="kb-studio">
      <section className="kb-hero-row">
        <div>
          <h1>知识库管理</h1>
          <p>管理、索引和优化你的向量数据源。</p>
        </div>
        <button className="button primary" type="button" onClick={submit} disabled={pending || !name.trim()}>
          <span className="material-symbols-outlined">add_circle</span>
          创建新知识库
        </button>
      </section>

      {error ? <div className="alert-error">{error}</div> : null}

      <section className="kb-filter-grid">
        <div className="kb-filter-bar">
          <button type="button">所有类型 <span className="material-symbols-outlined">expand_more</span></button>
          <button type="button">最近更新 <span className="material-symbols-outlined">swap_vert</span></button>
          <span className="filter-divider" />
          <span className="filter-chip active">启用中（{items.length}）</span>
          <span className="filter-chip">已归档（0）</span>
        </div>
        <div className="kb-storage">
          <span>向量存储占用</span>
          <strong>{formatNumber(Math.max(1, Math.round(totals.chunks / 1000)))} MB / 5 GB</strong>
        </div>
      </section>

      <section className="kb-create-strip">
        <label>
          <span>名称</span>
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="例如：RAG 学习笔记" />
        </label>
        <label>
          <span>描述</span>
          <input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="知识库用途" />
        </label>
        <button className="button secondary" type="button" onClick={load} disabled={pending}>
          <span className="material-symbols-outlined">sync</span>
          刷新
        </button>
      </section>

      <section className="kb-pipeline-grid">
        {items.map((item, index) => (
          <article className="kb-pipeline-card" key={item.id}>
            <div className="kb-card-top">
              <div className="kb-card-identity">
                <div className="kb-card-icon">
                  <span className="material-symbols-outlined">description</span>
                </div>
                <div>
                  <h2>{item.name}</h2>
                  <p>{item.description || "暂无描述"}</p>
                </div>
              </div>
              <div className="kb-toggle">
                <span>启用中</span>
                <i><b /></i>
              </div>
            </div>

            <div className="kb-model-box">
              <div>
                <span>向量模型</span>
                <code>{modelNames[index % modelNames.length]}</code>
              </div>
              <div>
                <span>切分策略</span>
                <strong>{chunkStrategies[index % chunkStrategies.length]}</strong>
              </div>
            </div>

            <div className="kb-mini-stats">
              <span>文档 <strong>{formatNumber(item.documentCount)}</strong></span>
              <span>片段 <strong>{formatNumber(item.chunkCount)}</strong></span>
              <span>延迟 <strong>{item.chunkCount ? "18ms" : "--"}</strong></span>
            </div>

            <div className="kb-card-footer">
              <span>最近更新：{formatDateTime(item.updatedAt)}</span>
              <div>
                <button title="重新索引" type="button"><span className="material-symbols-outlined">sync</span></button>
                <button title="设置" type="button"><span className="material-symbols-outlined">settings</span></button>
                <button title="删除" type="button" onClick={() => void remove(item.id)}>
                  <span className="material-symbols-outlined">delete</span>
                </button>
              </div>
            </div>
          </article>
        ))}

        <button className="kb-add-card" type="button" onClick={submit} disabled={pending || !name.trim()}>
          <span className="material-symbols-outlined">add</span>
          <strong>添加新知识库</strong>
          <small>连接外部数据源或上传本地文件</small>
        </button>
      </section>

      <section className="kb-bottom-grid">
        <article className="kb-analytics-card">
          <h3><span className="material-symbols-outlined">monitoring</span> 检索相关性趋势</h3>
          <div className="trend-bars">
            {[40, 56, 45, 70, 85, 80, 95].map((height, index) => (
              <i key={index} style={{ height: `${height}%` }} />
            ))}
          </div>
          <div className="trend-labels"><span>周一</span><span>周二</span><span>周三</span><span>周四</span><span>周五</span><span>周六</span><span>周日</span></div>
        </article>
        <article className="kb-activity-card">
          <div className="kb-activity-head">
            <h3><span className="material-symbols-outlined">history</span> 最近活动</h3>
            <button type="button">查看全部</button>
          </div>
          <div className="kb-activity-list">
            <Activity color="green" text={`当前共有 ${formatNumber(totals.documents)} 份文档可用于检索`} time="刚刚" />
            <Activity color="primary" text={`向量片段总量 ${formatNumber(totals.chunks)}，可继续通过文档中心扩充`} time="今日" />
            <Activity color="orange" text="默认策略已纳入混合召回与父子块评测链路" time="近期" />
          </div>
        </article>
      </section>
    </div>
  );
}

function Activity({ color, text, time }: { color: "green" | "primary" | "orange"; text: string; time: string }) {
  return (
    <div className={`kb-activity-row ${color}`}>
      <i />
      <span>{text}</span>
      <code>{time}</code>
    </div>
  );
}
