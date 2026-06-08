import type { ApiEnvelope } from "../types";

const DEFAULT_BASE_URL = "/api";
const DEFAULT_TIMEOUT = 15000;
export const API_RUNTIME_SETTINGS_KEY = "agent-knowledge-settings";

interface RuntimeApiSettings {
  apiBaseUrl?: string;
  timeoutMs?: number;
  includeTraceHeader?: boolean;
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
  traceId?: string;
}

export class ApiError extends Error {
  status: number;
  traceId?: string;

  constructor(message: string, status: number, traceId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.traceId = traceId;
  }
}

function resolveBaseUrl(): string {
  const runtimeBaseUrl = readRuntimeSettings().apiBaseUrl;
  if (runtimeBaseUrl && runtimeBaseUrl.trim().length > 0) {
    return runtimeBaseUrl.trim().replace(/\/$/, "");
  }

  const value = import.meta.env.VITE_API_BASE_URL;
  return typeof value === "string" && value.trim().length > 0 ? value : DEFAULT_BASE_URL;
}

function readRuntimeSettings(): RuntimeApiSettings {
  try {
    const raw = window.localStorage.getItem(API_RUNTIME_SETTINGS_KEY);
    if (!raw) {
      return {};
    }

    const parsed = JSON.parse(raw) as RuntimeApiSettings;
    return typeof parsed === "object" && parsed !== null ? parsed : {};
  } catch {
    return {};
  }
}

function resolveTimeoutMs(options: RequestOptions): number {
  if (options.timeoutMs) {
    return options.timeoutMs;
  }

  const runtimeTimeout = readRuntimeSettings().timeoutMs;
  return typeof runtimeTimeout === "number" && runtimeTimeout > 0 ? runtimeTimeout : DEFAULT_TIMEOUT;
}

function buildHeaders(options: RequestOptions): Headers {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");

  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const includeTraceHeader = readRuntimeSettings().includeTraceHeader !== false;
  if (includeTraceHeader && options.traceId) {
    headers.set("X-Trace-Id", options.traceId);
  }

  return headers;
}

function withTimeout(timeoutMs: number): AbortSignal {
  const controller = new AbortController();
  window.setTimeout(() => controller.abort(), timeoutMs);
  return controller.signal;
}

function isApiEnvelope<T>(payload: unknown): payload is ApiEnvelope<T> {
  return typeof payload === "object" && payload !== null && "data" in payload;
}

function extractTraceId<T>(payload: unknown, response: Response): string | undefined {
  const headerTraceId = response.headers.get("X-Trace-Id");
  if (headerTraceId) {
    return headerTraceId;
  }

  if (typeof payload === "object" && payload !== null && "traceId" in payload) {
    return String((payload as ApiEnvelope<T>).traceId ?? "");
  }

  return undefined;
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null) {
    return fallback;
  }

  // Spring Boot ApiResponse: { error: { code, message } }
  if ("error" in payload) {
    const error = (payload as { error?: { code?: string; message?: string } }).error;
    if (error?.message) {
      return error.code ? `[${error.code}] ${error.message}` : error.message;
    }
  }

  return fallback;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${resolveBaseUrl()}${path}`, {
    ...options,
    headers: buildHeaders(options),
    signal: options.signal ?? withTimeout(resolveTimeoutMs(options))
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? ((await response.json()) as ApiEnvelope<T> | T) : null;
  const traceId = extractTraceId<T>(payload, response);

  if (!response.ok) {
    const message = extractErrorMessage(payload, `请求失败，状态码 ${response.status}`);
    throw new ApiError(message, response.status, traceId);
  }

  if (isJson && isApiEnvelope<T>(payload)) {
    return payload.data;
  }

  return payload as T;
}
