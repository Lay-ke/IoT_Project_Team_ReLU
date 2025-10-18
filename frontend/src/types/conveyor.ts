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

// ---- Probability mappings for each detected fault type ----
export interface FaultProbabilities {
  [faultType: string]: number; // e.g., { pulley: 0.89, normal: 0.07, "ball bearing": 0.01 }
}

// ---- Top-K classes (simplified subset of all probabilities) ----
export interface TopKProbabilities {
  [faultType: string]: number;
}

// ---- Inference content structure ----
export interface InferenceContent {
  predicted_class: string; // e.g., "pulley"
  predicted_class_id: number; // numeric class label from model
  confidence: number; // model confidence 0–1
  top_k: TopKProbabilities; // top predicted categories
  all_probabilities: FaultProbabilities; // all model class probabilities
  timestamp: string; // ISO timestamp, e.g., "2025-10-14T07:03:21.316764Z"
}

// ---- Wrapper metadata for storage and retrieval ----
export interface InferenceRecord {
  key: string; // e.g. "inference/conveyor-A001/20251014_070320.json"
  last_modified: string; // ISO timestamp
  content: InferenceContent;
}

// ---- Collection of inference entries ----
export type InferenceRecordList = InferenceRecord[];
