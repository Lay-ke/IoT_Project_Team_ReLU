# FaultCast Maintenance System - Design Document

## Overview

The FaultCast system is designed as a sophisticated AI-powered predictive maintenance platform that transforms raw sensor data into actionable maintenance insights. The system is built using the **Strands Agents SDK** with a **single unified agent** architecture and AWS Bedrock Nova Pro integration.

The architecture follows the Strands SDK agent model where a single agent is created using the `Agent()` class with multiple specialized `@tool` decorated functions. This design leverages Strands SDK's native capabilities for tool composition, AWS Bedrock integration, and intelligent tool selection, providing maximum flexibility and maintainability in a simplified architecture.

## AWS AI Agent Compliance

### Meeting AWS AI Agent Requirements

#### 1. Large Language Model (LLM) Integration
- **Primary LLM**: AWS Bedrock Nova Pro (eu-west-1) for reasoning and decision-making
- **Model**: `eu.amazon.nova-pro-v1:0`

#### 2. AWS AI Services Integration
1. **AWS Bedrock**: Nova Pro model for agent reasoning, tool selection, and response generation
2. **Future**: Amazon SageMaker for custom ML models
3. **Future**: Amazon Textract for PDF processing of maintenance manuals

#### 3. AI Agent Qualification Criteria
- **Reasoning LLM**: AWS Bedrock Nova Pro provides autonomous decision-making
- **Autonomous Capabilities**: Agent operates independently with tool composition
- **External Integrations**: Sensor data, maintenance databases, and future CMMS integration

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              FaultCast Maintenance System                   │
│                (Single Agent Architecture)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         FaultCast Maintenance Agent                   │ │
│  │         (Strands SDK Agent)                           │ │
│  │                                                       │ │
│  │  Model: AWS Bedrock Nova Pro (eu-west-1)            │ │
│  │  Region: eu-west-1                                   │ │
│  │                                                       │ │
│  │  Tools:                                              │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │ @tool get_sensor_readings()                 │    │ │
│  │  │ - Retrieves sensor data                     │    │ │
│  │  │ - Simulates anomalies for testing           │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  │                                                       │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │ @tool search_prediction_history()           │    │ │
│  │  │ - Queries ML prediction knowledge base      │    │ │
│  │  │ - Retrieves historical fault patterns       │    │ │
│  │  │ - Returns confidence scores & probabilities │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  │                                                       │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │ @tool analyze_anomaly()                     │    │ │
│  │  │ - Analyzes sensor readings                  │    │ │
│  │  │ - Classifies severity                       │    │ │
│  │  │ - Identifies anomalies                      │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  │                                                       │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │ @tool generate_maintenance_recommendations()│    │ │
│  │  │ - Creates maintenance plans                 │    │ │
│  │  │ - Estimates costs and time                  │    │ │
│  │  │ - Prioritizes actions                       │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### FaultCast Maintenance Agent

**Purpose**: Single unified agent that handles all maintenance analysis tasks

**Implementation**:
```python
from strands import Agent, tool

faultcast_agent = Agent(
    model="eu.amazon.nova-pro-v1:0",
    system_prompt="You are FaultCast, an expert AI maintenance engineer...",
    tools=[
        get_sensor_readings,
        search_prediction_history,
        analyze_anomaly,
        generate_maintenance_recommendations
    ]
)
```

**Capabilities**:
- Natural language understanding of maintenance queries
- Intelligent tool selection and composition
- Synthesis of tool results into actionable guidance
- Context-aware responses using Nova Pro

## Tool Specifications

### Tool 1: get_sensor_readings

**Purpose**: Retrieve current sensor data from conveyor belt equipment

**Signature**:
```python
@tool
def get_sensor_readings(
    machine_id: str = "CONV_001",
    include_anomaly: bool = False
) -> dict
```

**Returns**:
```json
{
  "machine_id": "CONV_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "sensors": {
    "vibration": 2.1,
    "temperature": 72.0,
    "current": 12.5,
    "speed": 1200.0
  }
}
```

### Tool 2: search_prediction_history

**Purpose**: Search AWS Bedrock Knowledge Base for ML model predictions and historical fault patterns

**Signature**:
```python
@tool
def search_prediction_history(
    machine_id: str,
    query: str = ""
) -> dict
```

**Returns**:
```json
{
  "machine_id": "conveyor-A001",
  "query": "Device ID: conveyor-A001",
  "predictions_found": 3,
  "predictions": [
    {
      "content": "--- Predictive Maintenance Inference Report ---\nDevice ID: conveyor-A001\nPredicted Fault Type: ball bearing\nConfidence Score: 0.85\nTop Class Probabilities:\n• ball bearing: 0.850\n• normal: 0.095\n• idler roller fault: 0.055\nOperational Feature Snapshot:\n- Mean Speed (rpm): 120.28\n- Mean Vibration (m/s²): 1.20\n- Stress Index: 4.5",
      "score": 0.92,
      "source": "s3://bucket/conveyor_batches/20251013_143719_conveyor-A001.json"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Knowledge Base Content**:
The knowledge base stores inference reports containing:
- Device ID and time window
- Predicted fault types (normal, ball bearing, idler roller fault, etc.)
- Confidence scores and class probabilities
- Operational features (speed, load, temperature, vibration, current)
- Stress indices, thermal ratios, and power metrics
- Feature correlations

### Tool 3: analyze_anomaly

**Purpose**: Analyze sensor readings for anomalies and classify severity

**Signature**:
```python
@tool
def analyze_anomaly(sensor_readings: dict) -> dict
```

**Returns**:
```json
{
  "machine_id": "CONV_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "anomalies": [
    {
      "sensor": "vibration",
      "value": 4.2,
      "unit": "mm/s",
      "severity": "critical",
      "threshold_exceeded": 4.0,
      "message": "Vibration critically high at 4.2 mm/s"
    }
  ],
  "anomaly_count": 1,
  "overall_status": "critical"
}
```

### Tool 4: generate_maintenance_recommendations

**Purpose**: Generate specific maintenance recommendations based on anomalies

**Signature**:
```python
@tool
def generate_maintenance_recommendations(anomaly_analysis: dict) -> dict
```

**Returns**:
```json
{
  "machine_id": "CONV_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "recommendations": [
    {
      "action": "Emergency shutdown and bearing inspection required",
      "reason": "Critical vibration level (4.2 mm/s) indicates imminent bearing failure",
      "priority": "immediate",
      "estimated_cost_usd": 600,
      "estimated_time_hours": 4,
      "parts_needed": ["bearings", "alignment_tools"]
    }
  ],
  "total_actions": 1,
  "total_estimated_cost_usd": 600,
  "total_estimated_time_hours": 4
}
```

## Agent Workflow

### Example: Complete Equipment Analysis with ML Predictions

1. **User Query**: "Analyze conveyor belt conveyor-A001 for any issues"

2. **Agent Reasoning** (Nova Pro):
   - Understands the request requires complete analysis
   - Decides to use all four tools in sequence

3. **Tool Execution**:
   ```
   Tool #1: get_sensor_readings(machine_id="conveyor-A001", include_anomaly=True)
   Tool #2: search_prediction_history(machine_id="conveyor-A001", query="")
   Tool #3: analyze_anomaly(sensor_readings=<result_from_tool_1>)
   Tool #4: generate_maintenance_recommendations(anomaly_analysis=<result_from_tool_3>)
   ```

4. **Response Synthesis** (Nova Pro):
   - Combines real-time sensor data with ML predictions
   - Correlates current readings with historical patterns
   - Provides actionable guidance with confidence levels
   - Prioritizes recommendations based on both data sources

5. **User Response**: Clear, actionable maintenance guidance backed by ML insights

## Extensibility

### Adding New Tools

The single-agent architecture makes it easy to add new capabilities:

```python
@tool
def create_work_order(recommendations: dict) -> dict:
    """Create a work order from maintenance recommendations"""
    # Implementation
    pass

@tool
def schedule_maintenance(work_order: dict, constraints: dict) -> dict:
    """Find optimal maintenance window"""
    # Implementation
    pass

# Add to agent
faultcast_agent = Agent(
    model="eu.amazon.nova-pro-v1:0",
    tools=[
        get_sensor_readings,
        search_prediction_history,
        analyze_anomaly,
        generate_maintenance_recommendations,
        create_work_order,        # New tool
        schedule_maintenance      # New tool
    ]
)
```

The agent automatically learns to use new tools based on their docstrings and parameters.

## Benefits of Single Agent Architecture

### Simplicity
- One agent to manage and deploy
- Simpler codebase and maintenance
- Easier debugging and testing

### Flexibility
- Agent intelligently composes tools
- Easy to add new capabilities
- Natural tool chaining

### Strands SDK Alignment
- Follows Strands SDK best practices
- Leverages native tool composition
- Clean, idiomatic implementation

### Cost Efficiency
- Single model invocation per query
- No inter-agent communication overhead
- Efficient token usage

## Deployment

### Local Development
```bash
python faultcast/agents/faultcast_maintenance_agent.py
```

### Production Deployment (Future)
- AWS Lambda function hosting the agent
- API Gateway for external access
- CloudWatch for logging and monitoring
- DynamoDB for conversation history

## Security

- AWS IAM roles for Bedrock access
- Environment variables for credentials
- Input validation on all tool parameters
- Rate limiting on API endpoints (future)

## Monitoring

- Tool execution logging
- Response time tracking
- Error rate monitoring
- User satisfaction feedback (future)
