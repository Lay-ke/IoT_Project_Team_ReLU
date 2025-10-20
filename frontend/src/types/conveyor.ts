export interface ConveyorReading {
  timestamp: string; // ISO 8601 timestamp
  device_id: string;
  "Speed (rpm)": number;
  "Load (kg)": number;
  "Temperature (℃)": number;
  "Vibration (m/s²)": number;
  "Current (A)": number;
  Fault: "normal" | "pulley" | "ball bearing" | "gear" | string; // Expandable for other fault types
}

export interface ConveyorBatch {
  key: string;
  last_modified: string; // ISO 8601 timestamp
  content: ConveyorReading[];
}

export type ConveyorBatchList = ConveyorBatch[];

export type HealthStatus = "healthy" | "warning" | "critical";

// ---- New Maintenance Schedule Types ----

export interface FaultDetails {
  fault_type: string;
  severity: "critical" | "monitor" | "warning" | "low" | string;
  priority: "immediate" | "scheduled" | "deferred" | string;
  confidence_score: number; // 0–1 range
}

export interface SchedulingInfo {
  urgency_hours: number; // how soon it must be addressed
  action_required_by: string; // ISO timestamp
  estimated_duration_hours: number;
}

export interface FinancialImpact {
  downtime_cost_per_hour_usd: number;
  estimated_downtime_cost_usd: number;
  repair_cost_usd: number;
  replacement_cost_usd: number;
  total_repair_cost_usd: number;
  total_replacement_cost_usd: number;
  recommended_action: "repair" | "replace" | string;
  estimated_direct_cost_usd: number;
  estimated_total_cost_usd: number;
}

export interface CostBenefitOption {
  direct_cost_usd: number;
  downtime_hours: number;
  downtime_cost_usd: number;
  total_cost_usd: number;
}

export interface CostBenefitAnalysis {
  repair_option: CostBenefitOption;
  replacement_option: CostBenefitOption;
  cost_savings_usd: number;
  recommended_action: "repair" | "replace" | string;
  recommendation_reason: string;
}

export interface MaintenanceContent {
  schedule_id: string;
  machine_id: string;
  created_at: string; // ISO timestamp
  fault_details: FaultDetails;
  scheduling_info: SchedulingInfo;
  financial_impact: FinancialImpact;
  cost_benefit_analysis: CostBenefitAnalysis;
}

export interface MaintenanceSchedule {
  key: string; // e.g. maintenance-schedules/20251017172838_CONV_001.json
  last_modified: string; // ISO timestamp
  content: MaintenanceContent;
}

export type MaintenanceScheduleList = MaintenanceSchedule[];

// ---- Top-K classes (simplified subset of all probabilities) ----
export interface TopKProbabilities {
  [faultType: string]: number;
}

// ---- A single prediction from the model ----
export interface Prediction {
  predicted_class: string;
  predicted_class_id: number;
  confidence: number;
  top_k: TopKProbabilities;
  timestamp: string; // ISO timestamp
}

// ---- Inference content structure ----
export interface InferenceContent {
  predictions: Prediction[];
}

// ---- Wrapper metadata for storage and retrieval ----
export interface InferenceRecord {
  key: string; // e.g. "inference/conveyor-A001/20251014_070320.json"
  last_modified: string; // ISO timestamp
  content: InferenceContent;
}

// ---- Collection of inference entries ----
export type InferenceRecordList = InferenceRecord[];
