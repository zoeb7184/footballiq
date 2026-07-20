import { cn } from "@/lib/utils";

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-edge bg-raised px-3 text-sm text-fg " +
          "placeholder:text-fg-muted focus-visible:border-accent focus-visible:outline-none",
        className,
      )}
      {...props}
    />
  );
}
