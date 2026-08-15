"""Human-readable command-line entry point for JARVIS Daily Intelligence."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping

from .daily_summary import DailySummaryError, DailySummaryResult, daily_summary_service_from_environment


def render_daily_summary(result: DailySummaryResult) -> str:
    """Render only user-relevant summary content, never the raw MiTiR task record."""
    lines = ["Daily Intelligence"]
    if result.reporting_at:
        lines.append(f"Reported: {result.reporting_at}")
    if result.status:
        lines.append(f"Status: {result.status}")
    if result.headline:
        lines.extend(["", result.headline])
    _append_section(lines, "Important items", result.important_items)
    _append_section(lines, "Alerts", result.alerts)
    _append_section(lines, "Sources", result.source_references)
    return "\n".join(lines)


def _append_section(lines: list[str], title: str, values: tuple[object, ...]) -> None:
    if not values:
        return
    lines.extend(["", f"{title}:"])
    lines.extend(f"- {_render_value(value)}" for value in values)


def _render_value(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("title", "headline", "summary", "text"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate
        return "; ".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diagnostic", action="store_true",
        help="include safe task and correlation references after the readable summary",
    )
    args = parser.parse_args()
    try:
        result = daily_summary_service_from_environment().get_daily_summary()
    except DailySummaryError as exc:
        print(f"Daily Summary unavailable [{exc.category}]: {exc}", file=sys.stderr)
        return 2
    print(render_daily_summary(result))
    if args.diagnostic:
        print(
            "\nDiagnostics:"
            f"\n- Task: {result.task_id}"
            f"\n- Correlation: {result.correlation_id}"
            f"\n- Terminal state: {result.terminal_state}"
            f"\n- Completed: {result.completed_at or 'not provided'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
