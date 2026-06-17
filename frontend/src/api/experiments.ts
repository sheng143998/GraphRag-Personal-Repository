import type {
  CreateEvaluationCaseRequest,
  ImportEvaluationCasesPayload,
  ImportEvaluationCasesResponse,
  ExperimentEvaluationRequest,
  ExperimentEvaluationResponse,
  ExperimentEvaluationSummary,
  EvaluationCaseRecord,
  ExperimentRecord,
  ExperimentRequest,
  ExperimentUpdateRequest,
  EvaluateEvaluationCaseRequest,
  RunEvaluationCasesBatchRequest,
  RunEvaluationCasesBatchResponse,
  UpdateEvaluationCaseRequest
} from "../types";
import { apiRequest } from "./client";

export function fetchExperiments(): Promise<ExperimentRecord[]> {
  return apiRequest<ExperimentRecord[]>("/rag/experiments");
}

export function fetchExperimentById(id: string): Promise<ExperimentRecord> {
  return apiRequest<ExperimentRecord>(`/rag/experiments/${id}`);
}

export function fetchExperimentEvaluationSummary(limit = 20): Promise<ExperimentEvaluationSummary> {
  return apiRequest<ExperimentEvaluationSummary>(`/rag/experiment-evaluations/summary?limit=${limit}`);
}

export function createExperiment(payload: ExperimentRequest): Promise<ExperimentRecord> {
  return apiRequest<ExperimentRecord>("/rag/experiments", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateExperiment(id: string, payload: ExperimentUpdateRequest): Promise<ExperimentRecord> {
  return apiRequest<ExperimentRecord>(`/rag/experiments/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function evaluateExperiment(
  id: string,
  payload: ExperimentEvaluationRequest
): Promise<ExperimentEvaluationResponse> {
  return apiRequest<ExperimentEvaluationResponse>(`/rag/experiments/${id}/evaluate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteExperiment(id: string): Promise<void> {
  return apiRequest<void>(`/rag/experiments/${id}`, { method: "DELETE" });
}

export function fetchEvaluationCases(experimentId?: string): Promise<EvaluationCaseRecord[]> {
  const suffix = experimentId ? `?experimentId=${experimentId}` : "";
  return apiRequest<EvaluationCaseRecord[]>(`/rag/evaluation-cases${suffix}`);
}

export function createEvaluationCase(payload: CreateEvaluationCaseRequest): Promise<EvaluationCaseRecord> {
  return apiRequest<EvaluationCaseRecord>("/rag/evaluation-cases", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateEvaluationCase(id: string, payload: UpdateEvaluationCaseRequest): Promise<EvaluationCaseRecord> {
  return apiRequest<EvaluationCaseRecord>(`/rag/evaluation-cases/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteEvaluationCase(id: string): Promise<void> {
  return apiRequest<void>(`/rag/evaluation-cases/${id}`, { method: "DELETE" });
}

export function evaluateEvaluationCase(
  id: string,
  payload: EvaluateEvaluationCaseRequest
): Promise<ExperimentEvaluationResponse> {
  return apiRequest<ExperimentEvaluationResponse>(`/rag/evaluation-cases/${id}/evaluate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function runEvaluationCasesBatch(
  payload: RunEvaluationCasesBatchRequest
): Promise<RunEvaluationCasesBatchResponse> {
  return apiRequest<RunEvaluationCasesBatchResponse>("/rag/evaluation-cases/run-batch", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function importEvaluationCases(
  payload: ImportEvaluationCasesPayload
): Promise<ImportEvaluationCasesResponse> {
  return apiRequest<ImportEvaluationCasesResponse>("/rag/evaluation-cases/import", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
