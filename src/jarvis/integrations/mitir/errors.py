"""MiTiR client exceptions."""

from .models import TaskError


class MiTiRError(Exception):
    """Base class for MiTiR integration failures."""


class MiTiRTransportError(MiTiRError):
    """Network or invalid-response failure before a valid API error is received."""


class MiTiRAPIError(MiTiRError):
    """Structured error returned by MiTiR."""

    def __init__(self, status_code: int, error: TaskError) -> None:
        super().__init__(f"MiTiR API error {status_code}: {error.code}: {error.message}")
        self.status_code = status_code
        self.error = error

