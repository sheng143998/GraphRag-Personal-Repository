import { ChangeEvent, DragEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowDown,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  File,
  FileArchive,
  FileCode2,
  FileText,
  FolderOpen,
  Loader2,
  RefreshCw,
  Trash2,
  Upload,
  X
} from "lucide-react";
import {
  deleteDocument,
  fetchDocumentById,
  fetchDocuments,
  uploadDocument,
  uploadDocumentsBatch
} from "../../api/documents";
import { fetchKnowledgeBases } from "../../api/knowledgeBases";
import type {
  BatchUploadFileItem,
  DocumentProcessStatus,
  DocumentRecord,
  KnowledgeBaseSummary,
  UploadResponse
} from "../../types";
import "./documents.css";

type UploadMode = "single" | "multiple" | "folder";
type StatusFilter = "ALL" | DocumentProcessStatus;

interface SelectedFileItem {
  file: File;
  relativePath: string;
}

interface SkippedFileItem {
  name: string;
  reason: string;
}

interface PipelineStep {
  key: "uploaded" | "parsing" | "chunking" | "embedding" | "searchable" | "review";
  label: string;
  description: string;
}

interface StatusMeta {
  label: string;
  detail: string;
  className: string;
  icon: typeof File;
  phaseIndex: number;
  tone: "neutral" | "active" | "success" | "danger";
}

const DOCUMENT_TYPES = [
  { value: "tech_note", label: "技术笔记" },
  { value: "development_experience", label: "开发经验" },
  { value: "project_experience", label: "项目经验" },
  { value: "interview_experience", label: "面试经验" },
  { value: "code_snippet", label: "代码片段" },
  { value: "job_description", label: "招聘需求" }
];

const ALLOWED_FILE_TYPES = new Set(["md", "txt", "csv", "html", "json", "log", "docx", "pdf", "xlsx", "xls"]);
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024;
const POLL_INTERVAL_MS = 2200;
const MAX_POLL_ATTEMPTS = 36;
const PIPELINE_STEPS: PipelineStep[] = [
  { key: "uploaded", label: "已上传", description: "文件已进入后端任务队列" },
  { key: "parsing", label: "解析中", description: "提取正文、表格和版面结构" },
  { key: "chunking", label: "切分中", description: "按文档类型生成知识片段" },
  { key: "embedding", label: "向量化", description: "写入 embedding 与检索索引" },
  { key: "searchable", label: "可检索", description: "可在问答和实验中召回" },
  { key: "review", label: "失败复查", description: "查看错误、调整格式后重试" }
];

function sortByUpdatedAt(items: DocumentRecord[]): DocumentRecord[] {
  return [...items].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function inferFileType(name: string): string {
  const parts = name.trim().split(".");
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : "txt";
}

function formatDate(value?: string): string {
  if (!value) {
    return "--";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value.replace("T", " ").slice(0, 19);
  }

  return parsed.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatBytes(value: number): string {
  if (value >= 1024 * 1024) {
    return `${(value / 1024 / 1024).toFixed(1)} MB`;
  }
  if (value >= 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${value} B`;
}

function toSelectedFileItem(file: File): SelectedFileItem {
  const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
  return { file, relativePath };
}

function fileIcon(fileType?: string) {
  const normalized = (fileType || "").toLowerCase();
  if (normalized === "pdf") return <FileArchive size={18} />;
  if (["md", "txt", "html", "json", "log", "csv"].includes(normalized)) return <FileCode2 size={18} />;
  return <FileText size={18} />;
}

function statusMeta(status: DocumentProcessStatus | string): StatusMeta {
  if (status === "INDEXED") {
    return {
      label: "可检索",
      detail: "已完成解析、切分和向量化",
      className: "status-indexed",
      icon: CheckCircle2,
      phaseIndex: 4,
      tone: "success"
    };
  }
  if (status === "PROCESSING") {
    return {
      label: "解析中",
      detail: "正在解析、切分并生成向量",
      className: "status-processing",
      icon: Loader2,
      phaseIndex: 1,
      tone: "active"
    };
  }
  if (status === "UPLOADED") {
    return {
      label: "已上传",
      detail: "已提交到入库队列，等待解析",
      className: "status-uploaded",
      icon: Upload,
      phaseIndex: 0,
      tone: "neutral"
    };
  }
  if (status === "FAILED") {
    return {
      label: "失败复查",
      detail: "入库未完成，请复查文件或解析日志",
      className: "status-failed",
      icon: AlertCircle,
      phaseIndex: 5,
      tone: "danger"
    };
  }
  return {
    label: status,
    detail: "等待状态同步",
    className: "status-muted",
    icon: File,
    phaseIndex: 0,
    tone: "neutral"
  };
}

function pipelineClassName(stepIndex: number, meta: StatusMeta): string {
  if (meta.tone === "danger") {
    return stepIndex === PIPELINE_STEPS.length - 1 ? "is-current is-danger" : "is-muted";
  }
  if (meta.tone === "success") {
    return stepIndex <= meta.phaseIndex ? "is-done" : "is-muted";
  }
  if (meta.tone === "active" && stepIndex > 0 && stepIndex <= 3) {
    return "is-current";
  }
  if (stepIndex < meta.phaseIndex) {
    return "is-done";
  }
  if (stepIndex === meta.phaseIndex) {
    return "is-current";
  }
  return "is-muted";
}

function pipelineHint(status: DocumentProcessStatus | string, chunkCount?: number): string {
  if (status === "INDEXED") return `已生成 ${chunkCount ?? 0} 个片段，可被检索召回。`;
  if (status === "FAILED") return "建议打开详情复查文件格式、解析器和错误日志。";
  if (status === "UPLOADED") return "已接收文件，后台任务即将开始解析。";
  return chunkCount ? `已返回 ${chunkCount} 个片段，向量索引仍在同步。` : "解析、切分、向量化正在后台推进。";
}

function PipelineRail(props: { status: DocumentProcessStatus | string; compact?: boolean }) {
  const meta = statusMeta(props.status);
  return (
    <ol className={props.compact ? "pipeline-rail compact" : "pipeline-rail"} aria-label="文档入库流水线">
      {PIPELINE_STEPS.map((step, index) => (
        <li className={pipelineClassName(index, meta)} key={step.key}>
          <span className="pipeline-dot" />
          <span className="pipeline-label">{step.label}</span>
          {!props.compact ? <small>{step.description}</small> : null}
        </li>
      ))}
    </ol>
  );
}

export function DocumentCenter() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseSummary[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<DocumentRecord | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [lastError, setLastError] = useState("");
  const [activityItems, setActivityItems] = useState<UploadResponse[]>([]);
  const pollingTimers = useRef(new Map<string, number>());

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    setLastError("");
    try {
      setDocuments(sortByUpdatedAt(await fetchDocuments()));
    } catch (error) {
      setLastError(error instanceof Error ? error.message : "无法加载文档列表。");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDocuments();
    void fetchKnowledgeBases()
      .then((items) => setKnowledgeBases(items))
      .catch((error) => {
        setKnowledgeBases([]);
        setLastError(error instanceof Error ? error.message : "无法加载知识库列表。");
      });

    return () => {
      pollingTimers.current.forEach((timer) => window.clearInterval(timer));
      pollingTimers.current.clear();
    };
  }, [loadDocuments]);

  const pollDocumentStatus = useCallback(async (documentId: string) => {
    const existing = pollingTimers.current.get(documentId);
    if (existing) {
      window.clearInterval(existing);
    }

    let attempts = 0;
    const timer = window.setInterval(async () => {
      attempts += 1;
      try {
        const doc = await fetchDocumentById(documentId);
        setDocuments((current) => {
          const next = current.some((item) => item.id === doc.id)
            ? current.map((item) => (item.id === doc.id ? doc : item))
            : [doc, ...current];
          return sortByUpdatedAt(next);
        });
        if (selectedDocument?.id === doc.id) {
          setSelectedDocument(doc);
        }

        if (doc.status === "INDEXED" || doc.status === "FAILED" || attempts >= MAX_POLL_ATTEMPTS) {
          window.clearInterval(timer);
          pollingTimers.current.delete(documentId);
          void loadDocuments();
        }
      } catch {
        if (attempts >= MAX_POLL_ATTEMPTS) {
          window.clearInterval(timer);
          pollingTimers.current.delete(documentId);
        }
      }
    }, POLL_INTERVAL_MS);

    pollingTimers.current.set(documentId, timer);
  }, [loadDocuments, selectedDocument?.id]);

  const handleUpload = async (input: {
    mode: UploadMode;
    knowledgeBaseId: string;
    documentType: string;
    title: string;
    files: SelectedFileItem[];
  }) => {
    setIsUploading(true);
    setLastError("");
    try {
      if (input.mode === "single") {
        const selected = input.files[0];
        const result = await uploadDocument({
          knowledgeBaseId: input.knowledgeBaseId,
          title: input.title || selected.file.name.replace(/\.[^.]+$/, ""),
          documentType: input.documentType,
          fileName: selected.file.name,
          fileType: inferFileType(selected.file.name),
          file: selected.file,
          sourceType: "LOCAL_UPLOAD",
          sourcePath: selected.relativePath || selected.file.name,
          metadata: {
            source: "frontend-react",
            uploadMode: input.mode,
            relativePath: selected.relativePath
          }
        });
        setActivityItems((current) => [result, ...current].slice(0, 8));
        await loadDocuments();
        void pollDocumentStatus(result.id);
      } else {
        const files: BatchUploadFileItem[] = input.files.map((item) => ({
          file: item.file,
          relativePath: item.relativePath
        }));
        const result = await uploadDocumentsBatch({
          knowledgeBaseId: input.knowledgeBaseId,
          title: input.title || undefined,
          documentType: input.documentType,
          sourceType: input.mode === "folder" ? "LOCAL_FOLDER_UPLOAD" : "LOCAL_BATCH_UPLOAD",
          files,
          metadata: {
            source: "frontend-react",
            uploadMode: input.mode
          }
        });
        setActivityItems((current) => [...result.documents, ...current].slice(0, 8));
        await loadDocuments();
        result.documents.forEach((item) => void pollDocumentStatus(item.id));
      }
    } catch (error) {
      setLastError(error instanceof Error ? error.message : "上传任务提交失败。");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectDocument = async (document: DocumentRecord) => {
    setSelectedDocument(document);
    setLastError("");
    try {
      setSelectedDocument(await fetchDocumentById(document.id));
    } catch (error) {
      setLastError(error instanceof Error ? error.message : "无法加载文档详情。");
    }
  };

  const handleDelete = async (document: DocumentRecord) => {
    const confirmed = window.confirm(`确定删除文档「${document.title}」吗？`);
    if (!confirmed) return;
    setLastError("");
    try {
      await deleteDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      if (selectedDocument?.id === document.id) {
        setSelectedDocument(null);
      }
    } catch (error) {
      setLastError(error instanceof Error ? error.message : "删除文档失败。");
    }
  };

  const filteredDocuments = useMemo(() => {
    if (statusFilter === "ALL") return documents;
    return documents.filter((document) => document.status === statusFilter);
  }, [documents, statusFilter]);

  const queueCount = documents.filter((document) => document.status === "PROCESSING" || document.status === "UPLOADED").length;

  return (
    <div className="documents-page">
      <UploadSection
        activityItems={activityItems}
        isUploading={isUploading}
        knowledgeBases={knowledgeBases}
        onUpload={handleUpload}
        queueCount={queueCount}
      />

      {lastError ? (
        <div className="error-banner" role="alert">
          <AlertCircle size={17} />
          <span>{lastError}</span>
        </div>
      ) : null}

      <DocumentTable
        documents={filteredDocuments}
        isLoading={isLoading}
        onDelete={handleDelete}
        onRefresh={loadDocuments}
        onSelect={handleSelectDocument}
        selectedId={selectedDocument?.id}
        statusFilter={statusFilter}
        totalCount={documents.length}
        onStatusFilterChange={setStatusFilter}
      />

      <DocumentDetailDrawer document={selectedDocument} onClose={() => setSelectedDocument(null)} />
    </div>
  );
}

function UploadSection(props: {
  activityItems: UploadResponse[];
  isUploading: boolean;
  knowledgeBases: KnowledgeBaseSummary[];
  onUpload: (input: {
    mode: UploadMode;
    knowledgeBaseId: string;
    documentType: string;
    title: string;
    files: SelectedFileItem[];
  }) => Promise<void>;
  queueCount: number;
}) {
  const [uploadMode, setUploadMode] = useState<UploadMode>("single");
  const [knowledgeBaseId, setKnowledgeBaseId] = useState("");
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0].value);
  const [title, setTitle] = useState("");
  const [files, setFiles] = useState<SelectedFileItem[]>([]);
  const [skippedFiles, setSkippedFiles] = useState<SkippedFileItem[]>([]);
  const [validationMessage, setValidationMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const folderInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!knowledgeBaseId && props.knowledgeBases[0]?.id) {
      setKnowledgeBaseId(props.knowledgeBases[0].id);
    }
  }, [knowledgeBaseId, props.knowledgeBases]);

  useEffect(() => {
    if (folderInputRef.current) {
      folderInputRef.current.setAttribute("webkitdirectory", "");
      folderInputRef.current.setAttribute("directory", "");
    }
  }, [uploadMode]);

  const previewFiles = files.slice(0, 5);
  const currentInputRef = uploadMode === "folder" ? folderInputRef : fileInputRef;

  function handleFiles(nextFiles: FileList | File[]) {
    const skipped: SkippedFileItem[] = [];
    const selected = Array.from(nextFiles)
      .map(toSelectedFileItem)
      .filter((item) => {
        if (!ALLOWED_FILE_TYPES.has(inferFileType(item.file.name))) {
          skipped.push({ name: item.relativePath, reason: "不支持的文件类型" });
          return false;
        }
        if (item.file.size > MAX_FILE_SIZE_BYTES) {
          skipped.push({ name: item.relativePath, reason: "超过 50 MB" });
          return false;
        }
        return true;
      });
    setFiles(selected);
    setSkippedFiles(skipped);
    if (!title && uploadMode === "single" && selected[0]) {
      setTitle(selected[0].file.name.replace(/\.[^.]+$/, ""));
    }
    setValidationMessage("");
  }

  function validateUpload(): string {
    if (!knowledgeBaseId) return "请先选择目标知识库。";
    if (!files.length) return uploadMode === "folder" ? "请选择一个文件夹。" : "请选择至少一个文件。";
    if (uploadMode === "single" && files.length !== 1) return "单文件模式只能选择一个文件。";

    return "";
  }

  async function submit() {
    const message = validateUpload();
    setValidationMessage(message);
    if (message) return;

    await props.onUpload({
      mode: uploadMode,
      knowledgeBaseId,
      documentType,
      title: title.trim(),
      files
    });
    setFiles([]);
    setSkippedFiles([]);
    setTitle("");
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (folderInputRef.current) folderInputRef.current.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (event.dataTransfer.files.length) {
      handleFiles(event.dataTransfer.files);
    }
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files) {
      handleFiles(event.target.files);
    }
  }

  return (
    <section className="upload-grid">
      <div className="section-heading">
        <div>
          <h2>文档入库流水线</h2>
          <p>上传后持续跟踪解析、切分、向量化和可检索状态，避免资料丢在后台黑箱里。</p>
        </div>
        <div className="mode-switch" aria-label="上传模式">
          {(["single", "multiple", "folder"] as UploadMode[]).map((mode) => (
            <button
              className={uploadMode === mode ? "selected" : ""}
              key={mode}
              type="button"
              onClick={() => {
                setUploadMode(mode);
                setFiles([]);
                setSkippedFiles([]);
              }}
            >
              {mode === "single" ? "单文件" : mode === "multiple" ? "多文件" : "文件夹"}
            </button>
          ))}
        </div>
      </div>

      <div className="upload-layout">
        <div className="dropzone" onDragOver={(event) => event.preventDefault()} onDrop={handleDrop}>
          <div className="upload-stage-strip">
            {PIPELINE_STEPS.map((step) => (
              <span key={step.key}>{step.label}</span>
            ))}
          </div>
          <div className="dropzone-icon">
            <Upload size={23} />
          </div>
          <h3>上传资料并进入入库队列</h3>
          <p>支持 PDF、MD、TXT、DOCX、CSV、HTML、JSON、Excel，单文件最大 50MB。</p>

          <div className="upload-controls">
            <label>
              <span>目标知识库</span>
              <select value={knowledgeBaseId} onChange={(event) => setKnowledgeBaseId(event.target.value)}>
                {!props.knowledgeBases.length ? <option value="">暂无可用知识库</option> : null}
                {props.knowledgeBases.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>文档类型</span>
              <select value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
                {DOCUMENT_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>标题</span>
              <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="批量上传可留空" />
            </label>
          </div>

          <div className="button-row">
            <button className="primary-button" type="button" onClick={() => currentInputRef.current?.click()}>
              {uploadMode === "folder" ? <FolderOpen size={16} /> : <FileText size={16} />}
              {uploadMode === "folder" ? "选择文件夹" : "选择文件"}
            </button>
            <button className="secondary-button" type="button" disabled={props.isUploading} onClick={submit}>
              {props.isUploading ? <Loader2 className="spin" size={16} /> : <Upload size={16} />}
              {props.isUploading ? "提交中..." : `提交 ${files.length || 0} 个任务`}
            </button>
          </div>

          <input
            ref={fileInputRef}
            hidden
            multiple={uploadMode !== "single"}
            type="file"
            accept=".md,.txt,.csv,.html,.json,.log,.docx,.pdf,.xlsx,.xls"
            onChange={handleInputChange}
          />
          <input
            ref={folderInputRef}
            hidden
            multiple
            type="file"
            accept=".md,.txt,.csv,.html,.json,.log,.docx,.pdf,.xlsx,.xls"
            onChange={handleInputChange}
          />

          {validationMessage ? <div className="validation-message">{validationMessage}</div> : null}

          {files.length ? (
            <div className="selected-files">
              <strong>已选择 {files.length} 个文件</strong>
              {previewFiles.map((item) => (
                <span key={`${item.relativePath}-${item.file.size}`}>
                  {item.relativePath} · {formatBytes(item.file.size)}
                </span>
              ))}
              {files.length > previewFiles.length ? <span>还有 {files.length - previewFiles.length} 个文件...</span> : null}
            </div>
          ) : null}

          {skippedFiles.length ? (
            <div className="selected-files skipped-files">
              <strong>已跳过 {skippedFiles.length} 个文件</strong>
              {skippedFiles.slice(0, 4).map((item) => (
                <span key={`${item.name}-${item.reason}`}>
                  {item.name} · {item.reason}
                </span>
              ))}
              {skippedFiles.length > 4 ? <span>还有 {skippedFiles.length - 4} 个文件已跳过...</span> : null}
            </div>
          ) : null}
        </div>

        <CurrentActivity activityItems={props.activityItems} queueCount={props.queueCount} />
      </div>
    </section>
  );
}

function CurrentActivity(props: { activityItems: UploadResponse[]; queueCount: number }) {
  return (
    <aside className="activity-panel">
      <div className="activity-header">
        <div>
          <h4>上传活动</h4>
          <p>最近任务的后台推进情况</p>
        </div>
        <span>{props.queueCount} 个排队</span>
      </div>
      {props.activityItems.length ? (
        <div className="activity-list">
          {props.activityItems.slice(0, 4).map((item) => {
            const meta = statusMeta(item.status);
            const StatusIcon = meta.icon;
            return (
              <div className="activity-item" key={item.id}>
                <div className="activity-line">
                  <span className="activity-name">
                    <FileText size={14} />
                    {item.fileName || item.title}
                  </span>
                  <span className={`activity-state ${meta.className}`}>
                    <StatusIcon size={12} className={item.status === "PROCESSING" ? "spin" : ""} />
                    {meta.label}
                  </span>
                </div>
                <PipelineRail compact status={item.status} />
                <span className="activity-hint">{pipelineHint(item.status, item.chunkCount)}</span>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="activity-empty">暂无新的上传任务。提交后会在这里显示阶段进度。</div>
      )}
      <div className="activity-footer">
        <span>失败任务会进入“失败复查”，不会被静默隐藏。</span>
      </div>
    </aside>
  );
}

function DocumentTable(props: {
  documents: DocumentRecord[];
  isLoading: boolean;
  onDelete: (document: DocumentRecord) => void;
  onRefresh: () => void;
  onSelect: (document: DocumentRecord) => void;
  selectedId?: string;
  statusFilter: StatusFilter;
  totalCount: number;
  onStatusFilterChange: (value: StatusFilter) => void;
}) {
  return (
    <section className="document-table-panel">
      <div className="table-toolbar">
        <div className="table-tools-left">
          <div className="select-wrap">
            <select value={props.statusFilter} onChange={(event) => props.onStatusFilterChange(event.target.value as StatusFilter)}>
              <option value="ALL">全部文档</option>
              <option value="UPLOADED">状态：已上传</option>
              <option value="PROCESSING">状态：解析中</option>
              <option value="INDEXED">状态：可检索</option>
              <option value="FAILED">状态：失败复查</option>
            </select>
          </div>
          <span className="showing-count">显示 {props.documents.length} / {props.totalCount} 条</span>
        </div>
        <button className="icon-button" type="button" onClick={props.onRefresh} aria-label="刷新文档">
          <RefreshCw size={17} className={props.isLoading ? "spin" : ""} />
        </button>
      </div>

      <div className="table-scroll">
        <table className="document-table">
          <thead>
            <tr>
              <th>
                <span>名称 <ArrowDown size={12} /></span>
              </th>
              <th>类型</th>
              <th>状态</th>
              <th>入库阶段</th>
              <th>片段</th>
              <th>更新时间</th>
              <th className="actions-column">操作</th>
            </tr>
          </thead>
          <tbody>
            {props.documents.length ? (
              props.documents.map((document) => (
                <DocumentRow
                  document={document}
                  isSelected={props.selectedId === document.id}
                  key={document.id}
                  onDelete={props.onDelete}
                  onSelect={props.onSelect}
                />
              ))
            ) : (
              <tr>
                <td className="empty-table" colSpan={7}>
                  {props.isLoading ? "正在加载文档列表..." : "暂无文档。"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination-strip">
        <div className="pager">
          <button disabled type="button"><ChevronLeft size={16} /></button>
          <button className="current" type="button">1</button>
          <button disabled type="button"><ChevronRight size={16} /></button>
        </div>
        <span>每页 25 行</span>
      </div>
    </section>
  );
}

function DocumentRow(props: {
  document: DocumentRecord;
  isSelected: boolean;
  onDelete: (document: DocumentRecord) => void;
  onSelect: (document: DocumentRecord) => void;
}) {
  const meta = statusMeta(props.document.status);
  const StatusIcon = meta.icon;

  return (
    <tr className={props.isSelected ? "selected-row" : ""}>
      <td>
        <button className="document-name-cell" type="button" onClick={() => props.onSelect(props.document)}>
          <span className="file-type-icon">{fileIcon(props.document.fileType)}</span>
          <span>
            <strong>{props.document.title || props.document.fileName}</strong>
            <small>{props.document.sourcePath || props.document.fileName}</small>
          </span>
        </button>
      </td>
      <td>{props.document.fileType || props.document.documentType}</td>
      <td>
        <span className={`status-badge ${meta.className}`}>
          <StatusIcon size={12} className={props.document.status === "PROCESSING" ? "pulse-dot" : ""} />
          {meta.label}
        </span>
        <small className="status-detail">{meta.detail}</small>
      </td>
      <td>
        <PipelineRail compact status={props.document.status} />
      </td>
      <td className="mono-cell">{props.document.chunkCount ?? "--"}</td>
      <td>{formatDate(props.document.updatedAt)}</td>
      <td className="actions-column">
        <div className="row-actions">
          <button className="row-action" type="button" onClick={() => props.onSelect(props.document)} title="预览">
            <FileText size={16} />
          </button>
          <button className="row-action danger" type="button" onClick={() => props.onDelete(props.document)} title="删除">
            <Trash2 size={16} />
          </button>
        </div>
      </td>
    </tr>
  );
}

function DocumentDetailDrawer(props: { document: DocumentRecord | null; onClose: () => void }) {
  if (!props.document) {
    return null;
  }

  const parser = props.document.parserName
    ? `${props.document.parserName}${props.document.parserVersion ? ` ${props.document.parserVersion}` : ""}`
    : "未记录解析器";
  const chunks = props.document.chunks ?? [];
  const meta = statusMeta(props.document.status);
  const StatusIcon = meta.icon;

  return (
    <aside className="detail-drawer" aria-label="文档详情">
      <div className="drawer-header">
        <div>
          <h3>{props.document.title}</h3>
          <p>{props.document.sourcePath || props.document.fileName}</p>
        </div>
        <button className="icon-button" type="button" onClick={props.onClose} aria-label="关闭预览">
          <X size={17} />
        </button>
      </div>

      <div className="drawer-metrics">
        <div>
          <span>状态</span>
          <strong className={meta.className}>
            <StatusIcon size={14} className={props.document.status === "PROCESSING" ? "spin" : ""} />
            {meta.label}
          </strong>
        </div>
        <div>
          <span>片段</span>
          <strong>{props.document.chunkCount ?? chunks.length}</strong>
        </div>
        <div>
          <span>解析器</span>
          <strong>{parser}</strong>
        </div>
      </div>

      <section className="drawer-pipeline">
        <div className="chunk-preview-heading">
          <h4>入库进度</h4>
          <span>{pipelineHint(props.document.status, props.document.chunkCount ?? chunks.length)}</span>
        </div>
        <PipelineRail status={props.document.status} />
      </section>

      {props.document.status === "FAILED" ? (
        <div className="review-callout">
          <AlertCircle size={16} />
          <div>
            <strong>需要复查</strong>
            <p>优先确认文件是否损坏、格式是否受支持、PDF 是否需要 OCR，必要时重新上传。</p>
          </div>
        </div>
      ) : null}

      {props.document.summary ? <p className="drawer-summary">{props.document.summary}</p> : null}

      <dl className="metadata-grid">
        <dt>知识库</dt>
        <dd>{props.document.knowledgeBaseName || props.document.knowledgeBaseId}</dd>
        <dt>文档类型</dt>
        <dd>{props.document.documentType}</dd>
        <dt>来源类型</dt>
        <dd>{props.document.sourceType || "--"}</dd>
        <dt>更新时间</dt>
        <dd>{formatDate(props.document.updatedAt)}</dd>
      </dl>

      <div className="chunk-preview-heading">
        <h4>片段预览</h4>
      </div>
      {chunks.length ? (
        <div className="chunk-list">
          {chunks.map((chunk) => (
            <article className="chunk-card" key={chunk.id}>
              <div className="chunk-title">
                <strong>片段 {chunk.chunkIndex}</strong>
                <span>{chunk.chunkStrategy || "默认策略"}</span>
              </div>
              <p>{chunk.contentPreview}</p>
              <small>
                {chunk.pageNumber ? `第 ${chunk.pageNumber} 页` : ""}
                {chunk.sheetName ? ` 工作表 ${chunk.sheetName}` : ""}
                {chunk.rowRange ? ` 行 ${chunk.rowRange}` : ""}
              </small>
            </article>
          ))}
        </div>
      ) : (
        <div className="activity-empty">当前文档暂未返回 chunk 预览。</div>
      )}
    </aside>
  );
}
