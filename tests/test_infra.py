"""Tests for cfmat.infra: parallel map."""

import math
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from cfmat.infra import parallel


def square_plus_offset(x):
    return x * x + parallel.shared("offset")


def nested(x):
    # a pool inside a worker must fall back to serial instead of spawning more processes
    return sum(parallel.parallel_map(abs, [-x, x], workers=2, backend="process"))


@pytest.mark.parametrize("backend", ["serial", "thread", "process"])
def test_parallel_map_preserves_order_and_shares_data(backend):
    out = parallel.parallel_map(square_plus_offset, range(20), workers=2, backend=backend, shared={"offset": 1})
    assert out == [x * x + 1 for x in range(20)]


def test_nested_pools_run_serially_inside_workers():
    assert parallel.parallel_map(nested, [1, 2, 3], workers=2, backend="process") == [2, 4, 6]


def test_shared_values_do_not_leak_between_calls():
    parallel.parallel_map(square_plus_offset, [1], backend="serial", shared={"offset": 5})
    with pytest.raises(KeyError):
        parallel.shared("offset")


def test_bad_backend_and_benchmark():
    with pytest.raises(ValueError):
        parallel.parallel_map(abs, [1, 2], backend="gpu")
    timings = parallel.benchmark(math.sqrt, range(100), backends=("serial", "thread"))
    assert set(timings) == {"serial", "thread"} and all(t >= 0 for t in timings.values())


def offset_after_pause(x):
    time.sleep(0.01)
    return x + parallel.shared("offset")


def run_map_with_offset(offset):
    return parallel.parallel_map(offset_after_pause, range(8), workers=4, backend="thread", shared={"offset": offset})


def test_concurrent_thread_maps_keep_their_own_shared_values():
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = pool.map(run_map_with_offset, [100, 200])
    assert a == [x + 100 for x in range(8)] and b == [x + 200 for x in range(8)]


def inner_serial_map(x):
    parallel.parallel_map(abs, [1, 2], backend="serial", shared={"offset": -999})
    return x + parallel.shared("offset")   # the nested call must not overwrite this worker's value


def test_nested_serial_map_inside_thread_worker_restores_values():
    out = parallel.parallel_map(inner_serial_map, range(6), workers=3, backend="thread", shared={"offset": 1})
    assert out == [x + 1 for x in range(6)]
