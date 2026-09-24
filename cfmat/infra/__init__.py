"""Infrastructure helpers.

parallel   serial/thread/process map with shared worker data
paths      sample-data, user-data and output locations
plotting   off-screen charts saved to the output folder (import it explicitly:
           it selects a matplotlib backend)
"""

from . import parallel, paths

__all__ = [
    "parallel",
    "paths",
]
