import { useEffect, useMemo, useState } from "react";
import { createChatSession, fetchChatMessages, fetchChatSessions, fetchKnowledgeBases, sendAssistantTurn } from "../api";
import type { ChatMessageRecord, ChatSession, CitationSource, KnowledgeBaseSummary } from "../types";
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
  const title = textValue(value.title) ?? sourcePath ?? documentId ?? chunkId ?? `Source ${index + 1}`;
  const preview = textValue(metadata.content_preview) ?? textValue(metadata.preview) ?? textValue(value.snippet);
  const pageNumber = value.pageNumber ?? value.page_number;
  const sheetName = textValue(value.sheetName) ?? textValue(value.sheet_name);
  const location = textValue(value.location) ?? sourcePath ?? sheetName ?? (pageNumber ? `page ${pageNumber}` : undefined) ?? chunkId ?? title;

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

export function ChatPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseSummary[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState("");
  const [messages, setMessages] = useState<ChatMessageRecord[]>([]);
  const [question, setQuestion] = useState("");
  const [strategy, setStrategy] = useState("advanced-rag");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const currentKb = knowledgeBases[0];

  const latestCitations = useMemo(() => {
    const latest = [...messages].reverse().find((item) => item.role === "assistant" && item.citations);
    return parseCitations(latest?.citations);
  }, [messages]);

  async function loadBase() {
    const [kbList, sessionList] = await Promise.allSettled([fetchKnowledgeBases(), fetchChatSessions()]);
    if (kbList.status === "fulfilled") setKnowledgeBases(kbList.value);
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
        retrievalOptions: {}
      });
      if (response.userMessage && response.assistantMessage) {
        setMessages((current) => [...current, response.userMessage!, response.assistantMessage!]);
      } else {
        await loadMessages(sessionId);
      }
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "RAG 提问失败。");
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
        <button className="new-chat-button" disabled={!currentKb || pending} onClick={() => {
          setCurrentSessionId("");
          setMessages([]);
        }} type="button">
          <span className="material-symbols-outlined">add</span>
          New Chat
        </button>
        <div className="chat-session-list">
          {sessions.map((session) => (
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
        </div>
      </aside>

      <section className="chat-main">
        {error ? <div className="alert-error">{error}</div> : null}
        <div className="message-stream">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div className="assistant-avatar">
                <span className="material-symbols-outlined fill-icon">smart_toy</span>
              </div>
              <h2>Start a RAG analysis</h2>
              <p>Current knowledge base: {currentKb?.name ?? "No knowledge base available"}</p>
            </div>
          ) : (
            <div className="message-column">
              {messages.map((message) => (
                <article className={`message-row message-row--${message.role}`} key={message.id}>
                  <div className="message-avatar">
                    <span className="material-symbols-outlined">{message.role === "user" ? "person" : "smart_toy"}</span>
                  </div>
                  <div className="message-content">
                    <div className="message-meta">{message.role === "user" ? "User" : "Assistant"} · {formatDateTime(message.createdAt)}</div>
                    <div className="message-bubble">
                      <p>{message.content}</p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <footer className="chat-composer">
          <select value={strategy} onChange={(event) => setStrategy(event.target.value)}>
            <option value="advanced-rag">advanced-rag</option>
            <option value="hybrid-rerank">hybrid-rerank</option>
            <option value="parent-child">parent-child</option>
            <option value="graph-rag">graph-rag</option>
          </select>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question about your knowledge base..." />
          <button className="send-button" disabled={pending || !question.trim() || !currentKb} onClick={submit} type="button">
            <span className="material-symbols-outlined">send</span>
            {pending ? "Running" : "Send"}
          </button>
          <p>RAG SYSTEM ACTIVE · MODEL: OpenAI-compatible · TEMP: 0.2</p>
        </footer>
      </section>

      <aside className="chat-side-panel">
        <section className="citation-panel">
          <div className="citation-panel-head">
            <h2>Source & Context</h2>
            <span className="material-symbols-outlined">close</span>
          </div>
          <div className="trace-box">
            <h3>RETRIEVAL TRACE</h3>
            <dl>
              <div><dt>Strategy</dt><dd>{strategy}</dd></div>
              <div><dt>Top-K</dt><dd>5 chunks</dd></div>
              <div><dt>Knowledge Base</dt><dd>{currentKb?.name ?? "--"}</dd></div>
            </dl>
            <i><b /></i>
          </div>
          <div className="citation-list">
            {latestCitations.length > 0 ? latestCitations.map((item) => (
              <div className="citation-item" key={item.id}>
                <div className="citation-topline">
                  <span>[{item.id.slice(0, 4)}]</span>
                  <code>score: {Math.round((item.score ?? 0) * 100) / 100}</code>
                </div>
                <strong>{item.title}</strong>
                <p>{item.snippet}</p>
                <small>{item.location || item.strategy}</small>
              </div>
            )) : <div className="empty-state">暂无引用。</div>}
          </div>
          <button className="export-trace-button" type="button">
            <span className="material-symbols-outlined">download</span>
            Export Trace JSON
          </button>
        </section>
      </aside>
    </div>
  );
}
