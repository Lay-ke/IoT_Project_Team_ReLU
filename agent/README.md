# FaultCast - AI-Powered Predictive Maintenance System

FaultCast is an intelligent predictive maintenance system for conveyor belt systems, powered by AWS Bedrock AgentCore and machine learning.

## Features

- **Single Intelligent Agent**: One agent with 6 specialized tools
- **Real-time Monitoring**: IoT sensor data processing
- **ML-Powered Predictions**: Fault detection and classification
- **Financial Analysis**: Cost-benefit analysis for repair vs replace decisions
- **Automated Scheduling**: Work schedule generation with cost estimates
- **Knowledge Base Integration**: Maintenance playbooks and historical data

## Architecture

- **AWS Bedrock AgentCore**: Agent runtime with Amazon Nova Pro
- **AWS IoT Core**: Sensor data ingestion
- **Amazon SageMaker**: ML model hosting
- **AWS Bedrock Knowledge Base**: Document retrieval
- **Amazon S3**: Work schedule storage
- **AWS Systems Manager**: Configuration management

## Quick Start

### Prerequisites

- Python 3.9+
- AWS CLI configured
- Terraform >= 1.0
- AWS Bedrock AgentCore CLI

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

4. Deploy infrastructure:
   ```bash
   cd terraform
   terraform init
   terraform apply -var-file="environments/dev/terraform.tfvars"
   ```

5. Deploy agent:
   ```bash
   agentcore configure --entrypoint faultcast_agentcore.py
   agentcore launch
   ```

## Project Structure

```
faultcast/
├── faultcast/                  # Main agent code
│   └── agents/                 # Agent implementation
├── terraform/                  # Infrastructure as Code
│   ├── modules/                # Terraform modules
│   └── environments/           # Environment configs
├── docs/                       # Documentation
├── tests/                      # Test files
├── scripts/                    # Utility scripts
├── faultcast_agentcore.py      # AgentCore wrapper
├── agentcore-requirements.txt  # Agent dependencies
└── README.md                   # This file
```

## Documentation

- [Architecture Overview](docs/FAULTCAST_ARCHITECTURE.md)
- [Agent Invocation Guide](docs/AGENT_INVOCATION_GUIDE.md)
- [Quick Reference](docs/QUICK_REFERENCE.md)
- [Deployment Status](docs/DEPLOYMENT_STATUS.md)
- [Terraform README](terraform/README.md)

## Agent Capabilities

The FaultCast agent includes 6 specialized tools:

1. **get_sensor_readings()** - Real-time sensor data
2. **search_prediction_history()** - ML prediction history
3. **analyze_anomaly()** - Anomaly detection
4. **search_maintenance_playbook()** - Maintenance procedures
5. **classify_fault_severity()** - Severity classification
6. **create_work_schedule()** - Work schedule generation

## Usage

### Invoke Agent via CLI

```bash
agentcore invoke '{"prompt": "Check conveyor-A001"}'
```

### Invoke Agent via Python

```python
import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='eu-west-1')

response = client.invoke_agent_runtime(
    agentRuntimeArn='YOUR_AGENT_ARN',
    payload=json.dumps({"prompt": "Check conveyor-A001"}).encode(),
    contentType='application/json',
    accept='application/json'
)

result = json.loads(response['response'].read())
print(result)
```

### Process ML Prediction

```python
payload = {
    "machine_id": "conveyor-A001",
    "prediction": {
        "predicted_class": "pulley",
        "confidence": 0.961,
        "top_k": {
            "pulley": 0.961,
            "normal": 0.025
        }
    }
}

response = client.invoke_agent_runtime(
    agentRuntimeArn='YOUR_AGENT_ARN',
    payload=json.dumps(payload).encode(),
    contentType='application/json',
    accept='application/json'
)
```

## Testing

Run tests:
```bash
cd tests
python test_local_agent.py
python test_actual_format.py
```

## Configuration

Configuration is managed via AWS Systems Manager Parameter Store:

- `/faultcast/knowledge-base-id`
- `/faultcast/knowledge-base-region`
- `/faultcast/work-schedule-bucket`
- `/faultcast/work-schedule-prefix`

## Work Schedule Output

Work schedules include comprehensive financial analysis:

```json
{
  "schedule_id": "WS-conveyor-A001-...",
  "fault_details": {
    "fault_type": "pulley",
    "severity": "critical",
    "confidence_score": 0.961
  },
  "financial_impact": {
    "downtime_cost_per_hour_usd": 600,
    "repair_cost_usd": 400,
    "replacement_cost_usd": 1200,
    "recommended_action": "repair",
    "estimated_total_cost_usd": 3400
  },
  "cost_benefit_analysis": {
    "repair_option": {...},
    "replacement_option": {...},
    "cost_savings_usd": 2600
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions, please open an issue on GitHub.

---

**Agent ARN**: `arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV`  
**Region**: `eu-west-1`  
**Status**: Production Ready ✅
