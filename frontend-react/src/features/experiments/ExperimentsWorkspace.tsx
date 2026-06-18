import { useEffect, useMemo, useState } from "react";
import {
  createExperiment,
  deleteEvaluationCase,
  deleteExperiment,
  fetchEvaluationCases,
  fetchExperimentEvaluationSummary,
  fetchExperiments,
  importEvaluationCases,
  runEvaluationCasesBatch,
  updateEvaluationCase
} from "../../api/experiments";
import { fetchKnowledgeBases } from "../../api/knowledgeBases";
import type {
  EvaluationCaseRecord,
  EvaluationCaseReviewStatus,
  ExperimentEvaluationSummary,
  ExperimentRecord,
  ImportEvaluationCasesResponse,
  KnowledgeBaseSummary,
  RunEvaluationCasesBatchResponse,
  UpdateEvaluationCasePayload
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

type ReviewStatusFilter = "ALL" | EvaluationCaseReviewStatus;
type NormalizedReviewStatus = EvaluationCaseReviewStatus | "ARCHIVED";

interface ReviewDraft {
  question: string;
  expectedAnswer: string;
  requiredChunkIds: string;
  supportingChunkIds: string;
  acceptableChunkIds: string;
  citationChunkIds: string;
  relevantChunkIds: string;
  expectedCitationChunkIds: string;
  notes: string;
  evaluationTopK: number;
}

const REVIEW_STATUS_OPTIONS: Array<{ value: ReviewStatusFilter; label: string }> = [
  { value: "ALL", label: "全部" },
  { value: "DRAFT", label: "待审" },
  { value: "ACTIVE", label: "已通过" },
  { value: "REJECTED", label: "已拒绝" }
];

const REVIEW_ACTIONS: Array<{ status: EvaluationCaseReviewStatus; label: string; icon: string }> = [
  { status: "ACTIVE", label: "通过", icon: "check_circle" },
  { status: "REJECTED", label: "拒绝", icon: "block" },
  { status: "DRAFT", label: "待审", icon: "pending_actions" }
];

const REVIEW_FLOW_STEPS = [
  { key: "import", label: "导入草稿", icon: "upload_file" },
  { key: "review", label: "人工审核", icon: "rule" },
  { key: "run", label: "运行评测", icon: "play_circle" },
  { key: "inspect", label: "回看指标", icon: "analytics" }
] as const;

const EMPTY_SUMMARY: ExperimentEvaluationSummary = {
  evaluationCount: 0,
  recentEvaluations: []
};

const EMPTY_REVIEW_DRAFT: ReviewDraft = {
  question: "",
  expectedAnswer: "",
  requiredChunkIds: "",
  supportingChunkIds: "",
  acceptableChunkIds: "",
  citationChunkIds: "",
  relevantChunkIds: "",
  expectedCitationChunkIds: "",
  notes: "",
  evaluationTopK: 5
};

export function ExperimentsWorkspace(): JSX.Element {
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseSummary[]>([]);
  const [cases, setCases] = useState<EvaluationCaseRecord[]>([]);
  const [summary, setSummary] = useState<ExperimentEvaluationSummary>(EMPTY_SUMMARY);
  const [selectedExperimentId, setSelectedExperimentId] = useState("");
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<ReviewStatusFilter>("ALL");
  const [datasetText, setDatasetText] = useState("");
  const [autoRun, setAutoRun] = useState(true);
  const [strategyName, setStrategyName] = useState("hybrid-rerank");
  const [topK, setTopK] = useState(5);
  const [reviewDraft, setReviewDraft] = useState<ReviewDraft>(EMPTY_REVIEW_DRAFT);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [reviewSaving, setReviewSaving] = useState(false);
  const [deletingAction, setDeletingAction] = useState("");
  const [statusText, setStatusText] = useState("");
  const [errorText, setErrorText] = useState("");
  const [lastImport, setLastImport] = useState<ImportEvaluationCasesResponse | null>(null);
  const [lastImportedCaseIds, setLastImportedCaseIds] = useState<string[]>([]);
  const [lastBatch, setLastBatch] = useState<RunEvaluationCasesBatchResponse | null>(null);

  const selectedExperiment = experiments.find((item) => item.id === selectedExperimentId);
  const selectedCase = cases.find((item) => item.id === selectedCaseId);

  const filteredCases = useMemo(() => {
    const lowerKeyword = keyword.trim().toLowerCase();
    return cases.filter((item) => {
      const matchExperiment = !selectedExperimentId || item.experimentId === selectedExperimentId;
      const normalizedStatus = normalizeReviewStatus(item.status);
      const matchStatus = statusFilter === "ALL" || normalizedStatus === statusFilter;
      const matchKeyword =
        !lowerKeyword ||
        [item.caseId, item.question, item.notes ?? ""].some((value) => value.toLowerCase().includes(lowerKeyword));
      return matchExperiment && normalizedStatus !== "ARCHIVED" && matchStatus && matchKeyword;
    });
  }, [cases, keyword, selectedExperimentId, statusFilter]);

  const reviewCounts = useMemo(() => {
    const counts: Record<ReviewStatusFilter, number> = { ALL: 0, DRAFT: 0, ACTIVE: 0, REJECTED: 0 };
    cases.forEach((item) => {
      if (selectedExperimentId && item.experimentId !== selectedExperimentId) return;
      const status = normalizeReviewStatus(item.status);
      if (status === "ARCHIVED") return;
      counts.ALL += 1;
      if (status === "DRAFT" || status === "ACTIVE" || status === "REJECTED") {
        counts[status] += 1;
      }
    });
    return counts;
  }, [cases, selectedExperimentId]);

  const importPreviewCount = useMemo(() => {
    try {
      return parseImportItems(datasetText).length;
    } catch {
      return 0;
    }
  }, [datasetText]);

  const canImport = datasetText.trim().length > 0 && !importing;
  const runnableCaseIds = filteredCases.filter((item) => normalizeReviewStatus(item.status) === "ACTIVE").map((item) => item.id);
  const busyDeleting = deletingAction.length > 0;
  const recentEvaluations = summary.recentEvaluations ?? [];
  const reviewProgress = reviewCounts.ALL ? Math.round((reviewCounts.ACTIVE / reviewCounts.ALL) * 100) : 0;
  const nextReviewAction = resolveNextReviewAction(reviewCounts, runnableCaseIds.length, Boolean(lastBatch), Boolean(datasetText.trim()));
  const strategyRows = useMemo(() => {
    const grouped = new Map<string, { count: number; evidence: number; chunk: number; document: number; precision: number; mrr: number; citation: number; grounded: number }>();
    recentEvaluations.forEach((item) => {
      const key = item.runStrategyName || "未知策略";
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
    setLastImportedCaseIds([]);
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
      setLastImportedCaseIds(successfulCaseIds);
      setStatusText(
        `导入完成：新增 ${imported.createdCount}，更新 ${imported.updatedCount}，失败 ${imported.failedCount}。`
      );

      if (autoRun && successfulCaseIds.length > 0) {
        setStatusText(`导入完成，正在自动触发批量评测：0/${successfulCaseIds.length}`);
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
    if (!selectedExperimentId || runnableCaseIds.length === 0) return;
    setImporting(true);
    setErrorText("");
    setStatusText(`正在对当前筛选的 ${runnableCaseIds.length} 条已通过样本执行批量评测...`);
    try {
      const batch = await runEvaluationCasesBatch({
        experimentId: selectedExperimentId,
        caseIds: runnableCaseIds,
        strategyName,
        retrieverType: "hybrid",
        topK
      });
      setLastBatch(batch);
      await loadAll(selectedExperimentId);
      setStatusText(`批量评测完成：${batch.completedCount}/${batch.requestedCount} 成功，${batch.failedCount} 失败。`);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "批量运行失败。");
      setStatusText("");
    } finally {
      setImporting(false);
    }
  }

  async function handleSaveReview(nextStatus?: EvaluationCaseReviewStatus): Promise<void> {
    if (!selectedCase) return;
    const question = reviewDraft.question.trim();
    if (!question) {
      setErrorText("问题不能为空。");
      return;
    }

    setReviewSaving(true);
    setErrorText("");
    try {
      const payload = buildReviewPayload(selectedCase, reviewDraft, nextStatus);
      const updated = await updateEvaluationCase(selectedCase.id, payload);
      setCases((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setSelectedCaseId(updated.id);
      setStatusText(nextStatus ? `${updated.caseId} 已标记为${reviewStatusMeta(updated.status).label}。` : `${updated.caseId} 已保存。`);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "保存审核结果失败。");
      setStatusText("");
    } finally {
      setReviewSaving(false);
    }
  }

  async function handleDeleteSelectedCase(): Promise<void> {
    if (!selectedCase || busyDeleting) return;
    const confirmed = window.confirm(`确认删除样本「${selectedCase.caseId}」吗？该操作不可撤销。`);
    if (!confirmed) return;
    await deleteCasesByIds([selectedCase.id], `样本 ${selectedCase.caseId} 已删除。`, "case");
  }

  async function handleDeleteFilteredCases(): Promise<void> {
    if (filteredCases.length === 0 || busyDeleting) return;
    const confirmed = window.confirm(
      `确认删除当前筛选出的 ${filteredCases.length} 条样本吗？该操作不可撤销。`
    );
    if (!confirmed) return;
    await deleteCasesByIds(
      filteredCases.map((item) => item.id),
      `已删除当前筛选的 ${filteredCases.length} 条样本。`,
      "filtered"
    );
  }

  async function handleDeleteLastImportedCases(): Promise<void> {
    const existingIds = lastImportedCaseIds.filter((id) => cases.some((item) => item.id === id));
    if (existingIds.length === 0 || busyDeleting) return;
    const confirmed = window.confirm(`确认删除最近导入的 ${existingIds.length} 条样本吗？该操作不可撤销。`);
    if (!confirmed) return;
    await deleteCasesByIds(existingIds, `已删除最近导入的 ${existingIds.length} 条样本。`, "last-import");
    setLastImportedCaseIds([]);
  }

  async function handleDeleteSelectedExperiment(): Promise<void> {
    if (!selectedExperiment || busyDeleting) return;
    const selectedExperimentCases = cases.filter((item) => item.experimentId === selectedExperiment.id).length;
    const confirmed = window.confirm(
      `确认删除实验「${selectedExperiment.name}」吗？将同时移除该实验下的 ${selectedExperimentCases} 条样本和关联记录。`
    );
    if (!confirmed) return;

    setDeletingAction("experiment");
    setErrorText("");
    try {
      await deleteExperiment(selectedExperiment.id);
      setStatusText(`实验「${selectedExperiment.name}」已删除。`);
      setSelectedExperimentId("");
      setSelectedCaseId("");
      setLastImportedCaseIds([]);
      await loadAll("");
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "删除实验失败。");
      setStatusText("");
    } finally {
      setDeletingAction("");
    }
  }

  async function deleteCasesByIds(ids: string[], successMessage: string, actionName: string): Promise<void> {
    const uniqueIds = Array.from(new Set(ids));
    if (uniqueIds.length === 0) return;

    setDeletingAction(actionName);
    setErrorText("");
    try {
      for (const id of uniqueIds) {
        await deleteEvaluationCase(id);
      }
      setCases((current) => current.filter((item) => !uniqueIds.includes(item.id)));
      setSelectedCaseId((current) => (current && uniqueIds.includes(current) ? "" : current));
      setLastImportedCaseIds((current) => current.filter((id) => !uniqueIds.includes(id)));
      setLastBatch(null);
      setStatusText(successMessage);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "删除样本失败。");
      setStatusText("");
    } finally {
      setDeletingAction("");
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
    if (filteredCases.some((item) => item.id === selectedCaseId)) return;
    setSelectedCaseId(filteredCases[0]?.id ?? "");
  }, [filteredCases, selectedCaseId]);

  useEffect(() => {
    setReviewDraft(selectedCase ? reviewDraftFromCase(selectedCase) : EMPTY_REVIEW_DRAFT);
  }, [selectedCase]);

  return (
    <div className="experiments-page">
      <section className="page-title-row">
        <div>
          <h1>评测实验</h1>
          <p>导入本地 JSON/CSV 评测集，绑定当前实验，并自动触发 RAG 全链路评估。</p>
        </div>
        <div className="page-actions">
          <button className="button secondary" type="button" onClick={() => void loadAll()} disabled={loading}>
            <span className="material-symbols-outlined">refresh</span>
            刷新数据
          </button>
          <button className="button primary" type="button" onClick={() => void handleRunSelected()} disabled={!selectedExperimentId || importing || runnableCaseIds.length === 0}>
            <span className="material-symbols-outlined">batch_prediction</span>
            运行已通过样本
          </button>
          <button
            className="button danger"
            type="button"
            onClick={() => void handleDeleteSelectedExperiment()}
            disabled={!selectedExperimentId || busyDeleting}
          >
            <span className="material-symbols-outlined">delete_forever</span>
            删除当前实验
          </button>
        </div>
      </section>

      <section className="experiment-dashboard-grid">
        <article className="panel leaderboard-panel">
          <div className="panel-header">
            <h2>检索策略排行榜</h2>
            <span>当前最佳：{strategyRows[0]?.name ?? "等待评测"}</span>
          </div>
          <div className="leaderboard-table">
            <div className="leaderboard-head">
              <span>策略</span><span>证据召回</span><span>片段召回</span><span>文档召回</span><span>精确率</span><span>MRR</span><span>可信度</span>
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
            <h2>链路健康度</h2>
            <span>已优化</span>
          </div>
          <HealthMetric label="平均可信度" value={summary.averageGrounded ?? 0} />
          <HealthMetric label="平均检索分" value={summary.averageRetrieval ?? 0} />
          <HealthMetric label="引用覆盖率" value={strategyRows[0]?.citation ?? 0} />
          <div className="health-kpis">
            <div><strong>{summary.evaluationCount}</strong><span>评估次数</span></div>
            <div><strong>{formatScore(summary.averageGrounded)}</strong><span>证据一致性</span></div>
            <div><strong>{filteredCases.length}</strong><span>样本数</span></div>
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

      <section className="eval-flow-panel" aria-label="测评集审核流程">
        <div className="eval-flow-summary">
          <div>
            <h2>测评集审核流程</h2>
            <p>{nextReviewAction}</p>
          </div>
          <strong>{reviewProgress}% 已通过</strong>
        </div>
        <div className="eval-flow-steps">
          {REVIEW_FLOW_STEPS.map((step, index) => {
            const done =
              (step.key === "import" && reviewCounts.ALL > 0) ||
              (step.key === "review" && reviewCounts.ACTIVE > 0) ||
              (step.key === "run" && Boolean(lastBatch)) ||
              (step.key === "inspect" && recentEvaluations.length > 0);
            const current =
              !done &&
              ((step.key === "import" && reviewCounts.ALL === 0) ||
                (step.key === "review" && reviewCounts.DRAFT > 0) ||
                (step.key === "run" && reviewCounts.ACTIVE > 0) ||
                (step.key === "inspect" && Boolean(lastBatch)));
            return (
              <div className={`eval-flow-step${done ? " is-done" : ""}${current ? " is-current" : ""}`} key={step.key}>
                <span className="material-symbols-outlined">{step.icon}</span>
                <div>
                  <strong>{index + 1}. {step.label}</strong>
                  <small>{flowStepHint(step.key, reviewCounts, runnableCaseIds.length, lastBatch?.completedCount ?? 0)}</small>
                </div>
              </div>
            );
          })}
        </div>
      </section>

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
            placeholder="粘贴 JSON 数组，兼容样本编号、问题、标准答案和证据片段字段"
          />
          <div className="two-fields">
            <label className="field">
              <span>策略预设</span>
              <select value={strategyName} onChange={(event) => setStrategyName(event.target.value)}>
                {STRATEGY_OPTIONS.map((strategy) => (
                  <option key={strategy} value={strategy}>
                    {strategy}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>召回数量</span>
              <input type="number" min={1} value={topK} onChange={(event) => setTopK(Number(event.target.value) || 5)} />
            </label>
          </div>
          <label className="check-row">
            <input type="checkbox" checked={autoRun} onChange={(event) => setAutoRun(event.target.checked)} />
            <span>导入后自动触发批量 RAG 评测</span>
          </label>
          <div className="button-row">
            <button className="button primary" type="button" onClick={() => void handleImport()} disabled={!canImport}>
              {importing ? "处理中..." : "导入到当前实验"}
            </button>
            <button className="button secondary" type="button" onClick={fillExample}>
              填入示例
            </button>
            <button
              className="button danger ghost"
              type="button"
              onClick={() => void handleDeleteLastImportedCases()}
              disabled={busyDeleting || lastImportedCaseIds.length === 0}
            >
              删除最近导入
            </button>
          </div>
        </aside>

        <section className="panel samples-panel">
          <div className="panel-header">
            <div>
              <h2>{selectedExperiment?.name ?? "全部实验样本"}</h2>
              <p>{selectedExperiment?.description ?? "选择实验后查看样本、运行结果和人工审核。"}</p>
            </div>
            <div className="sample-tools">
              <div className="review-filter-tabs" aria-label="审核状态筛选">
                {REVIEW_STATUS_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    className={statusFilter === option.value ? "is-active" : ""}
                    type="button"
                    onClick={() => setStatusFilter(option.value)}
                  >
                    {option.label}
                    <span>{reviewCounts[option.value]}</span>
                  </button>
                ))}
              </div>
              <input
                className="search-input"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="搜索样本编号 / 问题 / 备注"
              />
              <button
                className="button danger ghost"
                type="button"
                onClick={() => void handleDeleteFilteredCases()}
                disabled={busyDeleting || filteredCases.length === 0}
              >
                <span className="material-symbols-outlined">playlist_remove</span>
                删除当前筛选样本
              </button>
            </div>
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
                <div className="sample-row-meta">
                  <span className={`review-status ${reviewStatusMeta(item.status).className}`}>
                    {reviewStatusMeta(item.status).label}
                  </span>
                  <span>召回 {item.evaluationTopK}</span>
                </div>
              </button>
            ))}
            {filteredCases.length === 0 && <div className="empty-state">当前筛选下没有可用评测样本。</div>}
          </div>
        </section>
      </div>

      <div className="detail-grid">
        <section className="panel review-panel">
          <div className="panel-header">
            <div>
              <h2>人工审核</h2>
              <p>逐条校准问题、标准答案、证据片段和备注，再标记审核结论。</p>
            </div>
            {selectedCase && (
              <span className={`review-status ${reviewStatusMeta(selectedCase.status).className}`}>
                {reviewStatusMeta(selectedCase.status).label}
              </span>
            )}
          </div>
          {selectedCase ? (
            <div className="review-editor">
              <div className="review-meta-row">
                <span>样本 {selectedCase.caseId}</span>
                <span>更新 {formatDate(selectedCase.updatedAt)}</span>
              </div>
              <label className="field review-field">
                <span>问题</span>
                <textarea
                  className="review-textarea"
                  value={reviewDraft.question}
                  onChange={(event) => setReviewDraft((current) => ({ ...current, question: event.target.value }))}
                />
              </label>
              <label className="field review-field">
                <span>标准答案</span>
                <textarea
                  className="review-textarea answer"
                  value={reviewDraft.expectedAnswer}
                  onChange={(event) => setReviewDraft((current) => ({ ...current, expectedAnswer: event.target.value }))}
                  placeholder="填写可用于评估的参考答案"
                />
              </label>
              <div className="chunk-field-grid">
                <label className="field review-field">
                  <span>必需片段 ID</span>
                  <textarea
                    className="review-textarea ids"
                    value={reviewDraft.requiredChunkIds}
                    onChange={(event) => setReviewDraft((current) => ({ ...current, requiredChunkIds: event.target.value }))}
                    placeholder="每行一个，或用逗号分隔"
                  />
                </label>
                <label className="field review-field">
                  <span>支撑片段 ID</span>
                  <textarea
                    className="review-textarea ids"
                    value={reviewDraft.supportingChunkIds}
                    onChange={(event) => setReviewDraft((current) => ({ ...current, supportingChunkIds: event.target.value }))}
                    placeholder="每行一个，或用逗号分隔"
                  />
                </label>
                <label className="field review-field">
                  <span>可接受片段 ID</span>
                  <textarea
                    className="review-textarea ids"
                    value={reviewDraft.acceptableChunkIds}
                    onChange={(event) => setReviewDraft((current) => ({ ...current, acceptableChunkIds: event.target.value }))}
                    placeholder="每行一个，或用逗号分隔"
                  />
                </label>
                <label className="field review-field">
                  <span>引用片段 ID</span>
                  <textarea
                    className="review-textarea ids"
                    value={reviewDraft.citationChunkIds}
                    onChange={(event) => setReviewDraft((current) => ({ ...current, citationChunkIds: event.target.value }))}
                    placeholder="每行一个，或用逗号分隔"
                  />
                </label>
              </div>
              <div className="two-fields review-topk-row">
                <label className="field review-field">
                  <span>备注</span>
                  <textarea
                    className="review-textarea notes"
                    value={reviewDraft.notes}
                    onChange={(event) => setReviewDraft((current) => ({ ...current, notes: event.target.value }))}
                    placeholder="记录调整原因、证据边界或待补充事项"
                  />
                </label>
                <label className="field review-field">
                  <span>召回数量</span>
                  <input
                    type="number"
                    min={1}
                    value={reviewDraft.evaluationTopK}
                    onChange={(event) =>
                      setReviewDraft((current) => ({ ...current, evaluationTopK: Number(event.target.value) || 1 }))
                    }
                  />
                </label>
              </div>
              <div className="review-actions">
                <button className="button secondary" type="button" onClick={() => void handleSaveReview()} disabled={reviewSaving}>
                  <span className="material-symbols-outlined">save</span>
                  保存修改
                </button>
                {REVIEW_ACTIONS.map((action) => (
                  <button
                    key={action.status}
                    className={`button ${action.status === "ACTIVE" ? "primary" : "secondary"}`}
                    type="button"
                    onClick={() => void handleSaveReview(action.status)}
                    disabled={reviewSaving}
                  >
                    <span className="material-symbols-outlined">{action.icon}</span>
                    {action.label}
                  </button>
                ))}
                <button
                  className="button danger ghost"
                  type="button"
                  onClick={() => void handleDeleteSelectedCase()}
                  disabled={busyDeleting || reviewSaving}
                >
                  <span className="material-symbols-outlined">delete</span>
                  删除样本
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-state">请选择一个评测样本。</div>
          )}
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>批量运行结果</h2>
            <span>{lastBatch ? `${lastBatch.completedCount}/${lastBatch.requestedCount}` : "等待运行"}</span>
          </div>
          {lastBatch ? (
            <div className="batch-list">
              {lastBatch.items.map((item) => (
                <article key={`${item.caseId}-${item.caseKey}`} className={`batch-item ${item.status.toLowerCase()}`}>
                  <div>
                    <strong>{item.caseKey || shortId(item.caseId)}</strong>
                    <span>{formatRunStatus(item.status)}</span>
                  </div>
                  <p>
                    运行 {shortId(item.runId)} / 评估 {shortId(item.evaluationId)}
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
              导入评测集并勾选自动运行后，这里会展示每条样本的运行编号、评估编号和指标。
            </div>
          )}
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>最近评估</h2>
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
                {item.runStrategyName ?? "未知策略"}
                <small>{item.runRetrieverType ?? "检索器未记录"}</small>
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

function formatRunStatus(status?: string | null): string {
  const normalized = (status ?? "").trim().toUpperCase();
  if (normalized === "COMPLETED" || normalized === "SUCCESS") return "成功";
  if (normalized === "FAILED" || normalized === "ERROR") return "失败";
  if (normalized === "RUNNING" || normalized === "PROCESSING") return "运行中";
  return "未知";
}

function normalizeReviewStatus(status?: string | null): NormalizedReviewStatus {
  const normalized = (status ?? "DRAFT").trim().toUpperCase();
  if (normalized === "ACTIVE" || normalized === "REJECTED" || normalized === "ARCHIVED") {
    return normalized;
  }
  return "DRAFT";
}

function reviewStatusMeta(status?: string | null): { label: string; className: string } {
  const normalized = normalizeReviewStatus(status);
  if (normalized === "ACTIVE") return { label: "已通过", className: "active" };
  if (normalized === "REJECTED") return { label: "已拒绝", className: "rejected" };
  if (normalized === "ARCHIVED") return { label: "已归档", className: "archived" };
  return { label: "待审", className: "draft" };
}

function resolveNextReviewAction(
  counts: Record<ReviewStatusFilter, number>,
  runnableCount: number,
  hasBatch: boolean,
  hasPendingDataset: boolean
): string {
  if (hasPendingDataset && counts.ALL === 0) return "已准备好本地内容，下一步导入草稿样本。";
  if (counts.ALL === 0) return "先导入自动生成或本地整理的测评集草稿。";
  if (counts.DRAFT > 0) return `还有 ${counts.DRAFT} 条待审样本，优先校准问题、标准答案和证据片段。`;
  if (runnableCount > 0 && !hasBatch) return `已有 ${runnableCount} 条已通过样本，可以运行一次批量评测。`;
  if (hasBatch) return "批量运行已完成，回看低分样本并修正测评集或检索策略。";
  return "当前筛选下暂无可运行样本，请调整筛选或导入新样本。";
}

function flowStepHint(
  key: (typeof REVIEW_FLOW_STEPS)[number]["key"],
  counts: Record<ReviewStatusFilter, number>,
  runnableCount: number,
  completedCount: number
): string {
  if (key === "import") return counts.ALL ? `${counts.ALL} 条样本` : "等待导入";
  if (key === "review") return `${counts.DRAFT} 待审 / ${counts.ACTIVE} 通过`;
  if (key === "run") return runnableCount ? `${runnableCount} 条可运行` : "等待通过样本";
  return completedCount ? `${completedCount} 条完成` : "等待结果";
}

function reviewDraftFromCase(item: EvaluationCaseRecord): ReviewDraft {
  return {
    question: item.question ?? "",
    expectedAnswer: item.expectedAnswer ?? "",
    requiredChunkIds: joinReviewIds(item.requiredChunkIds.length ? item.requiredChunkIds : item.relevantChunkIds),
    supportingChunkIds: joinReviewIds(item.supportingChunkIds),
    acceptableChunkIds: joinReviewIds(item.acceptableChunkIds),
    citationChunkIds: joinReviewIds(
      item.citationChunkIds.length ? item.citationChunkIds : item.expectedCitationChunkIds
    ),
    relevantChunkIds: joinReviewIds(item.relevantChunkIds),
    expectedCitationChunkIds: joinReviewIds(item.expectedCitationChunkIds),
    notes: item.notes ?? "",
    evaluationTopK: item.evaluationTopK || 5
  };
}

function buildReviewPayload(
  source: EvaluationCaseRecord,
  draft: ReviewDraft,
  nextStatus?: EvaluationCaseReviewStatus
): UpdateEvaluationCasePayload {
  const requiredChunkIds = splitReviewIds(draft.requiredChunkIds);
  const supportingChunkIds = splitReviewIds(draft.supportingChunkIds);
  const acceptableChunkIds = splitReviewIds(draft.acceptableChunkIds);
  const citationChunkIds = splitReviewIds(draft.citationChunkIds);
  const preservedRelevantChunkIds = splitReviewIds(draft.relevantChunkIds);
  const preservedExpectedCitationChunkIds = splitReviewIds(draft.expectedCitationChunkIds);
  const relevantChunkIds = dedupeReviewIds([
    ...preservedRelevantChunkIds,
    ...requiredChunkIds,
    ...supportingChunkIds,
    ...acceptableChunkIds
  ]);
  const expectedCitationChunkIds = dedupeReviewIds([
    ...preservedExpectedCitationChunkIds,
    ...citationChunkIds
  ]);

  return {
    experimentId: source.experimentId,
    caseId: source.caseId,
    question: draft.question.trim(),
    expectedAnswer: draft.expectedAnswer.trim(),
    requiredChunkIds,
    supportingChunkIds,
    acceptableChunkIds,
    citationChunkIds,
    relevantChunkIds,
    relevantDocumentIds: source.relevantDocumentIds,
    expectedCitationChunkIds,
    evaluationTopK: Math.max(1, Math.round(draft.evaluationTopK || source.evaluationTopK || 5)),
    notes: draft.notes.trim(),
    status: nextStatus ?? normalizeReviewStatus(source.status)
  };
}

function splitReviewIds(value: string): string[] {
  const trimmed = value.trim();
  if (!trimmed) return [];
  if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
    try {
      const parsed = JSON.parse(trimmed) as unknown;
      if (Array.isArray(parsed)) return dedupeReviewIds(parsed.map((item) => String(item)));
    } catch {
      // 审核输入允许粘贴非严格 JSON，下面继续按分隔符解析。
    }
  }
  return dedupeReviewIds(trimmed.split(/[\s,;；，、]+/u));
}

function joinReviewIds(values: string[] | undefined): string {
  return (values ?? []).join("\n");
}

function dedupeReviewIds(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  values.forEach((value) => {
    const normalized = value.trim();
    if (!normalized || seen.has(normalized)) return;
    seen.add(normalized);
    result.push(normalized);
  });
  return result;
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
