import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});
const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  title: {
    default: "FootballIQ — AI you can audit",
    template: "%s · FootballIQ",
  },
  description:
    "Decision-intelligence platform demonstrated on the FIFA World Cup 2026: " +
    "explainable ML valuations, SHAP you can verify in the browser, a grounded " +
    "AI analyst, graph analytics, and seeded Monte Carlo simulation.",
  openGraph: {
    title: "FootballIQ — AI you can audit",
    description:
      "Every prediction explains itself. Every analyst answer cites its SQL.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} h-full`}
    >
      <body className="flex min-h-full flex-col bg-base text-fg">
        {children}
      </body>
    </html>
  );
}
