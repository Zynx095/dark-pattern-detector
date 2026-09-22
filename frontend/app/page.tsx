"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { ShieldAlert, FileWarning } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { AnalyzerForm } from "@/components/home/AnalyzerForm";
import { Reveal } from "@/components/shared/Reveal";
import { analyzeUrl, analyzeScreenshot } from "@/lib/api";
import type { AnalysisResult } from "@/types";

// Not needed until an analysis completes, so it is split out of the
// initial homepage bundle rather than shipped upfront.
const ResultsPanel = dynamic(() => import("@/components/home/ResultsPanel"), {
  loading: () => (
    <div className="space-y-4">
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  ),
});

/** Homepage: lets a visitor analyze a URL or screenshot and view the results. */
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

      <Reveal delay={200}>
        <AnalyzerForm
          url={url}
          onUrlChange={setUrl}
          onAnalyzeUrl={handleAnalyzeUrl}
          file={file}
          onFileChange={setFile}
          onAnalyzeScreenshot={handleAnalyzeScreenshot}
          dragActive={dragActive}
          onDragActiveChange={setDragActive}
          loading={loading}
        />
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

      {result && !loading && <ResultsPanel result={result} analyzedUrl={analyzedUrl} />}
    </div>
  );
}
