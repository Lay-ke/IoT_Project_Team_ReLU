import { Card } from "@/components/ui/card";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceArea } from "recharts";
import { ConveyorReading, InferenceData } from "@/types/conveyor";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface TimeSeriesChartProps {
  data: ConveyorReading[];
  inferenceData?: InferenceData[];
}

const metrics = [
  { key: "Speed (rpm)", color: "hsl(var(--chart-1))", label: "Speed" },
  { key: "Load (kg)", color: "hsl(var(--chart-2))", label: "Load" },
  { key: "Temperature (℃)", color: "hsl(var(--chart-3))", label: "Temperature" },
  { key: "Vibration (m/s²)", color: "hsl(var(--chart-4))", label: "Vibration" },
  { key: "Current (A)", color: "hsl(var(--chart-5))", label: "Current" },
] as const;

export function TimeSeriesChart({ data, inferenceData = [] }: TimeSeriesChartProps) {
  const [visibleMetrics, setVisibleMetrics] = useState<Set<string>>(
    new Set(metrics.map(m => m.key))
  );
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');

  const toggleMetric = (key: string) => {
    setVisibleMetrics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  const chartData = data.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit' 
    }),
    ...metrics.reduce((acc, m) => ({
      ...acc,
      [m.label]: d[m.key]
    }), {})
  }));

  const anomalies = inferenceData
    .filter(inf => inf.content.predictions?.[0]?.predicted_class !== 'normal')
    .map(inf => new Date(inf.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }));


  return (
    <Card className="bg-gradient-card border-border p-6">
      <div className="mb-4 flex flex-wrap items-center gap-4">
        <div className="flex flex-wrap gap-2">
          {metrics.map(metric => (
            <Button
              key={metric.key}
              size="sm"
              variant={visibleMetrics.has(metric.key) ? "default" : "outline"}
              onClick={() => toggleMetric(metric.key)}
              className="text-xs"
              style={{
                backgroundColor: visibleMetrics.has(metric.key) ? metric.color : undefined,
                borderColor: metric.color,
              }}
            >
              {metric.label}
            </Button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <Button onClick={() => setChartType('line')} variant={chartType === 'line' ? 'default' : 'outline'} size="sm">Line</Button>
          <Button onClick={() => setChartType('bar')} variant={chartType === 'bar' ? 'default' : 'outline'} size="sm">Bar</Button>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        {chartType === 'line' ? (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="time" 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
              }}
              labelStyle={{ color: "hsl(var(--foreground))" }}
            />
            <Legend wrapperStyle={{ color: "hsl(var(--foreground))" }} />
            {anomalies.map((anomaly, index) => (
              <ReferenceArea
                key={index}
                x1={anomaly}
                x2={anomaly} // Since it's a single point in time, x1 and x2 are the same
                stroke="hsl(var(--destructive) / 0.5)"
                fill="hsl(var(--destructive) / 0.2)"
                ifOverflow="visible"
              />
            ))}
            {metrics.map(metric => (
              visibleMetrics.has(metric.key) && (
                <Line
                  key={metric.key}
                  type="monotone"
                  dataKey={metric.label}
                  stroke={metric.color}
                  strokeWidth={2}
                  dot={false}
                  animationDuration={300}
                />
              )
            ))}
          </LineChart>
        ) : (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="time" 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
              }}
              labelStyle={{ color: "hsl(var(--foreground))" }}
            />
            <Legend wrapperStyle={{ color: "hsl(var(--foreground))" }} />
            {anomalies.map((anomaly, index) => (
              <ReferenceArea
                key={index}
                x1={anomaly}
                x2={anomaly} // Since it's a single point in time, x1 and x2 are the same
                stroke="hsl(var(--destructive) / 0.5)"
                fill="hsl(var(--destructive) / 0.2)"
                ifOverflow="visible"
              />
            ))}
            {metrics.map(metric => (
              visibleMetrics.has(metric.key) && (
                <Bar
                  key={metric.key}
                  dataKey={metric.label}
                  fill={metric.color}
                  animationDuration={300}
                />
              )
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </Card>
  );
}
