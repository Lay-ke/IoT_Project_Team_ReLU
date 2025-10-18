import { HealthStatus } from "@/types/conveyor";
import { Activity, AlertTriangle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: HealthStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = {
    healthy: {
      label: "Healthy",
      icon: Activity,
      bgClass: "bg-success/20 border-success",
      textClass: "text-success-foreground",
      iconClass: "text-success",
      glowClass: "shadow-glow-success",
    },
    warning: {
      label: "At Risk",
      icon: AlertTriangle,
      bgClass: "bg-warning/20 border-warning",
      textClass: "text-warning-foreground",
      iconClass: "text-warning",
      glowClass: "shadow-glow-warning",
    },
    critical: {
      label: "Critical",
      icon: XCircle,
      bgClass: "bg-destructive/20 border-destructive",
      textClass: "text-destructive-foreground",
      iconClass: "text-destructive",
      glowClass: "shadow-glow-critical",
    },
  };

  const { label, icon: Icon, bgClass, textClass, iconClass, glowClass } = config[status];

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all duration-300",
        bgClass,
        glowClass,
        status !== "healthy" && "animate-pulse-glow",
        className
      )}
    >
      <Icon className={cn("h-5 w-5", iconClass)} />
      <span className={cn("font-semibold text-lg", textClass)}>{label}</span>
    </div>
  );
}
