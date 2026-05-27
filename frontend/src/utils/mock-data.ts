import type {
  AppSettings,
  ChatMessage,
  CitationSource,
  DocumentRecord,
  ExperimentRecord,
  KnowledgeBaseSummary,
  RagStrategyOption
} from "../types";

export const ragStrategyOptions: RagStrategyOption[] = [
  {
    value: "hybrid-rerank",
    label: "Hybrid + Rerank",
    description: "适合技术笔记与开发经验，兼顾语义召回和关键词精度。"
  },
  {
    value: "parent-child",
    label: "Parent-Child",
    description: "先用小块精准召回，再回填大块上下文，适合项目总结。"
  },
  {
    value: "metadata-filter",
    label: "Metadata Filter",
    description: "按技术栈、标签和时间过滤，适合代码片段和招聘 JD。"
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
    name: "Spring 事务与隔离级别.md",
    documentType: "技术笔记",
    fileType: "markdown",
    knowledgeBaseName: "工程知识库",
    status: "indexed",
    updatedAt: "2026-05-25 17:50"
  },
  {
    id: "doc-2",
    name: "RAG 实验复盘-召回失败案例.docx",
    documentType: "开发经验",
    fileType: "word",
    knowledgeBaseName: "工程知识库",
    status: "processing",
    updatedAt: "2026-05-25 18:04"
  },
  {
    id: "doc-3",
    name: "高级 Java 开发岗位 JD.pdf",
    documentType: "招聘 JD",
    fileType: "pdf",
    knowledgeBaseName: "面试与复习",
    status: "indexed",
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
    updatedAt: "2026-05-25 17:20"
  },
  {
    id: "exp-2",
    name: "Parent-Child 在项目复盘中的效果",
    strategy: "Parent-Child",
    precision: "0.74",
    recall: "0.89",
    updatedAt: "2026-05-24 22:15"
  }
];

export const mockSettings: AppSettings = {
  apiBaseUrl: "/api",
  defaultKnowledgeBaseId: "kb-engineering",
  timeoutMs: 15000,
  includeTraceHeader: true
};
