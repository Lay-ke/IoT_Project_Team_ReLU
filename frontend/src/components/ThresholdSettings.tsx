import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Thresholds } from "@/types/conveyor";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { Settings } from "lucide-react";

interface ThresholdSettingsProps {
  thresholds: Thresholds;
  onSave: (newThresholds: Thresholds) => void;
}

const metricNames: (keyof Thresholds)[] = [
  "speed",
  "load",
  "temperature",
  "vibration",
  "current",
];

export function ThresholdSettings({
  thresholds,
  onSave,
}: ThresholdSettingsProps) {
  const [localThresholds, setLocalThresholds] = useState<Thresholds>(thresholds);
  const { toast } = useToast();

  const handleInputChange = (
    metric: keyof Thresholds,
    level: "warning" | "critical",
    value: string
  ) => {
    setLocalThresholds((prev) => ({
      ...prev,
      [metric]: {
        ...prev[metric],
        [level]: parseFloat(value) || 0,
      },
    }));
  };

  const handleSave = () => {
    onSave(localThresholds);
    toast({
      title: "Settings Saved",
      description: "Thresholds have been updated.",
    });
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Threshold Settings</SheetTitle>
          <SheetDescription>
            Adjust the warning and critical thresholds for sensor metrics.
          </SheetDescription>
        </SheetHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-3 items-center gap-4 px-1">
            <Label className="text-sm font-medium text-muted-foreground">Metric</Label>
            <Label className="text-sm font-medium text-muted-foreground">Warning</Label>
            <Label className="text-sm font-medium text-muted-foreground">Critical</Label>
          </div>
          {metricNames.map((metric) => (
            <div key={metric} className="grid grid-cols-3 items-center gap-4">
              <Label htmlFor={`${metric}-warning`} className="capitalize">
                {metric}
              </Label>
              <Input
                id={`${metric}-warning`}
                type="number"
                value={localThresholds[metric].warning}
                onChange={(e) =>
                  handleInputChange(metric, "warning", e.target.value)
                }
                className="col-span-1"
                placeholder="Warning"
              />
              <Input
                id={`${metric}-critical`}
                type="number"
                value={localThresholds[metric].critical}
                onChange={(e) =>
                  handleInputChange(metric, "critical", e.target.value)
                }
                className="col-span-1"
                placeholder="Critical"
              />
            </div>
          ))}
        </div>
        <div className="flex justify-end">
          <Button onClick={handleSave}>Save Changes</Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
