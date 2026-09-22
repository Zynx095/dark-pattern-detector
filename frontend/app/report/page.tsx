"use client";

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { createReport } from "@/lib/api";
import { CheckCircle2, FileWarning, Loader2 } from "lucide-react";

const PATTERN_CATEGORIES = [
  { value: "hidden_recurring_fee", label: "Hidden Recurring Fee" },
  { value: "forced_continuity", label: "Forced Continuity / Hard-to-Cancel Subscription" },
  { value: "drip_pricing", label: "Drip Pricing (fees added at checkout)" },
  { value: "confirmshaming", label: "Confirmshaming" },
  { value: "false_urgency", label: "False Urgency / Countdown Timer" },
  { value: "sneak_into_basket", label: "Sneak Into Basket" },
  { value: "misleading_free_trial", label: "Misleading Free Trial" },
  { value: "other", label: "Other Deceptive Pattern" },
];

function ReportForm() {
  const params = useSearchParams();
  const router = useRouter();

  const [url, setUrl] = useState(params.get("url") || "");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [evidence, setEvidence] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || !description.trim() || !category) return;
    setLoading(true);
    setError(null);
    try {
      await createReport({
        url: url.trim(),
        description: description.trim(),
        pattern_category: category,
        severity,
        evidence: evidence.trim() || undefined,
      });
      setSuccess(true);
      setTimeout(() => router.push("/index"), 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit report.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <Card className="mx-auto max-w-lg">
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <CheckCircle2 className="size-10 text-emerald-600" />
          <p className="text-lg font-semibold">Report submitted</p>
          <p className="text-sm text-muted-foreground">
            Thank you for helping keep other consumers safe. Redirecting…
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mx-auto max-w-lg">
      <CardHeader>
        <CardTitle>Submit a Consumer Report</CardTitle>
        <CardDescription>
          Help the community by documenting a deceptive experience you encountered.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Website URL</label>
            <Input
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Pattern Category</label>
            <Select value={category} onValueChange={(v) => setCategory(v || "")} required>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a pattern type" />
              </SelectTrigger>
              <SelectContent>
                {PATTERN_CATEGORIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Severity</label>
            <Select value={severity} onValueChange={(v) => setSeverity(v || "medium")}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Description</label>
            <Textarea
              placeholder="Describe what happened, what you expected vs. what occurred..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={4}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Evidence <span className="text-muted-foreground">(optional)</span>
            </label>
            <Textarea
              placeholder="Quote exact text, prices shown, or link to a screenshot..."
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
              rows={3}
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <FileWarning className="size-4" />
              <AlertTitle>Submission failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={loading || !url.trim() || !description.trim() || !category}
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : "Submit Report"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function ReportPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <Suspense fallback={null}>
        <ReportForm />
      </Suspense>
    </div>
  );
}
