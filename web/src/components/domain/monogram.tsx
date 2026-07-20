import { cn } from "@/lib/utils";

/**
 * Team/entity monogram — the dataset carries no crest imagery, so identity
 * is a deliberate generated badge (FIFA code on a confederation hue), not a
 * scraped copyrighted crest.
 */

const CONFED_HUES: Record<string, string> = {
  UEFA: "bg-info-dim text-info",
  CONMEBOL: "bg-accent-dim text-accent",
  CONCACAF: "bg-signal-dim text-signal",
  CAF: "bg-critical-dim text-critical",
  AFC: "bg-[rgba(192,132,252,0.12)] text-[#c084fc]",
  OFC: "bg-[rgba(34,211,238,0.12)] text-[#22d3ee]",
};

export function Monogram({
  code,
  confederation,
  size = "md",
  className,
}: {
  code: string;
  confederation?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const hue = (confederation && CONFED_HUES[confederation]) || "bg-raised text-fg-secondary";
  return (
    <span
      aria-hidden="true"
      className={cn(
        "num inline-flex items-center justify-center rounded-full border border-edge font-semibold",
        hue,
        size === "sm" && "h-7 w-7 text-[10px]",
        size === "md" && "h-10 w-10 text-xs",
        size === "lg" && "h-14 w-14 text-sm",
        className,
      )}
    >
      {code}
    </span>
  );
}
