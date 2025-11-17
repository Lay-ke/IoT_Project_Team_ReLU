#!/usr/bin/env python3
"""
Test script to verify SSM Parameter Store configuration loading
"""

import boto3
import os
from botocore.exceptions import ClientError

def test_ssm_access():
    """Test if we can access SSM parameters"""
    print("="*70)
    print("Testing SSM Parameter Store Access")
    print("="*70)
    
    region = os.getenv('AWS_REGION', 'eu-west-1')
    print(f"\nRegion: {region}")
    
    try:
        ssm = boto3.client('ssm', region_name=region)
        
        # Test 1: Get parameters by path
        print("\n[Test 1] Getting parameters by path: /faultcast")
        response = ssm.get_parameters_by_path(
            Path='/faultcast',
            Recursive=True,
            WithDecryption=True
        )
        
        if response['Parameters']:
            print(f"✅ Successfully retrieved {len(response['Parameters'])} parameters")
            print("\nParameters found:")
            for param in response['Parameters']:
                param_name = param['Name'].split('/')[-1]
                param_value = param['Value']
                print(f"  - {param_name}: {param_value}")
        else:
            print("⚠️  No parameters found at /faultcast")
            return False
        
        # Test 2: Set environment variables
        print("\n[Test 2] Setting environment variables from SSM")
        for param in response['Parameters']:
            param_name = param['Name'].split('/')[-1]
            param_value = param['Value']
            env_var_name = param_name.upper().replace('-', '_')
            os.environ[env_var_name] = param_value
            print(f"  ✅ Set {env_var_name} = {param_value}")
        
        # Test 3: Verify environment variables
        print("\n[Test 3] Verifying environment variables")
        required_vars = [
            'KNOWLEDGE_BASE_ID',
            'KNOWLEDGE_BASE_REGION',
            'WORK_SCHEDULE_BUCKET',
            'WORK_SCHEDULE_PREFIX'
        ]
        
        all_set = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                print(f"  ✅ {var} = {value}")
            else:
                print(f"  ❌ {var} is not set")
                all_set = False
        
        if all_set:
            print("\n✅ All required environment variables are set!")
            return True
        else:
            print("\n❌ Some environment variables are missing")
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"\n❌ AWS Error: {error_code}")
        print(f"   Message: {error_msg}")
        
        if error_code == 'AccessDeniedException':
            print("\n💡 Solution:")
            print("   1. Ensure IAM role/user has ssm:GetParametersByPath permission")
            print("   2. Wait 5-10 minutes for IAM changes to propagate")
            print("   3. Verify the policy is attached to the correct role")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

def test_individual_parameters():
    """Test accessing individual parameters"""
    print("\n" + "="*70)
    print("Testing Individual Parameter Access")
    print("="*70)
    
    region = os.getenv('AWS_REGION', 'eu-west-1')
    ssm = boto3.client('ssm', region_name=region)
    
    parameters = [
        '/faultcast/knowledge-base-id',
        '/faultcast/knowledge-base-region',
        '/faultcast/work-schedule-bucket',
        '/faultcast/work-schedule-prefix'
    ]
    
    success_count = 0
    for param_name in parameters:
        try:
            response = ssm.get_parameter(Name=param_name)
            value = response['Parameter']['Value']
            print(f"✅ {param_name}: {value}")
            success_count += 1
        except ClientError as e:
            print(f"❌ {param_name}: {e.response['Error']['Code']}")
    
    print(f"\n{success_count}/{len(parameters)} parameters accessible")
    return success_count == len(parameters)

def test_iam_role():
    """Test current IAM identity"""
    print("\n" + "="*70)
    print("Testing IAM Identity")
    print("="*70)
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"\nCurrent IAM Identity:")
        print(f"  Account: {identity['Account']}")
        print(f"  User/Role ARN: {identity['Arn']}")
        print(f"  User ID: {identity['UserId']}")
        
        return True
    except Exception as e:
        print(f"❌ Error getting IAM identity: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n🔍 FaultCast SSM Configuration Test\n")
    
    # Test IAM identity
    test_iam_role()
    
    # Test SSM access
    ssm_success = test_ssm_access()
    
    # Test individual parameters
    individual_success = test_individual_parameters()
    
    # Final summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    if ssm_success and individual_success:
        print("\n✅ All tests passed!")
        print("   The agent should be able to load SSM configuration successfully.")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        print("   The agent may not be able to load SSM configuration.")
        print("\n💡 Next steps:")
        print("   1. Check IAM permissions")
        print("   2. Wait for IAM propagation (5-10 minutes)")
        print("   3. Verify SSM parameters exist")
        return 1

if __name__ == "__main__":
    exit(main())
