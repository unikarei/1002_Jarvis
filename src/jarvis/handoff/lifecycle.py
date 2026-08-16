"""Idempotent cancellation and deterministic interrupted-job recovery."""
from .state_store import ExecutionRecord, StateStore

_TERMINAL = frozenset({"completed", "failed", "cancelled", "rejected"})


class CancellationService:
    def __init__(self, store: StateStore) -> None: self._store = store
    def cancel(self, message_id: str) -> ExecutionRecord:
        record = self._store.get(message_id)
        if record is None: raise KeyError(message_id)
        if record.processing_state in _TERMINAL: return record
        return self._store.update(message_id, processing_state="cancelled", finished=True)


class RecoveryManager:
    def __init__(self, store: StateStore) -> None: self._store = store
    def recover_interrupted(self) -> tuple[ExecutionRecord, ...]:
        return tuple(self._store.update(record.message_id, processing_state="blocked", error_category="interrupted", finished=True) for record in self._store.unfinished())
