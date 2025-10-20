#!/bin/bash
# FaultCast Agent - AgentCore Deployment Script

set -e

echo "======================================================================"
echo "FaultCast Agent - AWS Bedrock AgentCore Deployment"
echo "======================================================================"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source faultcast-env/bin/activate"
    exit 1
fi

# Step 1: Install AgentCore SDK
echo ""
echo "Step 1: Installing AgentCore SDK..."
pip install bedrock-agentcore bedrock-agentcore-starter-toolkit

# Step 2: Install requirements
echo ""
echo "Step 2: Installing agent requirements..."
pip install -r agentcore-requirements.txt

# Step 3: Test locally (optional)
echo ""
echo "Step 3: Would you like to test locally first? (y/n)"
read -r test_local

if [[ "$test_local" == "y" ]]; then
    echo "Starting local test server..."
    echo "Press Ctrl+C to stop and continue with deployment"
    python faultcast_agentcore.py &
    SERVER_PID=$!
    
    sleep 3
    
    echo ""
    echo "Testing agent..."
    curl -X POST http://localhost:8080/invocations \
      -H "Content-Type: application/json" \
      -d '{"prompt": "Hello, are you working?"}' \
      || echo "Test failed - check if server started correctly"
    
    echo ""
    echo "Stopping test server..."
    kill $SERVER_PID
    
    echo ""
    echo "Continue with deployment? (y/n)"
    read -r continue_deploy
    
    if [[ "$continue_deploy" != "y" ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
fi

# Step 4: Configure AgentCore
echo ""
echo "Step 4: Configuring AgentCore deployment..."
agentcore configure --entrypoint faultcast_agentcore.py

# Step 5: Deploy to AWS
echo ""
echo "Step 5: Deploying to AWS Bedrock AgentCore..."
echo "This will:"
echo "  - Package your agent"
echo "  - Create Docker image"
echo "  - Push to ECR"
echo "  - Deploy to AgentCore"
echo ""
echo "Proceed with deployment? (y/n)"
read -r proceed

if [[ "$proceed" == "y" ]]; then
    agentcore launch
    
    echo ""
    echo "======================================================================"
    echo "✅ Deployment Complete!"
    echo "======================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Test your agent:"
    echo "     agentcore invoke '{\"prompt\": \"Check conveyor-A001\"}'"
    echo ""
    echo "  2. View logs in CloudWatch"
    echo ""
    echo "  3. Enable observability (see FAULTCAST_AGENTCORE_DEPLOYMENT.md)"
    echo ""
    echo "======================================================================"
else
    echo "Deployment cancelled"
    exit 0
fi
