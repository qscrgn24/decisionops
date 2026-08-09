from collections.abc import Generator
from contextlib import contextmanager
from threading import Lock

from app.core.config import settings


class OptimizationBusyError(RuntimeError):
    pass


class UserOptimizationBusyError(OptimizationBusyError):
    pass


class GlobalOptimizationBusyError(OptimizationBusyError):
    pass


class OptimizationExecutionGuard:
    def __init__(self, *, max_global: int) -> None:
        if max_global < 1:
            raise ValueError("max_global must be at least 1.")

        self.max_global = max_global
        self._lock = Lock()
        self._active_users: set[int] = set()
        self._active_total = 0

    @contextmanager
    def acquire(self, *, user_id: int) -> Generator[None, None, None]:
        with self._lock:
            if user_id in self._active_users:
                raise UserOptimizationBusyError("An Optimization is already running for this user.")

            if self._active_total >= self.max_global:
                raise GlobalOptimizationBusyError("Optimization capacity is currently full.")

            self._active_users.add(user_id)
            self._active_total += 1

        try:
            yield
        finally:
            with self._lock:
                self._active_users.discard(user_id)
                self._active_total -= 1


optimization_guard = OptimizationExecutionGuard(max_global=settings.MAX_GLOBAL_OPTIMIZATIONS)