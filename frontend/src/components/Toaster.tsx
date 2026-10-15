import { useToast } from "@/hooks/useToast";
import { CheckCircle, AlertCircle, Info, X } from "lucide-react";
import clsx from "clsx";

export function Toaster() {
  const { toasts, removeToast } = useToast();

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => {
        const Icon = icons[toast.type];
        return (
          <div
            key={toast.id}
            className={clsx(
              "pointer-events-auto flex items-start gap-3 w-80 px-4 py-3 rounded-lg border shadow-lg animate-slideIn",
              toast.type === "success" && "border-green-500/50 bg-green-500/10 text-green-300",
              toast.type === "error" && "border-red-500/50 bg-red-500/10 text-red-300",
              toast.type === "info" && "border-blue-500/50 bg-blue-500/10 text-blue-300"
            )}
            role="alert"
          >
            <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <p className="flex-1 text-sm">{toast.message}</p>
            <button
              onClick={() => removeToast(toast.id)}
              className="flex-shrink-0 p-1 hover:bg-white/10 rounded transition-colors"
              aria-label="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}