from __future__ import annotations

import time
from collections import defaultdict


class AttemptTracker:
    def __init__(self, max_failures: int = 5, window_seconds: int = 900) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[str, list[float]] = defaultdict(list)

    def _prune(self, key: str, now: float) -> None:
        cutoff = now - self.window_seconds
        self._failures[key] = [stamp for stamp in self._failures[key] if stamp >= cutoff]

    def is_locked(self, key: str, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        self._prune(key, current)
        return len(self._failures[key]) >= self.max_failures

    def register_failure(self, key: str, now: float | None = None) -> None:
        current = time.time() if now is None else now
        self._prune(key, current)
        self._failures[key].append(current)

    def clear(self, key: str) -> None:
        self._failures.pop(key, None)
