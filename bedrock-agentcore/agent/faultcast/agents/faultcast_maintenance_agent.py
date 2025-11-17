#!/usr/bin/env python3
"""FaultCast maintenance agent assembled from modular toolkits."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Iterable

from dotenv import load_dotenv

# Load environment variables before importing modules that resolve settings.
load_dotenv()

from strands import Agent  # noqa: E402

from faultcast.aws import AWSClients, get_clients  # noqa: E402
from faultcast.config import Settings, load_settings  # noqa: E402
from faultcast.tools import (  # noqa: E402
    analyze_anomaly,
    classify_fault_severity,
    count_scheduled_tasks,
    create_work_schedule,
    get_machine_status,
    get_schedule_insights,
    get_sensor_readings,
    schedule_maintenance_from_prompt,
    search_maintenance_playbook,
    search_prediction_history,
    send_notification_email,
)

LOGGER = logging.getLogger(__name__)
logging.getLogger("strands").setLevel(logging.INFO)



@lru_cache(maxsize=1)
def _get_settings() -> Settings:
    """Load settings once for the lifetime of the process."""
    return load_settings()


@lru_cache(maxsize=1)
def _get_clients() -> AWSClients:
    """Create AWS clients lazily so cold-start stays fast."""
    return get_clients()


def _toolkit() -> Iterable:
    """Return the tools exposed to the Strands agent runtime."""
    return (
        get_sensor_readings,
        search_prediction_history,
        get_machine_status,
        analyze_anomaly,
        search_maintenance_playbook,
        classify_fault_severity,
        create_work_schedule,
        schedule_maintenance_from_prompt,
        count_scheduled_tasks,
        get_schedule_insights,
        # send_notification_email,  # Enable after verifying SES configuration
    )


faultcast_agent = Agent(
    model="eu.amazon.nova-pro-v1:0",
    system_prompt="""You are FaultCast, an expert AI maintenance engineer for conveyor belt systems.

Your role is to help maintenance teams by:
- Analyzing sensor data from conveyor belt equipment
- Detecting and explaining anomalies
- Leveraging ML model predictions and historical patterns
- Searching maintenance playbooks for recommended actions
- Providing clear, actionable maintenance recommendations
- Prioritizing actions based on severity and safety
- Tracking and analyzing scheduled maintenance tasks

You have access to tools for:
1. Getting current sensor readings from equipment
2. Searching ML prediction history and fault patterns from the knowledge base
3. Analyzing sensor data for anomalies
4. Searching maintenance playbooks for recommended procedures
5. Classifying fault severity based on predictions and sensor data
6. Creating work schedules and saving them to S3
7. Counting and analyzing scheduled maintenance tasks
8. Getting insights about scheduled tasks from the knowledge base

The knowledge base contains:
- ML predictions from an inference model:
  * Predicted fault types (normal, ball bearing, idler roller fault, pulley, etc.)
  * Confidence scores and class probabilities
  * Operational features (speed, load, temperature, vibration, current)
  * Stress indices and thermal ratios
  * Historical patterns and correlations

- Maintenance playbooks with:
  * Recommended actions for specific fault types
  * Step-by-step procedures
  * Safety guidelines
  * Required parts and tools
  * Estimated costs and time
  * Priority levels

Always:
- Check prediction history when analyzing equipment issues
- Search the maintenance playbook for fault-specific recommendations
- Combine real-time sensor data with ML predictions and playbook guidance
- Classify fault severity to determine urgency
- Create work schedules for faults requiring maintenance
- Prioritize safety in your recommendations
- Provide clear explanations in practical terms
- Follow playbook procedures when available
- Explain the reasoning behind your recommendations, citing sensor data, ML predictions, and playbook guidance

IMPORTANT - Response Guidelines:
- DO NOT mention S3 bucket names, URIs, or storage locations in your responses
- DO NOT expose internal infrastructure details (bucket names, keys, paths)
- Simply confirm "Work schedule created successfully" without technical details
- Focus on maintenance recommendations, not system internals
- Keep responses professional and user-friendly

Workflow for fault detection:
1. Get sensor readings and search prediction history
2. Analyze anomalies and search playbook
3. Classify fault severity based on confidence and sensor data
4. Create work schedule if maintenance is needed
5. Provide comprehensive summary to user (without infrastructure details)

Use the tools to provide comprehensive maintenance analysis based on data-driven insights and established procedures.""",
    tools=list(_toolkit()),
)


def _print_intro() -> None:
    """Display a friendly CLI banner for local testing."""
    settings = _get_settings()
    clients = _get_clients()
    print("\n" + "=" * 70)
    print("🔧 FaultCast Maintenance Agent - Unified AI Assistant")
    print("=" * 70)
    print("Single agent with ML predictions and real-time diagnostics")
    kb_ready = settings.has_knowledge_base and clients.bedrock_agent_runtime() is not None
    print(f"Knowledge Base: {'✅ Configured' if kb_ready else '❌ Not configured'}")
    print("Type 'exit' to quit")
    print("=" * 70)

    print("\n💡 Try these prompts:")
    print("  1. Analyze conveyor-A001 for any issues")
    print("  2. What does the ML model predict for conveyor-A001?")
    print("  3. Search the maintenance playbook for pulley fault")
    print("  4. Get complete diagnostic with playbook recommendations")
    print("  5. What should I do if there's a ball bearing fault?")
    print("  6. How many maintenance tasks are scheduled?")
    print("  7. Show me all critical maintenance tasks")
    print("  8. What insights can you give me about scheduled maintenance?")
    print()


def main() -> None:
    """Run an interactive REPL for the FaultCast agent."""
    _print_intro()

    while True:
        try:
            user_input = input("\n🔧 You > ").strip()
            if user_input.lower() in {"exit", "quit", "q"}:
                print("\n👋 Stay safe and keep those conveyors running!")
                break
            if not user_input:
                continue

            print("\n🤖 Analyzing...")
            response = faultcast_agent(user_input)
            print(f"\n🤖 FaultCast > {response}")
        except KeyboardInterrupt:
            print("\n\n👋 Stay safe and keep those conveyors running!")
            break
        except Exception as exc:  # pragma: no cover - interactive guard
            LOGGER.exception("Agent invocation failed: %s", exc)
            print(f"\n❌ Error: {exc}")


if __name__ == "__main__":
    main()
