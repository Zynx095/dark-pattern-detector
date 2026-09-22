"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskBadge } from "@/components/shared/RiskBadge";
import { ReportListItem } from "@/components/domain/ReportListItem";
import { getWebsiteProfile, voteOnReport } from "@/lib/api";
import { riskProgressColor, formatDate, formatPatternType } from "@/lib/utils-display";
import type { WebsiteProfile } from "@/types";
import { Globe, FileText } from "lucide-react";

/** Public profile page for a single domain: its risk score and community report history. */
export default function DomainProfilePage({
  params,
}: {
  params: Promise<{ domain: string }>;
}) {
  const { domain } = use(params);
  const decodedDomain = decodeURIComponent(domain);

  const [profile, setProfile] = useState<WebsiteProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [votingId, setVotingId] = useState<number | null>(null);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [decodedDomain]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await getWebsiteProfile(decodedDomain);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Domain not found.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVote(reportId: number, vote: "confirm" | "dispute") {
    setVotingId(reportId);
    try {
      await voteOnReport(reportId, vote);
      await load();
    } catch {
      // ignore
    } finally {
      setVotingId(null);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-10 sm:px-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16 text-center sm:px-6">
        <Globe className="mx-auto mb-3 size-10 text-muted-foreground" />
        <p className="text-lg font-semibold">Domain not found</p>
        <p className="mb-4 text-sm text-muted-foreground">{error}</p>
        <Link href="/directory" className={buttonVariants({ variant: "secondary" })}>
          Back to Community Index
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div className="flex items-center gap-2">
            <Globe className="size-5 text-muted-foreground" />
            <CardTitle className="text-xl">{profile.domain}</CardTitle>
          </div>
          <RiskBadge level={profile.risk_level} />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Risk Score</span>
              <span className="font-semibold">{Math.round(profile.risk_score)}/100</span>
            </div>
            <Progress
              value={profile.risk_score}
              className={`h-2.5 ${riskProgressColor(profile.risk_level)}`}
            />
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Total Reports" value={profile.total_reports} />
            <Stat label="Confirmed" value={profile.confirmed_reports} />
            <Stat
              label="Last Analyzed"
              value={formatDate(profile.last_analyzed)}
              small
            />
            <Stat label="Patterns" value={profile.detected_patterns.length} />
          </div>
          {profile.detected_patterns.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {profile.detected_patterns.map((p) => (
                <Badge key={p} variant="secondary">
                  {formatPatternType(p)}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
          <FileText className="size-4" />
          Report History
        </h2>
        {profile.recent_reports.length === 0 ? (
          <p className="text-sm text-muted-foreground">No reports yet for this domain.</p>
        ) : (
          <div className="space-y-3">
            {profile.recent_reports.map((report, i) => (
              <ReportListItem
                key={report.id}
                report={report}
                isLast={i === profile.recent_reports.length - 1}
                votingId={votingId}
                onVote={handleVote}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** Small labeled stat tile used in the domain profile summary grid. */
function Stat({
  label,
  value,
  small,
}: {
  label: string;
  value: string | number;
  small?: boolean;
}) {
  return (
    <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={small ? "text-sm font-semibold" : "text-lg font-semibold"}>{value}</p>
    </div>
  );
}
