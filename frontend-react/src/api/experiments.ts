import type {
  ExperimentEvaluationSummary,
  ExperimentRecord,
  ExperimentRequest,
  EvaluationCaseRecord,
  ImportEvaluationCasesPayload,
  ImportEvaluationCasesResponse,
  RunEvaluationCasesBatchRequest,
  RunEvaluationCasesBatchResponse,
  UpdateEvaluationCasePayload
} from "../types";
import { apiRequest } from "./client";

export function fetchExperiments(): Promise<ExperimentRecord[]> {
  return apiRequest<ExperimentRecord[]>("/rag/experiments");
}

export function createExperiment(payload: ExperimentRequest): Promise<ExperimentRecord> {
  return apiRequest<ExperimentRecord>("/rag/experiments", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function deleteExperiment(id: string): Promise<void> {
  return apiRequest<void>(`/rag/experiments/${encodeURIComponent(id)}`, {
    method: "DELETE"
  });
}

export function fetchExperimentEvaluationSummary(limit = 50): Promise<ExperimentEvaluationSummary> {
  return apiRequest<ExperimentEvaluationSummary>(`/rag/experiment-evaluations/summary?limit=${limit}`);
}

export function fetchEvaluationCases(experimentId?: string): Promise<EvaluationCaseRecord[]> {
  const suffix = experimentId ? `?experimentId=${encodeURIComponent(experimentId)}` : "";
  return apiRequest<EvaluationCaseRecord[]>(`/rag/evaluation-cases${suffix}`);
}

export function importEvaluationCases(
  payload: ImportEvaluationCasesPayload
): Promise<ImportEvaluationCasesResponse> {
  return apiRequest<ImportEvaluationCasesResponse>("/rag/evaluation-cases/import", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateEvaluationCase(
  id: string,
  payload: UpdateEvaluationCasePayload
): Promise<EvaluationCaseRecord> {
  return apiRequest<EvaluationCaseRecord>(`/rag/evaluation-cases/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteEvaluationCase(id: string): Promise<void> {
  return apiRequest<void>(`/rag/evaluation-cases/${encodeURIComponent(id)}`, {
    method: "DELETE"
  });
}

export function runEvaluationCasesBatch(
  payload: RunEvaluationCasesBatchRequest
): Promise<RunEvaluationCasesBatchResponse> {
  return apiRequest<RunEvaluationCasesBatchResponse>("/rag/evaluation-cases/run-batch", {
    method: "POST",
    timeoutMs: 240000,
    body: JSON.stringify(payload)
  });
}
