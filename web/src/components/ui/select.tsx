"use client";

import { cn } from "@/lib/utils";

/** Native select, token-styled: reliable, accessible, zero-JS overhead. */
export function Select({
  className,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-10 rounded-md border border-edge bg-raised px-3 pr-8 text-sm text-fg " +
          "focus-visible:border-accent focus-visible:outline-none cursor-pointer",
        className,
      )}
      {...props}
    />
  );
}
