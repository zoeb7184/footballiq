"use client";

import { useRouter } from "next/navigation";
import { LogOut, Menu, Search } from "lucide-react";
import { useHealth } from "@/lib/api/queries";
import { useUiStore } from "@/lib/store";
import { cn } from "@/lib/utils";

function LiveDot() {
  const health = useHealth();
  const up = health.data?.data.status === "alive";
  const label = health.isPending ? "checking API" : up ? "API live" : "API waking / snapshot mode";
  return (
    <span className="flex items-center gap-1.5 text-[11px] text-fg-muted" title={label}>
      <span
        aria-hidden="true"
        className={cn(
          "h-2 w-2 rounded-full",
          health.isPending ? "bg-fg-muted" : up ? "bg-accent" : "bg-signal",
        )}
      />
      <span className="hidden sm:inline">{label}</span>
    </span>
  );
}

export function Topbar() {
  const { setSidebarOpen, setPaletteOpen } = useUiStore();
  const router = useRouter();

  async function signOut() {
    await fetch("/api/session", { method: "DELETE" });
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-edge bg-base/80 px-4 backdrop-blur">
      <button
        aria-label="Open navigation"
        className="rounded-md p-2 text-fg-secondary hover:bg-raised lg:hidden"
        onClick={() => setSidebarOpen(true)}
      >
        <Menu className="h-5 w-5" aria-hidden="true" />
      </button>
      <button
        onClick={() => setPaletteOpen(true)}
        className="flex h-9 flex-1 max-w-md items-center gap-2 rounded-md border border-edge bg-raised px-3 text-sm text-fg-muted transition-colors hover:border-edge-strong"
      >
        <Search className="h-4 w-4" aria-hidden="true" />
        <span className="flex-1 text-left">Search teams, players…</span>
        <kbd className="num hidden rounded border border-edge bg-surface px-1.5 py-0.5 text-[10px] sm:inline">
          ⌘K
        </kbd>
      </button>
      <div className="ml-auto flex items-center gap-3">
        <LiveDot />
        <button
          onClick={signOut}
          className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-fg-secondary hover:bg-raised hover:text-fg"
        >
          <LogOut className="h-3.5 w-3.5" aria-hidden="true" /> Exit demo
        </button>
      </div>
    </header>
  );
}
