import {
  Activity,
  BarChart3,
  Bot,
  CalendarDays,
  GitCompareArrows,
  LayoutDashboard,
  Network,
  ShieldCheck,
  Sparkles,
  Users,
  UserSearch,
  Wallet,
} from "lucide-react";

export const NAV_GROUPS = [
  {
    label: "Overview",
    items: [{ href: "/app/overview", label: "Command center", icon: LayoutDashboard }],
  },
  {
    label: "Tournament",
    items: [
      { href: "/app/matches", label: "Matches", icon: CalendarDays },
      { href: "/app/simulator", label: "Simulator", icon: Sparkles },
    ],
  },
  {
    label: "Scouting",
    items: [
      { href: "/app/players", label: "Players", icon: UserSearch },
      { href: "/app/valuations", label: "Valuations", icon: Wallet },
      { href: "/app/teams", label: "Teams", icon: Users },
      { href: "/app/compare", label: "Compare", icon: GitCompareArrows },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { href: "/app/analyst", label: "AI Analyst", icon: Bot },
      { href: "/app/network", label: "Talent network", icon: Network },
    ],
  },
  {
    label: "Governance",
    items: [
      { href: "/app/models", label: "Model performance", icon: BarChart3 },
      { href: "/app/status", label: "System status", icon: Activity },
    ],
  },
] as const;

export const BRAND_ICON = ShieldCheck;
