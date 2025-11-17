"""Diagnostic tools for the FaultCast agent."""

from __future__ import annotations

import random
from collections import Counter
from datetime import datetime
import json
import re

from strands import tool

from faultcast.tools import knowledge


@tool
def get_sensor_readings(machine_id: str = "CONV_001", include_anomaly: bool = False) -> dict:
    """Simulate current sensor readings for conveyor belt equipment."""
    baselines = {
        "vibration": 2.0,
        "temperature": 70.0,
        "current": 12.0,
        "speed": 1200.0,
    }

    readings = {
        "machine_id": machine_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sensors": {},
    }

    for sensor, baseline in baselines.items():
        if include_anomaly and random.random() < 0.4:
            value = baseline * random.uniform(1.5, 2.0)
        else:
            value = baseline + random.uniform(-0.2, 0.2) * baseline
        readings["sensors"][sensor] = round(value, 2)

    return readings


@tool
def analyze_anomaly(sensor_readings: dict) -> dict:
    """Analyze sensor readings for anomalies and classify severity."""
    thresholds = {
        "vibration": {"warning": 3.0, "critical": 4.0, "unit": "mm/s"},
        "temperature": {"warning": 80, "critical": 90, "unit": "°C"},
        "current": {"warning": 15, "critical": 18, "unit": "A"},
        "speed": {"warning": 1300, "critical": 1400, "unit": "rpm"},
    }

    sensors = sensor_readings.get("sensors", {})
    anomalies = []

    for sensor, value in sensors.items():
        if sensor not in thresholds:
            continue
        limits = thresholds[sensor]
        if value > limits["critical"]:
            anomalies.append(
                {
                    "sensor": sensor,
                    "value": value,
                    "unit": limits["unit"],
                    "severity": "critical",
                    "threshold_exceeded": limits["critical"],
                    "message": f"{sensor.title()} critically high at {value} {limits['unit']}",
                }
            )
        elif value > limits["warning"]:
            anomalies.append(
                {
                    "sensor": sensor,
                    "value": value,
                    "unit": limits["unit"],
                    "severity": "warning",
                    "threshold_exceeded": limits["warning"],
                    "message": f"{sensor.title()} elevated at {value} {limits['unit']}",
                }
            )

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
        "overall_status": overall_status,
    }


@tool
def get_machine_status(machine_id: str) -> dict:
    """Get comprehensive machine health status from sensors and KB predictions."""
    sensor_data = get_sensor_readings(machine_id)
    anomaly_analysis = analyze_anomaly(sensor_data)
    ml_predictions = knowledge.search_prediction_history(machine_id)

    sensor_status = anomaly_analysis.get("overall_status", "normal")
    anomalies = anomaly_analysis.get("anomalies", [])

    predictions = ml_predictions.get("predictions", [])
    prediction_text = " ".join(p.get("content", "").lower() for p in predictions[:3])

    fault_counts: Counter[str] = Counter()
    dominant_fault: str | None = None
    dominant_count: int = 0

    parsed_predictions = []
    fault_pattern = re.compile(r'"(Fault|fault|predicted_class|predicted_fault)"\s*:\s*"([^"]+)"')

    for entry in predictions:
        content = entry.get("content", "")
        normalized_batch = []

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = []

        if isinstance(parsed, dict):
            parsed = [parsed]
        if isinstance(parsed, list):
            normalized_batch.extend(record for record in parsed if isinstance(record, dict))

        if not normalized_batch:
            normalized_batch = []

        for fault_match in fault_pattern.findall(content):
            fault_value = fault_match[1].strip().lower()
            if fault_value:
                fault_counts[fault_value] += 1

        if normalized_batch:
            parsed_predictions.append(normalized_batch)

    overall_status = "healthy"
    recommendation = "Continue normal operations"

    if predictions and not ml_predictions.get("error"):
        if any(word in prediction_text for word in ["critical", "failure", "fault detected", "high risk"]):
            overall_status = "critical"
            recommendation = "Immediate maintenance required based on ML predictions"
        elif any(word in prediction_text for word in ["warning", "elevated", "monitor", "potential"]):
            overall_status = "warning"
            recommendation = "Schedule maintenance soon based on ML predictions"
        elif "normal" in prediction_text or "healthy" in prediction_text:
            overall_status = "healthy"
            recommendation = "Machine operating normally according to ML model"

    if fault_counts:
        dominant_fault, dominant_count = fault_counts.most_common(1)[0]
        if dominant_fault not in {"normal", "none", "no fault", "healthy"}:
            if sensor_status == "critical" or dominant_fault in {"ball bearing", "pulley", "idler roller fault"}:
                overall_status = "critical"
                recommendation = (
                    f"Immediate maintenance recommended – knowledge base shows frequent '{dominant_fault}' faults"
                )
            else:
                overall_status = "warning"
                recommendation = (
                    f"Schedule maintenance – knowledge base indicates recurring '{dominant_fault}' faults"
                )
        if parsed_predictions:
            ml_predictions["parsed_records"] = parsed_predictions

    if sensor_status == "critical":
        overall_status = "critical"
        recommendation = "Immediate maintenance required - critical sensor readings detected"
    elif sensor_status == "warning" and overall_status == "healthy":
        overall_status = "warning"
        recommendation = "Monitor closely - elevated sensor readings detected"

    ml_summary = {
        "machine_id": machine_id,
        "predictions_found": ml_predictions.get("predictions_found", 0),
        "has_predictions": bool(predictions),
        "recent_predictions": predictions[:3] if predictions else [],
    }
    if fault_counts:
        ml_summary["parsed_fault_counts"] = dict(fault_counts)
        ml_summary["dominant_fault"] = dominant_fault
        ml_summary["dominant_fault_count"] = dominant_count
    if parsed_predictions:
        ml_summary["parsed_records"] = parsed_predictions
    if ml_predictions.get("error"):
        ml_summary["error"] = ml_predictions["error"]
        ml_summary["message"] = ml_predictions.get("message")

    return {
        "machine_id": machine_id,
        "overall_status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sensor_readings": sensor_data.get("sensors", {}),
        "sensor_status": sensor_status,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "ml_predictions": ml_summary,
        "recommendation": recommendation,
    }
