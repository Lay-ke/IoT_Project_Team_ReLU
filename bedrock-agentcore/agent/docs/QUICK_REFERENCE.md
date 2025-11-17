# FaultCast Agent - Quick Reference

## 🚀 Quick Start

```bash
# Test the agent
agentcore invoke '{"prompt": "Hello"}'

# Analyze a machine
agentcore invoke '{"prompt": "Check conveyor-A001"}'

# Process ML prediction
agentcore invoke '{
  "prediction": {
    "machine_id": "conveyor-A001",
    "predicted_fault": "pulley",
    "confidence_score": 0.961
  }
}'
```

## 📋 Agent Details

| Property | Value |
|----------|-------|
| **ARN** | `arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV` |
| **Region** | `eu-west-1` |
| **Name** | `relu_agent` |

## 🔑 Required Permissions

```json
{
  "Effect": "Allow",
  "Action": ["bedrock-agentcore:InvokeAgentRuntime"],
  "Resource": "arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV"
}
```

## 📊 Severity Levels

| Level | Confidence | Urgency | Cost |
|-------|-----------|---------|------|
| 🔴 Critical | ≥90% | 24h | $800 |
| 🟡 Warning | ≥70% | 48h | $500 |
| 🟠 Caution | ≥50% | 1wk | $300 |
| 🟢 Monitor | <50% | 2wk | $150 |

## 📁 Output Location

Work schedules: `s3://predictive-maintenance-feature-store/maintenance-schedules/`

## 📖 Full Documentation

See `AGENT_INVOCATION_GUIDE.md` for complete details.
