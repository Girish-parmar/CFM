"""Running research tasks in parallel (Module 17).

Backtests of many parameter sets, many instruments or many strategies are
independent of each other, so they parallelise well:

* ``backend="process"``: separate Python processes, true multi-core speed-up for
  Python-heavy work (bar-by-bar backtest loops). Tasks and results are pickled,
  so share large inputs once per worker with ``initializer``/``shared``.
* ``backend="thread"``: threads in one process. Cheap to start; helps when the
  work releases the GIL (NumPy, pandas, I/O such as downloading data).
* ``backend="serial"``: a plain loop, for debugging and reproducibility.

On Windows and macOS, process pools start with "spawn": call them from inside
``if __name__ == "__main__":`` in scripts. Inside a worker process
``parallel_map`` always runs serially, so nested pools cannot fork-bomb.
"""

from __future__ import annotations

import math
import multiprocessing as mp
import os
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any

_SHARED: dict[str, Any] = {}  # set once per worker process by the pool initializer
_LOCAL = threading.local()     # per-thread values for the serial and thread backends


def _set_shared(values: dict[str, Any]) -> None:
    _SHARED.clear()
    _SHARED.update(values)


def shared(name: str) -> Any:
    """Read a value that ``parallel_map(..., shared={...})`` sent to this worker.

    Values set for the current thread (serial and thread backends) take priority
    over values set for the current worker process (process backend), so
    concurrent or nested maps never see each other's data.
    """
    values = getattr(_LOCAL, "values", None)
    if values is not None and name in values:
        return values[name]
    return _SHARED[name]


class _WithShared:
    """Call ``func`` with ``values`` visible to ``shared()`` in the calling thread only."""

    def __init__(self, func: Callable[[Any], Any], values: dict[str, Any]) -> None:
        self.func, self.values = func, values

    def __call__(self, item: Any) -> Any:
        previous = getattr(_LOCAL, "values", None)
        _LOCAL.values = self.values
        try:
            return self.func(item)
        finally:
            _LOCAL.values = previous


def available_workers() -> int:
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:  # pragma: no cover - macOS/Windows
        return os.cpu_count() or 1


def in_worker_process() -> bool:
    return mp.parent_process() is not None


def parallel_map(
    func: Callable[[Any], Any],
    items: Iterable[Any],
    workers: int | None = None,
    backend: str = "process",
    shared: dict[str, Any] | None = None,
    chunksize: int | None = None,
) -> list[Any]:
    """``[func(item) for item in items]``, in parallel, preserving order.

    ``shared`` is a dict made available to every worker via ``shared(name)``;
    it is sent once per worker instead of once per task. ``func`` must be a
    module-level function for the process backend.
    """
    items = list(items)
    if backend not in ("process", "thread", "serial"):
        raise ValueError("backend must be 'process', 'thread' or 'serial'")
    workers = workers or available_workers()
    if backend == "serial" or workers == 1 or len(items) <= 1 or in_worker_process():
        run = _WithShared(func, shared or {})
        return [run(item) for item in items]
    workers = min(workers, len(items))
    if backend == "thread":
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(_WithShared(func, shared or {}), items))
    chunksize = chunksize or max(1, math.ceil(len(items) / (workers * 4)))
    with ProcessPoolExecutor(max_workers=workers, initializer=_set_shared, initargs=(shared or {},)) as pool:
        return list(pool.map(func, items, chunksize=chunksize))


def benchmark(func: Callable[[Any], Any], items: Iterable[Any], shared: dict[str, Any] | None = None,
              workers: int | None = None, backends: tuple[str, ...] = ("serial", "thread", "process")) -> dict[str, float]:
    """Wall-clock seconds for the same job on each backend."""
    items = list(items)
    timings = {}
    for backend in backends:
        start = time.perf_counter()
        parallel_map(func, items, workers=workers, backend=backend, shared=shared)
        timings[backend] = time.perf_counter() - start
    return timings
