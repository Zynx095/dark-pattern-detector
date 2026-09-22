import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { formatDate, formatPatternType, severityColorClasses } from "@/lib/utils-display";
import type { ConsumerReport } from "@/types";

export interface ReportListItemProps {
  report: ConsumerReport;
  isLast: boolean;
  votingId: number | null;
  onVote: (reportId: number, vote: "confirm" | "dispute") => void;
}

/** A single community report row on a domain's profile page, with confirm/dispute voting. */
export function ReportListItem({ report, isLast, votingId, onVote }: ReportListItemProps) {
  return (
    <Card>
      <CardContent className="space-y-3 py-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Badge className={severityColorClasses(report.severity || "medium")} variant="secondary">
            {formatPatternType(report.pattern_type)}
          </Badge>
          <span className="text-xs text-muted-foreground">{formatDate(report.created_at)}</span>
        </div>
        <p className="text-sm leading-relaxed">{report.description}</p>
        {report.evidence && (
          <p className="rounded-md bg-slate-50 p-2 text-xs text-muted-foreground dark:bg-slate-900">
            {report.evidence}
          </p>
        )}
        {!isLast && <Separator />}
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Community confidence: {Math.round(report.community_score * 100)}%
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={votingId === report.id}
              onClick={() => onVote(report.id, "confirm")}
              className="gap-1.5 transition-colors hover:border-emerald-400 hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-emerald-950 dark:hover:text-emerald-300"
            >
              <ThumbsUp className="size-3.5" />
              Confirm
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={votingId === report.id}
              onClick={() => onVote(report.id, "dispute")}
              className="gap-1.5 transition-colors hover:border-red-400 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950 dark:hover:text-red-300"
            >
              <ThumbsDown className="size-3.5" />
              Dispute
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
