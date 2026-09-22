export interface FinancialImpact {
  has_hidden_fee: boolean;
  estimated_amount: string | null;
  is_recurring: boolean;
  frequency: string | null;
}

export interface DetectedPattern {
  type: string;
  severity: "low" | "medium" | "high" | string;
  confidence: number;
  evidence: string;
  explanation: string;
  financial_impact: FinancialImpact;
}

export interface AnalysisResult {
  overall_risk_score: number;
  risk_level: "low" | "medium" | "high" | string;
  patterns: DetectedPattern[];
}

export interface ConsumerReport {
  id: number;
  website_id: number;
  submitted_url: string;
  description: string;
  pattern_type: string;
  severity?: string;
  evidence?: string | null;
  screenshot_path?: string | null;
  analysis_id?: number | null;
  community_score: number;
  status: string;
  created_at: string;
}

export interface WebsiteProfile {
  domain: string;
  risk_score: number;
  risk_level: string;
  total_reports: number;
  confirmed_reports: number;
  detected_patterns: string[];
  recent_reports: ConsumerReport[];
  last_analyzed: string | null;
}

export interface IndexItem {
  domain: string;
  report_count: number;
  risk_score: number;
  risk_level: string;
  community_confidence: number;
  major_patterns: string[];
  first_reported: string;
}

export interface VoteResponse {
  message: string;
  confirm_count: number;
  dispute_count: number;
  community_confidence: number;
}

export interface ConsumerReportCreate {
  url: string;
  description: string;
  pattern_category: string;
  severity?: string;
  evidence?: string;
  analysis_id?: number;
}
