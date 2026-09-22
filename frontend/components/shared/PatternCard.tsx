import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { HiddenFeeAlert } from "@/components/shared/HiddenFeeAlert";
import { severityColorClasses, formatPatternType } from "@/lib/utils-display";
import type { DetectedPattern } from "@/types";
import { Terminal } from "lucide-react";

export function PatternCard({ pattern }: { pattern: DetectedPattern }) {
  return (
    <Card className="border-slate-200 transition-shadow hover:shadow-md dark:border-slate-800">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base">
            {formatPatternType(pattern.type)}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge className={severityColorClasses(pattern.severity)} variant="secondary">
              {pattern.severity}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {Math.round(pattern.confidence * 100)}% confidence
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <HiddenFeeAlert impact={pattern.financial_impact} />

        <div className="space-y-1.5">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <Terminal className="size-3.5" />
            Evidence Extracted
          </p>
          <div className="rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 shadow-inner dark:border-slate-800">
            <p className="font-mono text-[0.8rem] leading-relaxed text-emerald-400 selection:bg-emerald-400/30">
              <span className="select-none text-slate-500">{"> "}</span>
              &ldquo;{pattern.evidence}&rdquo;
            </p>
          </div>
        </div>

        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Why this matters
          </p>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {pattern.explanation}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
