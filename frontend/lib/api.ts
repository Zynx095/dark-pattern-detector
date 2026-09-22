import type {
  AnalysisResult,
  ConsumerReport,
  ConsumerReportCreate,
  IndexItem,
  VoteResponse,
  WebsiteProfile,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Issues a JSON (or FormData) request against the backend API and parses the response. */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return res.json();
}

/** Analyzes a checkout/subscription page by URL for dark patterns and hidden fees. */
export function analyzeUrl(url: string) {
  return request<AnalysisResult>("/api/analyze/url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

/** Analyzes an uploaded screenshot for dark patterns and hidden fees. */
export function analyzeScreenshot(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<AnalysisResult>("/api/analyze/screenshot", {
    method: "POST",
    body: form,
  });
}

/** Submits a new community report for a domain. */
export function createReport(payload: ConsumerReportCreate) {
  return request<ConsumerReport>("/api/reports", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** Lists community reports, optionally filtered by domain and/or pattern type. */
export function listReports(params?: { domain?: string; pattern_type?: string }) {
  const qs = new URLSearchParams();
  if (params?.domain) qs.set("domain", params.domain);
  if (params?.pattern_type) qs.set("pattern_type", params.pattern_type);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return request<ConsumerReport[]>(`/api/reports${suffix}`);
}

/** Fetches a single community report by id. */
export function getReport(id: number) {
  return request<ConsumerReport>(`/api/reports/${id}`);
}

/** Casts a confirm/dispute vote on a community report. */
export function voteOnReport(id: number, vote: "confirm" | "dispute") {
  return request<VoteResponse>(`/api/reports/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote }),
  });
}

/** Fetches the community safety index, ranked by report activity. */
export function getIndex(limit = 20) {
  return request<IndexItem[]>(`/api/index?limit=${limit}`);
}

/** Fetches the aggregated risk profile and report history for a domain. */
export function getWebsiteProfile(domain: string) {
  return request<WebsiteProfile>(`/api/websites/${encodeURIComponent(domain)}`);
}

/** Searches indexed domains by query string. */
export function searchWebsites(q: string) {
  return request<IndexItem[]>(`/api/search?q=${encodeURIComponent(q)}`);
}

/** Checks backend API health/version. */
export function checkHealth() {
  return request<{ status: string; version: string }>("/health");
}
