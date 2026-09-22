import Link from "next/link";
import { Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { RiskBadge } from "@/components/shared/RiskBadge";
import { PatternCard } from "@/components/shared/PatternCard";
import { Reveal } from "@/components/shared/Reveal";
import { riskProgressColor } from "@/lib/utils-display";
import type { AnalysisResult } from "@/types";

export interface ResultsPanelProps {
  result: AnalysisResult;
  analyzedUrl: string;
}

/**
 * Renders an analysis result: the overall risk score, the list of detected
 * dark patterns, and a call-to-action to submit a community report.
 * Loaded on demand — not needed until an analysis has completed.
 */
export default function ResultsPanel({ result, analyzedUrl }: ResultsPanelProps) {
  const hasHiddenFee = result.patterns.some((p) => p.financial_impact.has_hidden_fee);

  return (
    <div className="space-y-6">
      <Reveal>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle>Overall Risk Assessment</CardTitle>
            <RiskBadge level={result.risk_level} />
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Risk Score</span>
              <span className="font-semibold">{Math.round(result.overall_risk_score)}/100</span>
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

      <div className="space-y-4">
        <Reveal delay={80}>
          <h2 className="text-lg font-semibold">Detected Patterns ({result.patterns.length})</h2>
        </Reveal>
        {result.patterns.length === 0 ? (
          <p className="text-sm text-muted-foreground">No deceptive patterns detected.</p>
        ) : (
          result.patterns.map((p, i) => (
            <Reveal key={i} delay={120 + i * 90}>
              <PatternCard pattern={p} />
            </Reveal>
          ))
        )}
      </div>

      <Reveal delay={120 + result.patterns.length * 90 + 60}>
        <Card className="border-slate-200 bg-slate-50 dark:bg-slate-900">
          <CardContent className="flex flex-col items-center gap-3 py-6 text-center sm:flex-row sm:justify-between sm:text-left">
            <div>
              <p className="font-semibold">Experienced this yourself?</p>
              <p className="text-sm text-muted-foreground">
                Submit a community report to warn other consumers.
              </p>
            </div>
            <Link href={`/report?url=${encodeURIComponent(analyzedUrl)}`} className={buttonVariants()}>
              <Users className="size-4" />
              Submit a Report
            </Link>
          </CardContent>
        </Card>
      </Reveal>
    </div>
  );
}
