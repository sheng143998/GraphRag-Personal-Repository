import type { ImportEvaluationCaseItem } from "../../types";

const APPROVED_DECISIONS = new Set(["approve", "approved", "active", "pass", "passed", "ok", "y", "yes", "通过", "已通过", "同意", "启用", "采纳", "保留"]);
const REJECTED_DECISIONS = new Set(["reject", "rejected", "drop", "dropped", "discard", "discarded", "n", "no", "拒绝", "不通过", "驳回", "剔除", "删除", "作废", "停用"]);
const DRAFT_DECISIONS = new Set(["draft", "pending", "review", "revise", "needs_revision", "待审", "待审核", "草稿", "需修改", "修改后再审"]);
const SKIP_DECISIONS = new Set(["skip", "skipped", "ignore", "ignored", "跳过", "忽略"]);

export function parseImportItems(raw: string): ImportEvaluationCaseItem[] {
  const text = raw.trim();
  if (!text) return [];
  if (text.startsWith("[") || text.startsWith("{")) {
    const parsed = JSON.parse(text) as unknown;
    const items =
      typeof parsed === "object" &&
      parsed !== null &&
      "items" in parsed &&
      Array.isArray((parsed as { items?: unknown }).items)
        ? (parsed as { items: unknown[] }).items
        : Array.isArray(parsed)
          ? parsed
          : [parsed];
    return items.map(normalizeImportRow);
  }
  return parseCsv(text).map(normalizeImportRow);
}

function normalizeImportRow(row: unknown, index: number): ImportEvaluationCaseItem {
  if (typeof row !== "object" || row === null) {
    throw new Error(`第 ${index + 1} 行不是有效对象。`);
  }
  const record = row as Record<string, unknown>;
  const question = stringField(record, "question", "问题");
  if (!question) throw new Error(`第 ${index + 1} 行缺少 question。`);
  const notes = [stringField(record, "notes", "备注"), stringField(record, "humanNotes", "human_notes", "人工备注")]
    .filter(Boolean)
    .join("\n");
  return {
    caseId: stringField(record, "caseId", "case_id", "样本ID") || `case-${index + 1}`,
    question,
    requiredChunkIds: listField(record, "requiredChunkIds", "required_chunk_ids", "required"),
    supportingChunkIds: listField(record, "supportingChunkIds", "supporting_chunk_ids", "supporting"),
    acceptableChunkIds: listField(record, "acceptableChunkIds", "acceptable_chunk_ids", "acceptable"),
    citationChunkIds: listField(record, "citationChunkIds", "citation_chunk_ids", "citation"),
    expectedAnswer: stringField(record, "expectedAnswer", "expected_answer", "标准答案"),
    relevantChunkIds: listField(record, "relevantChunkIds", "relevant_chunk_ids", "相关ChunkIDs"),
    relevantDocumentIds: listField(record, "relevantDocumentIds", "relevant_document_ids", "相关DocumentIDs"),
    expectedCitationChunkIds: listField(
      record,
      "expectedCitationChunkIds",
      "expected_citation_chunk_ids",
      "期望引用ChunkIDs"
    ),
    evaluationTopK: numberField(record, "evaluationTopK", "evaluation_top_k", "topK") ?? 5,
    notes,
    status: reviewStatusField(record) || "ACTIVE"
  };
}

function parseCsv(text: string): Record<string, string>[] {
  const lines = text.split(/\r?\n/).filter((line) => line.trim());
  if (lines.length < 2) return [];
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = splitCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header.trim(), values[index] ?? ""]));
  });
}

function splitCsvLine(line: string): string[] {
  const values: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === "\"" && next === "\"") {
      current += "\"";
      index += 1;
    } else if (char === "\"") {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      values.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current.trim());
  return values;
}

function stringField(record: Record<string, unknown>, ...keys: string[]): string {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string") return value.trim();
    if (value != null) return String(value).trim();
  }
  return "";
}

function listField(record: Record<string, unknown>, ...keys: string[]): string[] {
  for (const key of keys) {
    const value = record[key];
    if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean);
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
        try {
          const parsed = JSON.parse(trimmed) as unknown;
          if (Array.isArray(parsed)) return parsed.map((item) => String(item).trim()).filter(Boolean);
        } catch {
          // 回退到分隔符解析，便于处理手工 CSV 中的不完整 JSON。
        }
      }
      return trimmed.split(/\r?\n|,|，|;|；/).map((item) => item.trim()).filter(Boolean);
    }
  }
  return [];
}

function numberField(record: Record<string, unknown>, ...keys: string[]): number | undefined {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "number") return value;
    if (typeof value === "string" && value.trim()) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : undefined;
    }
  }
  return undefined;
}

function reviewStatusField(record: Record<string, unknown>): string {
  const decision = normalizeToken(stringField(record, "humanDecision", "human_decision", "人工决策", "审核结论"));
  if (decision) {
    const mapped = mapReviewStatus(decision);
    if (mapped) return mapped;
  }

  const reviewStatus = normalizeToken(stringField(record, "reviewStatus", "review_status", "审核状态"));
  const mappedReviewStatus = mapReviewStatus(reviewStatus);
  if (mappedReviewStatus) return mappedReviewStatus;

  const status = normalizeToken(stringField(record, "status", "状态"));
  return mapReviewStatus(status) || status.toUpperCase();
}

function mapReviewStatus(value: string): string {
  if (!value) return "";
  if (APPROVED_DECISIONS.has(value)) return "ACTIVE";
  if (REJECTED_DECISIONS.has(value)) return "REJECTED";
  if (DRAFT_DECISIONS.has(value)) return "DRAFT";
  if (SKIP_DECISIONS.has(value)) return "ARCHIVED";
  return "";
}

function normalizeToken(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, "_");
}
