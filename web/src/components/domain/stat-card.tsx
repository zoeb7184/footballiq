import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  tone?: "accent" | "signal" | "critical";
}) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 p-4">
        <span className="text-xs uppercase tracking-wide text-fg-muted">{label}</span>
        <span
          className={cn(
            "num text-2xl font-semibold",
            tone === "accent" && "text-accent",
            tone === "signal" && "text-signal",
            tone === "critical" && "text-critical",
          )}
        >
          {value}
        </span>
        {hint ? <span className="text-xs text-fg-muted">{hint}</span> : null}
      </CardContent>
    </Card>
  );
}
