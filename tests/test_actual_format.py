#!/usr/bin/env python3
"""
Test with actual ML prediction format (no machine_id in prediction)
"""

import sys
import os
import json

# Add faultcast directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the invoke function
from faultcast_agentcore import invoke

print("="*70)
print("Test 1: Prediction without machine_id (should use 'unknown-machine')")
print("="*70)

payload1 = {
    "prediction": {
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

print("\nPayload:")
print(json.dumps(payload1, indent=2))

try:
    result = invoke(payload1)
    print(f"\n✅ Status: {result.get('status')}")
    print(f"Result preview: {result.get('result')[:300]}...")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")

print("\n" + "="*70)
print("Test 2: Prediction with machine_id at root level")
print("="*70)

payload2 = {
    "machine_id": "conveyor-A001",
    "prediction": {
        "predicted_class": "pulley",
        "predicted_class_id": 5,
        "confidence": 0.961,
        "top_k": {
            "pulley": 0.961,
            "normal": 0.025,
            "belt slippage": 0.014
        },
        "timestamp": "2025-10-15T12:00:00.000000Z"
    }
}

print("\nPayload:")
print(json.dumps(payload2, indent=2))

try:
    result = invoke(payload2)
    print(f"\n✅ Status: {result.get('status')}")
    print(f"Result preview: {result.get('result')[:300]}...")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")

print("\n" + "="*70)
print("Test 3: Prediction with machine_id inside prediction")
print("="*70)

payload3 = {
    "prediction": {
        "machine_id": "conveyor-B002",
        "predicted_class": "idler roller fault",
        "predicted_class_id": 4,
        "confidence": 0.78,
        "top_k": {
            "idler roller fault": 0.78,
            "normal": 0.15,
            "belt slippage": 0.07
        },
        "timestamp": "2025-10-15T12:00:00.000000Z"
    }
}

print("\nPayload:")
print(json.dumps(payload3, indent=2))

try:
    result = invoke(payload3)
    print(f"\n✅ Status: {result.get('status')}")
    print(f"Result preview: {result.get('result')[:300]}...")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
