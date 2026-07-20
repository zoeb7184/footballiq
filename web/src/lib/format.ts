/** Formatting helpers — every number in the UI goes through here. */

const eur = new Intl.NumberFormat("en", {
  style: "currency",
  currency: "EUR",
  notation: "compact",
  maximumFractionDigits: 1,
});

const eurFull = new Intl.NumberFormat("en", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

const num = new Intl.NumberFormat("en");

export function fmtEur(value: number): string {
  return eur.format(value);
}

export function fmtEurFull(value: number): string {
  return eurFull.format(value);
}

export function fmtNum(value: number): string {
  return num.format(value);
}

export function fmtPct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function fmtSigned(value: number, fmt: (v: number) => string): string {
  return `${value >= 0 ? "+" : ""}${fmt(value)}`;
}

export function fmtDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en", { day: "numeric", month: "short", year: "numeric" });
}

export function ageFrom(dobIso: string): number | null {
  const dob = new Date(dobIso);
  if (Number.isNaN(dob.getTime())) return null;
  return Math.floor((Date.now() - dob.getTime()) / (365.25 * 24 * 3600 * 1000));
}
