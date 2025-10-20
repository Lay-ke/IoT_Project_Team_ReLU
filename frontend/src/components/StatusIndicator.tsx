import { HealthStatus } from "@/types/conveyor";
import { AlertCircle, AlertTriangle, CheckCircle } from "lucide-react";

interface StatusIndicatorProps {
  status: HealthStatus;
  deviceId: string;
}

export function StatusIndicator({ status, deviceId }: StatusIndicatorProps) {
  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      label: "Healthy",
      color: "text-success",
      bgColor: "bg-success/10",
      borderColor: "border-success/30",
    },
    warning: {
      icon: AlertTriangle,
      label: "At Risk",
      color: "text-warning",
      bgColor: "bg-warning/10",
      borderColor: "border-warning/30",
    },
    critical: {
      icon: AlertCircle,
      label: "Critical",
      color: "text-destructive",
      bgColor: "bg-destructive/10",
      borderColor: "border-destructive/30",
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div
      className={`rounded-lg border ${config.borderColor} ${config.bgColor} p-6`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-muted-foreground">
          System Status
        </h3>
        <span className="text-xs font-mono text-muted-foreground">
          {deviceId}
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className={`rounded-full p-3 ${config.bgColor}`}>
          <Icon
            className={`h-8 w-8 ${config.color} ${
              status === "critical" ? "status-pulse" : ""
            }`}
          />
        </div>
        <div>
          <div className={`text-2xl font-bold ${config.color}`}>
            {config.label}
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {status === "healthy" && "All parameters within normal range"}
            {status === "warning" &&
              "Parameters approaching critical thresholds"}
            {status === "critical" && "Immediate maintenance required"}
          </p>
        </div>
      </div>
    </div>
  );
}