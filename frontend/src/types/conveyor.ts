export type HealthStatus = "healthy" | "warning" | "critical";

export interface ConveyorReading {
  timestamp: string;
  "Speed (rpm)": number;
  "Load (kg)": number;
  "Temperature (℃)": number;
  "Vibration (m/s²)": number;
  "Current (A)": number;
}

export interface MaintenanceSchedule {
  id: string;
  task: string;
  dueDate: string;
  status: "pending" | "in-progress" | "completed";
}

export interface InferenceData {
  id: string;
  timestamp: string;
  content: {
    predictions: {
      predicted_class: string;
      confidence: number;
    }[];
  };
}

export type InferenceRecordList = InferenceData[];

export type Thresholds = {
  speed: { warning: number; critical: number };
  load: { warning: number; critical: number };
  temperature: { warning: number; critical: number };
  vibration: { warning: number; critical: number };
  current: { warning: number; critical: number };
};