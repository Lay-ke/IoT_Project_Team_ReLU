# FaultCast Agent - Invocation Guide

## Agent Information

**Agent Name**: `relu_agent`  
**Agent ARN**: `arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV`  
**Region**: `eu-west-1`  
**Account**: `771826808190`

## Configuration

The agent retrieves its configuration from AWS Systems Manager Parameter Store:
- `/faultcast/knowledge-base-id` → Knowledge Base ID
- `/faultcast/knowledge-base-region` → Knowledge Base Region
- `/faultcast/work-schedule-bucket` → S3 Bucket for work schedules
- `/faultcast/work-schedule-prefix` → S3 Prefix for work schedules

## Required IAM Permissions

To invoke the agent, your IAM user/role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV"
    }
  ]
}
```

## Invocation Methods

### 1. Using agentcore CLI (Recommended for Testing)

```bash
# Simple query
agentcore invoke '{"prompt": "Check conveyor-A001"}'

# ML Prediction
agentcore invoke '{
  "prediction": {
    "machine_id": "conveyor-A001",
    "predicted_fault": "pulley",
    "confidence_score": 0.961
  }
}'
```

### 2. Using AWS CLI

```bash
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV" \
  --region eu-west-1 \
  --payload '{"prompt": "Check conveyor-A001"}' \
  --output json
```

### 3. Using Python (boto3)

```python
import boto3
import json

def invoke_faultcast_agent(payload):
    """
    Invoke the FaultCast agent
    
    Args:
        payload (dict): Input payload with 'prompt' or 'prediction'
    
    Returns:
        dict: Agent response
    """
    client = boto3.client('bedrock-agentcore', region_name='eu-west-1')
    
    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV',
        payload=json.dumps(payload).encode(),
        contentType='application/json',
        accept='application/json'
    )
    
    # Read the streaming response
    result_bytes = response['response'].read()
    result = json.loads(result_bytes.decode())
    return result

# Example 1: Simple query
response = invoke_faultcast_agent({
    "prompt": "Check conveyor-A001 for any issues"
})
print(f"Status: {response['status']}")
print(f"Result: {response['result']}")

# Example 2: ML Prediction
response = invoke_faultcast_agent({
    "prediction": {
        "machine_id": "conveyor-A001",
        "predicted_fault": "pulley",
        "confidence_score": 0.961
    }
})
print(f"Status: {response['status']}")
print(f"Result: {response['result']}")
```

### 4. Using Python with Session ID (for tracking)

```python
import boto3
import json
from datetime import datetime

def invoke_with_session(payload, session_id=None):
    """
    Invoke agent with session tracking
    
    Args:
        payload (dict): Input payload
        session_id (str): Optional session ID for tracking
    
    Returns:
        dict: Agent response
    """
    client = boto3.client('bedrock-agentcore', region_name='eu-west-1')
    
    # Add session ID if not provided
    if session_id:
        payload['session_id'] = session_id
    else:
        payload['session_id'] = f"session-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV',
        payload=json.dumps(payload).encode(),
        contentType='application/json',
        accept='application/json'
    )
    
    # Read the streaming response
    result_bytes = response['response'].read()
    return json.loads(result_bytes.decode())

# Example with session tracking
response = invoke_with_session({
    "prediction": {
        "machine_id": "conveyor-A001",
        "predicted_fault": "ball_bearing",
        "confidence_score": 0.85
    }
}, session_id="maintenance-team-001")

print(f"Session: {response.get('session_id')}")
print(f"Status: {response.get('status')}")
print(f"Result: {response.get('result')}")
```

## Input Payload Formats

### Format 1: Direct Query
```json
{
  "prompt": "Analyze conveyor-A001 for maintenance needs"
}
```

### Format 2: ML Prediction
```json
{
  "prediction": {
    "machine_id": "conveyor-A001",
    "predicted_fault": "pulley",
    "confidence_score": 0.961
  }
}
```

### Format 3: With Session ID
```json
{
  "prompt": "Check conveyor-A001",
  "session_id": "maintenance-team-001"
}
```

## Response Format

```json
{
  "result": "Agent response text with analysis and recommendations",
  "status": "success",
  "session_id": "session-20251015083303",
  "timestamp": "2025-10-15T08:33:14.034197Z"
}
```

## Agent Capabilities

The FaultCast agent can:

1. **Get Sensor Readings** - Retrieve real-time sensor data from equipment
2. **Search Prediction History** - Query ML prediction history from Knowledge Base
3. **Analyze Anomalies** - Detect and classify anomalies in sensor data
4. **Search Maintenance Playbook** - Find relevant maintenance procedures
5. **Classify Fault Severity** - Determine urgency and priority levels
6. **Create Work Schedules** - Generate and save maintenance schedules to S3

## Fault Severity Levels

| Severity | Confidence | Urgency | Cost | Duration |
|----------|-----------|---------|------|----------|
| Critical | ≥ 90% | 24 hours | $800 | 6 hours |
| Warning | ≥ 70% | 48 hours | $500 | 4 hours |
| Caution | ≥ 50% | 1 week | $300 | 3 hours |
| Monitor | < 50% | 2 weeks | $150 | 2 hours |

## Monitoring and Logs

### CloudWatch Logs
```bash
# Tail runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/relu_agent-K1lW4rCNbV-DEFAULT \
  --log-stream-name-prefix "2025/10/15/[runtime-logs]" \
  --follow

# View logs from last hour
aws logs tail /aws/bedrock-agentcore/runtimes/relu_agent-K1lW4rCNbV-DEFAULT \
  --log-stream-name-prefix "2025/10/15/[runtime-logs]" \
  --since 1h
```

### GenAI Observability Dashboard
https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#gen-ai-observability/agent-core

## Work Schedule Output

Work schedules are saved to S3:
- **Bucket**: `predictive-maintenance-feature-store`
- **Prefix**: `maintenance-schedules/`
- **Format**: `YYYYMMDDHHMMSS_<machine-id>.json`

Example S3 path:
```
s3://predictive-maintenance-feature-store/maintenance-schedules/20251015083303_conveyor-A001.json
```

## Troubleshooting

### Issue: Access Denied
**Solution**: Ensure your IAM role has `bedrock-agentcore:InvokeAgentRuntime` permission

### Issue: Agent Not Responding
**Solution**: Check CloudWatch logs for errors

### Issue: Knowledge Base Not Found
**Solution**: Verify SSM parameters are set correctly

### Issue: S3 Access Denied
**Solution**: Ensure agent execution role has S3 write permissions

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review GenAI Observability Dashboard
3. Contact the FaultCast team

---

**Last Updated**: October 15, 2025  
**Agent Version**: 1.0  
**Deployment**: AWS Bedrock AgentCore
