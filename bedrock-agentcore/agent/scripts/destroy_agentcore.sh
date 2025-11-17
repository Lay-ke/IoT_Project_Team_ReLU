#!/bin/bash
# FaultCast Agent - AgentCore Destroy Script

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: destroy_agentcore.sh [options]

Options:
  -a, --agent NAME      Agent name defined in .bedrock_agentcore.yaml (defaults to default_agent)
  -r, --region REGION   Override AWS region from config
      --dry-run         Preview resources that would be deleted
  -f, --force           Skip confirmation prompt (passes --force to agentcore destroy)
      --delete-ecr      Also delete the ECR repository when destroying
      --skip-ssm        Do not remove the stored agent ARN from SSM Parameter Store
      --ssm-param PATH  Override the SSM parameter name (default: /faultcast/v2/agent-arn)
      --purge-local     Remove local AgentCore artifacts (.agentcore_build, deployment.zip, etc.)
  -h, --help            Show this help message and exit
EOF
}

FORCE_DESTROY=0
DRY_RUN=0
DELETE_ECR=0
PURGE_LOCAL=0
SKIP_SSM=0
AGENT_OVERRIDE=""
REGION_OVERRIDE=""
SSM_PARAM_NAME="/faultcast/v2/agent-arn"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -a|--agent)
            [[ $# -lt 2 ]] && { echo "Missing value for $1" >&2; usage; exit 1; }
            AGENT_OVERRIDE="$2"
            shift 2
            ;;
        -r|--region)
            [[ $# -lt 2 ]] && { echo "Missing value for $1" >&2; usage; exit 1; }
            REGION_OVERRIDE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -f|--force)
            FORCE_DESTROY=1
            shift
            ;;
        --delete-ecr)
            DELETE_ECR=1
            shift
            ;;
        --skip-ssm)
            SKIP_SSM=1
            shift
            ;;
        --ssm-param)
            [[ $# -lt 2 ]] && { echo "Missing value for $1" >&2; usage; exit 1; }
            SSM_PARAM_NAME="$2"
            shift 2
            ;;
        --purge-local)
            PURGE_LOCAL=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${PROJECT_ROOT}/.bedrock_agentcore.yaml"

if [[ ! -f "${PROJECT_ROOT}/faultcast_agentcore.py" ]]; then
    echo "❌ Unable to locate faultcast_agentcore.py. Run this script from within the agent project." >&2
    exit 1
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "❌ Missing .bedrock_agentcore.yaml. Deploy the agent at least once before running this destroy script." >&2
    exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
    echo "❌ AWS CLI not found in PATH. Install and configure AWS CLI before running this script." >&2
    exit 1
fi

# Resolve agentcore CLI path
if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/agentcore" ]]; then
    AGENTCORE_CLI="${VIRTUAL_ENV}/bin/agentcore"
elif [[ -x "${PROJECT_ROOT}/.venv/bin/agentcore" ]]; then
    AGENTCORE_CLI="${PROJECT_ROOT}/.venv/bin/agentcore"
elif command -v agentcore >/dev/null 2>&1; then
    AGENTCORE_CLI="$(command -v agentcore)"
else
    echo "❌ agentcore CLI not found. Install it with 'pip install bedrock-agentcore-starter-toolkit'." >&2
    exit 1
fi

PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "❌ Python interpreter '${PYTHON_BIN}' not found." >&2
    exit 1
fi

CONFIG_PY_OUTPUT=""
if ! CONFIG_PY_OUTPUT=$("${PYTHON_BIN}" - "$CONFIG_FILE" "$AGENT_OVERRIDE" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    sys.stderr.write("PyYAML is required to parse .bedrock_agentcore.yaml. Install it with 'pip install pyyaml'.\n")
    sys.exit(3)

config_path = Path(sys.argv[1])
agent_override = sys.argv[2] if len(sys.argv) > 2 else ""

try:
    data = yaml.safe_load(config_path.read_text()) or {}
except Exception as exc:  # pragma: no cover
    sys.stderr.write(f"Failed to read {config_path}: {exc}\n")
    sys.exit(4)

agents = data.get("agents") or {}
default_agent = data.get("default_agent") or ""

if agent_override:
    agent_key = agent_override
elif default_agent:
    agent_key = default_agent
elif agents:
    agent_key = next(iter(agents))
else:
    sys.stderr.write("No agents defined in .bedrock_agentcore.yaml\n")
    sys.exit(5)

if agent_key not in agents:
    options = ", ".join(sorted(agents.keys()))
    sys.stderr.write(f"Agent '{agent_key}' not found. Available agents: {options}\n")
    sys.exit(6)

agent_config = agents.get(agent_key) or {}
aws_cfg = agent_config.get("aws") or {}
agentcore_cfg = agent_config.get("bedrock_agentcore") or {}
memory_cfg = agent_config.get("memory") or {}

selected_agent = agent_key
region = str(aws_cfg.get("region") or "")
agent_arn = str(agentcore_cfg.get("agent_arn") or "")
memory_arn = str(memory_cfg.get("memory_arn") or "")
agent_display = str(agent_config.get("name") or agent_key)

print(selected_agent)
print(region)
print(agent_arn)
print(memory_arn)
print(agent_display)
PY
); then
    exit 1
fi

mapfile -t CONFIG_LINES <<<"${CONFIG_PY_OUTPUT}"
if [[ ${#CONFIG_LINES[@]} -lt 5 ]]; then
    echo "❌ Unable to parse configuration. Ensure .bedrock_agentcore.yaml is valid." >&2
    exit 1
fi

SELECTED_AGENT_KEY="${CONFIG_LINES[0]}"
CONFIG_REGION="${CONFIG_LINES[1]}"
AGENT_ARN="${CONFIG_LINES[2]}"
MEMORY_ARN="${CONFIG_LINES[3]}"
AGENT_DISPLAY_NAME="${CONFIG_LINES[4]}"

if [[ -n "${REGION_OVERRIDE}" ]]; then
    AWS_REGION="${REGION_OVERRIDE}"
else
    AWS_REGION="${CONFIG_REGION}"
fi

if [[ -z "${AWS_REGION}" ]]; then
    AWS_REGION="${AWS_DEFAULT_REGION:-${AWS_REGION:-}}"
fi

if [[ -z "${AWS_REGION}" ]]; then
    echo "❌ AWS region could not be determined. Provide --region or set AWS_DEFAULT_REGION." >&2
    exit 1
fi

if [[ -z "${AGENT_ARN}" ]]; then
    STATUS_OUTPUT="$(${AGENTCORE_CLI} status --agent "${SELECTED_AGENT_KEY}" 2>/dev/null || true)"
    AGENT_ARN="$(awk '/Agent ARN:/ {print $3; exit}' <<<"${STATUS_OUTPUT}")"
fi

if [[ -z "${AGENT_ARN}" ]]; then
    echo "⚠️  Unable to resolve Agent ARN automatically." >&2
    echo "    You may specify it manually via SSM or the AWS Console." >&2
fi

echo "======================================================================"
echo "FaultCast Agent - AWS Bedrock AgentCore Destroy"
echo "======================================================================"
echo "Agent key      : ${SELECTED_AGENT_KEY}"
echo "Display name   : ${AGENT_DISPLAY_NAME}"
echo "AWS region     : ${AWS_REGION}"
echo "Agent ARN      : ${AGENT_ARN:-<unknown>}"
if [[ -n "${MEMORY_ARN}" ]]; then
    echo "Memory ARN     : ${MEMORY_ARN}"
fi
echo "Dry run        : $([[ ${DRY_RUN} -eq 1 ]] && echo yes || echo no)"
if [[ ${DELETE_ECR} -eq 1 ]]; then
    echo "ECR cleanup    : enabled"
else
    echo "ECR cleanup    : disabled (use --delete-ecr to remove repository)"
fi
if [[ ${SKIP_SSM} -eq 1 ]]; then
    echo "SSM cleanup    : skipped"
else
    echo "SSM cleanup    : ${SSM_PARAM_NAME}"
fi
if [[ ${PURGE_LOCAL} -eq 1 ]]; then
    echo "Local artifacts: will be purged"
fi
echo "======================================================================"

if [[ ${FORCE_DESTROY} -eq 0 ]]; then
    read -r -p "Proceed with destroying these resources? (yes/no): " CONFIRM
    if [[ ! ${CONFIRM,,} =~ ^y(es)?$ ]]; then
        echo "Aborted by user."
        exit 0
    fi
fi

DESTROY_CMD=("${AGENTCORE_CLI}" "destroy" "--agent" "${SELECTED_AGENT_KEY}")
if [[ ${DRY_RUN} -eq 1 ]]; then
    DESTROY_CMD+=("--dry-run")
fi
if [[ ${FORCE_DESTROY} -eq 1 ]]; then
    DESTROY_CMD+=("--force")
fi
if [[ ${DELETE_ECR} -eq 1 ]]; then
    DESTROY_CMD+=("--delete-ecr-repo")
fi

echo "Running: ${DESTROY_CMD[*]}"
"${DESTROY_CMD[@]}"

echo ""
echo "AgentCore destroy command completed."

if [[ ${DRY_RUN} -eq 0 && ${SKIP_SSM} -eq 0 ]]; then
    echo "Removing cached SSM parameter (${SSM_PARAM_NAME}) if it exists..."
    if AWS_PAGER="" aws ssm get-parameter --name "${SSM_PARAM_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1; then
        if AWS_PAGER="" aws ssm delete-parameter --name "${SSM_PARAM_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1; then
            echo "✅ Removed SSM parameter ${SSM_PARAM_NAME}"
        else
            echo "⚠️  Unable to delete SSM parameter ${SSM_PARAM_NAME}" >&2
        fi
    else
        echo "SSM parameter ${SSM_PARAM_NAME} not found; skipping."
    fi
fi

if [[ ${DRY_RUN} -eq 0 && ${PURGE_LOCAL} -eq 1 ]]; then
    echo "Purging local AgentCore artifacts..."
    rm -rf "${PROJECT_ROOT}/.agentcore_build" \
           "${PROJECT_ROOT}/deployment.zip" \
           "${PROJECT_ROOT}/deployment_extracted"
    echo "✅ Removed local artifacts."
fi

echo ""
echo "======================================================================"
echo "✅ AgentCore resource cleanup finished."
echo "======================================================================"
echo ""
