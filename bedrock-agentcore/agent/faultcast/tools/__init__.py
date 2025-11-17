"""Tool entrypoints aggregated for the FaultCast agent."""

from faultcast.tools.diagnostics import (
    analyze_anomaly,
    get_machine_status,
    get_sensor_readings,
)
from faultcast.tools.knowledge import (
    get_schedule_insights,
    search_maintenance_playbook,
    search_prediction_history,
)
from faultcast.tools.scheduling import (
    classify_fault_severity,
    count_scheduled_tasks,
    create_work_schedule,
    schedule_maintenance_from_prompt,
    send_notification_email,
)

__all__ = [
    "analyze_anomaly",
    "classify_fault_severity",
    "count_scheduled_tasks",
    "create_work_schedule",
    "get_machine_status",
    "get_schedule_insights",
    "get_sensor_readings",
    "schedule_maintenance_from_prompt",
    "search_maintenance_playbook",
    "search_prediction_history",
    "send_notification_email",
]
