"""Windows Task Scheduler command construction; installation is operator-gated."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SchedulerTask:
    name: str
    command: tuple[str, ...]


def build_startup_task(*, python_executable: Path | str, module: str = "jarvis.handoff.service") -> SchedulerTask:
    action = f'"{python_executable}" -m {module} daemon'
    return SchedulerTask("JARVIS Git Handoff Automation", ("schtasks.exe", "/Create", "/TN", "JARVIS Git Handoff Automation", "/TR", action, "/SC", "ONLOGON", "/RL", "LIMITED", "/F"))
