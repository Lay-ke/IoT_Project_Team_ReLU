#!/bin/bash
# FaultCast Agent - AgentCore Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ! -f "${PROJECT_ROOT}/faultcast_agentcore.py" ]]; then
    echo "❌ Unable to locate faultcast_agentcore.py. Run this script from within the repo." >&2
    exit 1
fi

cd "${PROJECT_ROOT}"

SERVER_PID=""
cleanup() {
    if [[ -n "${SERVER_PID}" ]] && ps -p "${SERVER_PID}" > /dev/null 2>&1; then
        kill "${SERVER_PID}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

echo "======================================================================"
echo "FaultCast Agent - AWS Bedrock AgentCore Deployment"
echo "======================================================================"

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
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

# Step 3: Stage deployment bundle
echo ""
echo "Step 3: Preparing minimal deployment bundle..."
STAGING_DIR="${PROJECT_ROOT}/.agentcore_build"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

python - "$PROJECT_ROOT" "$STAGING_DIR" <<'PY'
import shutil
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
staging_dir = Path(sys.argv[2])
source = project_root / "faultcast"
destination = staging_dir / "faultcast"

if destination.exists():
    shutil.rmtree(destination)

ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
shutil.copytree(source, destination, ignore=ignore)
PY

cp "${PROJECT_ROOT}/faultcast_agentcore.py" "${STAGING_DIR}/"
cp "${PROJECT_ROOT}/agentcore-requirements.txt" "${STAGING_DIR}/"
if [[ -f "${PROJECT_ROOT}/__init__.py" ]]; then
    cp "${PROJECT_ROOT}/__init__.py" "${STAGING_DIR}/"
fi

echo "Deployment bundle size:"
du -sh "${STAGING_DIR}" 2>/dev/null || true

# Step 4: Test locally (optional)
echo ""
echo "Step 4: Would you like to test locally first? (y/n)"
read -r test_local

if [[ "${test_local}" == "y" ]]; then
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
    kill "${SERVER_PID}"
    SERVER_PID=""

    echo ""
    echo "Continue with deployment? (y/n)"
    read -r continue_deploy

    if [[ "${continue_deploy}" != "y" ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
fi

# Step 5: Configure AgentCore
echo ""
echo "Step 5: Configuring AgentCore deployment..."
agentcore configure \
    --entrypoint .agentcore_build/faultcast_agentcore.py \
    --deployment-type direct_code_deploy \
    --runtime PYTHON_3_12 \
    --requirements-file .agentcore_build/agentcore-requirements.txt

# Step 6: Deploy to AWS
echo ""
echo "Step 6: Deploying to AWS Bedrock AgentCore..."
echo "This will:"
echo "  - Package your agent"
echo "  - Create Docker image"
echo "  - Push to ECR"
echo "  - Deploy to AgentCore"
echo ""
echo "Proceed with deployment? (y/n)"
read -r proceed

if [[ "${proceed}" == "y" ]]; then
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
