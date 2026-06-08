import type { ExperimentRecord, ExperimentRequest, ExperimentUpdateRequest } from "../types";
import { apiRequest } from "./client";

export function fetchExperiments(): Promise<ExperimentRecord[]> {
  return apiRequest<ExperimentRecord[]>("/rag/experiments");
}

export function fetchExperimentById(id: string): Promise<ExperimentRecord> {
  return apiRequest<ExperimentRecord>(`/rag/experiments/${id}`);
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

export function deleteExperiment(id: string): Promise<void> {
  return apiRequest<void>(`/rag/experiments/${id}`, { method: "DELETE" });
}
