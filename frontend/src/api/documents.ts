import type { DocumentRecord, UploadPayload, UploadResponse } from "../types";
import { apiRequest } from "./client";

export function fetchDocuments(): Promise<DocumentRecord[]> {
  return apiRequest<DocumentRecord[]>("/documents");
}

export function uploadDocuments(payload: UploadPayload): Promise<UploadResponse> {
  return apiRequest<UploadResponse>("/documents/upload", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
