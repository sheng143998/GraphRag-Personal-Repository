import type {
  AppSettings,
  ChatMessage,
  CitationSource,
  DocumentRecord,
  ExperimentEvaluationSummary,
  ExperimentRecord,
  KnowledgeBaseSummary,
  RagStrategyOption
} from "../types";

export const ragStrategyOptions: RagStrategyOption[] = [
  {
    value: "basic-rag",
    label: "Basic RAG",
    description: "基础向量检索与回答生成链路，适合作为策略对比基线。"
  },
  {
    value: "hybrid-rerank",
    label: "Hybrid + Rerank",
    description: "混合语义与关键词召回后重排，适合技术笔记和开发经验。"
  },
  {
    value: "metadata-filter",
    label: "Metadata Filter",
    description: "按文档类型、技术栈、标签等元数据限制检索范围，适合代码片段和招聘 JD。"
  },
  {
    value: "parent-child",
    label: "Parent-Child",
    description: "先用小块精准召回，再补充父级或邻近上下文，适合项目总结。"
  },
  {
    value: "advanced-rag",
    label: "Advanced RAG",
    description: "组合查询改写、多查询、metadata filter、混合召回、重排和上下文增强。"
  },
  {
    value: "graph-rag",
    label: "GraphRAG",
    description: "Graph-enhanced retrieval with entity and relationship extraction for traceable graph context."
  }
];

export const mockKnowledgeBases: KnowledgeBaseSummary[] = [
  {
    id: "kb-engineering",
    name: "工程知识库",
    description: "技术笔记、源码分析、项目经验与复盘材料。",
    documentCount: 48,
    chunkCount: 1236,
    updatedAt: "2026-05-25 18:12"
  },
  {
    id: "kb-interview",
    name: "面试与复习",
    description: "面试题、招聘 JD、复习清单和答题反馈。",
    documentCount: 19,
    chunkCount: 462,
    updatedAt: "2026-05-24 21:30"
  }
];

export const mockDocuments: DocumentRecord[] = [
  {
    id: "doc-1",
    knowledgeBaseId: "kb-engineering",
    knowledgeBaseName: "工程知识库",
    title: "Spring 事务与隔离级别",
    documentType: "tech_note",
    fileName: "Spring 事务与隔离级别.md",
    fileType: "md",
    parserName: "plain-text-parser",
    parserVersion: "v1",
    status: "INDEXED",
    chunkCount: 12,
    createdAt: "2026-05-25T17:40:00",
    updatedAt: "2026-05-25 17:50"
  },
  {
    id: "doc-2",
    knowledgeBaseId: "kb-engineering",
    knowledgeBaseName: "工程知识库",
    title: "RAG 实验复盘-召回失败案例",
    documentType: "development_experience",
    fileName: "RAG 实验复盘-召回失败案例.docx",
    fileType: "docx",
    parserName: "docx-parser",
    parserVersion: "v1",
    status: "UPLOADED",
    chunkCount: 0,
    createdAt: "2026-05-25T17:59:00",
    updatedAt: "2026-05-25 18:04"
  },
  {
    id: "doc-3",
    knowledgeBaseId: "kb-interview",
    knowledgeBaseName: "面试与复习",
    title: "高级 Java 开发岗位 JD",
    documentType: "job_description",
    fileName: "高级 Java 开发岗位 JD.pdf",
    fileType: "pdf",
    parserName: "mineru-pdf-adapter",
    parserVersion: "reserved-v1",
    status: "INDEXED",
    chunkCount: 8,
    createdAt: "2026-05-24T20:00:00",
    updatedAt: "2026-05-24 20:18"
  }
];

const demoSources: CitationSource[] = [
  {
    id: "src-1",
    title: "Spring 事务与隔离级别.md",
    location: "chunk 12 · section 事务传播行为",
    strategy: "Hybrid + Rerank",
    score: 0.93,
    snippet: "REQUIRED 会加入已有事务；REQUIRES_NEW 会挂起外部事务并创建新事务。"
  },
  {
    id: "src-2",
    title: "RAG 实验复盘-召回失败案例.docx",
    location: "page 3 · lesson learned",
    strategy: "Parent-Child",
    score: 0.87,
    snippet: "多轮追问场景建议保留上一轮 rewritten query 与检索过滤条件。"
  }
];

export const mockMessages: ChatMessage[] = [
  {
    id: "msg-1",
    role: "user",
    content: "帮我总结 Spring 事务传播行为的核心差异，并给我一个面试回答思路。",
    createdAt: "18:16"
  },
  {
    id: "msg-2",
    role: "assistant",
    content:
      "可以先按“是否复用当前事务”和“异常时影响范围”来回答：\n1. REQUIRED 默认加入当前事务，是最常见的业务边界。\n2. REQUIRES_NEW 总是开启新事务，适合审计日志、补偿记录等独立提交场景。\n3. NESTED 基于保存点，适合同一事务内的局部回滚。\n\n面试时可以先讲定义，再补一个订单+日志的业务例子，最后点出不同数据库和代理方式下的注意事项。",
    createdAt: "18:16",
    sources: demoSources
  }
];

export const mockExperiments: ExperimentRecord[] = [
  {
    id: "exp-1",
    name: "技术笔记混合检索基线",
    strategy: "Hybrid + Rerank",
    precision: "0.78",
    recall: "0.84",
    createdAt: "2026-05-25T17:20:00",
    updatedAt: "2026-05-25 17:20",
    evaluations: [
      {
        id: "eval-1-latest",
        experimentId: "exp-1",
        runId: "run-advanced-2",
        runQuestion: "How does advanced RAG use metadata filters and rerank?",
        runStrategyName: "advanced-rag",
        runRetrieverType: "hybrid",
        runModelName: "stub-llm",
        runLatencyMs: 42,
        runCreatedAt: "2026-06-08T16:39:00",
        groundedScore: 0.86,
        retrievalScore: 0.81,
        expectedAnswer: "Hybrid retrieval should cite rerank evidence.",
        generatedAnswer: "Hybrid retrieval cites rerank evidence and metadata filters.",
        notes: "Improved after metadata filter tuning.",
        createdAt: "2026-06-08T16:40:00"
      },
      {
        id: "eval-1-previous",
        experimentId: "exp-1",
        runId: "run-advanced-1",
        runQuestion: "How should hybrid rerank cite retrieval evidence?",
        runStrategyName: "hybrid-rerank",
        runRetrieverType: "hybrid",
        runModelName: "stub-llm",
        runLatencyMs: 57,
        runCreatedAt: "2026-06-08T15:39:00",
        groundedScore: 0.78,
        retrievalScore: 0.75,
        expectedAnswer: "Hybrid retrieval should cite rerank evidence.",
        generatedAnswer: "Hybrid retrieval cites one source.",
        notes: "Baseline evaluation.",
        createdAt: "2026-06-08T15:40:00"
      }
    ]
  },
  {
    id: "exp-2",
    name: "Parent-Child 在项目复盘中的效果",
    strategy: "Parent-Child",
    precision: "0.74",
    recall: "0.89",
    createdAt: "2026-05-24T22:15:00",
    updatedAt: "2026-05-24 22:15",
    evaluations: [
      {
        id: "eval-2-latest",
        experimentId: "exp-2",
        runId: "run-parent-child-1",
        runQuestion: "How does parent-child retrieval improve project review answers?",
        runStrategyName: "parent-child",
        runRetrieverType: "vector",
        runModelName: "stub-llm",
        runLatencyMs: 61,
        runCreatedAt: "2026-06-08T14:19:00",
        groundedScore: 0.74,
        retrievalScore: 0.88,
        notes: "Parent context improved recall.",
        createdAt: "2026-06-08T14:20:00"
      }
    ]
  }
];

const mockEvaluationHistory = mockExperiments.flatMap((experiment) => experiment.evaluations ?? []);

export const mockExperimentEvaluationSummary: ExperimentEvaluationSummary = {
  evaluationCount: mockEvaluationHistory.length,
  averageGrounded:
    mockEvaluationHistory.reduce((total, evaluation) => total + (evaluation.groundedScore ?? 0), 0)
    / mockEvaluationHistory.length,
  averageRetrieval:
    mockEvaluationHistory.reduce((total, evaluation) => total + (evaluation.retrievalScore ?? 0), 0)
    / mockEvaluationHistory.length,
  bestExperimentId: "exp-1",
  bestExperimentName: mockExperiments[0].name,
  recentEvaluations: mockEvaluationHistory
};

export const mockSettings: AppSettings = {
  apiBaseUrl: "/api",
  aiServiceBaseUrl: "http://localhost:8001",
  defaultKnowledgeBaseId: "kb-engineering",
  timeoutMs: 15000,
  includeTraceHeader: true
};
