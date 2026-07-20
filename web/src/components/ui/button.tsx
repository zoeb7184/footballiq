import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium " +
    "transition-colors disabled:pointer-events-none disabled:opacity-50 " +
    "focus-visible:outline-2 focus-visible:outline-accent cursor-pointer",
  {
    variants: {
      variant: {
        primary: "bg-accent text-black hover:opacity-90",
        secondary: "bg-raised text-fg border border-edge hover:border-edge-strong",
        ghost: "text-fg-secondary hover:bg-raised hover:text-fg",
        danger: "bg-critical-dim text-critical border border-critical/30 hover:bg-critical/20",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4",
        lg: "h-12 px-6 text-base",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}

export { buttonVariants };
