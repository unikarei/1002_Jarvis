"""Synchronous client for MiTiR Integration API v0.2.0."""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib import error, request
from uuid import UUID

from pydantic import ValidationError

from .errors import MiTiRAPIError, MiTiRContractError, MiTiRTransportError
from .models import CapabilityList, ErrorEnvelope, Health, TaskRecord, TaskRequest


@dataclass(frozen=True)
class HTTPResponse:
    status_code: int
    body: bytes


class Transport(Protocol):
    def send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HTTPResponse: ...


class UrllibTransport:
    """Standard-library transport suitable for the Windows client."""

    def send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HTTPResponse:
        req = request.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return HTTPResponse(response.status, response.read())
        except error.HTTPError as exc:
            return HTTPResponse(exc.code, exc.read())
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise MiTiRTransportError(f"MiTiR request failed: {exc}") from exc


class MiTiRClient:
    """Contract-bound client; retries only safe reads and idempotent task creation."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: float = 10.0,
        max_retries: int = 2,
        retry_backoff: float = 0.25,
        transport: Transport | None = None,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must use http or https")
        if not token:
            raise ValueError("token must not be empty")
        if timeout <= 0 or max_retries < 0:
            raise ValueError("timeout must be positive and max_retries non-negative")
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._transport = transport or UrllibTransport()

    def get_health(self) -> Health:
        # The contract explicitly makes /health unauthenticated.
        data = self._request("GET", "/health", authenticated=False, retryable=True)
        return self._validate(Health, data)

    def list_capabilities(self) -> CapabilityList:
        data = self._request("GET", "/capabilities", authenticated=True, retryable=True)
        return self._validate(CapabilityList, data)

    def create_task(self, task: TaskRequest, *, idempotency_key: str) -> TaskRecord:
        if not 1 <= len(idempotency_key) <= 200:
            raise ValueError("idempotency_key length must be between 1 and 200")
        data = self._request(
            "POST",
            "/tasks",
            authenticated=True,
            retryable=True,
            json_body=task.model_dump(mode="json", exclude_none=True),
            extra_headers={"Idempotency-Key": idempotency_key},
        )
        return self._validate(TaskRecord, data)

    def get_task(self, task_id: UUID | str) -> TaskRecord:
        identifier = self._validated_uuid(task_id)
        data = self._request("GET", f"/tasks/{identifier}", authenticated=True, retryable=True)
        return self._validate(TaskRecord, data)

    def cancel_task(self, task_id: UUID | str) -> TaskRecord:
        identifier = self._validated_uuid(task_id)
        data = self._request(
            "POST", f"/tasks/{identifier}/cancel", authenticated=True, retryable=True
        )
        return self._validate(TaskRecord, data)

    @staticmethod
    def _validated_uuid(value: UUID | str) -> str:
        try:
            return str(UUID(str(value)))
        except ValueError as exc:
            raise ValueError("task_id must be a UUID") from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool,
        retryable: bool,
        json_body: dict[str, Any] | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if authenticated:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra_headers:
            headers.update(extra_headers)
        body = None
        if json_body is not None:
            body = json.dumps(json_body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"

        attempts = self._max_retries + 1 if retryable else 1
        for attempt in range(attempts):
            try:
                response = self._transport.send(
                    method, self._base_url + path, headers, body, self._timeout
                )
            except MiTiRTransportError:
                if attempt + 1 == attempts:
                    raise
                time.sleep(self._retry_backoff * (2**attempt))
                continue

            data = self._decode(response.body)
            if 200 <= response.status_code < 300:
                return data
            if response.status_code >= 500 and attempt + 1 < attempts:
                time.sleep(self._retry_backoff * (2**attempt))
                continue
            try:
                envelope = ErrorEnvelope.model_validate(data)
            except ValidationError as exc:
                raise MiTiRContractError(
                    f"MiTiR returned HTTP {response.status_code} without a valid error envelope"
                ) from exc
            raise MiTiRAPIError(response.status_code, envelope.error)
        raise AssertionError("unreachable")

    @staticmethod
    def _decode(body: bytes) -> dict[str, Any]:
        try:
            value = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MiTiRContractError("MiTiR returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise MiTiRContractError("MiTiR returned a non-object JSON response")
        return value

    @staticmethod
    def _validate(model: type[Any], data: dict[str, Any]) -> Any:
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise MiTiRContractError("MiTiR response does not match the Integration API contract") from exc
