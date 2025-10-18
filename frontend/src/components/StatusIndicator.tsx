import { AlertCircle, AlertTriangle, CheckCircle } from "lucide-react";

interface StatusIndicatorProps {
  status: "normal" | "warning" | "fault";
  deviceId: string;
}

export function StatusIndicator({ status, deviceId }: StatusIndicatorProps) {
  const statusConfig = {
    normal: {
      icon: CheckCircle,
      label: "Healthy",
      color: "text-green-400",
      bgColor: "bg-green-500/10",
      borderColor: "border-green-500/30",
    },
    warning: {
      icon: AlertTriangle,
      label: "At Risk",
      color: "text-yellow-400",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/30",
    },
    fault: {
      icon: AlertCircle,
      label: "Critical",
      color: "text-red-400",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/30",
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
            className={`h-8 w-8 ${config.color} ${status === "fault" ? "status-pulse" : ""}`}
          />
        </div>
        <div>
          <div className={`text-2xl font-bold ${config.color}`}>
            {config.label}
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {status === "normal" && "All parameters within normal range"}
            {status === "warning" &&
              "Parameters approaching critical thresholds"}
            {status === "fault" && "Immediate maintenance required"}
          </p>
        </div>
      </div>
    </div>
  );
}
