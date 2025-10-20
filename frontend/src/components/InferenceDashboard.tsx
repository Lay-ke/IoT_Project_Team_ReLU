import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { HealthStatus, InferenceRecord } from "@/types/conveyor";
import {
  AlertOctagon,
  AlertTriangle,
  BarChart2,
  CheckCircle,
  Settings,
} from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const getStatus = (
  predicted_class: string,
  confidence: number
): {
  status: HealthStatus;
  color: string;
  icon: React.ElementType;
} => {
  if (predicted_class !== "normal") {
    if (confidence > 0.7) {
      return { status: "critical", color: "destructive", icon: AlertOctagon };
    }
    if (confidence > 0.4) {
      return { status: "warning", color: "warning", icon: AlertTriangle };
    }
  }
  return { status: "healthy", color: "success", icon: CheckCircle };
};

export const InferenceDashboard = ({
  inference,
}: {
  inference: InferenceRecord;
}) => {
  if (
    !inference.content.predictions ||
    inference.content.predictions.length === 0
  ) {
    return (
      <Card className="bg-gradient-card border-border text-foreground shadow-lg font-sans">
        <CardHeader>
          <CardTitle>ML Inference Analysis</CardTitle>
          <CardDescription>No prediction data available.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const { key, content } = inference;
  const prediction = content.predictions[0];
  const { predicted_class, confidence, top_k, timestamp } = prediction;

  const machineId = key.split("/")[1];
  const formattedTimestamp = new Date(timestamp).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  });
  const statusInfo = getStatus(predicted_class, confidence);

  const probabilityData = Object.entries(top_k)
    .map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      probability: value * 100,
    }))
    .sort((a, b) => b.probability - a.probability);

  const getInterpretationText = () => {
    switch (statusInfo.status) {
      case "critical":
        return `Detected a potential ${predicted_class} fault with high confidence (${(
          confidence * 100
        ).toFixed(2)}%). This requires immediate attention.`;
      case "warning":
        return `Detected a potential ${predicted_class} fault with moderate confidence (${(
          confidence * 100
        ).toFixed(2)}%). Recommend monitoring.`;
      default:
        return `System is operating under normal conditions.`;
    }
  };

  const getEngineeringGuidanceText = () => {
    switch (statusInfo.status) {
      case "critical":
        return `There is a high likelihood (${(confidence * 100).toFixed(
          2
        )}%) of a ${predicted_class} fault. This requires immediate inspection to prevent system failure.`;
      case "warning":
        return `A potential ${predicted_class} fault has been detected with moderate confidence (${(
          confidence * 100
        ).toFixed(2)}%). Continued monitoring is recommended.`;
      default:
        return "The system is operating normally. No immediate action is required. Continuous monitoring is always recommended.";
    }
  };

  return (
    <Card className="bg-gradient-card border-border text-foreground shadow-lg font-sans">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-lg font-bold tracking-tight flex items-center gap-2">
            <Settings className="h-5 w-5" />
            ML Inference Analysis
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            {machineId} &bull; {formattedTimestamp}
          </CardDescription>
        </div>
        <Badge
          variant={
            statusInfo.color === "destructive"
              ? "destructive"
              : statusInfo.color === "warning"
              ? "secondary"
              : "default"
          }
          className={cn(
            statusInfo.color === "destructive" &&
              "bg-destructive/80 border-destructive text-destructive-foreground",
            statusInfo.color === "warning" &&
              "bg-warning/80 border-warning text-warning-foreground",
            statusInfo.color === "success" &&
              "bg-success/80 border-success text-success-foreground"
          )}
        >
          <statusInfo.icon className="h-4 w-4 mr-1" />
          {statusInfo.status.charAt(0).toUpperCase() +
            statusInfo.status.slice(1)}
        </Badge>
      </CardHeader>

      <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6">
        <div className="md:col-span-1 space-y-6">
          <Card className="bg-secondary/30 border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Fault Prediction</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold capitalize text-primary">
                {predicted_class}
              </p>
              <p className="text-sm text-muted-foreground">Confidence Level</p>
              <div className="flex items-center gap-2 mt-2">
                <Progress
                  value={confidence * 100}
                  className={cn(
                    "h-3",
                    statusInfo.color === "destructive" &&
                      "[&>div]:bg-destructive",
                    statusInfo.color === "warning" && "[&>div]:bg-warning",
                    statusInfo.color === "success" && "[&>div]:bg-success"
                  )}
                />
                <span className="font-mono text-sm font-semibold">
                  {(confidence * 100).toFixed(2)}%
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                {getInterpretationText()}
              </p>
            </CardContent>
          </Card>

          <Alert
            variant={
              statusInfo.color === "destructive" ? "destructive" : "default"
            }
            className={cn(
              "border-2",
              statusInfo.color === "destructive" &&
                "border-destructive/50 bg-destructive/10",
              statusInfo.color === "warning" &&
                "border-warning/50 bg-warning/10",
              statusInfo.color === "success" &&
                "border-success/50 bg-success/10"
            )}
          >
            <statusInfo.icon
              className={cn(
                "h-5 w-5",
                `text-[hsl(var(--${statusInfo.color}))]`
              )}
            />
            <AlertTitle
              className={cn(
                "font-bold",
                `text-[hsl(var(--${statusInfo.color}))]`
              )}
            >
              Engineering Guidance
            </AlertTitle>
            <AlertDescription className="text-xs">
              {getEngineeringGuidanceText()}
            </AlertDescription>
          </Alert>
        </div>

        <div className="md:col-span-2">
          <Card className="bg-secondary/30 border-border h-full">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart2 className="h-5 w-5" />
                Probability Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={probabilityData}
                  layout="vertical"
                  margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
                >
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    unit="%s"
                    tick={{
                      fill: "hsl(var(--muted-foreground))",
                      fontSize: 12,
                    }}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={110}
                    tick={{
                      fill: "hsl(var(--muted-foreground))",
                      fontSize: 12,
                    }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    cursor={{ fill: "hsl(var(--accent))" }}
                    contentStyle={{
                      backgroundColor: "hsl(var(--background))",
                      border: "1px solid hsl(var(--border))",
                    }}
                    formatter={(value: number) => [
                      `${value.toFixed(2)}%`,
                      "Probability",
                    ]}
                  />
                  <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                    {probabilityData.map((entry, index) => {
                      const isPredicted =
                        entry.name.toLowerCase() === predicted_class;
                      let color = "hsl(var(--primary))";
                      if (isPredicted) {
                        if (statusInfo.status === "critical")
                          color = "hsl(var(--destructive))";
                        else if (statusInfo.status === "warning")
                          color = "hsl(var(--warning))";
                        else color = "hsl(var(--success))";
                      } else if (entry.name.toLowerCase() === "normal") {
                        color = "hsl(var(--success))";
                      }
                      return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
};