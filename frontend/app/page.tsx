"use client";

import { useState } from "react";
import Link from "next/link";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskBadge } from "@/components/shared/RiskBadge";
import { PatternCard } from "@/components/shared/PatternCard";
import { Reveal } from "@/components/shared/Reveal";
import { analyzeUrl, analyzeScreenshot } from "@/lib/api";
import { riskProgressColor } from "@/lib/utils-display";
import type { AnalysisResult } from "@/types";
import {
  Search,
  Upload,
  ShieldAlert,
  Loader2,
  FileWarning,
  Users,
  ScanSearch,
} from "lucide-react";

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [analyzedUrl, setAnalyzedUrl] = useState<string>("");

  async function handleAnalyzeUrl(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeUrl(url.trim());
      setResult(data);
      setAnalyzedUrl(url.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyzeScreenshot() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeScreenshot(file);
      setResult(data);
      setAnalyzedUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type.startsWith("image/")) {
      setFile(dropped);
    }
  }

  const hasHiddenFee = result?.patterns.some((p) => p.financial_impact.has_hidden_fee);

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      {/* Hero */}
      <section className="relative mb-10 space-y-3 pt-4 pb-2 text-center">
        <Reveal>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300">
            <ShieldAlert className="size-3.5" />
            Consumer Safety Analyzer
          </div>
        </Reveal>
        <Reveal delay={80}>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Detect Dark Patterns &amp; Hidden Fees
          </h1>
        </Reveal>
        <Reveal delay={140}>
          <p className="mx-auto max-w-xl text-muted-foreground">
            Paste a URL or upload a screenshot to scan for deceptive UI tactics and
            undisclosed recurring charges before you check out.
          </p>
        </Reveal>
      </section>

      {/* Input Card — the focal point */}
      <Reveal delay={200}>
        <Card className="mb-8 border-slate-200 shadow-sm dark:border-slate-800">
          <CardContent className="pt-6 space-y-5">
            <form onSubmit={handleAnalyzeUrl} className="flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="https://example.com/checkout"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="h-11 pl-9 text-base"
                  disabled={loading}
                />
              </div>
              <Button
                type="submit"
                disabled={loading || !url.trim()}
                className="h-11 sm:w-44"
              >
                {loading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <>
                    <ScanSearch className="size-4" />
                    Analyze URL
                  </>
                )}
              </Button>
            </form>

            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs text-muted-foreground">OR</span>
              <div className="h-px flex-1 bg-border" />
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <label
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                className={`flex flex-1 cursor-pointer items-center gap-2 rounded-lg border-2 border-dashed px-4 py-3.5 text-sm transition-all ${
                  dragActive
                    ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                    : "border-slate-300 text-muted-foreground hover:border-slate-400 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900"
                }`}
              >
                <Upload className={`size-4 shrink-0 ${dragActive ? "animate-bounce" : ""}`} />
                <span className="truncate">
                  {file
                    ? file.name
                    : dragActive
                    ? "Drop the screenshot here"
                    : "Drag & drop a checkout/subscription screenshot, or click to browse"}
                </span>
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  disabled={loading}
                />
              </label>
              <Button
                variant="secondary"
                onClick={handleAnalyzeScreenshot}
                disabled={loading || !file}
                className="h-11 sm:w-44"
              >
                {loading ? <Loader2 className="size-4 animate-spin" /> : "Analyze Image"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </Reveal>

      {error && (
        <Alert variant="destructive" className="mb-8">
          <FileWarning className="size-4" />
          <AlertTitle>Analysis failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6">
          {/* Overall score */}
          <Reveal>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle>Overall Risk Assessment</CardTitle>
                <RiskBadge level={result.risk_level} />
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Risk Score</span>
                  <span className="font-semibold">
                    {Math.round(result.overall_risk_score)}/100
                  </span>
                </div>
                <Progress
                  value={result.overall_risk_score}
                  className={`h-2.5 ${riskProgressColor(result.risk_level)}`}
                />
                {hasHiddenFee && (
                  <p className="pt-1 text-sm font-medium text-red-600 dark:text-red-400">
                    ⚠ This analysis found at least one hidden or undisclosed fee.
                  </p>
                )}
              </CardContent>
            </Card>
          </Reveal>

          {/* Patterns */}
          <div className="space-y-4">
            <Reveal delay={80}>
              <h2 className="text-lg font-semibold">
                Detected Patterns ({result.patterns.length})
              </h2>
            </Reveal>
            {result.patterns.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No deceptive patterns detected.
              </p>
            ) : (
              result.patterns.map((p, i) => (
                <Reveal key={i} delay={120 + i * 90}>
                  <PatternCard pattern={p} />
                </Reveal>
              ))
            )}
          </div>

          {/* CTA */}
          <Reveal delay={120 + result.patterns.length * 90 + 60}>
            <Card className="border-slate-200 bg-slate-50 dark:bg-slate-900">
              <CardContent className="flex flex-col items-center gap-3 py-6 text-center sm:flex-row sm:justify-between sm:text-left">
                <div>
                  <p className="font-semibold">Experienced this yourself?</p>
                  <p className="text-sm text-muted-foreground">
                    Submit a community report to warn other consumers.
                  </p>
                </div>
                <Link
                  href={`/report?url=${encodeURIComponent(analyzedUrl)}`}
                  className={buttonVariants()}
                >
                  <Users className="size-4" />
                  Submit a Report
                </Link>
              </CardContent>
            </Card>
          </Reveal>
        </div>
      )}
    </div>
  );
}
