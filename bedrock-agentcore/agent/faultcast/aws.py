"""Helpers for creating AWS service clients used by the FaultCast agent."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from faultcast.config import Settings, load_settings

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover - local development without AWS libs
    boto3 = None  # type: ignore
    BotoCoreError = ClientError = Exception  # type: ignore

_LOGGER = logging.getLogger(__name__)


class AWSClients:
    """Lazily constructs AWS SDK clients based on runtime settings."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._bedrock_agent_runtime = None
        self._s3 = None
        self._ses = None

    @property
    def has_bedrock(self) -> bool:
        return bool(boto3 and self.settings.has_knowledge_base)

    @property
    def has_s3(self) -> bool:
        return bool(boto3 and self.settings.has_schedule_storage)

    @property
    def has_ses(self) -> bool:
        return bool(boto3 and self.settings.notification_email)

    def bedrock_agent_runtime(self):
        if not self.has_bedrock:
            return None
        if self._bedrock_agent_runtime is None:
            try:
                self._bedrock_agent_runtime = boto3.client(
                    "bedrock-agent-runtime",
                    region_name=self.settings.knowledge_base_region or self.settings.aws_region,
                )
            except Exception as exc:  # pragma: no cover - defensive guard
                _LOGGER.warning("Could not create Bedrock Agent Runtime client: %s", exc)
                return None
        return self._bedrock_agent_runtime

    def s3(self):
        if not self.has_s3:
            return None
        if self._s3 is None:
            try:
                self._s3 = boto3.client("s3", region_name=self.settings.aws_region)
            except Exception as exc:  # pragma: no cover - defensive guard
                _LOGGER.warning("Could not create S3 client: %s", exc)
                return None
        return self._s3

    def ses(self):
        if not self.has_ses:
            return None
        if self._ses is None:
            try:
                self._ses = boto3.client("ses", region_name=self.settings.aws_region)
            except Exception as exc:  # pragma: no cover - defensive guard
                _LOGGER.warning("Could not create SES client: %s", exc)
                return None
        return self._ses


@lru_cache(maxsize=1)
def get_clients(settings: Optional[Settings] = None) -> AWSClients:
    cfg = settings or load_settings()
    return AWSClients(cfg)


__all__ = ["AWSClients", "get_clients"]
