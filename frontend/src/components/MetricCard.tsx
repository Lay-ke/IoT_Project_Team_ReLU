import { Card } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { HealthStatus } from "@/types/conveyor";

interface MetricCardProps {
  title: string;
  value: string | number;
  unit: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "stable";
  status?: HealthStatus;
  className?: string;
}

export function MetricCard({ title, value, unit, icon: Icon, trend, status = "healthy", className }: MetricCardProps) {
  const trendColors = {
    up: "text-success",
    down: "text-destructive",
    stable: "text-muted-foreground",
  };

  const statusStyles = {
    healthy: "bg-gradient-card border-border hover:shadow-glow-cyan",
    warning: "bg-gradient-card border-warning/50 hover:shadow-glow-warning ring-1 ring-warning/20",
    critical: "bg-gradient-card border-destructive/50 hover:shadow-glow-critical ring-1 ring-destructive/20",
  };

  const iconStyles = {
    healthy: "bg-primary/20 text-primary",
    warning: "bg-warning/20 text-warning",
    critical: "bg-destructive/20 text-destructive",
  };

  return (
    <Card className={cn("p-4 transition-all duration-300", statusStyles[status], className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-muted-foreground text-sm font-medium mb-1">{title}</p>
          <div className="flex items-baseline gap-1">
            <p className="text-3xl font-bold text-foreground">{typeof value === "number" ? value.toFixed(2) : value}</p>
            <span className="text-primary text-sm font-medium">{unit}</span>
          </div>
          {trend && (
            <p className={cn("text-xs mt-1 font-medium", trendColors[trend])}>
              {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trend}
            </p>
          )}
        </div>
        <div className={cn("p-3 rounded-lg transition-colors duration-300", iconStyles[status])}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  );
}
