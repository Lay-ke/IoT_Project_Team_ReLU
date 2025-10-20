#!/usr/bin/env python3
"""
FaultCast Agent - AWS Bedrock AgentCore Deployment Wrapper

This wrapper enables the FaultCast maintenance agent to run on AWS Bedrock AgentCore Runtime.
It provides a simple HTTP interface for agent invocations.

Usage:
    Local testing:
        python faultcast_agentcore.py
    
    Deploy to AgentCore:
        agentcore configure --entrypoint faultcast_agentcore.py
        agentcore launch
"""

import sys
import os
import boto3

# Add faultcast directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from faultcast.agents.faultcast_maintenance_agent import faultcast_agent
from opentelemetry import baggage, context
import json
from datetime import datetime

# Load configuration from AWS Systems Manager Parameter Store
def load_config_from_ssm():
    """
    Load configuration from AWS Systems Manager Parameter Store
    
    Returns:
        dict: Configuration parameters
    """
    try:
        ssm = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
        
        # Get all FaultCast parameters
        response = ssm.get_parameters_by_path(
            Path='/faultcast',
            Recursive=True,
            WithDecryption=True
        )
        
        # Set environment variables from Parameter Store
        for param in response['Parameters']:
            param_name = param['Name'].split('/')[-1]  # Get last part of path
            param_value = param['Value']
            
            # Convert parameter names to environment variable format
            env_var_name = param_name.upper().replace('-', '_')
            os.environ[env_var_name] = param_value
            print(f"Loaded config: {env_var_name}")
        
        return True
    except Exception as e:
        print(f"Warning: Could not load config from SSM: {e}")
        print("Falling back to environment variables or defaults")
        return False

# Load configuration at startup
print("Loading configuration from AWS Systems Manager...")
load_config_from_ssm()

# Initialize AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """
    AgentCore entrypoint for FaultCast agent
    
    Handles two types of invocations:
    1. Direct user queries with prompt
    2. ML prediction data from Lambda triggers
    
    Args:
        payload (dict): Input payload with one of:
            - prompt (str): Direct user query
            - prediction (dict): ML prediction data (REQUIRED: predicted_class, confidence)
                - machine_id (str): Equipment identifier (optional, defaults to "conveyor_A001")
                - predicted_class (str): Fault type from ML model (REQUIRED)
                - confidence (float): Prediction confidence score (REQUIRED)
                - top_k (dict): Top K predictions with probabilities
                - all_probabilities (dict): All class probabilities
            - session_id (str): Optional session identifier for tracing
    
    Returns:
        dict: Response with result or error
    
    Examples:
        # Direct query
        {
            "prompt": "Analyze conveyor-A001 for any issues"
        }
        
        # ML prediction (detailed format - machine_id optional, defaults to conveyor_A001)
        {
            "prediction": {
                "predicted_class": "ball bearing",
                "confidence": 0.89,
                "top_k": {
                    "ball bearing": 0.89,
                    "normal": 0.08,
                    "pulley": 0.03
                }
            }
        }
        
        # ML prediction with machine_id specified
        {
            "prediction": {
                "machine_id": "conveyor_B002",
                "predicted_class": "pulley",
                "confidence": 0.95
            }
        }
    """
    
    # Set session ID in baggage for distributed tracing
    session_id = payload.get("session_id", f"session-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    ctx = baggage.set_baggage("session.id", session_id)
    context.attach(ctx)
    
    try:
        # Extract prompt from payload
        prompt = payload.get("prompt", "")
        
        # If no prompt but prediction data exists, create prompt from prediction
        if not prompt and "prediction" in payload:
            prediction = payload["prediction"]
            
            # Extract machine_id from prediction or payload root, default to conveyor_A001
            machine_id = prediction.get("machine_id") or payload.get("machine_id") or "conveyor_A001"
            
            # Handle both formats: simple and detailed ML prediction
            if "predicted_class" in prediction:
                # Detailed ML prediction format (actual format from ML model)
                fault_type = prediction.get("predicted_class")
                confidence = prediction.get("confidence", 0.0)
                
                # Validate required fields
                if not fault_type:
                    return {
                        "error": "Missing predicted_class",
                        "message": "Prediction payload must include 'predicted_class' field",
                        "status": "failed",
                        "session_id": session_id
                    }
                
                # Build top predictions string
                top_k = prediction.get("top_k", {})
                top_predictions = "\n".join([f"  - {fault}: {prob:.2%}" for fault, prob in top_k.items()])
                
                prompt = f"""
I have a prediction from the ML model for {machine_id}:
- Predicted Class: {fault_type}
- Confidence: {confidence:.2%}

Top predictions:
{top_predictions}

Please:
1. Classify the severity of this fault
2. Search the playbook for maintenance procedures
3. Create a work schedule and save it to S3
4. Provide a summary of actions taken
"""
            else:
                # Simple prediction format (backward compatibility)
                fault_type = prediction.get("predicted_fault")
                confidence = prediction.get("confidence_score", 0.0)
                
                # Validate required fields
                if not fault_type:
                    return {
                        "error": "Missing predicted_fault",
                        "message": "Prediction payload must include 'predicted_fault' field",
                        "status": "failed",
                        "session_id": session_id
                    }
                
                prompt = f"""
I have a prediction from the ML model for {machine_id}:
- Predicted Fault: {fault_type}
- Confidence Score: {confidence}

Please:
1. Classify the severity of this fault
2. Search the playbook for maintenance procedures
3. Create a work schedule and save it to S3
4. Provide a summary of actions taken
"""
        
        # Validate input
        if not prompt:
            return {
                "error": "Invalid input",
                "message": "Please provide either 'prompt' or 'prediction' in payload",
                "status": "failed",
                "session_id": session_id
            }
        
        # Call FaultCast agent
        print(f"[{session_id}] Processing request...")
        response = faultcast_agent(prompt)
        print(f"[{session_id}] Request completed")
        
        # Return successful response
        return {
            "result": str(response),
            "status": "success",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        # Handle errors gracefully
        error_msg = str(e)
        print(f"[{session_id}] Error: {error_msg}")
        
        return {
            "error": error_msg,
            "status": "failed",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


if __name__ == "__main__":
    """
    Run the agent locally for testing
    
    Usage:
        python faultcast_agentcore.py
    
    Then test with:
        curl -X POST http://localhost:8080/invocations \
          -H "Content-Type: application/json" \
          -d '{"prompt": "Check conveyor-A001"}'
    """
    port = int(os.getenv("PORT", "8080"))
    print("="*70)
    print("FaultCast Agent - AgentCore Runtime")
    print("="*70)
    print(f"Starting local server on http://localhost:{port}")
    print("\nTest with:")
    print(f"  curl -X POST http://localhost:{port}/invocations \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"prompt\": \"Analyze conveyor-A001\"}'")
    print("="*70)
    
    app.run(port=port)
