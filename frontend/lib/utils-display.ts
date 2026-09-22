/** Tailwind classes for a risk-level badge (low/medium/high). */
export function riskColorClasses(level: string): string {
  switch (level?.toLowerCase()) {
    case "high":
      return "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-900";
    case "medium":
      return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-900";
    default:
      return "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-900";
  }
}

/** Tailwind classes coloring a risk-score progress bar's fill. */
export function riskProgressColor(level: string): string {
  switch (level?.toLowerCase()) {
    case "high":
      return "[&>div]:bg-red-600";
    case "medium":
      return "[&>div]:bg-amber-500";
    default:
      return "[&>div]:bg-emerald-600";
  }
}

/** Tailwind classes for a severity badge (low/medium/high). */
export function severityColorClasses(severity: string): string {
  switch (severity?.toLowerCase()) {
    case "high":
      return "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300";
    case "medium":
      return "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300";
    default:
      return "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300";
  }
}

/** Formats an ISO date string for display, or "—" when absent/invalid. */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

/** Converts a snake_case pattern type into a human-readable title. */
export function formatPatternType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
