import { Badge } from "@/components/ui/badge";
import { riskColorClasses } from "@/lib/utils-display";
import { ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";

/** Badge showing a risk level (low/medium/high) with a matching icon and color. */
export function RiskBadge({ level }: { level: string }) {
  const Icon =
    level?.toLowerCase() === "high"
      ? ShieldAlert
      : level?.toLowerCase() === "medium"
      ? ShieldQuestion
      : ShieldCheck;

  return (
    <Badge
      variant="outline"
      className={`gap-1.5 font-medium border ${riskColorClasses(level)}`}
    >
      <Icon className="size-3.5" />
      {level ? level.charAt(0).toUpperCase() + level.slice(1) : "Unknown"} Risk
    </Badge>
  );
}
