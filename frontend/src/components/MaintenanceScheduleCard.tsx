import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { MaintenanceContent } from "@/types/conveyor";
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  Clock,
  DollarSign,
  HardHat,
  Info,
} from "lucide-react";
import { useEffect, useState } from "react";

interface MaintenanceScheduleCardProps {
  schedule: MaintenanceContent;
}

const severityConfig = {
  critical: { label: "Critical", color: "destructive", icon: AlertOctagon },
  monitor: { label: "Monitor", color: "warning", icon: AlertTriangle },
  warning: { label: "Warning", color: "warning", icon: AlertTriangle },
  low: { label: "Normal", color: "success", icon: CheckCircle },
  default: { label: "Unknown", color: "secondary", icon: Info },
};

const Countdown = ({ to }: { to: string }) => {
  const [remaining, setRemaining] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      const timeLeft = new Date(to).getTime() - Date.now();
      if (timeLeft <= 0) {
        setRemaining("Overdue");
        clearInterval(interval);
        return;
      }
      const hours = Math.floor(timeLeft / (1000 * 60 * 60));
      const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
      setRemaining(`${hours}h ${minutes}m`);
    }, 1000);

    return () => clearInterval(interval);
  }, [to]);

  return <span className="font-mono text-xs">⏳ {remaining}</span>;
};

export const MaintenanceScheduleCard = ({
  schedule,
}: MaintenanceScheduleCardProps) => {
  const {
    machine_id,
    schedule_id,
    fault_details,
    scheduling_info,
    cost_benefit_analysis,
  } = schedule;
  const { severity, priority, confidence_score, fault_type } = fault_details;
  const { action_required_by, estimated_duration_hours } = scheduling_info;

  const status =
    severityConfig[severity as keyof typeof severityConfig] ||
    severityConfig.default;

  return (
    <AccordionItem
      value={schedule_id}
      className="border-border bg-gradient-card rounded-lg border shadow-sm overflow-hidden !text-white"
    >
      <AccordionTrigger className="p-4 hover:no-underline">
        <div className="w-full flex flex-col gap-2 justify-start items-start">
          <div className="flex items-center gap-4">
            <HardHat className={cn("h-6 w-6", `text-${status.color}`)} />
            <div>
              <p className="font-bold text-base text-left">
                {machine_id} - <span className="capitalize">{fault_type}</span>
              </p>
              <p className="text-xs text-muted-foreground text-left">
                Due: {new Date(action_required_by).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Badge
              variant={
                status.color === "destructive"
                  ? "destructive"
                  : status.color === "warning"
                    ? "secondary"
                    : "default"
              }
              className="capitalize w-24 justify-center"
            >
              <status.icon className="h-3 w-3 mr-1" />
              {severity}
            </Badge>
            <Countdown to={action_required_by} />
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="p-0 border-t border-border">
        <div className="p-4 grid grid-cols-1 md:grid-cols-[2fr_3fr] gap-4 bg-secondary/20">
          {/* Left Column */}
          <div className="space-y-4">
            <Card className="bg-background/50">
              <CardHeader className="p-3 pb-0">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  Fault Details
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3">
                <p className="text-lg font-bold capitalize text-primary">
                  {fault_type}
                </p>
                <p className="text-xs text-muted-foreground">Confidence</p>
                <div className="flex items-center gap-2">
                  <Progress value={confidence_score * 100} className="h-2" />
                  <span className="font-mono text-xs">
                    {(confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-background/50">
              <CardHeader className="p-3 pb-0">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Scheduling
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted-foreground">Est. Duration</span>
                  <span className="font-semibold">
                    {estimated_duration_hours} hours
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted-foreground">Priority</span>
                  <span className="font-semibold capitalize">{priority}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column */}
          <Card className="bg-background/50">
            <CardHeader className="p-3 pb-0">
              <CardTitle className="text-sm flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Financial Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <Table>
                <TableHeader>
                  <TableRow className="text-xs">
                    <TableHead>Option</TableHead>
                    <TableHead className="text-right">Direct Cost</TableHead>
                    <TableHead className="text-right">Downtime Cost</TableHead>
                    <TableHead className="text-right">Total Cost</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="text-xs">
                  <TableRow
                    className={
                      cost_benefit_analysis?.recommended_action === "repair"
                        ? "bg-primary/10"
                        : ""
                    }
                  >
                    <TableCell className="font-medium">Repair</TableCell>
                    <TableCell className="text-right font-mono">
                      $
                      {cost_benefit_analysis?.repair_option.direct_cost_usd?.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      $
                      {cost_benefit_analysis?.repair_option.downtime_cost_usd?.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-bold font-mono">
                      $
                      {cost_benefit_analysis?.repair_option.total_cost_usd?.toLocaleString()}
                    </TableCell>
                  </TableRow>
                  <TableRow
                    className={
                      cost_benefit_analysis?.recommended_action === "replace"
                        ? "bg-primary/10"
                        : ""
                    }
                  >
                    <TableCell className="font-medium">Replace</TableCell>
                    <TableCell className="text-right font-mono">
                      $
                      {cost_benefit_analysis?.replacement_option.direct_cost_usd?.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      $
                      {cost_benefit_analysis?.replacement_option.downtime_cost_usd?.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-bold font-mono">
                      $
                      {cost_benefit_analysis?.replacement_option.total_cost_usd?.toLocaleString()}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
              <Alert className="mt-2 border-primary/50 bg-primary/10 text-primary-foreground">
                <AlertTitle className="text-xs font-bold text-white">
                  💡 Recommended: {cost_benefit_analysis?.recommended_action}
                </AlertTitle>
                <AlertDescription className="text-xs text-white">
                  {cost_benefit_analysis?.recommendation_reason}
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
        <CardFooter className="p-2 bg-background/20 border-t flex justify-between items-center">
          <p className="text-xs text-muted-foreground font-mono">
            {schedule_id}
          </p>
        </CardFooter>
      </AccordionContent>
    </AccordionItem>
  );
};
