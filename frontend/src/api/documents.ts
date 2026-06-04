import type { DocumentRecord, UploadPayload, UploadResponse } from "../types";
import { apiRequest } from "./client";

export function fetchDocuments(): Promise<DocumentRecord[]> {
  return apiRequest<DocumentRecord[]>("/documents");
}

export function fetchDocumentById(id: string): Promise<DocumentRecord> {
  return apiRequest<DocumentRecord>(`/documents/${id}`);
}

export function uploadDocuments(payload: UploadPayload): Promise<UploadResponse> {
  if (payload.file) {
    const formData = new FormData();
    formData.set("knowledgeBaseId", payload.knowledgeBaseId);
    formData.set("title", payload.title);
    formData.set("documentType", payload.documentType);
    formData.set("sourceType", payload.sourceType ?? "LOCAL_UPLOAD");
    formData.set("sourcePath", payload.sourcePath ?? payload.fileName);
    formData.set("summary", payload.summary ?? "");
    formData.set("metadata", JSON.stringify(payload.metadata ?? {}));
    formData.set("file", payload.file);

    return apiRequest<UploadResponse>("/documents/upload", {
      method: "POST",
      body: formData
    });
  }

  return apiRequest<UploadResponse>("/documents/upload", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function deleteDocument(id: string): Promise<void> {
  return apiRequest<void>(`/documents/${id}`, { method: "DELETE" });
}