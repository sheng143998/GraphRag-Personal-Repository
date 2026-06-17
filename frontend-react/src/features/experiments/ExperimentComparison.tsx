import { useEffect, useMemo, useState } from "react";
import { fetchExperimentEvaluationSummary, fetchExperiments } from "../../api/experiments";
import type { ExperimentEvaluationHistory, ExperimentEvaluationSummary, ExperimentRecord } from "../../types";
import { formatCost, formatDate, formatScore, scoreWidth, shortId, summarize } from "./formatters";

interface AggregateRow {
  key: string;
  experimentId: string;
  experimentName: string;
  strategy: string;
  count: number;
  averageGrounded?: number;
  averageRetrieval?: number;
  averageRecallAtK?: number;
  averagePrecisionAtK?: number;
  averageMrr?: number;
  averageCitationHit?: number;
  averageTotalTokens?: number;
  averageEstimatedCost?: number;
  averageLatencyMs?: number;
  quality?: number;
  latestAt: string;
  latestStrategy: string;
}

const EMPTY_SUMMARY: ExperimentEvaluationSummary = {
  evaluationCount: 0,
  recentEvaluations: []
};

export function ExperimentComparison(): JSX.Element {
  const [summary, setSummary] = useState<ExperimentEvaluationSummary>(EMPTY_SUMMARY);
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [selectedExperimentId, setSelectedExperimentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState("");

  const recentRows = summary.recentEvaluations ?? [];
  const filteredRows = useMemo(
    () =>
      recentRows.filter(
        (item) =>
          (!selectedStrategy || (item.runStrategyName ?? "unknown") === selectedStrategy) &&
          (!selectedExperimentId || item.experimentId === selectedExperimentId)
      ),
    [recentRows, selectedExperimentId, selectedStrategy]
  );

  const strategyOptions = useMemo(
    () => [...new Set(recentRows.map((item) => item.runStrategyName ?? "unknown"))].sort(),
    [recentRows]
  );

  const experimentOptions = useMemo(() => {
    const options = new Map<string, string>();
    for (const item of recentRows) {
      options.set(item.experimentId, item.experimentName ?? experimentName(item.experimentId, experiments));
    }
    return [...options.entries()].map(([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name));
  }, [experiments, recentRows]);

  const strategyRows = useMemo(
    () => aggregateRows(filteredRows, (item) => item.runStrategyName ?? "unknown").sort(sortByQuality),
    [filteredRows]
  );

  const experimentRows = useMemo(
    () => aggregateRows(filteredRows, (item) => item.experimentId).sort(sortByQuality),
    [filteredRows]
  );

  async function loadData(): Promise<void> {
    setLoading(true);
    setErrorText("");
    try {
      const [summaryValue, experimentRowsValue] = await Promise.all([
        fetchExperimentEvaluationSummary(100),
        fetchExperiments().catch(() => [])
      ]);
      setSummary(summaryValue);
      setExperiments(experimentRowsValue);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "加载实验对比数据失败。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  return (
    <div className="experiments-page">
      <section className="page-title-row">
        <div>
          <h1>RAG Strategy Comparison</h1>
          <p>按最近评估记录聚合 Recall、Precision、MRR、Citation、Tokens、Cost 和延迟。</p>
        </div>
        <button className="button secondary" type="button" onClick={() => void loadData()} disabled={loading}>
          刷新对比
        </button>
      </section>

      <section className="metric-grid">
        <Metric label="评估次数" value={summary.evaluationCount} />
        <Metric label="平均可信度" value={formatScore(summary.averageGrounded)} />
        <Metric label="平均检索分" value={formatScore(summary.averageRetrieval)} />
        <Metric label="最佳实验" value={summary.bestExperimentName ?? "待评估"} />
      </section>

      {errorText && <div className="status-banner error">{errorText}</div>}

      <section className="panel">
        <div className="comparison-filter-bar">
          <label className="field">
            <span>策略</span>
            <select value={selectedStrategy} onChange={(event) => setSelectedStrategy(event.target.value)}>
              <option value="">全部策略</option>
              {strategyOptions.map((strategy) => (
                <option key={strategy} value={strategy}>
                  {strategy}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>实验</span>
            <select value={selectedExperimentId} onChange={(event) => setSelectedExperimentId(event.target.value)}>
              <option value="">全部实验</option>
              {experimentOptions.map((experiment) => (
                <option key={experiment.id} value={experiment.id}>
                  {experiment.name}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button secondary"
            type="button"
            onClick={() => {
              setSelectedStrategy("");
              setSelectedExperimentId("");
            }}
            disabled={!selectedStrategy && !selectedExperimentId}
          >
            清除筛选
          </button>
        </div>
      </section>

      {summary.evaluationCount === 0 ? (
        <section className="panel empty-state">暂无持久化评估记录，请先在实验页导入评测集并运行 batch。</section>
      ) : (
        <div className="comparison-grid">
          <section className="panel">
            <div className="panel-header">
              <h2>策略指标排行</h2>
              <span>{strategyRows.length} 个策略</span>
            </div>
            <div className="comparison-list">
              {strategyRows.map((row) => (
                <article className="comparison-row" key={row.key}>
                  <div className="comparison-row-main">
                    <strong>{row.strategy}</strong>
                    <span>{row.count} 次评估</span>
                  </div>
                  <ScoreBar label="Grounded" value={row.averageGrounded} />
                  <ScoreBar label="Retrieval" value={row.averageRetrieval} />
                  <div className="metric-chip-row">
                    <span>Recall {formatScore(row.averageRecallAtK)}</span>
                    <span>Precision {formatScore(row.averagePrecisionAtK)}</span>
                    <span>MRR {formatScore(row.averageMrr)}</span>
                    <span>Citation {formatScore(row.averageCitationHit)}</span>
                  </div>
                  <p className="item-meta">
                    最近 {formatDate(row.latestAt)} / 延迟 {row.averageLatencyMs ? Math.round(row.averageLatencyMs) : "-"}ms
                    / Tokens {row.averageTotalTokens ? Math.round(row.averageTotalTokens) : "-"} / Cost{" "}
                    {formatCost(row.averageEstimatedCost)}
                  </p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>实验排行</h2>
              <span>{experimentRows.length} 个实验</span>
            </div>
            <div className="comparison-list">
              {experimentRows.map((row) => (
                <article className="comparison-row compact" key={row.key}>
                  <div className="comparison-row-main">
                    <strong>{row.experimentName}</strong>
                    <span>{row.count} 次评估</span>
                  </div>
                  <dl className="compact-metrics">
                    <div>
                      <dt>质量</dt>
                      <dd>{formatScore(row.quality)}</dd>
                    </div>
                    <div>
                      <dt>可信 / 检索</dt>
                      <dd>
                        {formatScore(row.averageGrounded)} / {formatScore(row.averageRetrieval)}
                      </dd>
                    </div>
                    <div>
                      <dt>最近策略</dt>
                      <dd>{row.latestStrategy}</dd>
                    </div>
                    <div>
                      <dt>Recall / MRR</dt>
                      <dd>
                        {formatScore(row.averageRecallAtK)} / {formatScore(row.averageMrr)}
                      </dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          </section>
        </div>
      )}

      <section className="panel">
        <div className="panel-header">
          <h2>Recent Evaluations</h2>
          <span>{filteredRows.length} 条</span>
        </div>
        <div className="evaluation-table">
          <div className="table-head">
            <span>实验</span>
            <span>策略</span>
            <span>问题</span>
            <span>质量</span>
            <span>Retrieval</span>
            <span>运行成本</span>
          </div>
          {filteredRows.map((evaluation) => (
            <div className="table-row" key={evaluation.id}>
              <span>
                <strong>{evaluation.experimentName ?? experimentName(evaluation.experimentId, experiments)}</strong>
                <small>{formatDate(evaluation.createdAt)}</small>
              </span>
              <span>
                {evaluation.runStrategyName ?? "unknown"}
                <small>{evaluation.runRetrieverType ?? "retriever 未记录"}</small>
              </span>
              <span>{summarize(evaluation.runQuestion, 96)}</span>
              <span>
                {formatScore(evaluation.groundedScore)}
                <small>{formatScore(evaluation.retrievalScore)}</small>
              </span>
              <span>
                R {formatScore(evaluation.recallAtK)} / P {formatScore(evaluation.precisionAtK)}
                <small>
                  MRR {formatScore(evaluation.mrr)} / Citation {formatScore(evaluation.citationHit)}
                </small>
              </span>
              <span>
                {shortId(evaluation.runId)}
                <small>
                  {evaluation.totalTokens ?? "-"} tokens / {formatCost(evaluation.estimatedCost)}
                </small>
                <small>{stageLatencySummary(evaluation)}</small>
              </span>
            </div>
          ))}
          {filteredRows.length === 0 && <div className="empty-state">当前筛选下没有评估记录。</div>}
        </div>
      </section>
    </div>
  );
}

function aggregateRows(
  evaluations: ExperimentEvaluationHistory[],
  keyFor: (evaluation: ExperimentEvaluationHistory) => string
): AggregateRow[] {
  const groups = new Map<string, ExperimentEvaluationHistory[]>();
  for (const evaluation of evaluations) {
    const key = keyFor(evaluation);
    groups.set(key, [...(groups.get(key) ?? []), evaluation]);
  }

  return [...groups.entries()].map(([key, items]) => {
    const sorted = [...items].sort((left, right) => right.createdAt.localeCompare(left.createdAt));
    const latest = sorted[0];
    const averageGrounded = average(items.map((item) => item.groundedScore));
    const averageRetrieval = average(items.map((item) => item.retrievalScore));
    const averageRecallAtK = average(items.map((item) => item.recallAtK));
    const averagePrecisionAtK = average(items.map((item) => item.precisionAtK));
    const averageMrr = average(items.map((item) => item.mrr));
    const averageCitationHit = average(items.map((item) => item.citationHit));

    return {
      key,
      experimentId: latest.experimentId,
      experimentName: latest.experimentName ?? latest.experimentId,
      strategy: latest.runStrategyName ?? key,
      count: items.length,
      averageGrounded,
      averageRetrieval,
      averageRecallAtK,
      averagePrecisionAtK,
      averageMrr,
      averageCitationHit,
      averageTotalTokens: average(items.map((item) => item.totalTokens)),
      averageEstimatedCost: average(items.map((item) => item.estimatedCost)),
      averageLatencyMs: average(items.map((item) => item.latencyMs ?? item.runLatencyMs)),
      quality: average([
        averageGrounded,
        averageRetrieval,
        averageRecallAtK,
        averagePrecisionAtK,
        averageMrr,
        averageCitationHit
      ]),
      latestAt: latest.createdAt,
      latestStrategy: latest.runStrategyName ?? "unknown"
    };
  });
}

function average(values: Array<number | null | undefined>): number | undefined {
  const valid = values.filter((value): value is number => value != null);
  if (valid.length === 0) return undefined;
  return valid.reduce((sum, value) => sum + value, 0) / valid.length;
}

function sortByQuality(left: AggregateRow, right: AggregateRow): number {
  return (right.quality ?? 0) - (left.quality ?? 0);
}

function experimentName(id: string, experiments: ExperimentRecord[]): string {
  return experiments.find((experiment) => experiment.id === id)?.name ?? shortId(id);
}

function stageLatencySummary(evaluation: ExperimentEvaluationHistory): string {
  return [
    ["Emb", evaluation.embeddingLatencyMs],
    ["Ret", evaluation.retrievalLatencyMs],
    ["Rerank", evaluation.rerankLatencyMs],
    ["LLM", evaluation.llmLatencyMs]
  ]
    .filter((item): item is [string, number] => item[1] != null)
    .map(([label, value]) => `${label} ${value}ms`)
    .join(" / ");
}

function Metric({ label, value }: { label: string; value: React.ReactNode }): JSX.Element {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ScoreBar({ label, value }: { label: string; value?: number }): JSX.Element {
  return (
    <div className="score-bar">
      <span>{label}</span>
      <div className="score-track">
        <div className="score-fill" style={{ width: scoreWidth(value) }} />
      </div>
      <strong>{formatScore(value)}</strong>
    </div>
  );
}
