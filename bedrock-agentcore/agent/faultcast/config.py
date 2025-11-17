"""Runtime configuration helpers for the FaultCast agent."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover - boto3 optional for local dev
    boto3 = None  # type: ignore
    BotoCoreError = ClientError = Exception  # type: ignore

_LOGGER = logging.getLogger(__name__)

_PLACEHOLDER_MARKERS = {
    "",
    "changeme",
    "placeholder",
    "your-value",
    "your_value",
    "todo",
}


def _looks_like_placeholder(value: str) -> bool:
    """Return True if the string appears to be a template placeholder."""
    lowered = value.lower()
    if lowered in _PLACEHOLDER_MARKERS:
        return True
    if lowered.startswith("your_"):
        return True
    if lowered.startswith("<") and lowered.endswith(">"):
        return True
    if value.startswith("{{") and value.endswith("}}"):
        return True
    return False


def _clean(value: Optional[str], default: Optional[str] = None) -> Optional[str]:
    """Normalize environment values, treating placeholders as missing."""
    if value is None:
        return default
    trimmed = value.strip()
    if not trimmed:
        return default
    if _looks_like_placeholder(trimmed):
        return default
    return trimmed


@dataclass
class Settings:
    """Holds runtime configuration derived from env/SSM."""

    aws_region: str = "eu-west-1"
    ssm_parameter_prefix: str = "/faultcast/v2"
    knowledge_base_id: Optional[str] = None
    knowledge_base_region: str = "eu-west-1"
    work_schedule_bucket: Optional[str] = None
    work_schedule_prefix: str = "maintenance-schedules/"
    notification_email: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)

    def apply(self) -> None:
        """Mirror the settings into ``os.environ`` for legacy call paths."""
        os.environ["AWS_REGION"] = self.aws_region
        os.environ.setdefault("AWS_DEFAULT_REGION", self.aws_region)
        os.environ["SSM_PARAMETER_PREFIX"] = self.ssm_parameter_prefix
        if self.knowledge_base_region:
            os.environ["KNOWLEDGE_BASE_REGION"] = self.knowledge_base_region
        if self.knowledge_base_id:
            os.environ["KNOWLEDGE_BASE_ID"] = self.knowledge_base_id
        if self.work_schedule_bucket:
            os.environ["WORK_SCHEDULE_BUCKET"] = self.work_schedule_bucket
        if self.work_schedule_prefix:
            os.environ["WORK_SCHEDULE_PREFIX"] = self.work_schedule_prefix
        if self.notification_email:
            os.environ["NOTIFICATION_EMAIL"] = self.notification_email
        for key, value in self.extra.items():
            os.environ[key] = value

    @property
    def has_knowledge_base(self) -> bool:
        return bool(self.knowledge_base_id)

    @property
    def has_schedule_storage(self) -> bool:
        return bool(self.work_schedule_bucket and self.work_schedule_prefix)


def _read_environment() -> Settings:
    region = _clean(os.getenv("AWS_REGION")) or _clean(
        os.getenv("AWS_DEFAULT_REGION")
    ) or "eu-west-1"
    kb_region = _clean(os.getenv("KNOWLEDGE_BASE_REGION"), region) or region
    prefix = _clean(os.getenv("WORK_SCHEDULE_PREFIX"), "maintenance-schedules/")
    if prefix and not prefix.endswith("/"):
        prefix = f"{prefix}/"

    settings = Settings(
        aws_region=region,
        ssm_parameter_prefix=_clean(os.getenv("SSM_PARAMETER_PREFIX"), "/faultcast/v2"),
        knowledge_base_id=_clean(os.getenv("KNOWLEDGE_BASE_ID")),
        knowledge_base_region=kb_region,
        work_schedule_bucket=_clean(os.getenv("WORK_SCHEDULE_BUCKET")),
        work_schedule_prefix=prefix or "maintenance-schedules/",
        notification_email=_clean(os.getenv("NOTIFICATION_EMAIL")),
    )
    return settings


def _fetch_ssm_parameters(settings: Settings) -> Dict[str, str]:
    """Load configuration overrides from SSM Parameter Store."""
    if not boto3:
        _LOGGER.debug("boto3 not available; skipping SSM parameter lookup")
        return {}

    try:
        ssm = boto3.client("ssm", region_name=settings.aws_region)
    except Exception as exc:  # pragma: no cover - defensive guard
        _LOGGER.warning("Could not create SSM client: %s", exc)
        return {}

    parameters: Dict[str, str] = {}
    try:
        paginator = ssm.get_paginator("get_parameters_by_path")
        for page in paginator.paginate(
            Path=settings.ssm_parameter_prefix,
            Recursive=True,
            WithDecryption=True,
        ):
            for param in page.get("Parameters", []):
                key = param["Name"].split("/")[-1].upper().replace("-", "_")
                parameters[key] = param.get("Value", "")
    except (BotoCoreError, ClientError) as exc:
        _LOGGER.warning("Could not retrieve SSM parameters from %s: %s", settings.ssm_parameter_prefix, exc)
    except Exception as exc:  # pragma: no cover - defensive guard
        _LOGGER.warning("Unexpected error loading SSM parameters: %s", exc)

    return parameters


def _merge_overrides(settings: Settings, overrides: Dict[str, str]) -> Settings:
    if not overrides:
        return settings

    merged = Settings(
        aws_region=_clean(overrides.get("AWS_REGION"), settings.aws_region)
        or settings.aws_region,
        ssm_parameter_prefix=settings.ssm_parameter_prefix,
        knowledge_base_id=_clean(overrides.get("KNOWLEDGE_BASE_ID"), settings.knowledge_base_id),
        knowledge_base_region=_clean(overrides.get("KNOWLEDGE_BASE_REGION"), settings.knowledge_base_region)
        or settings.knowledge_base_region,
        work_schedule_bucket=_clean(overrides.get("WORK_SCHEDULE_BUCKET"), settings.work_schedule_bucket),
        work_schedule_prefix=_clean(overrides.get("WORK_SCHEDULE_PREFIX"), settings.work_schedule_prefix)
        or settings.work_schedule_prefix,
        notification_email=_clean(overrides.get("NOTIFICATION_EMAIL"), settings.notification_email),
        extra={key: value for key, value in overrides.items() if key not in {
            "AWS_REGION",
            "KNOWLEDGE_BASE_ID",
            "KNOWLEDGE_BASE_REGION",
            "WORK_SCHEDULE_BUCKET",
            "WORK_SCHEDULE_PREFIX",
            "NOTIFICATION_EMAIL",
        }},
    )

    if merged.work_schedule_prefix and not merged.work_schedule_prefix.endswith("/"):
        merged.work_schedule_prefix = f"{merged.work_schedule_prefix}/"

    return merged


@lru_cache(maxsize=1)
def load_settings(use_ssm: bool = True) -> Settings:
    """Load configuration from environment and optional SSM."""
    settings = _read_environment()
    if use_ssm:
        overrides = _fetch_ssm_parameters(settings)
        settings = _merge_overrides(settings, overrides)
    return settings


def apply_settings(settings: Optional[Settings] = None, use_ssm: bool = True) -> Settings:
    """Load settings and apply them to ``os.environ`` for legacy callers."""
    cfg = settings or load_settings(use_ssm=use_ssm)
    cfg.apply()
    return cfg


__all__ = ["Settings", "load_settings", "apply_settings"]
