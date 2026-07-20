"use client";

import { AlertTriangle, Database, RefreshCw, SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";

export function ErrorState({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const problem = error instanceof ApiError ? error.problem : null;
  const sleeping = error instanceof ApiError && error.status === 503;
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-lg border border-edge bg-surface p-10 text-center"
    >
      <AlertTriangle className="h-8 w-8 text-signal" aria-hidden="true" />
      <p className="font-display font-semibold">
        {sleeping ? "The live backend is waking up" : (problem?.title ?? "Something went wrong")}
      </p>
      <p className="max-w-md text-sm text-fg-secondary">
        {sleeping
          ? "This demo runs on a free-tier API that sleeps when idle. It usually wakes within a minute — retry shortly."
          : (problem?.detail ?? "The request failed. The API may be unreachable.")}
      </p>
      {onRetry ? (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Retry
        </Button>
      ) : null}
    </div>
  );
}

export function EmptyState({
  title,
  hint,
  icon = "search",
}: {
  title: string;
  hint?: string;
  icon?: "search" | "data";
}) {
  const Icon = icon === "data" ? Database : SearchX;
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-edge bg-surface p-10 text-center">
      <Icon className="h-8 w-8 text-fg-muted" aria-hidden="true" />
      <p className="font-display font-semibold">{title}</p>
      {hint ? <p className="max-w-md text-sm text-fg-secondary">{hint}</p> : null}
    </div>
  );
}
