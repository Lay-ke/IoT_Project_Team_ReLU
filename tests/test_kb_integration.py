#!/usr/bin/env python3
"""
Test script for Knowledge Base integration
Run this to verify KB connectivity and search functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)
print(f"DEBUG: Loaded KNOWLEDGE_BASE_ID: {os.getenv('KNOWLEDGE_BASE_ID', 'NOT SET')}")
print(f"DEBUG: Loaded AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID', 'NOT SET')[:10]}...")
print()

def test_kb_configuration():
    """Test if KB environment variables are set"""
    print("=" * 70)
    print("Testing Knowledge Base Configuration")
    print("=" * 70)
    
    kb_id = os.getenv('KNOWLEDGE_BASE_ID', '')
    kb_region = os.getenv('KNOWLEDGE_BASE_REGION', 'eu-west-1')
    
    print(f"\nKNOWLEDGE_BASE_ID: {'✅ Set' if kb_id else '❌ Not set'}")
    print(f"KNOWLEDGE_BASE_REGION: {kb_region}")
    
    if not kb_id:
        print("\n⚠️  Warning: KNOWLEDGE_BASE_ID not set!")
        print("Set it in your .env file or environment:")
        print("  export KNOWLEDGE_BASE_ID='your-kb-id-here'")
        return False
    
    return True


def test_boto3_import():
    """Test if boto3 is available"""
    print("\n" + "=" * 70)
    print("Testing boto3 Installation")
    print("=" * 70)
    
    try:
        import boto3
        print("\n✅ boto3 is installed")
        print(f"   Version: {boto3.__version__}")
        return True
    except ImportError:
        print("\n❌ boto3 not found!")
        print("Install it with: pip install boto3")
        return False


def test_kb_connection():
    """Test connection to Knowledge Base"""
    print("\n" + "=" * 70)
    print("Testing Knowledge Base Connection")
    print("=" * 70)
    
    try:
        import boto3
        
        kb_id = os.getenv('KNOWLEDGE_BASE_ID', '')
        kb_region = os.getenv('KNOWLEDGE_BASE_REGION', 'eu-west-1')
        
        if not kb_id:
            print("\n⚠️  Skipping connection test - KB_ID not set")
            return False
        
        client = boto3.client('bedrock-agent-runtime', region_name=kb_region)
        
        # Try a simple query
        print(f"\nAttempting to query KB: {kb_id}")
        print(f"Region: {kb_region}")
        
        response = client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': 'test query'},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 1
                }
            }
        )
        
        results = response.get('retrievalResults', [])
        print(f"\n✅ Connection successful!")
        print(f"   Retrieved {len(results)} result(s)")
        
        if results:
            print("\n   Sample result:")
            print(f"   Score: {results[0].get('score', 0.0):.4f}")
            content = results[0].get('content', {}).get('text', '')
            print(f"   Content preview: {content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nPossible issues:")
        print("  - Invalid KNOWLEDGE_BASE_ID")
        print("  - Insufficient IAM permissions")
        print("  - KB not in specified region")
        print("  - AWS credentials not configured")
        return False


def test_agent_tool():
    """Test the search_prediction_history tool"""
    print("\n" + "=" * 70)
    print("Testing Agent Tool")
    print("=" * 70)
    
    try:
        # Import the tool
        sys.path.insert(0, 'faultcast/agents')
        from faultcast_maintenance_agent import search_prediction_history, KB_AVAILABLE
        
        print(f"\n✅ Tool imported successfully")
        print(f"   KB Available: {KB_AVAILABLE}")
        
        if not KB_AVAILABLE:
            print("\n⚠️  KB not configured - tool will return error message")
        
        # Test the tool
        print("\nTesting tool with machine_id='conveyor-A001'...")
        result = search_prediction_history(machine_id="conveyor-A001", query="")
        
        if 'error' in result:
            print(f"\n⚠️  Tool returned error: {result.get('message', 'Unknown error')}")
        else:
            print(f"\n✅ Tool executed successfully!")
            print(f"   Predictions found: {result.get('predictions_found', 0)}")
            
            if result.get('predictions'):
                print("\n   First prediction:")
                pred = result['predictions'][0]
                print(f"   Score: {pred.get('score', 0.0):.4f}")
                print(f"   Content preview: {pred.get('content', '')[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Tool test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🔧 FaultCast Knowledge Base Integration Test")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_kb_configuration()))
    results.append(("boto3 Installation", test_boto3_import()))
    results.append(("KB Connection", test_kb_connection()))
    results.append(("Agent Tool", test_agent_tool()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Knowledge Base integration is ready.")
    else:
        print("\n⚠️  Some tests failed. Review the output above for details.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
