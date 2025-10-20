#!/usr/bin/env python3
"""
Test with actual ML prediction format
"""

import sys
import os
import json

# Add faultcast directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the invoke function from faultcast_agentcore
from faultcast_agentcore import invoke

# Actual prediction format from ML model
payload = {
    "prediction": {
        "machine_id": "conveyor-A001",
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
}

print("="*70)
print("Testing FaultCast Agent with Actual ML Prediction Format")
print("="*70)
print("\nPayload:")
print(json.dumps(payload, indent=2))
print()

print("Invoking agent...")
print("-" * 70)

try:
    result = invoke(payload)
    
    print("\n✅ Success!")
    print(f"Status: {result.get('status')}")
    print(f"Session ID: {result.get('session_id')}")
    print(f"Timestamp: {result.get('timestamp')}")
    print(f"\nResult:\n{result.get('result')}")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
