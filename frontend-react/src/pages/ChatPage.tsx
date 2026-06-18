import { useEffect, useMemo, useState } from "react";
import { createChatSession, fetchChatMessages, fetchChatSessions, fetchKnowledgeBases, sendAssistantTurn } from "../api";
import type { AgentWorkflowStep, ChatMessageRecord, ChatSession, CitationSource, KnowledgeBaseSummary, SupportPlan } from "../types";
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

type PromptExample = {
  group: string;
  title: string;
  prompt: string;
  icon: string;
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

const AGENT_FLOW = [
  { key: "clarification", label: "问题澄清", icon: "contact_support", role: "补齐版本、范围和复现条件" },
  { key: "retrieval", label: "知识检索", icon: "travel_explore", role: "召回手册、SOP、历史工单" },
  { key: "code_log", label: "日志分析", icon: "terminal", role: "识别错误码、链路和异常信号" },
  { key: "diagnosis", label: "原因诊断", icon: "troubleshoot", role: "形成可验证的排查路径" },
  { key: "risk", label: "风险审查", icon: "policy", role: "检查 SLA、数据和变更风险" },
  { key: "escalation", label: "升级建议", icon: "assignment_add", role: "判断是否转二线或研发" },
  { key: "evaluation", label: "回答质检", icon: "fact_check", role: "核对证据覆盖与下一步" }
];

const PROMPT_EXAMPLES: PromptExample[] = [
  {
    group: "故障排查",
    title: "接口 502 间歇失败",
    icon: "sync_problem",
    prompt: "客户反馈升级后接口偶发 502，日志里出现 connection reset。请按一线售后排查流程给出判断、证据和下一步。"
  },
  {
    group: "设备与链路",
    title: "设备离线无法恢复",
    icon: "sensors_off",
    prompt: "设备离线后无法自动恢复，客户现场网络曾短暂抖动。需要给一线支持哪些核查步骤和客户回复口径？"
  },
  {
    group: "SLA 与升级",
    title: "证据不足时是否升级",
    icon: "priority_high",
    prompt: "客户要求 SLA 升级，但当前只有截图和口头描述，缺少日志。请判断是否升级、还需要哪些证据、如何回复客户。"
  },
  {
    group: "数据与配置",
    title: "配置变更后数据异常",
    icon: "manage_search",
    prompt: "客户在配置变更后发现统计数据异常，请帮我整理排查顺序、风险提醒、需要留存的证据和回滚建议。"
  }
];

function textValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function arrayValue(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : [];
}

function displayValue(value: unknown, fallback = "--"): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function matchWorkflowStep(steps: AgentWorkflowStep[], key: string): AgentWorkflowStep | undefined {
  const loweredKey = key.replace("_", "-");
  return steps.find((step) => {
    const raw = `${step.name} ${step.detail ?? ""}`.toLowerCase();
    return raw.includes(key) || raw.includes(loweredKey);
  });
}

function workflowStepState(step: AgentWorkflowStep | undefined, traceAttributes: Record<string, unknown>, key: string): "done" | "skipped" | "waiting" {
  const completed = arrayValue(traceAttributes.completed_gates);
  const skipped = arrayValue(traceAttributes.skipped_gates);
  if (step || completed.some((item) => item.includes(key))) return "done";
  if (skipped.some((item) => item.includes(key))) return "skipped";
  return "waiting";
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
  const pageLocation = pageNumber ? `第 ${pageNumber} 页` : undefined;
  const location = textValue(value.location) ?? sourcePath ?? sheetName ?? pageLocation ?? chunkId ?? title;

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

function SupportPlanBlock({ title, icon, tone, items }: { title: string; icon: string; tone?: "warning" | "success"; items: string[] }) {
  return (
    <section className={`support-plan-block ${tone ? `support-plan-block--${tone}` : ""}`}>
      <h4>
        <span className="material-symbols-outlined">{icon}</span>
        {title}
      </h4>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function MessageSupportPlan({ plan }: { plan: SupportPlan }) {
  const clarificationQuestions = listOrFallback(plan.clarificationQuestions, ["请补充产品版本、故障时间、影响范围、关键日志和最近变更。"]);
  const nextActions = listOrFallback(plan.nextActions, ["按诊断步骤执行，记录客户反馈，并在证据不足时转人工复核。"]);
  const riskNotes = listOrFallback(plan.riskNotes, ["回答必须保留证据引用；无法确认根因时不要承诺修复时效。"]);
  const evidenceReferences = listOrFallback(plan.evidenceReferences, ["结合右侧证据与追踪面板核查来源。"]);

  return (
    <section className="support-plan-card">
      <header className="support-plan-card__head">
        <div className="support-plan-card__mark">
          <span className="material-symbols-outlined fill-icon">support_agent</span>
        </div>
        <div>
          <span className="support-plan-eyebrow">售后诊断方案</span>
          <h3>{plan.issueSummary || "已根据知识库证据生成排查建议"}</h3>
        </div>
      </header>

      <div className="support-verdict">
        <div>
          <span>处理结论</span>
          <strong>{plan.escalation?.required ? "建议升级处理" : "一线可先按流程处理"}</strong>
        </div>
        <div>
          <span>严重程度</span>
          <strong>{plan.escalation?.severity ? SEVERITY_LABELS[plan.escalation.severity] ?? plan.escalation.severity : "待确认"}</strong>
        </div>
        <div>
          <span>升级队列</span>
          <strong>{plan.escalation?.suggestedQueue || "按默认售后队列"}</strong>
        </div>
      </div>

      {plan.escalation?.reason ? (
        <div className="support-escalation-note">
          <span className="material-symbols-outlined">report</span>
          <p>{plan.escalation.reason}</p>
        </div>
      ) : null}

      {plan.diagnosticSteps?.length ? (
        <section className="diagnostic-section">
          <h4>排查路径</h4>
          <ol className="diagnostic-steps">
            {plan.diagnosticSteps.map((step, index) => (
              <li key={`${step.order ?? index}-${step.action}`}>
                <span>{step.order ?? index + 1}</span>
                <div>
                  <strong>{step.action}</strong>
                  {step.expectedSignal ? <p>预期信号：{step.expectedSignal}</p> : null}
                  {step.evidenceHint ? <p>证据提示：{step.evidenceHint}</p> : null}
                  {step.fallback ? <p>兜底动作：{step.fallback}</p> : null}
                </div>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      <div className="support-plan-grid">
        <SupportPlanBlock title="需要澄清" icon="help" items={clarificationQuestions} />
        <SupportPlanBlock title="证据依据" icon="fact_check" tone="success" items={evidenceReferences} />
        <SupportPlanBlock title="风险提醒" icon="shield" tone="warning" items={riskNotes} />
        <SupportPlanBlock title="下一步动作" icon="flag" items={nextActions} />
      </div>
    </section>
  );
}

function AgentWorkflowPanel({
  steps,
  traceAttributes
}: {
  steps: AgentWorkflowStep[];
  traceAttributes: Record<string, unknown>;
}) {
  const completedGates = arrayValue(traceAttributes.completed_gates);
  const requiredGates = arrayValue(traceAttributes.required_gates);
  const skippedGates = arrayValue(traceAttributes.skipped_gates);
  const completionRate = requiredGates.length
    ? Math.round((completedGates.length / Math.max(1, requiredGates.length)) * 100)
    : steps.length
      ? Math.min(100, Math.round((steps.length / AGENT_FLOW.length) * 100))
      : 0;

  return (
    <section className="agent-flow-panel">
      <header className="agent-flow-panel__head">
        <div>
          <span>Agent supervisor</span>
          <h3>本轮编排进度</h3>
          <p>{displayValue(traceAttributes.workflow_runtime, "等待调用")} · {displayValue(traceAttributes.final_status ?? traceAttributes.workflow_status, "未运行")}</p>
        </div>
        <strong>{completionRate}%</strong>
      </header>
      <div className="agent-flow-progress" aria-label="Agent 编排完成度">
        <i style={{ width: `${completionRate}%` }} />
      </div>
      <ol className="agent-flow-list">
        {AGENT_FLOW.map((agent) => {
          const step = matchWorkflowStep(steps, agent.key);
          const state = workflowStepState(step, traceAttributes, agent.key);
          const statusLabel = state === "done" ? "已完成" : state === "skipped" ? "已跳过" : "等待触发";
          return (
            <li className={`agent-flow-item agent-flow-item--${state}`} key={agent.key}>
              <span className="material-symbols-outlined">{agent.icon}</span>
              <div>
                <strong>{agent.label}</strong>
                <small>{step?.detail || `${statusLabel} · ${agent.role}`}</small>
              </div>
              <em>{statusLabel}</em>
            </li>
          );
        })}
      </ol>
      <dl className="agent-gate-summary">
        <div><dt>必过关卡</dt><dd>{requiredGates.length || "--"}</dd></div>
        <div><dt>已完成</dt><dd>{completedGates.length || "--"}</dd></div>
        <div><dt>已跳过</dt><dd>{skippedGates.length || "--"}</dd></div>
      </dl>
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
  const [workflowStepsByMessageId, setWorkflowStepsByMessageId] = useState<Record<string, AgentWorkflowStep[]>>({});
  const [traceAttributesByMessageId, setTraceAttributesByMessageId] = useState<Record<string, Record<string, unknown>>>({});
  const [question, setQuestion] = useState("");
  const [strategy, setStrategy] = useState("advanced-rag");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const currentKb = knowledgeBases.find((item) => item.id === selectedKnowledgeBaseId) ?? knowledgeBases[0];
  const latestAssistant = latestAssistantMessage(messages);
  const latestSupportPlan = latestAssistant ? supportPlansByMessageId[latestAssistant.id] : undefined;
  const latestWorkflowSteps = latestAssistant ? workflowStepsByMessageId[latestAssistant.id] ?? [] : [];
  const latestTraceAttributes = latestAssistant ? traceAttributesByMessageId[latestAssistant.id] ?? {} : {};
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
        setWorkflowStepsByMessageId((current) => ({
          ...current,
          [response.assistantMessage!.id]: response.workflowSteps ?? []
        }));
        setTraceAttributesByMessageId((current) => ({
          ...current,
          [response.assistantMessage!.id]: response.traceAttributes ?? {}
        }));
      } else {
        await loadMessages(sessionId);
      }
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "售后知识检索失败，请稍后重试。");
    } finally {
      setPending(false);
    }
  }

  useEffect(() => {
    void loadBase();
  }, []);

  return (
    <div className="chat-workbench">
      <aside className="chat-sessions" aria-label="会话列表">
        <div className="chat-sessions__title">
          <span className="material-symbols-outlined">headset_mic</span>
          <div>
            <strong>售后问答</strong>
            <small>按知识库管理会话</small>
          </div>
        </div>
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
          新建售后问题
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
          {visibleSessions.length === 0 ? (
            <div className="empty-state">
              <span className="material-symbols-outlined">forum</span>
              <p>暂无会话记录</p>
              <small>提交第一个售后问题后会自动建档。</small>
            </div>
          ) : null}
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
              新建
            </button>
          </div>
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div className="chat-empty__header">
                <div className="assistant-avatar">
                  <span className="material-symbols-outlined fill-icon">support_agent</span>
                </div>
                <div>
                  <span>售后技术支持工作台</span>
                  <h2>把客户现象整理成可执行的排查结论</h2>
                  <p>当前知识库：{currentKb?.name ?? "暂无可用知识库"}。建议输入故障现象、环境版本、影响范围、日志片段和客户诉求。</p>
                </div>
              </div>
              <div className="empty-guide">
                <div><strong>1</strong><span>先确认客户影响面和紧急程度</span></div>
                <div><strong>2</strong><span>再让 Agent 检索手册、SOP 和历史工单</span></div>
                <div><strong>3</strong><span>最后输出结论、证据、风险和下一步</span></div>
              </div>
              <div className="prompt-examples" aria-label="示例问题">
                {PROMPT_EXAMPLES.map((example) => (
                  <button type="button" key={example.title} onClick={() => setQuestion(example.prompt)}>
                    <span className="material-symbols-outlined">{example.icon}</span>
                    <small>{example.group}</small>
                    <strong>{example.title}</strong>
                  </button>
                ))}
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
                      <div className="message-meta">{message.role === "user" ? "客户问题" : "Agent 回复"} · {formatDateTime(message.createdAt)}</div>
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
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="输入故障现象、日志报错、客户影响范围、SLA 诉求或已尝试的处理动作..."
          />
          <button className="send-button" disabled={pending || !question.trim() || !currentKb} onClick={submit} type="button">
            <span className="material-symbols-outlined">send</span>
            {pending ? "分析中" : "发送"}
          </button>
          <p>售后模式已启用 · 默认生成诊断方案 · 输出需包含证据和风险提示</p>
        </footer>
      </section>

      <aside className="chat-side-panel" aria-label="证据与编排">
        <section className="citation-panel">
          <header className="citation-panel-head">
            <div>
              <span>核查区</span>
              <h2>证据与追踪</h2>
            </div>
            <span className="material-symbols-outlined">fact_check</span>
          </header>
          <div className="trace-box">
            <h3>检索追踪</h3>
            <dl>
              <div><dt>策略</dt><dd>{STRATEGY_LABELS[strategy] ?? strategy}</dd></div>
              <div><dt>引用片段</dt><dd>{latestCitations.length || 0} 条</dd></div>
              <div><dt>知识库</dt><dd>{currentKb?.name ?? "--"}</dd></div>
              <div><dt>Trace</dt><dd>{latestAssistant?.traceId || displayValue(latestTraceAttributes.rag_trace_id)}</dd></div>
            </dl>
            <i><b style={{ width: `${latestCitations.length ? Math.min(100, latestCitations.length * 18) : 12}%` }} /></i>
          </div>
          <AgentWorkflowPanel steps={latestWorkflowSteps} traceAttributes={latestTraceAttributes} />
          {latestSupportPlan ? (
            <div className="side-support-summary">
              <span>{latestSupportPlan.escalation?.required ? "建议升级" : "一线处理"}</span>
              <strong>{latestSupportPlan.escalation?.ticketSummary || latestSupportPlan.issueSummary}</strong>
            </div>
          ) : (
            <div className="side-support-summary side-support-summary--empty">
              <span>等待回答</span>
              <strong>提交问题后会显示结论摘要、编排状态和引用证据。</strong>
            </div>
          )}
          <div className="citation-list">
            {latestCitations.length > 0 ? latestCitations.map((item, index) => (
              <article className="citation-item" key={item.id}>
                <div className="citation-topline">
                  <span>证据 {index + 1}</span>
                  <code>得分 {Math.round((item.score ?? 0) * 100) / 100}</code>
                </div>
                <strong>{item.title}</strong>
                <p>{item.snippet}</p>
                <small>{item.location || item.strategy}</small>
              </article>
            )) : (
              <div className="empty-state">
                <span className="material-symbols-outlined">article</span>
                <p>暂无引用证据</p>
                <small>Agent 回复后将在这里列出知识来源。</small>
              </div>
            )}
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
