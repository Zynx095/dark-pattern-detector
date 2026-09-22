"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskBadge } from "@/components/shared/RiskBadge";
import { getIndex, searchWebsites } from "@/lib/api";
import { formatDate, formatPatternType } from "@/lib/utils-display";
import type { IndexItem } from "@/types";
import { Search, Globe, FileText } from "lucide-react";
export const dynamic = "force-dynamic";
export default function CommunityIndexPage() {
  const [items, setItems] = useState<IndexItem[] | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await getIndex(50);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach backend.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return load();
    setLoading(true);
    setError(null);
    try {
      const data = await searchWebsites(query.trim());
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="mb-8 space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">Community Safety Index</h1>
        <p className="text-muted-foreground">
          Domains reported for deceptive practices, ranked by community activity.
        </p>
      </div>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by domain..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </form>

      {error && (
        <p className="mb-6 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      {loading && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      )}

      {!loading && items && items.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground">
            <Globe className="size-8" />
            <p>No domains found.</p>
          </CardContent>
        </Card>
      )}

      {!loading && items && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => (
            <Link key={item.domain} href={`/domain/${encodeURIComponent(item.domain)}`}>
              <Card className="transition-all hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md dark:hover:border-slate-600">
                <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 font-semibold">
                      <Globe className="size-4 text-muted-foreground" />
                      {item.domain}
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                      <FileText className="size-3" />
                      {item.report_count} report{item.report_count === 1 ? "" : "s"}
                      <span>· First reported {formatDate(item.first_reported)}</span>
                    </div>
                    {item.major_patterns.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {item.major_patterns.slice(0, 3).map((p) => (
                          <Badge key={p} variant="secondary" className="text-xs font-normal">
                            {formatPatternType(p)}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <RiskBadge level={item.risk_level} />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
