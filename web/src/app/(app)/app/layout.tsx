import type { Metadata } from "next";
import { CommandPalette } from "@/components/shell/command-palette";
import { Providers } from "@/components/shell/providers";
import { Sidebar } from "@/components/shell/sidebar";
import { Topbar } from "@/components/shell/topbar";

export const metadata: Metadata = {
  robots: { index: false }, // the app is a demo, not content
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <Providers>
      <div className="flex min-h-dvh">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main className="mx-auto w-full max-w-7xl flex-1 p-4 pb-16 sm:p-6">
            {children}
          </main>
        </div>
      </div>
      <CommandPalette />
    </Providers>
  );
}
