"""Read-only conversational JARVIS entry point."""

from __future__ import annotations

import argparse
import io
import os
import sys

from .conversation import SecretaryService
from .integrations.mitir.client import MiTiRClient
from .integrations.mitir.daily_summary import DailySummaryService
from .integrations.mitir.research_summary import ResearchSummaryService
from .integrations.mitir.specialist_read import ReadOnlySpecialistRunner
from .integrations.mitir.trading_context import TradingContextService


def secretary_from_environment(environment: dict[str, str] | None = None) -> SecretaryService:
    runtime = os.environ if environment is None else environment
    base_url, token = runtime.get("MITIR_BASE_URL"), runtime.get("MITIR_INTEGRATION_TOKEN")
    if not base_url or not token:
        raise ValueError("MiTiR runtime configuration is missing")
    client = MiTiRClient(base_url, token)
    return SecretaryService(
        DailySummaryService(client),
        ResearchSummaryService(ReadOnlySpecialistRunner(client)),
        TradingContextService(ReadOnlySpecialistRunner(client)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", help="one Daily, Research, or Trading status request")
    parser.add_argument("--diagnostic", action="store_true", help="include safe task/correlation metadata")
    args = parser.parse_args()
    try:
        response = secretary_from_environment().respond(args.message)
    except ValueError as exc:
        _safe_print(f"JARVIS unavailable [configuration_error]: {exc}", file=sys.stderr)
        return 2
    _safe_print(response.text)
    if args.diagnostic and response.task_id:
        _safe_print(f"\nDiagnostics:\n- Domain: {response.domain}\n- Task: {response.task_id}\n- Correlation: {response.correlation_id}\n- Terminal state: {response.terminal_state}")
    return 0


def _safe_print(text: str, *, file: io.TextIOBase = sys.stdout) -> None:
    """Keep a Windows legacy console from turning returned MiTiR Unicode into a traceback."""
    encoding = file.encoding or "utf-8"
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        print(text.encode(encoding, errors="replace").decode(encoding), file=file)


if __name__ == "__main__":
    raise SystemExit(main())
