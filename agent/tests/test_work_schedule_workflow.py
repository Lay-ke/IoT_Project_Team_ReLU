#!/usr/bin/env python3
"""
Test script for work schedule creation workflow
Simulates Lambda function calling the agent with prediction data
"""

import sys
sys.path.insert(0, 'faultcast/agents')

from faultcast_maintenance_agent import faultcast_agent

# Simulate prediction data from Lambda
prediction_data = {
    "machine_id": "conveyor-A001",
    "predicted_fault": "pulley",
    "confidence_score": 0.961,
    "timestamp": "2025-10-14T10:30:00Z",
    "operational_features": {
        "mean_speed_rpm": 119.87,
        "mean_vibration": 0.61,
        "mean_temperature": 38.89,
        "stress_index": 2.5912
    }
}

print("="*70)
print("FaultCast Work Schedule Workflow Test")
print("="*70)
print(f"\nPrediction Data:")
print(f"  Machine: {prediction_data['machine_id']}")
print(f"  Fault: {prediction_data['predicted_fault']}")
print(f"  Confidence: {prediction_data['confidence_score']}")
print("\n" + "="*70)

# Create prompt for agent
prompt = f"""
I have a prediction from the ML model for {prediction_data['machine_id']}:
- Predicted Fault: {prediction_data['predicted_fault']}
- Confidence Score: {prediction_data['confidence_score']}

Please:
1. Classify the severity of this fault
2. Search the playbook for maintenance procedures
3. Create a work schedule and save it to S3
4. Send a notification email if needed
5. Provide a summary of actions taken
"""

print("\nAgent Processing...\n")
response = faultcast_agent(prompt)
print(response)
print("\n" + "="*70)
