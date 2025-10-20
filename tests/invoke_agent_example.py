#!/usr/bin/env python3
"""
FaultCast Agent - Simple Invocation Example

This script shows how to invoke the FaultCast agent using boto3.
"""

import boto3
import json

# Agent configuration
AGENT_ARN = 'arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV'
REGION = 'eu-west-1'


def invoke_faultcast_agent(payload):
    """
    Invoke the FaultCast agent
    
    Args:
        payload (dict): Input payload with 'prompt' or 'prediction'
    
    Returns:
        dict: Agent response with 'status', 'result', 'session_id', 'timestamp'
    """
    client = boto3.client('bedrock-agentcore', region_name=REGION)
    
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_ARN,
        payload=json.dumps(payload).encode(),
        contentType='application/json',
        accept='application/json'
    )
    
    # Read the streaming response
    result_bytes = response['response'].read()
    return json.loads(result_bytes.decode())


# Example 1: Simple query
print("Example 1: Simple Query")
print("-" * 70)

response = invoke_faultcast_agent({
    "prompt": "Check conveyor-A001 for any issues"
})

print(f"Status: {response['status']}")
print(f"Session ID: {response['session_id']}")
print(f"Result: {response['result'][:200]}...")
print()


# Example 2: ML Prediction
print("Example 2: ML Prediction")
print("-" * 70)

response = invoke_faultcast_agent({
    "prediction": {
        "machine_id": "conveyor-A001",
        "predicted_fault": "pulley",
        "confidence_score": 0.961
    }
})

print(f"Status: {response['status']}")
print(f"Session ID: {response['session_id']}")
print(f"Result: {response['result'][:200]}...")
print()


# Example 3: With custom session ID
print("Example 3: With Custom Session ID")
print("-" * 70)

response = invoke_faultcast_agent({
    "prompt": "Analyze conveyor-B002",
    "session_id": "maintenance-team-001"
})

print(f"Status: {response['status']}")
print(f"Session ID: {response['session_id']}")
print(f"Result: {response['result'][:200]}...")
