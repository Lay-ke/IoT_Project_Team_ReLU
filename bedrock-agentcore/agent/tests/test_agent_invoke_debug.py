#!/usr/bin/env python3
"""
Debug script to see the actual response structure
"""

import boto3
import json

agent_arn = 'arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV'
region = 'eu-west-1'

client = boto3.client('bedrock-agentcore', region_name=region)

payload = {"prompt": "Hello"}

print("Invoking agent...")
response = client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    payload=json.dumps(payload).encode(),
    contentType='application/json',
    accept='application/json'
)

print("\nResponse keys:", response.keys())
print("\nFull response structure:")
for key, value in response.items():
    print(f"\n{key}: {type(value)}")
    if key != 'body':
        print(f"  Value: {value}")

if 'body' in response:
    print("\nReading body stream...")
    result_bytes = b''
    for chunk in response['body']:
        print(f"  Chunk type: {type(chunk)}, size: {len(chunk) if isinstance(chunk, bytes) else 'N/A'}")
        result_bytes += chunk
    
    print(f"\nTotal bytes: {len(result_bytes)}")
    print(f"Decoded: {result_bytes.decode()[:500]}")
