"""Knowledge-base related tools for the FaultCast agent."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from functools import lru_cache
from typing import Optional

from strands import tool

from faultcast.aws import get_clients

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_clients():
    """Return cached AWS clients to avoid repeated cold-start overhead."""
    return get_clients()


def _get_settings():
    return _get_clients().settings


ISO_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
SPACE_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")
COMPACT_TIMESTAMP_PATTERN = re.compile(r"\d{8}_\d{6}")

PREDICTED_FAULT_PATTERNS = (
    re.compile(r"Predicted Fault\s*[:=]\s*([A-Za-z0-9 \-_/]+)", re.IGNORECASE),
    re.compile(r"\"predicted_class\"\s*:\s*\"([^\"]+)\"", re.IGNORECASE),
    re.compile(r"\"Predicted Fault\"\s*:\s*\"([^\"]+)\"", re.IGNORECASE),
)

CONFIDENCE_PATTERNS = (
    re.compile(r"Confidence(?: Score)?\s*[:=]\s*([0-9]*\.?[0-9]+)", re.IGNORECASE),
    re.compile(r"\"confidence\"\s*:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE),
)


def _parse_timestamp(value: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _extract_latest_timestamp(content: str) -> Optional[datetime]:
    candidates = []
    for pattern in (ISO_TIMESTAMP_PATTERN, SPACE_TIMESTAMP_PATTERN, COMPACT_TIMESTAMP_PATTERN):
        for match in pattern.findall(content):
            parsed = _parse_timestamp(match)
            if parsed:
                candidates.append(parsed)
    if not candidates:
        return None
    return max(candidates)


def _extract_predicted_fault(content: str) -> Optional[str]:
    for pattern in PREDICTED_FAULT_PATTERNS:
        match = pattern.search(content)
        if match:
            fault = match.group(1).strip().lower()
            if fault:
                return fault
    # Fallback to first general fault key if present
    generic = re.search(r"\"Fault\"\s*:\s*\"([^\"]+)\"", content)
    if generic:
        fault = generic.group(1).strip().lower()
        if fault:
            return fault
    return None


def _extract_confidence(content: str) -> Optional[float]:
    for pattern in CONFIDENCE_PATTERNS:
        match = pattern.search(content)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                continue
    return None


def _fetch_latest_inference_entry(machine_id: str) -> Optional[dict]:
    """Return the latest ML inference artefact from S3 as a prediction entry."""

    clients = _get_clients()
    settings = clients.settings
    s3_client = clients.s3()
    bucket = settings.work_schedule_bucket
    if not s3_client or not bucket:
        return None

    prefix = f"knowledge-base-inference/{machine_id}/"

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
    except Exception as exc:  # pragma: no cover - defensive guard
        LOGGER.warning("Could not paginate inference artefacts: %s", exc)
        return None

    latest_obj = None
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if latest_obj is None or obj["LastModified"] > latest_obj["LastModified"]:
                    latest_obj = obj
    except Exception as exc:  # pragma: no cover - defensive guard
        LOGGER.warning("Could not list inference artefacts: %s", exc)
        return None

    if not latest_obj:
        return None

    key = latest_obj["Key"]
    obj = None
    try:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        content = obj["Body"].read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - defensive guard
        LOGGER.warning("Could not download inference artefact %s: %s", key, exc)
        return None
    finally:
        if obj is not None:
            try:
                obj["Body"].close()
            except Exception:  # pragma: no cover - best effort cleanup
                pass

    timestamp_dt = _extract_latest_timestamp(content)
    predicted_fault = _extract_predicted_fault(content)
    confidence = _extract_confidence(content)

    return {
        "content": content,
        "score": None,
        "source": f"s3://{bucket}/{key}",
        "timestamp": timestamp_dt.isoformat() + "Z" if timestamp_dt else None,
        "predicted_fault": predicted_fault,
        "confidence": confidence,
        "origin": "s3",
    }


def _kb_not_available_response(machine_id: str | None = None) -> dict:
    message = "Configure KNOWLEDGE_BASE_ID via environment variables or SSM to enable prediction search"
    response = {
        "error": "Knowledge Base not configured",
        "message": message,
    }
    if machine_id:
        response["machine_id"] = machine_id
    return response


@tool
def search_prediction_history(machine_id: str, query: str = "") -> dict:
    """Search the knowledge base for ML predictions and historical faults."""
    clients = _get_clients()
    settings = clients.settings

    if not settings.has_knowledge_base:
        return _kb_not_available_response(machine_id)

    kb_client = clients.bedrock_agent_runtime()
    if not kb_client:
        return {
            "error": "Knowledge Base client unavailable",
            "message": "Unable to create Bedrock Agent Runtime client; check AWS credentials",
            "machine_id": machine_id,
        }

    search_text = f"Device ID: {machine_id}"
    if query:
        search_text += f" {query}"

    try:
        response = kb_client.retrieve(
            knowledgeBaseId=settings.knowledge_base_id,
            retrievalQuery={"text": search_text},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 20}},
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        LOGGER.warning("Knowledge base retrieval failed: %s", exc)
        return {
            "error": "Knowledge Base query failed",
            "message": str(exc),
            "machine_id": machine_id,
        }

    predictions = []
    for result in response.get("retrievalResults", []):
        content = result.get("content", {}).get("text", "")
        timestamp_dt = _extract_latest_timestamp(content)
        predicted_fault = _extract_predicted_fault(content)
        confidence = _extract_confidence(content)
        predictions.append(
            {
                "content": content,
                "score": result.get("score", 0.0),
                "source": result.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
                "timestamp": timestamp_dt.isoformat() + "Z" if timestamp_dt else None,
                "predicted_fault": predicted_fault,
                "confidence": confidence,
                "origin": "knowledge_base",
            }
        )

    fallback_entry = _fetch_latest_inference_entry(machine_id)
    if fallback_entry:
        if not any(entry.get("source") == fallback_entry["source"] for entry in predictions):
            predictions.append(fallback_entry)

    predictions_found = len(predictions)

    def _sort_key(item: dict) -> datetime:
        ts_value = item.get("timestamp")
        if not ts_value:
            return datetime.min
        parsed = _parse_timestamp(ts_value)
        return parsed or datetime.min

    predictions.sort(key=_sort_key, reverse=True)

    latest_prediction = next((p for p in predictions if p.get("timestamp")), None)
    fault_counts = {}
    for entry in predictions:
        fault = entry.get("predicted_fault")
        if not fault:
            continue
        fault_counts[fault] = fault_counts.get(fault, 0) + 1

    result_payload = {
        "machine_id": machine_id,
        "query": search_text,
        "predictions_found": predictions_found,
        "predictions": predictions,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if latest_prediction:
        result_payload["latest_prediction"] = latest_prediction
    if fault_counts:
        result_payload["predicted_fault_counts"] = fault_counts

    return result_payload


@tool
def search_maintenance_playbook(
    fault_type: str = "",
    anomaly_type: str = "",
    severity: str = "",
) -> dict:
    """Search the playbook knowledge base for maintenance recommendations."""
    clients = _get_clients()
    settings = clients.settings

    if not settings.has_knowledge_base:
        return _kb_not_available_response()

    kb_client = clients.bedrock_agent_runtime()
    if not kb_client:
        return {
            "error": "Knowledge Base client unavailable",
            "message": "Unable to create Bedrock Agent Runtime client; check AWS credentials",
            "fault_type": fault_type,
            "anomaly_type": anomaly_type,
        }

    search_terms = []
    if fault_type:
        search_terms.append(f"fault type: {fault_type}")
    if anomaly_type:
        search_terms.append(f"anomaly: {anomaly_type}")
    if severity:
        search_terms.append(f"severity: {severity}")

    search_text = " ".join(search_terms) if search_terms else "maintenance playbook"

    try:
        response = kb_client.retrieve(
            knowledgeBaseId=settings.knowledge_base_id,
            retrievalQuery={"text": search_text},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        LOGGER.warning("Playbook retrieval failed: %s", exc)
        return {
            "error": "Knowledge Base query failed",
            "message": str(exc),
            "fault_type": fault_type,
            "anomaly_type": anomaly_type,
        }

    playbook_entries = []
    for result in response.get("retrievalResults", []):
        content = result.get("content", {}).get("text", "")
        playbook_entries.append(
            {
                "content": content,
                "relevance_score": result.get("score", 0.0),
                "source": result.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
            }
        )

    return {
        "fault_type": fault_type,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "playbook_entries_found": len(playbook_entries),
        "playbook_entries": playbook_entries,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@tool
def get_schedule_insights(query: str = "") -> dict:
    """Query the knowledge base for insights about scheduled maintenance tasks."""
    clients = _get_clients()
    settings = clients.settings

    if not settings.has_knowledge_base:
        return _kb_not_available_response()

    kb_client = clients.bedrock_agent_runtime()
    if not kb_client:
        return {
            "error": "Knowledge Base client unavailable",
            "message": "Unable to create Bedrock Agent Runtime client; check AWS credentials",
        }

    search_text = f"maintenance schedule {query}" if query else "maintenance schedule summary"

    try:
        response = kb_client.retrieve(
            knowledgeBaseId=settings.knowledge_base_id,
            retrievalQuery={"text": search_text},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}},
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        LOGGER.warning("Schedule insight retrieval failed: %s", exc)
        return {
            "error": "Knowledge Base query failed",
            "message": str(exc),
        }

    insights = []
    for result in response.get("retrievalResults", []):
        content = result.get("content", {}).get("text", "")
        insights.append(
            {
                "content": content,
                "relevance_score": result.get("score", 0.0),
                "source": result.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
            }
        )

    return {
        "query": search_text,
        "insights_found": len(insights),
        "insights": insights,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
