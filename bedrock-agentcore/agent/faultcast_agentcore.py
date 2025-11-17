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
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_PATH = os.path.join(BASE_DIR, "vendor")

if os.path.isdir(VENDOR_PATH):
    # Prepend vendored dependencies so AgentCore can resolve runtime libraries
    sys.path.insert(0, VENDOR_PATH)

# Add local module directory to import path
sys.path.insert(0, BASE_DIR)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from faultcast.config import apply_settings
from opentelemetry import baggage, context
from datetime import datetime

print("Loading FaultCast configuration...")
SETTINGS = None
_AGENT = None


def _ensure_settings():
    """Load configuration lazily to keep cold start under the runtime limit."""
    global SETTINGS
    if SETTINGS is None:
        start = time.time()
        loaded = apply_settings()
        print(
            f"Configuration loaded. Region: {loaded.aws_region}; KB configured: {bool(loaded.knowledge_base_id)}"
        )
        print(f"Settings ready in {time.time() - start:.3f}s")
        SETTINGS = loaded
    return SETTINGS


def _ensure_agent():
    """Import the FaultCast agent only when first needed."""
    global _AGENT
    if _AGENT is None:
        start = time.time()
        _ensure_settings()
        from faultcast.agents.faultcast_maintenance_agent import faultcast_agent as _faultcast_agent

        _AGENT = _faultcast_agent
        print(f"FaultCast agent import finished in {time.time() - start:.3f}s")
    return _AGENT

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
        invoke_start = time.time()
        _ensure_settings()
        agent = _ensure_agent()
        print(f"Invoke setup completed in {time.time() - invoke_start:.3f}s")
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
        exec_start = time.time()
        print(f"[{session_id}] Processing request...")
        response = agent(prompt)
        print(f"[{session_id}] Request completed in {time.time() - exec_start:.3f}s")
        
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
    
    _ensure_settings()
    _ensure_agent()
    app.run(port=port)
