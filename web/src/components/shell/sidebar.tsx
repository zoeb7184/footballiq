"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/lib/store";
import { BRAND_ICON, NAV_GROUPS } from "./nav";

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary" className="flex flex-1 flex-col gap-5 overflow-y-auto p-4">
      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-widest text-fg-muted">
            {group.label}
          </p>
          <ul className="flex flex-col gap-0.5">
            {group.items.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={onNavigate}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                      active
                        ? "bg-accent-dim font-medium text-accent"
                        : "text-fg-secondary hover:bg-raised hover:text-fg",
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useUiStore();
  const Brand = BRAND_ICON;

  const brand = (
    <Link href="/" className="flex items-center gap-2 px-4 py-4">
      <Brand className="h-6 w-6 text-accent" aria-hidden="true" />
      <span className="font-display text-base font-bold tracking-tight">
        Football<span className="text-accent">IQ</span>
      </span>
    </Link>
  );

  return (
    <>
      {/* Desktop */}
      <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col border-r border-edge bg-surface lg:flex">
        {brand}
        <NavLinks />
        <p className="border-t border-edge p-4 text-[11px] leading-relaxed text-fg-muted">
          Demo environment · real API, real model outputs
        </p>
      </aside>

      {/* Mobile drawer */}
      {sidebarOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <button
            aria-label="Close navigation"
            className="absolute inset-0 bg-black/60"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 flex-col border-r border-edge bg-surface">
            <div className="flex items-center justify-between pr-2">
              {brand}
              <button
                aria-label="Close navigation"
                className="rounded-md p-2 text-fg-secondary hover:bg-raised"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <NavLinks onNavigate={() => setSidebarOpen(false)} />
          </aside>
        </div>
      ) : null}
    </>
  );
}
