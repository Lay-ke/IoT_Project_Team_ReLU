# FaultCast Single Agent Architecture

## System Overview

FaultCast uses a **single intelligent agent** deployed on AWS Bedrock AgentCore with 6 specialized tools for comprehensive predictive maintenance.

## Architecture Diagram Components

### 1. Data Ingestion Layer
```
┌─────────────────────────────────────────────────────────────┐
│  Sensor Simulation (EventBridge Scheduler → Lambda)         │
│  • Generates streaming sensor data                          │
│  • Sends to IoT Core every minute                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  AWS IoT Core                                               │
│  • Receives sensor data streams                             │
│  • Filters and routes data                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  IoT Rule → Lambda (ML Inference)                           │
│  • Triggers on sensor data                                  │
│  • Invokes SageMaker endpoints                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. ML Inference Layer
```
┌─────────────────────────────────────────────────────────────┐
│  SageMaker Endpoints                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ Anomaly/Fault        │  │ RUL (Remaining       │        │
│  │ Detection Model      │  │ Useful Life) Model   │        │
│  │ • Classifies faults  │  │ • Predicts lifetime  │        │
│  │ • Confidence scores  │  │ • Time estimates     │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            ↓
                   ML Prediction Output
                   {
                     "predicted_class": "pulley",
                     "confidence": 0.961,
                     "top_k": {...}
                   }
```

### 3. Agent Layer (Core Intelligence)
```
┌─────────────────────────────────────────────────────────────┐
│  AWS Bedrock AgentCore - FaultCast Single Agent            │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Agent: relu_agent                                    │ │
│  │  Model: Amazon Nova Pro                               │ │
│  │  Memory: Short-term (STM_ONLY)                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  6 Specialized Tools:                                 │ │
│  │                                                        │ │
│  │  1. get_sensor_readings()                             │ │
│  │     • Retrieves real-time sensor data                 │ │
│  │     • Vibration, temp, current, speed                 │ │
│  │                                                        │ │
│  │  2. search_prediction_history()                       │ │
│  │     • Queries Knowledge Base                          │ │
│  │     • Historical ML predictions                       │ │
│  │                                                        │ │
│  │  3. analyze_anomaly()                                 │ │
│  │     • Detects anomalies in sensor data                │ │
│  │     • Threshold-based analysis                        │ │
│  │                                                        │ │
│  │  4. search_maintenance_playbook()                     │ │
│  │     • Queries Knowledge Base                          │ │
│  │     • Retrieves maintenance procedures                │ │
│  │                                                        │ │
│  │  5. classify_fault_severity()                         │ │
│  │     • Critical/Warning/Caution/Monitor                │ │
│  │     • Urgency and priority levels                     │ │
│  │                                                        │ │
│  │  6. create_work_schedule()                            │ │
│  │     • Financial impact analysis                       │ │
│  │     • Repair vs Replace recommendation                │ │
│  │     • Saves to S3                                     │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4. Knowledge & Storage Layer
```
┌─────────────────────────────────────────────────────────────┐
│  AWS Bedrock Knowledge Base                                │
│  • ML Prediction History                                    │
│  • Maintenance Playbooks                                    │
│  • Semantic search enabled                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Amazon S3                                                  │
│  • Work schedules (JSON)                                    │
│  • Prediction history                                       │
│  • Knowledge base documents                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AWS Systems Manager Parameter Store                       │
│  • /faultcast/knowledge-base-id                             │
│  • /faultcast/work-schedule-bucket                          │
│  • Runtime configuration                                    │
└─────────────────────────────────────────────────────────────┘
```

### 5. Output & Integration Layer
```
┌─────────────────────────────────────────────────────────────┐
│  Work Schedule Output (S3)                                  │
│  {                                                           │
│    "schedule_id": "WS-conveyor-A001-...",                   │
│    "fault_details": {                                       │
│      "fault_type": "pulley",                                │
│      "severity": "critical",                                │
│      "confidence_score": 0.961                              │
│    },                                                        │
│    "financial_impact": {                                    │
│      "downtime_cost_per_hour_usd": 600,                     │
│      "repair_cost_usd": 400,                                │
│      "replacement_cost_usd": 1200,                          │
│      "recommended_action": "repair",                        │
│      "estimated_total_cost_usd": 3400                       │
│    },                                                        │
│    "cost_benefit_analysis": {...}                           │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. Sensor Data → IoT Core → Lambda
2. Lambda → SageMaker (ML Inference)
3. ML Prediction → Bedrock AgentCore Agent
4. Agent executes tools in sequence:
   a. get_sensor_readings()
   b. search_prediction_history() [Knowledge Base]
   c. analyze_anomaly()
   d. search_maintenance_playbook() [Knowledge Base]
   e. classify_fault_severity()
   f. create_work_schedule() [→ S3]
5. Work Schedule → S3 → Downstream Systems
```

## Key Features

### Single Agent Benefits
- **Unified Intelligence**: One agent orchestrates all maintenance tasks
- **Context Awareness**: Maintains conversation context across tools
- **Simplified Architecture**: No inter-agent communication needed
- **Cost Effective**: Single agent deployment and management

### Financial Analysis
- **Downtime Cost**: Calculates revenue loss per hour
- **Repair vs Replace**: Cost-benefit analysis
- **Total Cost**: Direct costs + downtime costs
- **Recommendation**: Data-driven action (repair/replace)

### Fault Severity Levels
| Severity | Confidence | Urgency | Cost | Duration |
|----------|-----------|---------|------|----------|
| Critical | ≥90% | 24h | $800 | 6h |
| Warning | ≥70% | 48h | $500 | 4h |
| Caution | ≥50% | 1wk | $300 | 3h |
| Monitor | <50% | 2wk | $150 | 2h |

## AWS Services Used

1. **AWS IoT Core** - Sensor data ingestion
2. **AWS Lambda** - Event processing and ML invocation
3. **Amazon SageMaker** - ML model hosting
4. **AWS Bedrock AgentCore** - Agent runtime
5. **AWS Bedrock Knowledge Base** - Document retrieval
6. **Amazon S3** - Work schedule storage
7. **AWS Systems Manager** - Configuration management
8. **Amazon CloudWatch** - Logging and monitoring
9. **AWS EventBridge** - Scheduling

## Deployment

- **Platform**: AWS Bedrock AgentCore
- **Region**: eu-west-1
- **Agent ARN**: `arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV`
- **Container**: ARM64 Docker
- **Model**: Amazon Nova Pro
- **Memory**: Short-term (STM_ONLY)

## Integration Points

### Input
- ML predictions from Lambda (JSON format)
- Direct queries via boto3 or agentcore CLI

### Output
- Work schedules in S3 (JSON format)
- Agent responses with analysis and recommendations

---

**Note**: This is a single-agent architecture. The agent uses 6 specialized tools to handle all predictive maintenance tasks, replacing the previous multi-agent design.
