#!/usr/bin/env python3
"""
Test script to invoke FaultCast agent using boto3
"""

import boto3
import json

def invoke_agent(client, agent_arn, payload):
    """Helper function to invoke agent and parse response"""
    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        payload=json.dumps(payload).encode(),
        contentType='application/json',
        accept='application/json'
    )
    
    # Read the streaming response
    if 'response' in response:
        result_bytes = response['response'].read()
        return json.loads(result_bytes.decode())
    else:
        return response

def test_agent_invoke():
    """Test invoking the agent with boto3"""
    
    print("="*70)
    print("Testing FaultCast Agent Invocation with boto3")
    print("="*70)
    
    agent_arn = 'arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV'
    region = 'eu-west-1'
    
    print(f"\nAgent ARN: {agent_arn}")
    print(f"Region: {region}")
    
    try:
        # Create bedrock-agentcore client
        client = boto3.client('bedrock-agentcore', region_name=region)
        
        # Test 1: Simple prompt
        print("\n[Test 1] Simple prompt: 'Check conveyor-A001'")
        print("-" * 70)
        
        payload = {
            "prompt": "Check conveyor-A001"
        }
        
        result = invoke_agent(client, agent_arn, payload)
        
        print(f"Status: {result.get('status')}")
        print(f"Session ID: {result.get('session_id')}")
        print(f"Timestamp: {result.get('timestamp')}")
        print(f"\nResult:\n{result.get('result')[:500]}...")
        
        # Test 2: ML Prediction
        print("\n\n[Test 2] ML Prediction")
        print("-" * 70)
        
        payload = {
            "prediction": {
                "machine_id": "conveyor-B002",
                "predicted_fault": "ball_bearing",
                "confidence_score": 0.85
            }
        }
        
        result = invoke_agent(client, agent_arn, payload)
        
        print(f"Status: {result.get('status')}")
        print(f"Session ID: {result.get('session_id')}")
        print(f"\nResult:\n{result.get('result')[:500]}...")
        
        print("\n" + "="*70)
        print("✅ All tests passed!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        if hasattr(e, 'response'):
            print(f"Response: {e.response}")
        
        import traceback
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = test_agent_invoke()
    exit(0 if success else 1)
