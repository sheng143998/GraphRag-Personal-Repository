import type { FeedbackRecord, FeedbackRequest } from "../types";
import { apiRequest } from "./client";

export function createFeedback(payload: FeedbackRequest): Promise<FeedbackRecord> {
  return apiRequest<FeedbackRecord>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
