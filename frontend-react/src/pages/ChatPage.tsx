import { useEffect, useMemo, useState } from "react";
import { createChatSession, fetchChatMessages, fetchChatSessions, fetchKnowledgeBases, sendAssistantTurn } from "../api";
import type { ChatMessageRecord, ChatSession, CitationSource, KnowledgeBaseSummary, SupportPlan } from "../types";
import { formatDateTime } from "../utils/format";
import "./chat-page.css";
import "./pages.css";

type RawCitation = Partial<CitationSource> & {
  documentId?: string | null;
  document_id?: string | null;
  chunkId?: string | null;
  chunk_id?: string | null;
  sourcePath?: string | null;
  source_path?: string | null;
  score?: number | null;
  rerankScore?: number | null;
  rerank_score?: number | null;
  metadata?: Record<string, unknown> | null;
  pageNumber?: number | null;
  page_number?: number | null;
  sheetName?: string | null;
  sheet_name?: string | null;
};

const STRATEGY_LABELS: Record<string, string> = {
  "advanced-rag": "综合增强检索",
  "hybrid-rerank": "混合召回 + 重排",
  "parent-child": "父子块上下文",
  "graph-rag": "图谱增强检索"
};

const SEVERITY_LABELS: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
  critical: "紧急"
};

function textValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function normalizeCitation(value: string | RawCitation, index: number): CitationSource {
  if (typeof value === "string") {
    return {
      id: `citation-${index + 1}`,
      title: value,
      location: value,
      strategy: "history",
      score: 0,
      snippet: value
    };
  }

  const metadata = value.metadata ?? {};
  const chunkId = textValue(value.chunkId) ?? textValue(value.chunk_id);
  const documentId = textValue(value.documentId) ?? textValue(value.document_id);
  const sourcePath = textValue(value.sourcePath) ?? textValue(value.source_path);
  const title = textValue(value.title) ?? sourcePath ?? documentId ?? chunkId ?? `来源 ${index + 1}`;
  const preview = textValue(metadata.content_preview) ?? textValue(metadata.preview) ?? textValue(value.snippet);
  const pageNumber = value.pageNumber ?? value.page_number;
  const sheetName = textValue(value.sheetName) ?? textValue(value.sheet_name);
  const location = textValue(value.location) ?? sourcePath ?? sheetName ?? (pageNumber ? `第 ${pageNumber} 页` : undefined) ?? chunkId ?? title;

  return {
    id: textValue(value.id) ?? chunkId ?? documentId ?? `citation-${index + 1}`,
    title,
    location,
    strategy: textValue(value.strategy) ?? "agent",
    score: value.rerankScore ?? value.rerank_score ?? value.score ?? 0,
    snippet: preview ?? title
  };
}

function parseCitations(value?: string | null): CitationSource[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value) as Array<string | RawCitation>;
    return Array.isArray(parsed) ? parsed.map(normalizeCitation) : [];
  } catch {
    return [normalizeCitation(value, 0)];
  }
}

function latestAssistantMessage(messages: ChatMessageRecord[]): ChatMessageRecord | undefined {
  return [...messages].reverse().find((item) => item.role === "assistant");
}

function listOrFallback(values: string[] | undefined, fallback: string[]): string[] {
  return values && values.length ? values : fallback;
}

function MessageSupportPlan({ plan }: { plan: SupportPlan }) {
  const clarificationQuestions = listOrFallback(plan.clarificationQuestions, ["请补充产品版本、故障时间、影响范围和关键日志。"]);
  const nextActions = listOrFallback(plan.nextActions, ["按诊断步骤执行并记录客户反馈。"]);
  const riskNotes = listOrFallback(plan.riskNotes, ["回答必须保留证据引用，无法确认时转人工复核。"]);

  return (
    <section className="support-plan-card">
      <div className="support-plan-card__head">
        <span className="material-symbols-outlined fill-icon">support_agent</span>
        <div>
          <h3>售后诊断方案</h3>
          <p>{plan.issueSummary || "Agent 已根据知识库证据生成排查建议。"}</p>
        </div>
      </div>

      <div className="support-plan-grid">
        <div className="support-plan-section">
          <h4>澄清问题</h4>
          <ul>
            {clarificationQuestions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="support-plan-section">
          <h4>风险与升级</h4>
          <p>
            {plan.escalation?.required ? "建议升级处理" : "可先按一线支持流程排查"}
            {plan.escalation?.severity ? ` · 严重度：${SEVERITY_LABELS[plan.escalation.severity] ?? plan.escalation.severity}` : ""}
          </p>
          {plan.escalation?.reason ? <small>{plan.escalation.reason}</small> : null}
        </div>
      </div>

      {plan.diagnosticSteps?.length ? (
        <ol className="diagnostic-steps">
          {plan.diagnosticSteps.map((step) => (
            <li key={`${step.order ?? 0}-${step.action}`}>
              <strong>{step.action}</strong>
              {step.expectedSignal ? <span>预期信号：{step.expectedSignal}</span> : null}
              {step.evidenceHint ? <span>证据提示：{step.evidenceHint}</span> : null}
              {step.fallback ? <span>兜底动作：{step.fallback}</span> : null}
            </li>
          ))}
        </ol>
      ) : null}

      <div className="support-plan-grid support-plan-grid--compact">
        <div className="support-plan-section">
          <h4>证据引用</h4>
          <ul>
            {listOrFallback(plan.evidenceReferences, ["请结合右侧证据与追踪面板核查来源。"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="support-plan-section">
          <h4>下一步动作</h4>
          <ul>
            {nextActions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="support-plan-section support-plan-section--warning">
          <h4>风险提示</h4>
          <ul>
            {riskNotes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

export function ChatPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseSummary[]>([]);
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState("");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState("");
  const [messages, setMessages] = useState<ChatMessageRecord[]>([]);
  const [supportPlansByMessageId, setSupportPlansByMessageId] = useState<Record<string, SupportPlan>>({});
  const [question, setQuestion] = useState("");
  const [strategy, setStrategy] = useState("advanced-rag");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const currentKb = knowledgeBases.find((item) => item.id === selectedKnowledgeBaseId) ?? knowledgeBases[0];
  const latestAssistant = latestAssistantMessage(messages);
  const latestSupportPlan = latestAssistant ? supportPlansByMessageId[latestAssistant.id] : undefined;
  const visibleSessions = currentKb ? sessions.filter((session) => session.knowledgeBaseId === currentKb.id) : sessions;

  const latestCitations = useMemo(() => {
    const latest = [...messages].reverse().find((item) => item.role === "assistant" && item.citations);
    return parseCitations(latest?.citations);
  }, [messages]);

  async function loadBase() {
    const [kbList, sessionList] = await Promise.allSettled([fetchKnowledgeBases(), fetchChatSessions()]);
    if (kbList.status === "fulfilled") {
      setKnowledgeBases(kbList.value);
      setSelectedKnowledgeBaseId((current) => current || kbList.value[0]?.id || "");
    }
    if (sessionList.status === "fulfilled") setSessions(sessionList.value);
  }

  async function loadMessages(sessionId: string) {
    setCurrentSessionId(sessionId);
    setMessages(await fetchChatMessages(sessionId));
  }

  async function submit() {
    if (!question.trim() || !currentKb) return;
    setPending(true);
    setError("");
    try {
      let sessionId = currentSessionId;
      if (!sessionId) {
        const session = await createChatSession({ knowledgeBaseId: currentKb.id, title: question.trim().slice(0, 48) });
        setSessions((current) => [session, ...current]);
        sessionId = session.id;
        setCurrentSessionId(sessionId);
      }
      const response = await sendAssistantTurn(sessionId, {
        question,
        strategy,
        knowledgeBaseId: currentKb.id,
        sessionId,
        retrievalOptions: {},
        agentName: "technical-support-agent",
        variables: {
          mode: "technical-support",
          scenario: "after-sales",
          agent_profile: "customer-support"
        }
      });
      if (response.userMessage && response.assistantMessage) {
        setMessages((current) => [...current, response.userMessage!, response.assistantMessage!]);
        if (response.supportPlan) {
          setSupportPlansByMessageId((current) => ({
            ...current,
            [response.assistantMessage!.id]: response.supportPlan!
          }));
        }
      } else {
        await loadMessages(sessionId);
      }
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "售后知识检索失败。");
    } finally {
      setPending(false);
    }
  }

  useEffect(() => {
    void loadBase();
  }, []);

  return (
    <div className="chat-workbench">
      <aside className="chat-sessions">
        <label className="kb-selector">
          <span>当前知识库</span>
          <select
            value={currentKb?.id ?? ""}
            onChange={(event) => {
              setSelectedKnowledgeBaseId(event.target.value);
              setCurrentSessionId("");
              setMessages([]);
            }}
          >
            {!knowledgeBases.length ? <option value="">暂无可用知识库</option> : null}
            {knowledgeBases.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <button
          className="new-chat-button"
          disabled={!currentKb || pending}
          onClick={() => {
            setCurrentSessionId("");
            setMessages([]);
          }}
          type="button"
        >
          <span className="material-symbols-outlined">add</span>
          新建会话
        </button>
        <div className="chat-session-list">
          {visibleSessions.map((session) => (
            <button
              className={`chat-session-item ${session.id === currentSessionId ? "active" : ""}`}
              key={session.id}
              onClick={() => void loadMessages(session.id)}
              type="button"
            >
              <strong>{session.title}</strong>
              <span>{formatDateTime(session.updatedAt)}</span>
            </button>
          ))}
          {visibleSessions.length === 0 ? <div className="empty-state">暂无会话记录。</div> : null}
        </div>
      </aside>

      <section className="chat-main">
        {error ? <div className="alert-error">{error}</div> : null}
        <div className="message-stream">
          <div className="chat-mobile-tools">
            <label>
              <span>知识库</span>
              <select
                value={currentKb?.id ?? ""}
                onChange={(event) => {
                  setSelectedKnowledgeBaseId(event.target.value);
                  setCurrentSessionId("");
                  setMessages([]);
                }}
              >
                {!knowledgeBases.length ? <option value="">暂无可用知识库</option> : null}
                {knowledgeBases.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              disabled={!currentKb || pending}
              onClick={() => {
                setCurrentSessionId("");
                setMessages([]);
              }}
            >
              新建会话
            </button>
          </div>
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div className="assistant-avatar">
                <span className="material-symbols-outlined fill-icon">support_agent</span>
              </div>
              <h2>开始一次售后诊断</h2>
              <p>当前知识库：{currentKb?.name ?? "暂无可用知识库"}</p>
              <div className="prompt-examples">
                <button type="button" onClick={() => setQuestion("客户反馈升级后接口偶发 502，日志里出现 connection reset，应该如何排查？")}>
                  接口 502 排查
                </button>
                <button type="button" onClick={() => setQuestion("设备离线后无法自动恢复，需要给一线支持哪些核查步骤？")}>
                  设备离线恢复
                </button>
                <button type="button" onClick={() => setQuestion("客户要求 SLA 升级，当前证据不足时应该如何回复？")}>
                  SLA 升级判断
                </button>
              </div>
            </div>
          ) : (
            <div className="message-column">
              {messages.map((message) => {
                const plan = message.role === "assistant" ? supportPlansByMessageId[message.id] : undefined;
                return (
                  <article className={`message-row message-row--${message.role}`} key={message.id}>
                    <div className="message-avatar">
                      <span className="material-symbols-outlined">{message.role === "user" ? "person" : "support_agent"}</span>
                    </div>
                    <div className="message-content">
                      <div className="message-meta">{message.role === "user" ? "提问" : "Agent 回答"} · {formatDateTime(message.createdAt)}</div>
                      <div className="message-bubble">
                        <p>{message.content}</p>
                      </div>
                      {plan ? <MessageSupportPlan plan={plan} /> : null}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <footer className="chat-composer">
          <select value={strategy} onChange={(event) => setStrategy(event.target.value)} aria-label="检索策略">
            {Object.entries(STRATEGY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="输入故障现象、日志报错、客户影响范围或工单诉求..." />
          <button className="send-button" disabled={pending || !question.trim() || !currentKb} onClick={submit} type="button">
            <span className="material-symbols-outlined">send</span>
            {pending ? "检索中" : "发送"}
          </button>
          <p>售后模式已启用 · 经业务后端桥接 AI 服务 · 默认返回诊断方案</p>
        </footer>
      </section>

      <aside className="chat-side-panel">
        <section className="citation-panel">
          <div className="citation-panel-head">
            <h2>证据与追踪</h2>
            <span className="material-symbols-outlined">fact_check</span>
          </div>
          <div className="trace-box">
            <h3>检索追踪</h3>
            <dl>
              <div><dt>策略</dt><dd>{STRATEGY_LABELS[strategy] ?? strategy}</dd></div>
              <div><dt>召回数量</dt><dd>{latestCitations.length || 5} 个片段</dd></div>
              <div><dt>知识库</dt><dd>{currentKb?.name ?? "--"}</dd></div>
            </dl>
            <i><b style={{ width: `${latestCitations.length ? Math.min(100, latestCitations.length * 18) : 45}%` }} /></i>
          </div>
          {latestSupportPlan ? (
            <div className="side-support-summary">
              <strong>{latestSupportPlan.escalation?.required ? "建议升级" : "一线可先处理"}</strong>
              <span>{latestSupportPlan.escalation?.ticketSummary || latestSupportPlan.issueSummary}</span>
            </div>
          ) : null}
          <div className="citation-list">
            {latestCitations.length > 0 ? latestCitations.map((item) => (
              <div className="citation-item" key={item.id}>
                <div className="citation-topline">
                  <span>[{item.id.slice(0, 4)}]</span>
                  <code>得分 {Math.round((item.score ?? 0) * 100) / 100}</code>
                </div>
                <strong>{item.title}</strong>
                <p>{item.snippet}</p>
                <small>{item.location || item.strategy}</small>
              </div>
            )) : <div className="empty-state">暂无引用。</div>}
          </div>
          <button className="export-trace-button" type="button" disabled={!latestCitations.length}>
            <span className="material-symbols-outlined">download</span>
            导出追踪 JSON
          </button>
        </section>
      </aside>
    </div>
  );
}
