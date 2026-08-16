# Phase 5 Operator Runbook

## Safe modes

- `dry-run`: parse, validate, policy-check, and report without creating a worktree or invoking an agent.
- `one-shot`: fetch the dedicated monitoring clone once; do not use a developer worktree.
- `daemon`: run only after the monitoring clone, state directory, retention, kill switch, and scheduler account have been reviewed.

The emergency kill switch leaves L0 inspection available and blocks agent execution. Blocked and approval-required messages require an operator decision; never edit immutable incoming entries.

## Windows startup

The scheduler helper only builds the limited-account `schtasks.exe /Create ... /SC ONLOGON` command. Do not register it until the user explicitly approves the exact task/account/action. Review the command, disk space, Git clone location, and state/log roots first.

## Recovery and retention

On restart, inspect unfinished executions and publish/record a deterministic blocked outcome rather than guessing how to resume. Retain logs/worktrees according to configured limits; cleanup must be limited to runner-owned paths and must not remove developer worktrees.
