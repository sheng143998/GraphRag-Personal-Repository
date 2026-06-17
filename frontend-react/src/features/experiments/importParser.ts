import type { ImportEvaluationCaseItem } from "../../types";

export function parseImportItems(raw: string): ImportEvaluationCaseItem[] {
  const text = raw.trim();
  if (!text) return [];
  if (text.startsWith("[") || text.startsWith("{")) {
    const parsed = JSON.parse(text) as unknown;
    return (Array.isArray(parsed) ? parsed : [parsed]).map(normalizeImportRow);
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
    notes: stringField(record, "notes", "备注"),
    status: stringField(record, "status", "状态") || "ACTIVE"
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
    if (typeof value === "string") return value.split(/\r?\n|,|;/).map((item) => item.trim()).filter(Boolean);
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
