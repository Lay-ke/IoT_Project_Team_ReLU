#!/usr/bin/env python3
"""
AWS Setup and Verification Script for FaultCast Multi-Agent System
"""

import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

def setup_aws_credentials():
    """Setup and verify AWS credentials"""
    load_dotenv()
    
    print("🔧 Setting up AWS credentials...")
    
    # Check if credentials are available
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            print("❌ No AWS credentials found!")
            print("Please set up your credentials using one of these methods:")
            print("1. AWS CLI: aws configure")
            print("2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            print("3. IAM roles (for EC2 instances)")
            print("4. Copy .env.example to .env and fill in your credentials")
            return False
            
        print("✅ AWS credentials found")
        return True
        
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        return False

def verify_bedrock_access():
    """Verify access to AWS Bedrock service"""
    print("🔧 Verifying AWS Bedrock access...")
    
    try:
        bedrock = boto3.client('bedrock', region_name=os.getenv('BEDROCK_REGION', 'us-east-1'))
        
        # List available foundation models
        response = bedrock.list_foundation_models()
        
        # Check if Nova models are available
        nova_models = [model for model in response['modelSummaries'] 
                      if 'nova' in model['modelId'].lower()]
        
        if nova_models:
            print("✅ AWS Bedrock access verified")
            print(f"✅ Found {len(nova_models)} Nova models available")
            for model in nova_models[:3]:  # Show first 3
                print(f"   - {model['modelId']}")
        else:
            print("⚠️  Bedrock accessible but no Nova models found")
            print("   Available models:")
            for model in response['modelSummaries'][:3]:
                print(f"   - {model['modelId']}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnauthorizedOperation':
            print("❌ Access denied to Bedrock. Please check IAM permissions.")
        elif error_code == 'AccessDenied':
            print("❌ Access denied to Bedrock. Please request access to Bedrock service.")
        else:
            print(f"❌ Bedrock error: {e}")
        return False
        
    except NoCredentialsError:
        print("❌ No AWS credentials configured for Bedrock access")
        return False
        
    except Exception as e:
        print(f"❌ Error accessing Bedrock: {e}")
        return False

def verify_other_aws_services():
    """Verify access to other required AWS services"""
    print("🔧 Verifying other AWS services...")
    
    services_to_check = [
        ('dynamodb', 'DynamoDB'),
        ('lambda', 'Lambda'),
        ('s3', 'S3')
    ]
    
    results = {}
    
    for service_name, display_name in services_to_check:
        try:
            client = boto3.client(service_name)
            
            if service_name == 'dynamodb':
                client.list_tables()
            elif service_name == 'lambda':
                client.list_functions(MaxItems=1)
            elif service_name == 's3':
                client.list_buckets()
                
            print(f"✅ {display_name} access verified")
            results[service_name] = True
            
        except ClientError as e:
            print(f"⚠️  {display_name} access limited: {e.response['Error']['Code']}")
            results[service_name] = False
        except Exception as e:
            print(f"❌ {display_name} error: {e}")
            results[service_name] = False
    
    return results

def main():
    """Main setup function"""
    print("🚀 FaultCast Multi-Agent System - AWS Setup")
    print("=" * 50)
    
    # Step 1: Check credentials
    if not setup_aws_credentials():
        return False
    
    # Step 2: Verify Bedrock access
    bedrock_ok = verify_bedrock_access()
    
    # Step 3: Verify other services
    services_ok = verify_other_aws_services()
    
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    print(f"   AWS Credentials: ✅")
    print(f"   Bedrock Access: {'✅' if bedrock_ok else '❌'}")
    
    for service, status in services_ok.items():
        print(f"   {service.upper()}: {'✅' if status else '⚠️'}")
    
    if bedrock_ok:
        print("\n🎉 AWS setup completed successfully!")
        print("You can now proceed with agent development.")
    else:
        print("\n⚠️  Setup completed with warnings.")
        print("Please resolve Bedrock access issues before proceeding.")
    
    return bedrock_ok

if __name__ == "__main__":
    main()