import { forwardRef } from "react";
import clsx from "clsx";

export const Card = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={clsx("card", className)} {...props}>
      {children}
    </div>
  )
);
Card.displayName = "Card";

export const Badge = forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement> & { variant?: string }>(
  ({ className, variant = "pending", children, ...props }, ref) => (
    <span ref={ref} className={clsx("badge", `badge-${variant}`, className)} {...props}>
      {children}
    </span>
  )
);
Badge.displayName = "Badge";

export const ProgressBar = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { value: number }>(
  ({ className, value, ...props }, ref) => (
    <div ref={ref} className={clsx("progress-bar", className)} {...props}>
      <div className="progress-bar-fill" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  )
);
ProgressBar.displayName = "ProgressBar";

export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={clsx("input", className)} {...props} />
  )
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea ref={ref} className={clsx("input", className)} {...props} />
  )
);
Textarea.displayName = "Textarea";

export const Label = forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label ref={ref} className={clsx("label", className)} {...props} />
  )
);
Label.displayName = "Label";

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "danger" | "ghost";
    size?: "sm" | "md" | "lg";
  }
>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => (
    <button
      ref={ref}
      className={clsx("btn", `btn-${variant}`, `btn-${size}`, className)}
      {...props}
    >
      {children}
    </button>
  )
);
Button.displayName = "Button";