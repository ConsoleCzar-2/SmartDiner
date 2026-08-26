import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
    {
        variants: {
            variant: {
                default:
                    "bg-primary text-primary-foreground hover:bg-primary/85",
                outline: "border border-border bg-transparent hover:bg-muted",
                ghost: "hover:bg-muted",
                destructive:
                    "bg-destructive text-white hover:bg-destructive/85",
            },
            size: {
                default: "h-9 px-4 py-2",
                sm: "h-8 px-3 text-xs",
                lg: "h-10 px-5",
                icon: "h-9 w-9",
            },
        },
        defaultVariants: { variant: "default", size: "default" },
    },
);

export interface ButtonProps
    extends
        React.ButtonHTMLAttributes<HTMLButtonElement>,
        VariantProps<typeof buttonVariants> {}
export function Button({ className, variant, size, ...props }: ButtonProps) {
    return (
        <button
            className={cn(buttonVariants({ variant, size }), className)}
            {...props}
        />
    );
}
export { buttonVariants };
