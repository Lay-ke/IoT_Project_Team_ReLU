import { Chatbot } from "@/components/Chatbot";
import { InferenceDashboard } from "@/components/InferenceDashboard";
import { Logo } from "@/components/Logo";
import { MaintenanceScheduleList } from "@/components/MaintenanceScheduleList";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { StatusIndicator } from "@/components/StatusIndicator";
import { TimeSeriesChart } from "@/components/TimeSeriesChart";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { useInferenceData } from "@/hooks/useInferenceData";
import { DataService } from "@/services/mockDataService";
import { ConveyorReading, HealthStatus } from "@/types/conveyor";
import {
  Activity,
  Gauge,
  MessageCircle,
  Thermometer,
  Waves,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

const DEVICE_ID = "conveyor-A001";
const REFRESH_INTERVAL = 60000; // 60 seconds

// Thresholds for metric status
const THRESHOLDS = {
  speed: { warning: 130, critical: 140 },
  load: { warning: 550, critical: 600 },
  temperature: { warning: 45, critical: 50 },
  vibration: { warning: 0.7, critical: 0.85 },
  current: { warning: 4.0, critical: 4.5 },
};

const getMetricStatus = (
  value: number,
  metric: keyof typeof THRESHOLDS
): HealthStatus => {
  const threshold = THRESHOLDS[metric];
  if (value >= threshold.critical) return "critical";
  if (value >= threshold.warning) return "warning";
  return "healthy";
};

const Index = () => {
  const { data: inferenceData } = useInferenceData();

  const [currentData, setCurrentData] = useState<ConveyorReading | null>(null);
  const [historicalData, setHistoricalData] = useState<ConveyorReading[]>([]);
  const [healthStatus, setHealthStatus] = useState<HealthStatus>("healthy");
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const { toast } = useToast();

  useEffect(() => {
    if (inferenceData && inferenceData.length > 0) {
      const latestInference = inferenceData[0].content;
      const { predicted_class, confidence } = latestInference;

      let newStatus: HealthStatus = "healthy";
      if (predicted_class !== "normal") {
        if (confidence > 0.7) {
          newStatus = "critical";
        } else if (confidence > 0.4) {
          newStatus = "warning";
        }
      }
      setHealthStatus(newStatus);
    }
  }, [inferenceData]);

  const fetchData = useCallback(async () => {
    try {
      const [raw, history] = await Promise.all([
        DataService.fetchLatestRawData(),
        DataService.fetchHistoricalData(),
      ]);

      if (raw) {
        setCurrentData(raw);
      }
      setHistoricalData(history);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast({
        title: "Data Fetch Error",
        description:
          "Failed to retrieve conveyor data. Retrying in 15 seconds...",
        variant: "destructive",
      });

      // Retry after 15 seconds
      setTimeout(fetchData, 15000);
    }
  }, [toast]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (!currentData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading conveyor data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Logo />
              <div>
                <h1 className="text-2xl font-bold text-foreground">
                  Conveyor Belt Monitoring
                </h1>
                <p className="text-sm text-muted-foreground">
                  Device: {DEVICE_ID}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-muted-foreground">Last Updated</p>
                <p className="text-sm font-medium text-foreground">
                  {lastUpdated.toLocaleTimeString()}
                </p>
              </div>
              <StatusBadge status={healthStatus} />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-3 py-6 grid lg:grid-cols-[500px_2fr] gap-4">
        {/* Current Metrics Grid */}
        <div className="space-y-6">
          <StatusIndicator
            status={
              healthStatus === "healthy"
                ? "normal"
                : healthStatus === "warning"
                  ? "warning"
                  : "fault"
            }
            deviceId={DEVICE_ID}
          />
          <div className="grid grid-cols-1 md:grid-cols-2  gap-4 animate-fade-in h-max">
            <MetricCard
              title="Speed"
              value={currentData["Speed (rpm)"]}
              unit="rpm"
              icon={Gauge}
              status={getMetricStatus(currentData["Speed (rpm)"], "speed")}
            />
            <MetricCard
              title="Load"
              value={currentData["Load (kg)"]}
              unit="kg"
              icon={Activity}
              status={getMetricStatus(currentData["Load (kg)"], "load")}
            />
            <MetricCard
              title="Temperature"
              value={currentData["Temperature (℃)"]}
              unit="°C"
              icon={Thermometer}
              status={getMetricStatus(
                currentData["Temperature (℃)"],
                "temperature"
              )}
            />
            <MetricCard
              title="Vibration"
              value={currentData["Vibration (m/s²)"]}
              unit="m/s²"
              icon={Waves}
              status={getMetricStatus(
                currentData["Vibration (m/s²)"],
                "vibration"
              )}
            />
            <MetricCard
              title="Current"
              value={currentData["Current (A)"]}
              unit="A"
              icon={Zap}
              status={getMetricStatus(currentData["Current (A)"], "current")}
            />
          </div>
          <Separator />
          <div className="mt-3">
            <MaintenanceScheduleList />
          </div>
        </div>

        {/* Charts Section */}
        <div className="space-y-6">
          {inferenceData && inferenceData.length > 0 && (
            <InferenceDashboard inference={inferenceData[0]} />
          )}
          <TimeSeriesChart data={historicalData} />
        </div>

        {/* Floating Action Button with Chatbot Popover */}
        <Popover>
          <PopoverTrigger asChild>
            <Button
              size="icon"
              className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg hover:scale-110 transition-transform z-50"
            >
              <MessageCircle className="h-6 w-6" />
            </Button>
          </PopoverTrigger>
          <PopoverContent
            align="end"
            side="top"
            sideOffset={16}
            className="w-[400px] h-[600px] p-0"
          >
            <Chatbot />
          </PopoverContent>
        </Popover>
      </main>
    </div>
  );
};

export default Index;
