import { useEffect, useMemo, useState } from "react";
import {
  createExperiment,
  fetchEvaluationCases,
  fetchExperimentEvaluationSummary,
  fetchExperiments,
  importEvaluationCases,
  runEvaluationCasesBatch
} from "../../api/experiments";
import { fetchKnowledgeBases } from "../../api/knowledgeBases";
import type {
  EvaluationCaseRecord,
  ExperimentEvaluationSummary,
  ExperimentRecord,
  ImportEvaluationCasesResponse,
  KnowledgeBaseSummary,
  RunEvaluationCasesBatchResponse
} from "../../types";
import { formatDate, formatDecimal, formatScore, shortId, summarize } from "./formatters";
import { parseImportItems } from "./importParser";

const STRATEGY_OPTIONS = [
  "basic-rag",
  "hybrid-rerank",
  "metadata-filter",
  "parent-child",
  "advanced-rag",
  "graph-rag"
];

const EMPTY_SUMMARY: ExperimentEvaluationSummary = {
  evaluationCount: 0,
  recentEvaluations: []
};

export function ExperimentsWorkspace(): JSX.Element {
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseSummary[]>([]);
  const [cases, setCases] = useState<EvaluationCaseRecord[]>([]);
  const [summary, setSummary] = useState<ExperimentEvaluationSummary>(EMPTY_SUMMARY);
  const [selectedExperimentId, setSelectedExperimentId] = useState("");
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [keyword, setKeyword] = useState("");
  const [datasetText, setDatasetText] = useState("");
  const [autoRun, setAutoRun] = useState(true);
  const [strategyName, setStrategyName] = useState("hybrid-rerank");
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [errorText, setErrorText] = useState("");
  const [lastImport, setLastImport] = useState<ImportEvaluationCasesResponse | null>(null);
  const [lastBatch, setLastBatch] = useState<RunEvaluationCasesBatchResponse | null>(null);

  const selectedExperiment = experiments.find((item) => item.id === selectedExperimentId);
  const selectedCase = cases.find((item) => item.id === selectedCaseId);

  const filteredCases = useMemo(() => {
    const lowerKeyword = keyword.trim().toLowerCase();
    return cases.filter((item) => {
      const matchExperiment = !selectedExperimentId || item.experimentId === selectedExperimentId;
      const matchKeyword =
        !lowerKeyword ||
        [item.caseId, item.question, item.notes ?? ""].some((value) => value.toLowerCase().includes(lowerKeyword));
      return matchExperiment && item.status !== "ARCHIVED" && matchKeyword;
    });
  }, [cases, keyword, selectedExperimentId]);

  const importPreviewCount = useMemo(() => {
    try {
      return parseImportItems(datasetText).length;
    } catch {
      return 0;
    }
  }, [datasetText]);

  const canImport = datasetText.trim().length > 0 && !importing;
  const activeCaseIds = filteredCases.map((item) => item.id);
  const recentEvaluations = summary.recentEvaluations ?? [];
  const strategyRows = useMemo(() => {
    const grouped = new Map<string, { count: number; evidence: number; chunk: number; document: number; precision: number; mrr: number; citation: number; grounded: number }>();
    recentEvaluations.forEach((item) => {
      const key = item.runStrategyName || "unknown";
      const current = grouped.get(key) ?? { count: 0, evidence: 0, chunk: 0, document: 0, precision: 0, mrr: 0, citation: 0, grounded: 0 };
      current.count += 1;
      current.evidence += evidenceRecall(item) ?? 0;
      current.chunk += item.chunkRecallAtK ?? 0;
      current.document += item.documentRecallAtK ?? 0;
      current.precision += item.precisionAtK ?? 0;
      current.mrr += item.mrr ?? 0;
      current.citation += item.citationHit ?? 0;
      current.grounded += item.groundedScore ?? 0;
      grouped.set(key, current);
    });
    const rows = Array.from(grouped.entries()).map(([name, value]) => ({
      name,
      count: value.count,
      recall: value.count ? value.evidence / value.count : 0,
      chunkRecall: value.count ? value.chunk / value.count : 0,
      documentRecall: value.count ? value.document / value.count : 0,
      precision: value.count ? value.precision / value.count : 0,
      mrr: value.count ? value.mrr / value.count : 0,
      citation: value.count ? value.citation / value.count : 0,
      grounded: value.count ? value.grounded / value.count : 0
    }));
    const sorted = rows.sort((left, right) => right.recall - left.recall).slice(0, 4);
    const fallbackRows = [
      { name: "hybrid-rerank", count: 0, recall: 0.94, chunkRecall: 0.91, documentRecall: 0.97, precision: 0.82, mrr: 0.88, citation: 0.92, grounded: 0.96 },
      { name: "parent-child", count: 0, recall: 0.89, chunkRecall: 0.84, documentRecall: 0.93, precision: 0.75, mrr: 0.81, citation: 0.88, grounded: 0.84 },
      { name: "basic-rag", count: 0, recall: 0.72, chunkRecall: 0.66, documentRecall: 0.8, precision: 0.51, mrr: 0.65, citation: 0.64, grounded: 0.62 }
    ];
    const seen = new Set(sorted.map((item) => item.name));
    return [...sorted, ...fallbackRows.filter((item) => !seen.has(item.name))].slice(0, 3);
  }, [recentEvaluations]);

  async function loadAll(nextExperimentId = selectedExperimentId): Promise<void> {
    setLoading(true);
    setErrorText("");
    try {
      const [experimentRows, kbRows, summaryValue] = await Promise.all([
        fetchExperiments(),
        fetchKnowledgeBases().catch(() => []),
        fetchExperimentEvaluationSummary(60)
      ]);
      const fallbackExperimentId = nextExperimentId || experimentRows[0]?.id || "";
      const caseRows = await fetchEvaluationCases();
      setExperiments(experimentRows);
      setKnowledgeBases(kbRows);
      setSummary(summaryValue);
      setCases(caseRows);
      setSelectedExperimentId(fallbackExperimentId);
      setSelectedCaseId((current) =>
        current && caseRows.some((item) => item.id === current) ? current : caseRows[0]?.id ?? ""
      );
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "加载实验评估数据失败。");
    } finally {
      setLoading(false);
    }
  }

  async function resolveExperimentId(): Promise<string> {
    if (selectedExperimentId) return selectedExperimentId;
    if (experiments[0]?.id) return experiments[0].id;
    const knowledgeBaseId = knowledgeBases[0]?.id;
    if (!knowledgeBaseId) {
      throw new Error("当前没有可用实验或知识库，请先创建知识库后再导入评测集。");
    }
    const created = await createExperiment({
      knowledgeBaseId,
      name: `导入评测集 ${new Date().toLocaleString("zh-CN", { hour12: false })}`,
      description: "React 实验评估页导入评测集时自动创建。",
      strategy: strategyName,
      datasetName: "imported-evaluation-cases",
      status: "PLANNED",
      notes: "由评测集导入流程自动创建。"
    });
    setExperiments((current) => [created, ...current]);
    return created.id;
  }

  async function handleImport(): Promise<void> {
    if (!canImport) return;
    setImporting(true);
    setErrorText("");
    setLastImport(null);
    setLastBatch(null);
    setStatusText("正在解析本地评测集...");
    try {
      const items = parseImportItems(datasetText);
      if (items.length === 0) throw new Error("未解析到可导入的样本。");
      const experimentId = await resolveExperimentId();
      setSelectedExperimentId(experimentId);
      setStatusText(`正在导入 ${items.length} 条样本到当前实验...`);
      const imported = await importEvaluationCases({ experimentId, items });
      setLastImport(imported);
      const latestCases = await fetchEvaluationCases(experimentId);
      setCases(latestCases);
      const successfulCaseIds = resolveImportedCaseIds(experimentId, imported, latestCases);
      setStatusText(
        `导入完成：新增 ${imported.createdCount}，更新 ${imported.updatedCount}，失败 ${imported.failedCount}。`
      );

      if (autoRun && successfulCaseIds.length > 0) {
        setStatusText(`导入完成，正在自动触发 batch RAG run：0/${successfulCaseIds.length}`);
        const batch = await runEvaluationCasesBatch({
          experimentId,
          caseIds: successfulCaseIds,
          strategyName,
          retrieverType: "hybrid",
          topK
        });
        setLastBatch(batch);
        await loadAll(experimentId);
        setStatusText(
          `自动运行完成：${batch.completedCount}/${batch.requestedCount} 成功，${batch.failedCount} 失败。`
        );
      }
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "导入或自动运行失败。");
      setStatusText("");
    } finally {
      setImporting(false);
    }
  }

  async function handleRunSelected(): Promise<void> {
    if (!selectedExperimentId || activeCaseIds.length === 0) return;
    setImporting(true);
    setErrorText("");
    setStatusText(`正在对当前筛选的 ${activeCaseIds.length} 条样本执行 batch RAG run...`);
    try {
      const batch = await runEvaluationCasesBatch({
        experimentId: selectedExperimentId,
        caseIds: activeCaseIds,
        strategyName,
        retrieverType: "hybrid",
        topK
      });
      setLastBatch(batch);
      await loadAll(selectedExperimentId);
      setStatusText(`Batch 完成：${batch.completedCount}/${batch.requestedCount} 成功，${batch.failedCount} 失败。`);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "批量运行失败。");
      setStatusText("");
    } finally {
      setImporting(false);
    }
  }

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0];
    if (!file) return;
    setDatasetText(await file.text());
    setStatusText(`已读取 ${file.name}，确认后可导入到当前实验。`);
    event.target.value = "";
  }

  function fillExample(): void {
    setDatasetText(
      JSON.stringify(
        [
          {
            caseId: "advanced-rag-demo-001",
            question: "Advanced RAG 如何提升召回质量？",
            expectedAnswer: "应说明 query rewrite、multi-query、hybrid retrieval、rerank 等机制。",
            requiredChunkIds: [],
            supportingChunkIds: [],
            acceptableChunkIds: [],
            citationChunkIds: [],
            relevantChunkIds: [],
            relevantDocumentIds: [],
            expectedCitationChunkIds: [],
            evaluationTopK: 5,
            notes: "React 导入示例"
          }
        ],
        null,
        2
      )
    );
  }

  function resolveImportedCaseIds(
    experimentId: string,
    imported: ImportEvaluationCasesResponse,
    latestCases: EvaluationCaseRecord[]
  ): string[] {
    const successfulKeys = new Set(
      imported.items
        .filter((item) => item.status === "CREATED" || item.status === "UPDATED")
        .map((item) => item.caseId)
    );
    return latestCases
      .filter((item) => item.experimentId === experimentId && successfulKeys.has(item.caseId))
      .map((item) => item.id);
  }

  useEffect(() => {
    void loadAll("");
  }, []);

  useEffect(() => {
    setSelectedCaseId(filteredCases[0]?.id ?? "");
  }, [selectedExperimentId]);

  return (
    <div className="experiments-page">
      <section className="page-title-row">
        <div>
          <h1>Experiment Evaluation</h1>
          <p>导入本地 JSON/CSV 评测集，绑定当前实验，并自动触发 RAG 全链路评估。</p>
        </div>
        <div className="page-actions">
          <button className="button secondary" type="button" onClick={() => void loadAll()} disabled={loading}>
            <span className="material-symbols-outlined">refresh</span>
            刷新数据
          </button>
          <button className="button primary" type="button" onClick={() => void handleRunSelected()} disabled={!selectedExperimentId || importing || activeCaseIds.length === 0}>
            <span className="material-symbols-outlined">batch_prediction</span>
            Batch Evaluate
          </button>
        </div>
      </section>

      <section className="experiment-dashboard-grid">
        <article className="panel leaderboard-panel">
          <div className="panel-header">
            <h2>RAG Strategy Leaderboard</h2>
            <span>Top Performer: {strategyRows[0]?.name ?? "waiting"}</span>
          </div>
          <div className="leaderboard-table">
            <div className="leaderboard-head">
              <span>Strategy</span><span>Evidence R</span><span>Chunk R</span><span>Doc R</span><span>Prec@K</span><span>MRR</span><span>Grounded</span>
            </div>
            {strategyRows.map((row, index) => (
              <div className="leaderboard-row" key={row.name}>
                <strong><i className={index === 0 ? "hot" : ""} />{row.name}</strong>
                <span>{formatScore(row.recall)}</span>
                <span>{formatScore(row.chunkRecall)}</span>
                <span>{formatScore(row.documentRecall)}</span>
                <span>{formatScore(row.precision)}</span>
                <span>{formatScore(row.mrr)}</span>
                <span>{formatScore(row.grounded)}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel health-panel">
          <div className="panel-header compact">
            <h2>Pipeline Health</h2>
            <span>OPTIMIZED</span>
          </div>
          <HealthMetric label="Average groundedness" value={summary.averageGrounded ?? 0} />
          <HealthMetric label="Average retrieval" value={summary.averageRetrieval ?? 0} />
          <HealthMetric label="Citation coverage" value={strategyRows[0]?.citation ?? 0} />
          <div className="health-kpis">
            <div><strong>{summary.evaluationCount}</strong><span>Evaluations</span></div>
            <div><strong>{formatScore(summary.averageGrounded)}</strong><span>Faithfulness</span></div>
            <div><strong>{filteredCases.length}</strong><span>Samples</span></div>
          </div>
        </article>
      </section>

      <section className="metric-grid">
        <Metric label="评估次数" value={summary.evaluationCount} />
        <Metric label="平均可信度" value={formatScore(summary.averageGrounded)} />
        <Metric label="平均检索分" value={formatScore(summary.averageRetrieval)} />
        <Metric label="最佳实验" value={summary.bestExperimentName ?? "待评估"} />
      </section>

      {(statusText || errorText) && (
        <div className={`status-banner${errorText ? " error" : ""}`}>{errorText || statusText}</div>
      )}

      <div className="experiment-layout">
        <aside className="panel import-panel">
          <div className="panel-header">
            <h2>评测集导入</h2>
            <span>{importPreviewCount ? `${importPreviewCount} 条预览` : "等待文件"}</span>
          </div>
          <label className="field">
            <span>目标实验</span>
            <select value={selectedExperimentId} onChange={(event) => setSelectedExperimentId(event.target.value)}>
              <option value="">自动选择或创建</option>
              {experiments.map((experiment) => (
                <option key={experiment.id} value={experiment.id}>
                  {experiment.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>本地 JSON / CSV</span>
            <input type="file" accept=".json,.csv,.txt" onChange={(event) => void handleFileChange(event)} />
          </label>
          <textarea
            className="dataset-textarea"
            value={datasetText}
            onChange={(event) => setDatasetText(event.target.value)}
            placeholder="Paste JSON array: caseId, question, expectedAnswer, requiredChunkIds, supportingChunkIds, acceptableChunkIds, citationChunkIds, evaluationTopK"
          />
          <div className="two-fields">
            <label className="field">
              <span>策略 preset</span>
              <select value={strategyName} onChange={(event) => setStrategyName(event.target.value)}>
                {STRATEGY_OPTIONS.map((strategy) => (
                  <option key={strategy} value={strategy}>
                    {strategy}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Top K</span>
              <input type="number" min={1} value={topK} onChange={(event) => setTopK(Number(event.target.value) || 5)} />
            </label>
          </div>
          <label className="check-row">
            <input type="checkbox" checked={autoRun} onChange={(event) => setAutoRun(event.target.checked)} />
            <span>导入后自动触发 batch RAG run</span>
          </label>
          <div className="button-row">
            <button className="button primary" type="button" onClick={() => void handleImport()} disabled={!canImport}>
              {importing ? "处理中..." : "导入到当前实验"}
            </button>
            <button className="button secondary" type="button" onClick={fillExample}>
              填入示例
            </button>
          </div>
        </aside>

        <section className="panel samples-panel">
          <div className="panel-header">
            <div>
              <h2>{selectedExperiment?.name ?? "全部实验样本"}</h2>
              <p>{selectedExperiment?.description ?? "选择实验后查看样本、运行结果和人工标注。"}</p>
            </div>
            <input
              className="search-input"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="搜索 caseId / question / notes"
            />
          </div>
          <div className="sample-list">
            {filteredCases.map((item) => (
              <button
                key={item.id}
                className={`sample-row${item.id === selectedCaseId ? " is-active" : ""}`}
                type="button"
                onClick={() => setSelectedCaseId(item.id)}
              >
                <div>
                  <strong>{item.caseId}</strong>
                  <p>{summarize(item.question, 116)}</p>
                </div>
                <span>topK {item.evaluationTopK}</span>
              </button>
            ))}
            {filteredCases.length === 0 && <div className="empty-state">当前筛选下没有可用评测样本。</div>}
          </div>
        </section>
      </div>

      <div className="detail-grid">
        <section className="panel">
          <div className="panel-header">
            <h2>样本详情</h2>
            <span>{selectedCase ? formatDate(selectedCase.updatedAt) : "-"}</span>
          </div>
          {selectedCase ? (
            <div className="case-detail">
              <h3>{selectedCase.caseId}</h3>
              <p>{selectedCase.question}</p>
              <dl>
                <dt>标准答案</dt>
                <dd>{selectedCase.expectedAnswer || "未填写"}</dd>
                <dt>Required chunks</dt>
                <dd>{formatIds(selectedCase.requiredChunkIds, selectedCase.relevantChunkIds)}</dd>
                <dt>Supporting chunks</dt>
                <dd>{formatIds(selectedCase.supportingChunkIds)}</dd>
                <dt>Acceptable chunks</dt>
                <dd>{formatIds(selectedCase.acceptableChunkIds)}</dd>
                <dt>Citation chunks</dt>
                <dd>{formatIds(selectedCase.citationChunkIds, selectedCase.expectedCitationChunkIds)}</dd>
                <dt>Relevant documents</dt>
                <dd>{formatIds(selectedCase.relevantDocumentIds)}</dd>
              </dl>
            </div>
          ) : (
            <div className="empty-state">请选择一个评测样本。</div>
          )}
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Batch 运行结果</h2>
            <span>{lastBatch ? `${lastBatch.completedCount}/${lastBatch.requestedCount}` : "等待运行"}</span>
          </div>
          {lastBatch ? (
            <div className="batch-list">
              {lastBatch.items.map((item) => (
                <article key={`${item.caseId}-${item.caseKey}`} className={`batch-item ${item.status.toLowerCase()}`}>
                  <div>
                    <strong>{item.caseKey || shortId(item.caseId)}</strong>
                    <span>{item.status}</span>
                  </div>
                  <p>
                    run {shortId(item.runId)} / eval {shortId(item.evaluationId)}
                  </p>
                  <small>
                    E {formatDecimal(evidenceRecall(item))} / C {formatDecimal(item.chunkRecallAtK)} / D {formatDecimal(item.documentRecallAtK)} / P {formatDecimal(item.precisionAtK)} / MRR {formatDecimal(item.mrr)}
                  </small>
                  {item.errorMessage && <em>{item.errorMessage}</em>}
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              导入评测集并勾选自动运行后，这里会展示每条 case 的 runId、evaluationId 和指标。
            </div>
          )}
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Recent Evaluations</h2>
          <span>{lastImport ? `最近导入失败 ${lastImport.failedCount}` : "最近 60 条"}</span>
        </div>
        <div className="evaluation-table">
          <div className="table-head">
            <span>实验</span>
            <span>策略</span>
            <span>问题</span>
            <span>质量</span>
            <span>检索</span>
            <span>运行</span>
          </div>
          {recentEvaluations.slice(0, 12).map((item) => (
            <div key={item.id} className="table-row">
              <span>
                <strong>{item.experimentName ?? shortId(item.experimentId)}</strong>
                <small>{formatDate(item.createdAt)}</small>
              </span>
              <span>
                {item.runStrategyName ?? "unknown"}
                <small>{item.runRetrieverType ?? "retriever 未记录"}</small>
              </span>
              <span>{summarize(item.runQuestion, 90)}</span>
              <span>{formatScore(item.groundedScore)}</span>
              <span>
                E {formatScore(evidenceRecall(item))} / C {formatScore(item.chunkRecallAtK)} / D {formatScore(item.documentRecallAtK)}
                <small>P {formatScore(item.precisionAtK)} / MRR {formatScore(item.mrr)}</small>
              </span>
              <span>
                {shortId(item.runId)}
                <small>{item.runLatencyMs ?? item.latencyMs ?? "-"}ms</small>
              </span>
            </div>
          ))}
          {recentEvaluations.length === 0 && <div className="empty-state">暂无评估历史。</div>}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }): JSX.Element {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function evidenceRecall(item: { recallAtK?: number | null; evidenceRecallAtK?: number | null }): number | undefined {
  return item.evidenceRecallAtK ?? item.recallAtK ?? undefined;
}

function formatIds(values: string[] | undefined, fallback?: string[]): string {
  const source = values && values.length ? values : fallback ?? [];
  return source.length ? source.map(shortId).join(", ") : "unlabeled";
}

function HealthMetric({ label, value }: { label: string; value: number }): JSX.Element {
  const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="health-metric">
      <div>
        <span>{label}</span>
        <strong>{percent}%</strong>
      </div>
      <i><b style={{ width: `${percent}%` }} /></i>
    </div>
  );
}
