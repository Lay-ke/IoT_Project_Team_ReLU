#!/usr/bin/env python3
"""
Test FaultCast agent locally with actual prediction format
"""

import sys
import os

# Add faultcast directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faultcast.agents.faultcast_maintenance_agent import faultcast_agent
import json

# Test 1: Check if environment variables are loaded
print("="*70)
print("Test 1: Environment Variables")
print("="*70)

env_vars = {
    'KNOWLEDGE_BASE_ID': os.getenv('KNOWLEDGE_BASE_ID'),
    'KNOWLEDGE_BASE_REGION': os.getenv('KNOWLEDGE_BASE_REGION'),
    'WORK_SCHEDULE_BUCKET': os.getenv('WORK_SCHEDULE_BUCKET'),
    'WORK_SCHEDULE_PREFIX': os.getenv('WORK_SCHEDULE_PREFIX')
}

for key, value in env_vars.items():
    status = "✅" if value else "❌"
    print(f"{status} {key}: {value}")

print()

# Test 2: Actual prediction format from ML model
print("="*70)
print("Test 2: Actual ML Prediction Format")
print("="*70)

prediction_data = {
    "predicted_class": "ball bearing",
    "predicted_class_id": 0,
    "confidence": 0.2654799222946167,
    "top_k": {
        "ball bearing": 0.2654799222946167,
        "normal": 0.22708022594451904,
        "central shaft": 0.14366528391838074
    },
    "all_probabilities": {
        "ball bearing": 0.2654799222946167,
        "belt slippage": 0.12602782249450684,
        "central shaft": 0.14366528391838074,
        "drive motor": 0.07486440241336823,
        "idler roller fault": 0.08777788281440735,
        "pulley": 0.07510445266962051,
        "normal": 0.22708022594451904
    },
    "timestamp": "2025-10-12T11:51:16.659623Z"
}

# Create prompt from prediction data
prompt = f"""
I have a prediction from the ML model:
- Predicted Class: {prediction_data['predicted_class']}
- Confidence: {prediction_data['confidence']:.2%}
- Machine ID: conveyor-A001

Top predictions:
"""
for fault, prob in prediction_data['top_k'].items():
    prompt += f"\n  - {fault}: {prob:.2%}"

prompt += """

Please:
1. Classify the severity of this fault
2. Search the playbook for maintenance procedures
3. Create a work schedule and save it to S3
4. Provide a summary of actions taken
"""

print("Prompt:")
print(prompt)
print()

print("Invoking agent...")
print("-" * 70)

try:
    response = faultcast_agent(prompt)
    print("\n✅ Agent Response:")
    print(response)
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Simple format (for comparison)
print("="*70)
print("Test 3: Simplified Prediction Format")
print("="*70)

simple_prompt = f"""
I have a prediction from the ML model for conveyor-A001:
- Predicted Fault: ball bearing
- Confidence Score: 0.265

Please analyze and create a maintenance schedule.
"""

print("Invoking agent with simplified format...")
print("-" * 70)

try:
    response = faultcast_agent(simple_prompt)
    print("\n✅ Agent Response:")
    print(response)
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
