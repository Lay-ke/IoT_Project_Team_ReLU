# FaultCast Agent – Predictive Maintenance on AWS Bedrock AgentCore

FaultCast is an end-to-end predictive maintenance solution for conveyor systems. It combines synthetic IoT telemetry, a trained ML classifier, and domain documentation to drive an intelligent Bedrock AgentCore runtime that can triage faults, run financial what-if analyses, and schedule maintenance crews.

This README is intentionally self-contained: it walks through the architecture, code layout, required infrastructure, deployment workflow, and operational commands so that a new engineer can replicate the full environment without searching for extra context.

---

## 1. Solution Overview

- **Single Bedrock AgentCore runtime** served by the entry point `faultcast_agentcore.py`
- **Six custom tools** (implemented with the Strands framework) that cover IoT telemetry queries, ML inference, anomaly triage, knowledge-base lookup, severity classification, and maintenance scheduling
- **Hybrid knowledge strategy**: real-time sensor data, ML predictions, and curated maintenance playbooks stored in an AWS Bedrock Knowledge Base
- **Automated financial analysis**: downstream evaluations weigh repair vs. replacement to generate a cost-efficient work order

The repository you are reading hosts the agent source (`bedrock-agentcore/agent`) and Terraform infrastructure (`bedrock-agentcore/terraform`). Supporting assets (frontend, ML training notebooks, etc.) live at the repository root.

---

## 2. Repository Layout (agent folder)

```
bedrock-agentcore/agent/
├── faultcast/                   # Python package with agent logic and utilities
│   ├── agents/                  # Strands agent + tool definitions
│   └── utils/                   # Data simulators, shared helpers
├── faultcast_agentcore.py       # Bedrock AgentCore entry point (main runtime)
├── agentcore-requirements.txt   # Deployment dependency lockfile
├── requirements.txt             # Runtime placeholder (vendored deps live in vendor/)
├── runtime-requirements.txt     # Notes for vendored deps
├── vendor/                      # Vendored wheel artifacts for cold-start safety
├── docs/                        # Agent-side documentation (invocation, architecture, etc.)
├── scripts/                     # Helper scripts (deploy, destroy, AWS helpers)
├── tests/                       # Local regression tests and samples
├── .agentcoreignore             # Explicit exclusions for packaged artifacts
├── .bedrock_agentcore.yaml      # Generated AgentCore config (per environment)
└── README.md                    # This document
```

> **Tip**: Inspect `docs/FAULTCAST_ARCHITECTURE.md` for diagrams and component-level design, and `docs/AGENT_INVOCATION_GUIDE.md` for example conversations.

---

## 3. Prerequisites

You will need:

1. **AWS account** with Bedrock AgentCore, Bedrock foundational models, SageMaker, S3, IoT Core, and Systems Manager access in your target region (defaults to `eu-west-1`).
2. **IAM permissions** to create/destroy the resources declared in `terraform/` (roles, policies, S3 buckets, knowledge base, etc.).
3. **Local tooling**:
   - Python 3.12 (matching the deployed runtime)
   - `python3 -m venv` or your preferred virtualenv tool
   - `pip` ≥ 24, `uv` is handled automatically by the CLI
   - Terraform ≥ 1.6
   - AWS CLI v2 with credentials configured (`aws configure sso` or key-based auth)
4. **AgentCore CLI**: installed automatically via `pip install bedrock-agentcore-starter-toolkit` in the steps below.

---

## 4. End-to-End Setup

Follow the steps in order; commands assume the repo root (`IoT_Project_Team_ReLU/`) as the starting directory.

### 4.1 Clone & bootstrap the Python environment

```bash
cd bedrock-agentcore/agent
python3 -m venv ../.venv
source ../.venv/bin/activate
python -m pip install --upgrade pip
pip install -r agentcore-requirements.txt
pip install bedrock-agentcore-starter-toolkit
```

The deployment dependencies (Strands, Bedrock AgentCore SDK, telemetry tooling) are intentionally installed into `.venv/`. The `.agentcoreignore` file prevents the virtual environment from being bundled into the artifact.

### 4.2 Provision infrastructure with Terraform

Terraform modules under `bedrock-agentcore/terraform/` create:

- Agent execution IAM roles and policies
- Bedrock Knowledge Base and S3 sync bucket
- Optional OpenSearch Serverless collection for knowledge-grounding
- SSM parameters storing shared IDs (agent ARN, KB ID, etc.)

Run:

```bash
cd ../terraform
terraform init
terraform apply -var-file="environments/dev/terraform.tfvars"
```

Key outputs:

- `agentcore_execution_role_arn`
- `knowledge_base_id`
- `work_schedule_bucket`
- Optional IoT/SageMaker endpoints depending on enabled modules

The deploy script (`terraform/scripts/deploy.sh`) also materialises `.bedrock_agentcore.yaml` from the template by injecting the Terraform outputs.

### 4.3 Generate the AgentCore config (if not using the deploy script)

If you prefer manual control:

```bash
cd ../agent

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-eu-west-1}
AGENTCORE_ROLE_ARN=$(cd ../terraform && terraform output -raw agentcore_execution_role_arn)

sed -e "s|{{AGENT_ENTRYPOINT}}|$(pwd)/faultcast_agentcore.py|g" \
    -e "s|{{SOURCE_PATH}}|$(pwd)|g" \
    -e "s|{{EXECUTION_ROLE_ARN}}|$AGENTCORE_ROLE_ARN|g" \
    -e "s|{{AWS_ACCOUNT_ID}}|$AWS_ACCOUNT_ID|g" \
    -e "s|{{AWS_REGION}}|$AWS_REGION|g" \
    -e "s|{{ECR_REPOSITORY}}|${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-faultcast|g" \
    .bedrock_agentcore.yaml.template > .bedrock_agentcore.yaml
```

The resulting config is consumed by the AgentCore CLI and should not be checked into version control.

### 4.4 Deploy the agent runtime

```bash
cd bedrock-agentcore/agent
source ../.venv/bin/activate
agentcore launch --force-rebuild-deps
```

What happens:

1. Dependencies are rebuilt for `manylinux2014_aarch64` (matching Bedrock’s Python 3.12 environment).
2. Source files are packaged, excluding paths listed in `.agentcoreignore`.
3. The zipped bundle is uploaded to the S3 bucket defined in `.bedrock_agentcore.yaml`.
4. AgentCore updates or creates the runtime `faultcast_agentcore` and warms the endpoint.

Successful deployment prints the agent ARN and CloudWatch log groups. Typical artifact size is < 5 MB; if you see the 750 MB limit error, re-run `git clean -fdX` or verify the ignore file excludes any terraform caches or local virtualenvs.

---

## 5. Operating the Agent

### 5.1 Status & invocation

```bash
agentcore status
agentcore invoke '{"prompt": "Check conveyor-A001"}'
```

Both commands respect the `default_agent` defined in `.bedrock_agentcore.yaml`. To list or switch agents, use `agentcore configure list` and `agentcore configure set-default`.

### 5.2 Programmatic invocation (Python)

```python
import boto3
import json

AGENT_ARN = "arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/faultcast_agentcore-bCrmIP2KZa"

client = boto3.client("bedrock-agentcore", region_name="eu-west-1")



response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_ARN,
    payload=json.dumps(payload).encode("utf-8"),
    contentType="application/json",
    accept="application/json",
)

print(json.loads(response["response"].read()))
```

For structured payloads (e.g., ML prediction uploads), send the JSON schema expected by the relevant tool. Refer to `faultcast/utils/data_simulator.py` for sample inputs.

### 5.3 Observability

- **CloudWatch Logs**: `/aws/bedrock-agentcore/runtimes/<agent-name>-DEFAULT`
- **OpenTelemetry traces**: Enabled automatically; the CLI registers the GenAI Observability dashboard URL on each deploy.
- Tail logs locally:

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/faultcast_agentcore-bCrmIP2KZa-DEFAULT \
  --region eu-west-1 \
  --since 10m \
  --log-stream-name-prefix "$(date +%Y/%m/%d)/[runtime-logs"
```

### 5.4 Teardown

To cleanly remove agent resources while leaving Terraform stacks intact:

```bash
./scripts/destroy_agentcore.sh --force --delete-ecr --purge-local
```

The script uses `agentcore destroy` under the hood, deletes the cached SSM agent ARN, and removes packaged artifacts. To drop infrastructure as well, run `terraform destroy` in `bedrock-agentcore/terraform`.

---

## 6. Agent Internals

### 6.1 Tooling stack

| Tool | Module | Purpose |
|------|--------|---------|
| `get_sensor_readings` | `faultcast.agents.faultcast_maintenance_agent` | Streams latest simulated telemetry for a conveyor ID |
| `search_prediction_history` | same | Queries historical ML inference records |
| `analyze_anomaly` | same | Runs anomaly heuristics and surfaces root causes |
| `search_maintenance_playbook` | Knowledge base bridge | Retrieves maintenance SOPs from Bedrock KB |
| `classify_fault_severity` | ML classifier wrapper | Maps anomalies to severity tiers using `ml_model/inference.py` |
| `create_work_schedule` | Scheduler module | Generates work orders, labour estimates, and financial breakdown |

All tools are orchestrated via Strands’ agent runtime (`strands-agents` and `strands-agents-tools` packages). See `faultcast/agents/faultcast_maintenance_agent.py` for the central agent definition.

### 6.2 Data & ML components

- Raw conveyor sensor CSVs: `ml_model/raw_dataset/conveyor_fault_dataset.csv`
- Training script: `ml_model/train .py`
- Inference module used by the agent: `ml_model/inference.py`
- Synthetic data generator: `faultcast/utils/data_simulator.py`

The Terraform stack provisions a SageMaker endpoint or optionally relies on local inference (depending on parameters). Update `.env` and SSM parameters if you relocate the model.

### 6.3 Knowledge base

Terraform creates an S3 bucket and knowledge base resource. Upload manuals/playbooks to `s3://predictive-maintenance-feature-store/knowledge-base-inference/` (default path) and trigger ingestion:

```bash
KB_ID=$(aws ssm get-parameter --name /faultcast/v2/knowledge-base-id --query Parameter.Value --output text --region eu-west-1)
DS_ID=$(aws bedrock-agent list-data-sources --knowledge-base-id "$KB_ID" --region eu-west-1 --query 'dataSourceSummaries[0].dataSourceId' --output text)
aws bedrock-agent start-ingestion-job --knowledge-base-id "$KB_ID" --data-source-id "$DS_ID" --region eu-west-1
```

---

## 7. Testing & Local Development

1. **Runtime smoke tests**: `python tests/test_local_agent.py`
2. **Schedule formatting test**: `python tests/test_work_schedule_workflow.py`
3. **Agent invocation harness**: `python tests/test_agent_invoke.py` (calls the local entry point in-process).

When iterating:

- Keep `vendor/` minimal; only vend dependencies that are not easily cross-compiled.
- Use `.agentcoreignore` to exclude local caches (e.g., `deployment_extracted/`, `.terraform/`). Updates to this file are crucial to keep the artifact below the 750 MB extraction cap.
- Run `agentcore launch --force-rebuild-deps` after dependency changes to ensure the dependency layer reflects your updates.

---

## 8. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `The extracted artifact size exceeds the allowed limit of 750MB` | Local caches or virtualenvs bundled | Delete `deployment_extracted/`, ensure `.agentcoreignore` includes `terraform/.terraform`, `.venv/`, `vendor` only if required |
| `The specified entrypoint could not be found` | `.bedrock_agentcore.yaml` has stale `entrypoint` or `source_path` | Regenerate the config (Section 4.3) so it points to `.../bedrock-agentcore/agent/` |
| `agentcore` CLI missing | Virtualenv not activated or toolkit not installed | Activate `.venv` and run `pip install bedrock-agentcore-starter-toolkit` |
| Knowledge base returns no documents | Ingestion not run or KB ID missing | Use the ingestion command above and verify `/faultcast/v2/knowledge-base-id` in SSM |
| Tests cannot import modules | PYTHONPATH does not include repo root | Run tests from `bedrock-agentcore/agent` with the virtualenv activated |

For deeper debugging, tail the CloudWatch logs and use `agentcore launch --force-rebuild-deps --auto-update-on-conflict` when adjusting tools.

---

## 9. Maintenance & Support

- **Teardown**: `./scripts/destroy_agentcore.sh` for runtime cleanup, `terraform destroy` for infrastructure.
- **Updating dependencies**: adjust `agentcore-requirements.txt`, reinstall inside `.venv`, then re-run `agentcore launch --force-rebuild-deps`.
- **Extending tools**: add new Strands tools inside `faultcast/agents/`, register them in the agent configuration, and update the relevant documentation in `docs/`.
- **Support**: create a GitHub issue or contact the maintainers listed in `docs/DEPLOYMENT_STATUS.md`.

Happy building! The combination of Terraform-managed infrastructure, reproducible packaging, and the documented workflows above should let you recreate the FaultCast deployment from scratch, adapt it to new conveyor lines, or repurpose the agent skeleton for other predictive maintenance domains.
