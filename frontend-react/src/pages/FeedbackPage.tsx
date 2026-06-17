import { Send } from "lucide-react";
import { useState } from "react";
import { createFeedback } from "../api";
import { Button } from "../components/primitives/Button";
import { Panel } from "../components/primitives/Panel";
import "./pages.css";

export function FeedbackPage() {
  const [runId, setRunId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [messageId, setMessageId] = useState("");
  const [rating, setRating] = useState(4);
  const [feedbackType, setFeedbackType] = useState("QUALITY");
  const [comment, setComment] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function submit() {
    setPending(true);
    setError("");
    setSuccess("");
    try {
      await createFeedback({ runId, sessionId, messageId, rating, feedbackType, comment: comment.trim() || undefined });
      setSuccess("反馈已提交。");
      setComment("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交反馈失败。");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="page-canvas page-stack">
      <header className="page-header">
        <div>
          <h2>Feedback</h2>
          <p>反馈会关联到具体 run / session / message，便于回溯检索与生成质量。</p>
        </div>
      </header>
      {error ? <div className="alert-error">{error}</div> : null}
      {success ? <div className="alert-success">{success}</div> : null}
      <Panel title="提交反馈">
        <div className="stacked-form">
          <label><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} /></label>
          <label><span>Session ID</span><input value={sessionId} onChange={(event) => setSessionId(event.target.value)} /></label>
          <label><span>Message ID</span><input value={messageId} onChange={(event) => setMessageId(event.target.value)} /></label>
          <label><span>评分</span><input min={1} max={5} type="number" value={rating} onChange={(event) => setRating(Number(event.target.value))} /></label>
          <label>
            <span>类型</span>
            <select value={feedbackType} onChange={(event) => setFeedbackType(event.target.value)}>
              <option value="QUALITY">QUALITY</option>
              <option value="CITATION">CITATION</option>
              <option value="RETRIEVAL">RETRIEVAL</option>
              <option value="LATENCY">LATENCY</option>
            </select>
          </label>
          <label><span>备注</span><textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={4} /></label>
          <div className="toolbar">
            <Button
              icon={<Send />}
              variant="primary"
              disabled={pending || !runId.trim() || !sessionId.trim() || !messageId.trim()}
              onClick={submit}
            >
              提交反馈
            </Button>
          </div>
        </div>
      </Panel>
    </div>
  );
}
