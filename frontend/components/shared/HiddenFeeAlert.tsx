import { AlertTriangle } from "lucide-react";
import type { FinancialImpact } from "@/types";

/** Prominent warning banner for a hidden or undisclosed fee; renders nothing if none was found. */
export function HiddenFeeAlert({ impact }: { impact: FinancialImpact }) {
  if (!impact?.has_hidden_fee) return null;

  return (
    <div className="relative flex items-start gap-4 overflow-hidden rounded-xl border-2 border-red-700 bg-red-600 p-5 text-white shadow-lg shadow-red-600/20 ring-4 ring-red-600/15 dark:border-red-600 dark:bg-red-700">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.15),transparent_60%)]" />
      <AlertTriangle className="relative mt-0.5 size-7 shrink-0 animate-glow-pulse" />
      <div className="relative space-y-1">
        <p className="text-xs font-bold uppercase tracking-widest text-red-100">
          Hidden Fee Warning
        </p>
        <p className="text-xl font-extrabold leading-tight tracking-tight">
          {impact.estimated_amount || "Unknown amount"}
          {impact.is_recurring && impact.frequency
            ? ` / ${impact.frequency}`
            : ""}
        </p>
        <p className="text-sm font-medium text-red-50">
          {impact.is_recurring
            ? "Recurring charge detected — not clearly disclosed at checkout."
            : "One-time hidden charge detected — not clearly disclosed at checkout."}
        </p>
      </div>
    </div>
  );
}
