import type {
  AnalysisResult,
  ConsumerReport,
  ConsumerReportCreate,
  IndexItem,
  VoteResponse,
  WebsiteProfile,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

export function analyzeUrl(url: string) {
  return request<AnalysisResult>("/api/analyze/url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function analyzeScreenshot(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<AnalysisResult>("/api/analyze/screenshot", {
    method: "POST",
    body: form,
  });
}

export function createReport(payload: ConsumerReportCreate) {
  return request<ConsumerReport>("/api/reports", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listReports(params?: { domain?: string; pattern_type?: string }) {
  const qs = new URLSearchParams();
  if (params?.domain) qs.set("domain", params.domain);
  if (params?.pattern_type) qs.set("pattern_type", params.pattern_type);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return request<ConsumerReport[]>(`/api/reports${suffix}`);
}

export function getReport(id: number) {
  return request<ConsumerReport>(`/api/reports/${id}`);
}

export function voteOnReport(id: number, vote: "confirm" | "dispute") {
  return request<VoteResponse>(`/api/reports/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote }),
  });
}

export function getIndex(limit = 20) {
  return request<IndexItem[]>(`/api/index?limit=${limit}`);
}

export function getWebsiteProfile(domain: string) {
  return request<WebsiteProfile>(`/api/websites/${encodeURIComponent(domain)}`);
}

export function searchWebsites(q: string) {
  return request<IndexItem[]>(`/api/search?q=${encodeURIComponent(q)}`);
}

export function checkHealth() {
  return request<{ status: string; version: string }>("/health");
}
