"""Scheduling and notification tools for the FaultCast agent."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict

from strands import tool

from faultcast.aws import get_clients

try:  # pragma: no cover - optional dependency
    from dateutil import parser as date_parser  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    date_parser = None  # type: ignore


LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_clients():
    """Return cached AWS clients for runtime tool use."""
    return get_clients()


def _get_settings():
    return _get_clients().settings

_COST_DATABASE: Dict[str, Dict[str, float]] = {
    "ball bearing": {
        "repair_cost": 350,
        "replacement_cost": 800,
        "repair_duration_hours": 4,
        "replacement_duration_hours": 6,
        "downtime_cost_per_hour": 500,
    },
    "pulley": {
        "repair_cost": 400,
        "replacement_cost": 1200,
        "repair_duration_hours": 5,
        "replacement_duration_hours": 8,
        "downtime_cost_per_hour": 600,
    },
    "idler roller fault": {
        "repair_cost": 250,
        "replacement_cost": 600,
        "repair_duration_hours": 3,
        "replacement_duration_hours": 5,
        "downtime_cost_per_hour": 400,
    },
    "drive motor": {
        "repair_cost": 800,
        "replacement_cost": 2500,
        "repair_duration_hours": 8,
        "replacement_duration_hours": 12,
        "downtime_cost_per_hour": 800,
    },
    "belt slippage": {
        "repair_cost": 150,
        "replacement_cost": 400,
        "repair_duration_hours": 2,
        "replacement_duration_hours": 4,
        "downtime_cost_per_hour": 300,
    },
    "central shaft": {
        "repair_cost": 600,
        "replacement_cost": 1800,
        "repair_duration_hours": 6,
        "replacement_duration_hours": 10,
        "downtime_cost_per_hour": 700,
    },
    "unknown": {
        "repair_cost": 300,
        "replacement_cost": 800,
        "repair_duration_hours": 4,
        "replacement_duration_hours": 6,
        "downtime_cost_per_hour": 400,
    },
}


def _normalize_fault_type(fault_type: str) -> str:
    if not fault_type:
        return "unspecified"
    lowered = fault_type.lower()
    if lowered in {"unknown", "none", ""}:
        return "unspecified"
    if lowered in {"normal", "no fault"}:
        return "normal"
    return lowered


@tool
def classify_fault_severity(
    fault_type: str,
    confidence_score: float,
    sensor_readings: dict | None = None,
) -> dict:
    """Classify the severity of a predicted fault based on confidence and sensor data."""
    if confidence_score < 0.4:
        return {
            "fault_type": fault_type,
            "confidence_score": confidence_score,
            "severity": "below_threshold",
            "priority": "no_action",
            "create_schedule": False,
            "message": f"Confidence score {confidence_score:.2%} is below 0.4 threshold. No schedule will be created.",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    normalized_fault = _normalize_fault_type(fault_type)
    if normalized_fault == "normal":
        return {
            "fault_type": fault_type,
            "confidence_score": confidence_score,
            "severity": "normal",
            "priority": "no_action",
            "create_schedule": False,
            "message": "No fault detected. No schedule will be created.",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    if confidence_score >= 0.8:
        severity = "critical"
        priority = "immediate"
        urgency_hours = 24
    else:
        severity = "monitor"
        priority = "scheduled"
        urgency_hours = 168

    if sensor_readings:
        sensors = sensor_readings.get("sensors", {})
        if sensors.get("temperature", 0) > 90 or sensors.get("vibration", 0) > 4.0:
            severity = "critical"
            priority = "immediate"
            urgency_hours = 24 if sensors.get("vibration", 0) <= 4.0 else 12
        elif sensors.get("temperature", 0) > 80 or sensors.get("vibration", 0) > 3.0:
            severity = "critical"
            priority = "within_24_hours"
            urgency_hours = 24

    action_required_by = datetime.utcnow() + timedelta(hours=urgency_hours)

    return {
        "fault_type": fault_type,
        "confidence_score": confidence_score,
        "severity": severity,
        "priority": priority,
        "urgency_hours": urgency_hours,
        "create_schedule": True,
        "action_required_by": action_required_by.isoformat() + "Z",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@tool
def create_work_schedule(
    machine_id: str,
    fault_classification: dict,
    playbook_recommendations: dict | None = None,
) -> dict:
    """Create a maintenance work schedule and persist it to S3."""
    if not fault_classification.get("create_schedule", True):
        return {
            "success": False,
            "machine_id": machine_id,
            "severity": fault_classification.get("severity"),
            "confidence_score": fault_classification.get("confidence_score"),
            "message": fault_classification.get(
                "message",
                "Schedule creation skipped based on classification",
            ),
            "schedule_created": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    clients = _get_clients()
    settings = clients.settings
    s3_client = clients.s3()
    if not s3_client or not settings.has_schedule_storage:
        return {
            "error": "S3 not configured",
            "message": "AWS S3 client or target location not configured",
            "machine_id": machine_id,
        }

    bucket = settings.work_schedule_bucket
    prefix = settings.work_schedule_prefix or "maintenance-schedules/"

    schedule_id = f"WS-{machine_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    urgency_hours = fault_classification.get("urgency_hours", 168)
    severity = fault_classification.get("severity", "normal")
    fault_type = fault_classification.get("fault_type", "unknown")

    cost_data = _COST_DATABASE.get(fault_type.lower(), _COST_DATABASE["unknown"])

    repair_downtime_cost = cost_data["repair_duration_hours"] * cost_data["downtime_cost_per_hour"]
    replacement_downtime_cost = cost_data["replacement_duration_hours"] * cost_data["downtime_cost_per_hour"]
    total_repair_cost = cost_data["repair_cost"] + repair_downtime_cost
    total_replacement_cost = cost_data["replacement_cost"] + replacement_downtime_cost

    if severity == "critical":
        if total_replacement_cost <= total_repair_cost * 1.5:
            recommended_action = "replace"
            estimated_duration_hours = cost_data["replacement_duration_hours"]
            estimated_direct_cost = cost_data["replacement_cost"]
        else:
            recommended_action = "repair"
            estimated_duration_hours = cost_data["repair_duration_hours"]
            estimated_direct_cost = cost_data["repair_cost"]
    elif severity == "warning":
        if total_replacement_cost < total_repair_cost * 0.8:
            recommended_action = "replace"
            estimated_duration_hours = cost_data["replacement_duration_hours"]
            estimated_direct_cost = cost_data["replacement_cost"]
        else:
            recommended_action = "repair"
            estimated_duration_hours = cost_data["repair_duration_hours"]
            estimated_direct_cost = cost_data["repair_cost"]
    else:
        recommended_action = "repair"
        estimated_duration_hours = cost_data["repair_duration_hours"]
        estimated_direct_cost = cost_data["repair_cost"]

    estimated_downtime_cost = estimated_duration_hours * cost_data["downtime_cost_per_hour"]
    estimated_total_cost = estimated_direct_cost + estimated_downtime_cost

    work_schedule = {
        "schedule_id": schedule_id,
        "machine_id": machine_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "fault_details": {
            "fault_type": fault_classification.get("fault_type", "unknown"),
            "severity": severity,
            "priority": fault_classification.get("priority", "scheduled"),
            "confidence_score": fault_classification.get("confidence_score", 0.0),
        },
        "scheduling_info": {
            "urgency_hours": urgency_hours,
            "action_required_by": fault_classification.get("action_required_by"),
            "estimated_duration_hours": estimated_duration_hours,
        },
        "financial_impact": {
            "downtime_cost_per_hour_usd": cost_data["downtime_cost_per_hour"],
            "estimated_downtime_cost_usd": estimated_downtime_cost,
            "repair_cost_usd": cost_data["repair_cost"],
            "replacement_cost_usd": cost_data["replacement_cost"],
            "total_repair_cost_usd": total_repair_cost,
            "total_replacement_cost_usd": total_replacement_cost,
            "recommended_action": recommended_action,
            "estimated_direct_cost_usd": estimated_direct_cost,
            "estimated_total_cost_usd": estimated_total_cost,
        },
        "cost_benefit_analysis": {
            "repair_option": {
                "direct_cost_usd": cost_data["repair_cost"],
                "downtime_hours": cost_data["repair_duration_hours"],
                "downtime_cost_usd": repair_downtime_cost,
                "total_cost_usd": total_repair_cost,
            },
            "replacement_option": {
                "direct_cost_usd": cost_data["replacement_cost"],
                "downtime_hours": cost_data["replacement_duration_hours"],
                "downtime_cost_usd": replacement_downtime_cost,
                "total_cost_usd": total_replacement_cost,
            },
            "cost_savings_usd": abs(total_repair_cost - total_replacement_cost),
            "recommended_action": recommended_action,
            "recommendation_reason": (
                f"{'Replacement' if recommended_action == 'replace' else 'Repair'} is more cost-effective with total cost of "
                f"${estimated_total_cost:.2f} vs ${total_replacement_cost if recommended_action == 'repair' else total_repair_cost:.2f}"
            ),
        },
    }

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    s3_key = f"{prefix}{timestamp}_{machine_id}.json"

    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json.dumps(work_schedule, indent=2),
            ContentType="application/json",
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        LOGGER.warning("Failed to write work schedule to S3: %s", exc)
        return {
            "error": "Failed to create work schedule",
            "message": str(exc),
            "machine_id": machine_id,
        }

    return {
        "success": True,
        "schedule_id": schedule_id,
        "machine_id": machine_id,
        "schedule_saved": True,
        "severity": severity,
        "priority": fault_classification.get("priority"),
        "action_required_by": fault_classification.get("action_required_by"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": f"Work schedule created and saved successfully for {machine_id}",
    }


@tool
def schedule_maintenance_from_prompt(
    machine_id: str,
    fault_type: str,
    scheduled_date: str,
    severity: str = "monitor",
    estimated_cost: float | None = None,
    notes: str = "",
) -> dict:
    """Schedule maintenance manually from a natural language prompt."""
    clients = _get_clients()
    settings = clients.settings
    s3_client = clients.s3()
    if not s3_client or not settings.has_schedule_storage:
        return {
            "error": "S3 not configured",
            "message": "AWS S3 client or target location not configured",
            "machine_id": machine_id,
        }

    if not date_parser:
        return {
            "error": "dateutil not available",
            "message": "Install python-dateutil to enable natural language date parsing",
            "machine_id": machine_id,
        }

    try:
        parsed_date = date_parser.parse(scheduled_date, fuzzy=True)
    except Exception as exc:  # pragma: no cover - date parsing guard
        return {
            "error": f"Could not parse date: {scheduled_date}",
            "message": str(exc),
            "machine_id": machine_id,
        }

    formatted_date = parsed_date.strftime("%Y-%m-%d")

    schedule_id = f"WS-{machine_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    work_schedule = {
        "schedule_id": schedule_id,
        "machine_id": machine_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "scheduled_date": formatted_date,
        "fault_details": {
            "fault_type": fault_type,
            "severity": severity,
            "priority": "immediate" if severity == "critical" else "scheduled",
            "source": "manual_scheduling",
        },
        "scheduling_info": {
            "estimated_cost_usd": estimated_cost,
            "notes": notes,
        },
    }

    prefix = settings.work_schedule_prefix or "maintenance-schedules/"
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    s3_key = f"{prefix}{timestamp}_{machine_id}.json"

    try:
        s3_client.put_object(
            Bucket=settings.work_schedule_bucket,
            Key=s3_key,
            Body=json.dumps(work_schedule, indent=2),
            ContentType="application/json",
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        LOGGER.warning("Failed to write manual schedule to S3: %s", exc)
        return {
            "error": "Failed to schedule maintenance",
            "message": str(exc),
            "machine_id": machine_id,
        }

    return {
        "success": True,
        "schedule_id": schedule_id,
        "machine_id": machine_id,
        "fault_type": fault_type,
        "scheduled_date": formatted_date,
        "severity": severity,
        "estimated_cost_usd": estimated_cost,
        "notes": notes,
        "message": f"Maintenance scheduled for {machine_id} on {formatted_date} to address {fault_type} fault",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@tool
def count_scheduled_tasks(
    machine_id: str = "",
    severity_filter: str = "",
) -> dict:
    """Count and analyze maintenance tasks stored in S3."""
    clients = _get_clients()
    settings = clients.settings
    s3_client = clients.s3()
    if not s3_client or not settings.has_schedule_storage:
        return {
            "error": "S3 not configured",
            "message": "AWS S3 client or target location not configured",
        }

    try:
        response = s3_client.list_objects_v2(
            Bucket=settings.work_schedule_bucket,
            Prefix=settings.work_schedule_prefix,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        LOGGER.warning("Failed to list schedules in S3: %s", exc)
        return {
            "error": "Failed to list schedules",
            "message": str(exc),
        }

    if "Contents" not in response:
        return {
            "total_tasks": 0,
            "message": "No scheduled maintenance tasks found",
            "bucket": settings.work_schedule_bucket,
            "prefix": settings.work_schedule_prefix,
        }

    tasks = []
    severity_counts = {"critical": 0, "warning": 0, "caution": 0, "normal": 0, "monitor": 0}
    machine_counts: Dict[str, int] = {}
    fault_type_counts: Dict[str, int] = {}
    total_estimated_cost = 0.0

    for obj in response["Contents"]:
        if obj["Key"] == settings.work_schedule_prefix:
            continue
        try:
            file_obj = s3_client.get_object(Bucket=settings.work_schedule_bucket, Key=obj["Key"])
            schedule_data = json.loads(file_obj["Body"].read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - skip malformed files
            LOGGER.warning("Failed to load schedule %s: %s", obj["Key"], exc)
            continue

        task_machine_id = schedule_data.get("machine_id", "unknown")
        fault_details = schedule_data.get("fault_details", {})
        task_severity = fault_details.get("severity", "unknown")
        task_fault_type = fault_details.get("fault_type", "unknown")
        scheduling_info = schedule_data.get("scheduling_info", {})
        financial_impact = schedule_data.get("financial_impact", {})

        if machine_id and task_machine_id != machine_id:
            continue
        if severity_filter and task_severity != severity_filter:
            continue

        if task_severity in severity_counts:
            severity_counts[task_severity] += 1
        machine_counts[task_machine_id] = machine_counts.get(task_machine_id, 0) + 1
        fault_type_counts[task_fault_type] = fault_type_counts.get(task_fault_type, 0) + 1

        estimated_cost = financial_impact.get("estimated_total_cost_usd", 0)
        if not estimated_cost:
            estimated_cost = schedule_data.get("estimated_cost_usd", 0)
        total_estimated_cost += estimated_cost

        tasks.append(
            {
                "schedule_id": schedule_data.get("schedule_id"),
                "machine_id": task_machine_id,
                "fault_type": task_fault_type,
                "severity": task_severity,
                "priority": fault_details.get("priority"),
                "action_required_by": scheduling_info.get("action_required_by"),
                "estimated_cost_usd": estimated_cost,
                "created_at": schedule_data.get("created_at"),
            }
        )

    severity_order = {"critical": 0, "warning": 1, "caution": 2, "normal": 3, "monitor": 4}
    tasks.sort(key=lambda x: severity_order.get(x.get("severity", "normal"), 5))

    result = {
        "total_tasks": len(tasks),
        "filters_applied": {
            "machine_id": machine_id or "none",
            "severity": severity_filter or "none",
        },
        "summary": {
            "by_severity": severity_counts,
            "by_machine": machine_counts,
            "by_fault_type": fault_type_counts,
            "total_estimated_cost_usd": round(total_estimated_cost, 2),
        },
        "tasks": tasks[:10],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if len(tasks) > 10:
        result["note"] = f"Showing 10 most urgent tasks out of {len(tasks)} total"

    return result


@tool
def send_notification_email(
    machine_id: str,
    severity: str,
    fault_type: str,
    work_schedule_details: dict | None = None,
) -> dict:
    """Send maintenance alerts via Amazon SES."""
    clients = _get_clients()
    settings = clients.settings
    ses_client = clients.ses()
    if not ses_client:
        return {
            "error": "SES not configured",
            "message": "AWS SES client not available",
            "machine_id": machine_id,
        }

    recipient = settings.notification_email
    if not recipient:
        return {
            "error": "Notification email not configured",
            "machine_id": machine_id,
        }

    if severity == "critical":
        subject = f"🚨 CRITICAL ALERT: {fault_type} fault on {machine_id}"
        priority = "Urgent"
    elif severity == "warning":
        subject = f"⚠️ WARNING: {fault_type} fault on {machine_id}"
        priority = "High"
    elif severity == "caution":
        subject = f"⚡ CAUTION: {fault_type} fault on {machine_id}"
        priority = "Medium"
    else:
        subject = f"ℹ️ INFO: Maintenance scheduled for {machine_id}"
        priority = "Normal"

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    body_text = (
        "FaultCast Maintenance Alert\n\n"
        f"Machine ID: {machine_id}\n"
        f"Fault Type: {fault_type}\n"
        f"Severity: {severity.upper()}\n"
        f"Priority: {priority}\n"
        f"Timestamp: {timestamp}\n"
    )

    if work_schedule_details:
        body_text += (
            "\nWork Schedule Created:\n"
            f"- Schedule ID: {work_schedule_details.get('schedule_id', 'N/A')}\n"
            f"- Action Required By: {work_schedule_details.get('action_required_by', 'N/A')}\n"
        )

    body_html = f"""
<html>
<head></head>
<body>
<h2>FaultCast Maintenance Alert</h2>
<table border="1" cellpadding="5" cellspacing="0">
<tr><td><strong>Machine ID</strong></td><td>{machine_id}</td></tr>
<tr><td><strong>Fault Type</strong></td><td>{fault_type}</td></tr>
<tr><td><strong>Severity</strong></td><td>{severity.upper()}</td></tr>
<tr><td><strong>Priority</strong></td><td>{priority}</td></tr>
<tr><td><strong>Timestamp</strong></td><td>{timestamp}</td></tr>
</table>
"""

    if work_schedule_details:
        body_html += f"""
<h3>Work Schedule Created</h3>
<ul>
<li><strong>Schedule ID:</strong> {work_schedule_details.get('schedule_id', 'N/A')}</li>
<li><strong>Action Required By:</strong> {work_schedule_details.get('action_required_by', 'N/A')}</li>
<li><strong>S3 Location:</strong> <code>{work_schedule_details.get('s3_uri', 'N/A')}</code></li>
</ul>
"""

    body_html += """
<p>Please review the work schedule and assign maintenance personnel.</p>
<hr>
<p><em>FaultCast Predictive Maintenance System</em></p>
</body>
</html>
"""

    try:
        response = ses_client.send_email(
            Source=recipient,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                },
            },
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        LOGGER.warning("Failed to send SES notification: %s", exc)
        return {
            "error": "Failed to send notification email",
            "message": str(exc),
            "machine_id": machine_id,
        }

    return {
        "success": True,
        "message_id": response.get("MessageId"),
        "machine_id": machine_id,
        "severity": severity,
        "recipient": recipient,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
