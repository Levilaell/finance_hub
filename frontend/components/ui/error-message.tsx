import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorMessageProps {
  title?: string;
  message: string;
  className?: string;
}

export function ErrorMessage({
  title = "Error",
  message,
  className,
}: ErrorMessageProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-destructive/50 bg-destructive/10 p-4",
        className
      )}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <AlertCircle className="h-5 w-5 text-destructive" />
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-destructive">{title}</h3>
          <div className="mt-1 text-sm text-destructive/80">{message}</div>
        </div>
      </div>
    </div>
  );
}