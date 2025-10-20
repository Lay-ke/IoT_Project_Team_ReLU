#!/usr/bin/env python3
"""
FaultCast Maintenance Agent - Single Agent with Multiple Tools

A unified AI agent for conveyor belt maintenance using Strands SDK.
Combines diagnostics, explanations, and recommendations in one agent.

Run: python faultcast_maintenance_agent.py
"""

import logging
import random
import os
from datetime import datetime
from strands import Agent, tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

# AWS Configuration
try:
    import boto3
    import json
    from datetime import datetime, timedelta
    
    # Knowledge Base client (initialized lazily)
    KB_CLIENT = None
    
    def get_kb_client():
        """Get or create Knowledge Base client"""
        global KB_CLIENT
        if KB_CLIENT is None:
            KB_CLIENT = boto3.client(
                'bedrock-agent-runtime',
                region_name=os.getenv('KNOWLEDGE_BASE_REGION', 'eu-west-1')
            )
        return KB_CLIENT
    
    def get_kb_id():
        """Get Knowledge Base ID from environment at runtime"""
        return os.getenv('KNOWLEDGE_BASE_ID', '')
    
    # S3 client for work schedules
    S3_CLIENT = boto3.client('s3', region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-west-1'))
    S3_BUCKET = os.getenv('WORK_SCHEDULE_BUCKET', 'predictive-maintenance-feature-store')
    S3_PREFIX = os.getenv('WORK_SCHEDULE_PREFIX', 'maintenance-schedules/')
    
    # SES client for email notifications
    SES_CLIENT = boto3.client('ses', region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-west-1'))
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', 'maintenance@example.com')
    
except ImportError:
    KB_CLIENT = None
    S3_CLIENT = None
    SES_CLIENT = None
    KB_ID = ''
    KB_AVAILABLE = False
    logging.warning("boto3 not available - AWS features disabled")


# ============================================================================
# DIAGNOSTIC TOOLS
# ============================================================================

@tool
def get_sensor_readings(machine_id: str = "CONV_001", include_anomaly: bool = False) -> dict:
    """Get current sensor readings from conveyor belt equipment.
    
    Args:
        machine_id: The machine identifier to get readings for
        include_anomaly: Whether to simulate anomalies for testing
        
    Returns:
        Dictionary with current sensor readings
    """
    # Baseline values
    baselines = {
        "vibration": 2.0,
        "temperature": 70.0,
        "current": 12.0,
        "speed": 1200.0
    }
    
    readings = {
        "machine_id": machine_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sensors": {}
    }
    
    # Generate readings with optional anomalies
    for sensor, baseline in baselines.items():
        if include_anomaly and random.random() < 0.4:
            # Inject anomaly
            value = baseline * random.uniform(1.5, 2.0)
        else:
            # Normal variation
            value = baseline + random.uniform(-0.2, 0.2) * baseline
        
        readings["sensors"][sensor] = round(value, 2)
    
    return readings


@tool
def search_prediction_history(machine_id: str, query: str = "") -> dict:
    """Search the knowledge base for ML model predictions and historical fault patterns.
    
    Args:
        machine_id: The machine identifier to search predictions for
        query: Optional search query to filter predictions (e.g., "ball bearing", "high vibration")
        
    Returns:
        Dictionary with prediction history and fault patterns from the inference model
    """
    kb_id = get_kb_id()
    if not kb_id:
        return {
            "error": "Knowledge Base not configured",
            "message": "Set KNOWLEDGE_BASE_ID environment variable to enable prediction search",
            "machine_id": machine_id
        }
    
    try:
        # Build search query
        search_text = f"Device ID: {machine_id}"
        if query:
            search_text += f" {query}"
        
        # Query the knowledge base
        kb_client = get_kb_client()
        response = kb_client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': search_text},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        # Parse results
        predictions = []
        for result in response.get('retrievalResults', []):
            content = result.get('content', {}).get('text', '')
            predictions.append({
                "content": content,
                "score": result.get('score', 0.0),
                "source": result.get('location', {}).get('s3Location', {}).get('uri', 'unknown')
            })
        
        return {
            "machine_id": machine_id,
            "query": search_text,
            "predictions_found": len(predictions),
            "predictions": predictions,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "machine_id": machine_id,
            "message": "Failed to query knowledge base"
        }


@tool
def analyze_anomaly(sensor_readings: dict) -> dict:
    """Analyze sensor readings for anomalies and determine severity.
    
    Args:
        sensor_readings: Dictionary containing sensor readings
        
    Returns:
        Dictionary with anomaly analysis and severity classification
    """
    # Define thresholds
    thresholds = {
        "vibration": {"warning": 3.0, "critical": 4.0, "unit": "mm/s"},
        "temperature": {"warning": 80, "critical": 90, "unit": "°C"},
        "current": {"warning": 15, "critical": 18, "unit": "A"},
        "speed": {"warning": 1300, "critical": 1400, "unit": "rpm"}
    }
    
    sensors = sensor_readings.get("sensors", {})
    anomalies = []
    
    # Check each sensor against thresholds
    for sensor, value in sensors.items():
        if sensor in thresholds:
            threshold = thresholds[sensor]
            
            if value > threshold["critical"]:
                anomalies.append({
                    "sensor": sensor,
                    "value": value,
                    "unit": threshold["unit"],
                    "severity": "critical",
                    "threshold_exceeded": threshold["critical"],
                    "message": f"{sensor.title()} critically high at {value} {threshold['unit']}"
                })
            elif value > threshold["warning"]:
                anomalies.append({
                    "sensor": sensor,
                    "value": value,
                    "unit": threshold["unit"],
                    "severity": "warning",
                    "threshold_exceeded": threshold["warning"],
                    "message": f"{sensor.title()} elevated at {value} {threshold['unit']}"
                })
    
    # Determine overall status
    if any(a["severity"] == "critical" for a in anomalies):
        overall_status = "critical"
    elif any(a["severity"] == "warning" for a in anomalies):
        overall_status = "warning"
    else:
        overall_status = "normal"
    
    return {
        "machine_id": sensor_readings.get("machine_id", "unknown"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "overall_status": overall_status
    }


# ============================================================================
# RECOMMENDATION TOOLS
# ============================================================================

@tool
def search_maintenance_playbook(
    fault_type: str = "",
    anomaly_type: str = "",
    severity: str = ""
) -> dict:
    """Search the knowledge base for maintenance playbook recommendations.
    
    Args:
        fault_type: Predicted fault type from ML model (e.g., "pulley", "ball bearing")
        anomaly_type: Type of anomaly detected (e.g., "vibration", "temperature")
        severity: Severity level (e.g., "critical", "warning", "normal")
        
    Returns:
        Dictionary with playbook recommendations from knowledge base
    """
    kb_id = get_kb_id()
    if not kb_id:
        return {
            "error": "Knowledge Base not configured",
            "message": "Set KNOWLEDGE_BASE_ID environment variable to enable playbook search",
            "fault_type": fault_type,
            "anomaly_type": anomaly_type
        }
    
    try:
        # Build search query for playbook
        search_terms = []
        if fault_type:
            search_terms.append(f"fault type: {fault_type}")
        if anomaly_type:
            search_terms.append(f"anomaly: {anomaly_type}")
        if severity:
            search_terms.append(f"severity: {severity}")
        
        search_text = " ".join(search_terms) if search_terms else "maintenance playbook"
        
        # Query the knowledge base for playbook
        kb_client = get_kb_client()
        response = kb_client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': search_text},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3
                }
            }
        )
        
        # Parse results
        playbook_entries = []
        for result in response.get('retrievalResults', []):
            content = result.get('content', {}).get('text', '')
            playbook_entries.append({
                "content": content,
                "relevance_score": result.get('score', 0.0),
                "source": result.get('location', {}).get('s3Location', {}).get('uri', 'unknown')
            })
        
        return {
            "fault_type": fault_type,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "playbook_entries_found": len(playbook_entries),
            "playbook_entries": playbook_entries,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "fault_type": fault_type,
            "anomaly_type": anomaly_type,
            "message": "Failed to query maintenance playbook"
        }


# ============================================================================
# WORK SCHEDULE & NOTIFICATION TOOLS
# ============================================================================

@tool
def classify_fault_severity(
    fault_type: str,
    confidence_score: float,
    sensor_readings: dict = None
) -> dict:
    """Classify the severity of a predicted fault based on confidence and sensor data.
    
    Only creates schedules for confidence >= 0.4. Returns two severity levels:
    - critical: High confidence faults requiring immediate action
    - monitor: Lower confidence faults to watch
    
    Args:
        fault_type: Predicted fault type (e.g., "pulley", "ball bearing")
        confidence_score: ML model confidence score (0-1)
        sensor_readings: Optional sensor readings for additional context
        
    Returns:
        Dictionary with severity classification and priority, or indication not to create schedule
    """
    # Don't create schedule if confidence is too low
    if confidence_score < 0.4:
        return {
            "fault_type": fault_type,
            "confidence_score": confidence_score,
            "severity": "below_threshold",
            "priority": "no_action",
            "create_schedule": False,
            "message": f"Confidence score {confidence_score:.2%} is below 0.4 threshold. No schedule will be created.",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    # Normalize fault type - handle empty, None, or "unknown"
    if not fault_type or fault_type.lower() in ["unknown", "none", ""]:
        fault_type = "unspecified"
    
    # Skip if fault type is normal/no fault
    if fault_type.lower() in ["normal", "no fault"]:
        return {
            "fault_type": fault_type,
            "confidence_score": confidence_score,
            "severity": "normal",
            "priority": "no_action",
            "create_schedule": False,
            "message": "No fault detected. No schedule will be created.",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    # Classify based on confidence score - only critical or monitor
    if confidence_score >= 0.8:
        severity = "critical"
        priority = "immediate"
        urgency_hours = 24
    else:  # 0.4 <= confidence < 0.8
        severity = "monitor"
        priority = "scheduled"
        urgency_hours = 168  # 1 week
    
    # Adjust based on sensor readings if provided
    if sensor_readings:
        sensors = sensor_readings.get("sensors", {})
        
        # Check for critical sensor values - override to critical
        if sensors.get("temperature", 0) > 90:
            severity = "critical"
            priority = "immediate"
            urgency_hours = 12
        elif sensors.get("vibration", 0) > 4.0:
            severity = "critical"
            priority = "immediate"
            urgency_hours = 24
        elif sensors.get("temperature", 0) > 80 or sensors.get("vibration", 0) > 3.0:
            # Elevate to critical if sensors are concerning
            severity = "critical"
            priority = "within_24_hours"
            urgency_hours = 24
    
    return {
        "fault_type": fault_type,
        "confidence_score": confidence_score,
        "severity": severity,
        "priority": priority,
        "urgency_hours": urgency_hours,
        "create_schedule": True,
        "action_required_by": (datetime.utcnow() + timedelta(hours=urgency_hours)).isoformat() + "Z",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@tool
def create_work_schedule(
    machine_id: str,
    fault_classification: dict,
    playbook_recommendations: dict = None
) -> dict:
    """Create a maintenance work schedule and save it to S3.
    
    Only creates schedule if fault_classification indicates create_schedule=True
    (confidence >= 0.4 and not a normal fault).
    
    Args:
        machine_id: Equipment identifier
        fault_classification: Severity classification from classify_fault_severity
        playbook_recommendations: Optional playbook guidance
        
    Returns:
        Dictionary with work schedule details and S3 location, or skip message
    """
    # Check if we should create a schedule
    if not fault_classification.get("create_schedule", True):
        return {
            "success": False,
            "machine_id": machine_id,
            "severity": fault_classification.get("severity"),
            "confidence_score": fault_classification.get("confidence_score"),
            "message": fault_classification.get("message", "Schedule creation skipped based on classification"),
            "schedule_created": False,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    if not S3_CLIENT:
        return {
            "error": "S3 not configured",
            "message": "AWS S3 client not available",
            "machine_id": machine_id
        }
    
    try:
        # Create work schedule
        schedule_id = f"WS-{machine_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Extract scheduling info
        urgency_hours = fault_classification.get("urgency_hours", 168)
        severity = fault_classification.get("severity", "normal")
        
        # Get fault type for cost estimation
        fault_type = fault_classification.get("fault_type", "unknown")
        
        # Financial impact analysis by fault type and severity
        cost_database = {
            "ball bearing": {
                "repair_cost": 350,
                "replacement_cost": 800,
                "repair_duration_hours": 4,
                "replacement_duration_hours": 6,
                "downtime_cost_per_hour": 500
            },
            "pulley": {
                "repair_cost": 400,
                "replacement_cost": 1200,
                "repair_duration_hours": 5,
                "replacement_duration_hours": 8,
                "downtime_cost_per_hour": 600
            },
            "idler roller fault": {
                "repair_cost": 250,
                "replacement_cost": 600,
                "repair_duration_hours": 3,
                "replacement_duration_hours": 5,
                "downtime_cost_per_hour": 400
            },
            "drive motor": {
                "repair_cost": 800,
                "replacement_cost": 2500,
                "repair_duration_hours": 8,
                "replacement_duration_hours": 12,
                "downtime_cost_per_hour": 800
            },
            "belt slippage": {
                "repair_cost": 150,
                "replacement_cost": 400,
                "repair_duration_hours": 2,
                "replacement_duration_hours": 4,
                "downtime_cost_per_hour": 300
            },
            "central shaft": {
                "repair_cost": 600,
                "replacement_cost": 1800,
                "repair_duration_hours": 6,
                "replacement_duration_hours": 10,
                "downtime_cost_per_hour": 700
            },
            "unknown": {
                "repair_cost": 300,
                "replacement_cost": 800,
                "repair_duration_hours": 4,
                "replacement_duration_hours": 6,
                "downtime_cost_per_hour": 400
            }
        }
        
        # Get cost data for this fault type
        cost_data = cost_database.get(fault_type.lower(), cost_database["unknown"])
        
        # Calculate total costs for repair vs replacement
        repair_downtime_cost = cost_data["repair_duration_hours"] * cost_data["downtime_cost_per_hour"]
        replacement_downtime_cost = cost_data["replacement_duration_hours"] * cost_data["downtime_cost_per_hour"]
        
        total_repair_cost = cost_data["repair_cost"] + repair_downtime_cost
        total_replacement_cost = cost_data["replacement_cost"] + replacement_downtime_cost
        
        # Determine recommended action based on severity and cost-benefit
        if severity == "critical":
            # For critical faults, consider replacement if cost difference is reasonable
            if total_replacement_cost <= total_repair_cost * 1.5:
                recommended_action = "replace"
                estimated_duration_hours = cost_data["replacement_duration_hours"]
                estimated_direct_cost = cost_data["replacement_cost"]
            else:
                recommended_action = "repair"
                estimated_duration_hours = cost_data["repair_duration_hours"]
                estimated_direct_cost = cost_data["repair_cost"]
        elif severity == "warning":
            # For warnings, prefer repair unless replacement is clearly better
            if total_replacement_cost < total_repair_cost * 0.8:
                recommended_action = "replace"
                estimated_duration_hours = cost_data["replacement_duration_hours"]
                estimated_direct_cost = cost_data["replacement_cost"]
            else:
                recommended_action = "repair"
                estimated_duration_hours = cost_data["repair_duration_hours"]
                estimated_direct_cost = cost_data["repair_cost"]
        else:
            # For caution/monitor, always repair
            recommended_action = "repair"
            estimated_duration_hours = cost_data["repair_duration_hours"]
            estimated_direct_cost = cost_data["repair_cost"]
        
        # Calculate total estimated cost including downtime
        estimated_downtime_cost = estimated_duration_hours * cost_data["downtime_cost_per_hour"]
        estimated_total_cost = estimated_direct_cost + estimated_downtime_cost
        
        work_schedule = {
            "schedule_id": schedule_id,
            "machine_id": machine_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "fault_details": {
                "fault_type": fault_classification.get("fault_type", "unknown"),
                "severity": fault_classification.get("severity", "normal"),
                "priority": fault_classification.get("priority", "scheduled"),
                "confidence_score": fault_classification.get("confidence_score", 0.0)
            },
            "scheduling_info": {
                "urgency_hours": urgency_hours,
                "action_required_by": fault_classification.get("action_required_by"),
                "estimated_duration_hours": estimated_duration_hours
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
                "estimated_total_cost_usd": estimated_total_cost
            },
            "cost_benefit_analysis": {
                "repair_option": {
                    "direct_cost_usd": cost_data["repair_cost"],
                    "downtime_hours": cost_data["repair_duration_hours"],
                    "downtime_cost_usd": repair_downtime_cost,
                    "total_cost_usd": total_repair_cost
                },
                "replacement_option": {
                    "direct_cost_usd": cost_data["replacement_cost"],
                    "downtime_hours": cost_data["replacement_duration_hours"],
                    "downtime_cost_usd": replacement_downtime_cost,
                    "total_cost_usd": total_replacement_cost
                },
                "cost_savings_usd": abs(total_repair_cost - total_replacement_cost),
                "recommended_action": recommended_action,
                "recommendation_reason": f"{'Replacement' if recommended_action == 'replace' else 'Repair'} is more cost-effective with total cost of ${estimated_total_cost:.2f} vs ${total_replacement_cost if recommended_action == 'repair' else total_repair_cost:.2f}"
            }
        }
        
        # Save to S3 - use timestamp as key in root of prefix
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        s3_key = f"{S3_PREFIX}{timestamp}_{machine_id}.json"
        
        S3_CLIENT.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(work_schedule, indent=2),
            ContentType='application/json'
        )
        
        return {
            "success": True,
            "schedule_id": schedule_id,
            "machine_id": machine_id,
            "schedule_saved": True,
            "severity": fault_classification.get("severity"),
            "priority": fault_classification.get("priority"),
            "action_required_by": fault_classification.get("action_required_by"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": f"Work schedule created and saved successfully for {machine_id}"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create work schedule",
            "machine_id": machine_id
        }


@tool
def send_notification_email(
    machine_id: str,
    severity: str,
    fault_type: str,
    work_schedule_details: dict = None
) -> dict:
    """Send email notification for maintenance alerts.
    
    Args:
        machine_id: Equipment identifier
        severity: Severity level (critical, warning, caution, normal)
        fault_type: Type of fault detected
        work_schedule_details: Optional work schedule information
        
    Returns:
        Dictionary with email sending status
    """
    if not SES_CLIENT:
        return {
            "error": "SES not configured",
            "message": "AWS SES client not available",
            "machine_id": machine_id
        }
    
    try:
        # Determine email priority and subject
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
        
        # Build email body
        body_text = f"""
FaultCast Maintenance Alert

Machine ID: {machine_id}
Fault Type: {fault_type}
Severity: {severity.upper()}
Priority: {priority}
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        if work_schedule_details:
            body_text += f"""
Work Schedule Created:
- Schedule ID: {work_schedule_details.get('schedule_id', 'N/A')}
- Action Required By: {work_schedule_details.get('action_required_by', 'N/A')}
- S3 Location: {work_schedule_details.get('s3_uri', 'N/A')}
"""
        
        body_text += """
Please review the work schedule and assign maintenance personnel.

---
FaultCast Predictive Maintenance System
"""
        
        body_html = f"""
<html>
<head></head>
<body>
<h2>FaultCast Maintenance Alert</h2>
<table border="1" cellpadding="5" cellspacing="0">
<tr><td><strong>Machine ID</strong></td><td>{machine_id}</td></tr>
<tr><td><strong>Fault Type</strong></td><td>{fault_type}</td></tr>
<tr><td><strong>Severity</strong></td><td><span style="color: {'red' if severity == 'critical' else 'orange' if severity == 'warning' else 'blue'};">{severity.upper()}</span></td></tr>
<tr><td><strong>Priority</strong></td><td>{priority}</td></tr>
<tr><td><strong>Timestamp</strong></td><td>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
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
        
        # Send email via SES
        response = SES_CLIENT.send_email(
            Source=NOTIFICATION_EMAIL,
            Destination={
                'ToAddresses': [NOTIFICATION_EMAIL]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': body_html,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        return {
            "success": True,
            "message_id": response.get('MessageId'),
            "machine_id": machine_id,
            "severity": severity,
            "recipient": NOTIFICATION_EMAIL,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to send notification email",
            "machine_id": machine_id
        }


# ============================================================================
# SCHEDULE ANALYSIS TOOLS
# ============================================================================

@tool
def count_scheduled_tasks(
    machine_id: str = "",
    severity_filter: str = ""
) -> dict:
    """Count and analyze maintenance tasks in the maintenance-schedules directory.
    
    Args:
        machine_id: Optional filter by specific machine ID
        severity_filter: Optional filter by severity (critical, warning, caution, normal)
        
    Returns:
        Dictionary with count statistics and task summaries
    """
    if not S3_CLIENT:
        return {
            "error": "S3 not configured",
            "message": "AWS S3 client not available"
        }
    
    try:
        # List all objects in the maintenance-schedules prefix
        response = S3_CLIENT.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=S3_PREFIX
        )
        
        if 'Contents' not in response:
            return {
                "total_tasks": 0,
                "message": "No scheduled maintenance tasks found",
                "bucket": S3_BUCKET,
                "prefix": S3_PREFIX
            }
        
        # Process each schedule file
        tasks = []
        severity_counts = {"critical": 0, "warning": 0, "caution": 0, "normal": 0, "monitor": 0}
        machine_counts = {}
        fault_type_counts = {}
        total_estimated_cost = 0.0
        
        for obj in response['Contents']:
            # Skip if it's just the prefix itself
            if obj['Key'] == S3_PREFIX:
                continue
            
            try:
                # Get the schedule file
                file_obj = S3_CLIENT.get_object(Bucket=S3_BUCKET, Key=obj['Key'])
                schedule_data = json.loads(file_obj['Body'].read().decode('utf-8'))
                
                # Extract key information
                task_machine_id = schedule_data.get('machine_id', 'unknown')
                fault_details = schedule_data.get('fault_details', {})
                task_severity = fault_details.get('severity', 'unknown')
                task_fault_type = fault_details.get('fault_type', 'unknown')
                scheduling_info = schedule_data.get('scheduling_info', {})
                financial_impact = schedule_data.get('financial_impact', {})
                
                # Apply filters
                if machine_id and task_machine_id != machine_id:
                    continue
                if severity_filter and task_severity != severity_filter:
                    continue
                
                # Count by severity
                if task_severity in severity_counts:
                    severity_counts[task_severity] += 1
                
                # Count by machine
                machine_counts[task_machine_id] = machine_counts.get(task_machine_id, 0) + 1
                
                # Count by fault type
                fault_type_counts[task_fault_type] = fault_type_counts.get(task_fault_type, 0) + 1
                
                # Sum costs - handle both old and new format
                # New format: financial_impact.estimated_total_cost_usd
                # Old format: estimated_cost_usd at root level
                estimated_cost = financial_impact.get('estimated_total_cost_usd', 0)
                if estimated_cost == 0:
                    # Try old format
                    estimated_cost = schedule_data.get('estimated_cost_usd', 0)
                total_estimated_cost += estimated_cost
                
                # Add to tasks list
                tasks.append({
                    "schedule_id": schedule_data.get('schedule_id'),
                    "machine_id": task_machine_id,
                    "fault_type": task_fault_type,
                    "severity": task_severity,
                    "priority": fault_details.get('priority'),
                    "action_required_by": scheduling_info.get('action_required_by'),
                    "estimated_cost_usd": estimated_cost,
                    "created_at": schedule_data.get('created_at')
                })
                
            except Exception as e:
                # Skip files that can't be parsed
                logging.warning(f"Could not parse schedule file {obj['Key']}: {e}")
                continue
        
        # Sort tasks by severity priority
        severity_order = {"critical": 0, "warning": 1, "caution": 2, "normal": 3, "monitor": 4}
        tasks.sort(key=lambda x: severity_order.get(x.get('severity', 'normal'), 5))
        
        # Build response
        result = {
            "total_tasks": len(tasks),
            "filters_applied": {
                "machine_id": machine_id if machine_id else "none",
                "severity": severity_filter if severity_filter else "none"
            },
            "summary": {
                "by_severity": severity_counts,
                "by_machine": machine_counts,
                "by_fault_type": fault_type_counts,
                "total_estimated_cost_usd": round(total_estimated_cost, 2)
            },
            "tasks": tasks[:10],  # Return top 10 most urgent tasks
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if len(tasks) > 10:
            result["note"] = f"Showing 10 most urgent tasks out of {len(tasks)} total"
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to count scheduled tasks"
        }


@tool
def get_schedule_insights(query: str = "") -> dict:
    """Get insights about scheduled maintenance tasks using the knowledge base.
    
    This tool searches the maintenance-schedules data source in the knowledge base
    to answer questions about scheduled tasks, patterns, and trends.
    
    Args:
        query: Question or query about scheduled maintenance tasks
               Examples: "How many critical tasks?", "What machines need attention?",
                        "What are the most common fault types?"
        
    Returns:
        Dictionary with insights from the knowledge base about scheduled tasks
    """
    kb_id = get_kb_id()
    if not kb_id:
        return {
            "error": "Knowledge Base not configured",
            "message": "Set KNOWLEDGE_BASE_ID environment variable to enable schedule insights"
        }
    
    try:
        # Build search query for schedules
        search_text = f"maintenance schedule {query}" if query else "maintenance schedule summary"
        
        # Query the knowledge base
        kb_client = get_kb_client()
        response = kb_client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': search_text},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        # Parse results
        insights = []
        for result in response.get('retrievalResults', []):
            content = result.get('content', {}).get('text', '')
            insights.append({
                "content": content,
                "relevance_score": result.get('score', 0.0),
                "source": result.get('location', {}).get('s3Location', {}).get('uri', 'unknown')
            })
        
        return {
            "query": search_text,
            "insights_found": len(insights),
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to get schedule insights from knowledge base"
        }


# ============================================================================
# CREATE THE UNIFIED FAULTCAST AGENT
# ============================================================================

faultcast_agent = Agent(
    model="eu.amazon.nova-pro-v1:0",  # Nova Pro in eu-west-1
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
    tools=[
        get_sensor_readings,
        search_prediction_history,
        analyze_anomaly,
        search_maintenance_playbook,
        classify_fault_severity,
        create_work_schedule,
        count_scheduled_tasks,
        get_schedule_insights,
        # send_notification_email  # Disabled for testing
    ]
)


# ============================================================================
# INTERACTIVE INTERFACE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔧 FaultCast Maintenance Agent - Unified AI Assistant")
    print("="*70)
    print("Single agent with ML predictions and real-time diagnostics")
    print(f"Knowledge Base: {'✅ Connected' if KB_AVAILABLE else '❌ Not configured'}")
    print("Type 'exit' to quit")
    print("="*70)
    
    # Sample prompts for testing
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
    
    # Interactive loop
    while True:
        try:
            user_input = input("\n🔧 You > ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Stay safe and keep those conveyors running!")
                break
            
            if not user_input:
                continue
            
            # Get response from unified agent
            print("\n🤖 Analyzing...")
            response = faultcast_agent(user_input)
            print(f"\n🤖 FaultCast > {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Stay safe and keep those conveyors running!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
