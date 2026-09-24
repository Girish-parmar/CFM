"""Load tools/route_manager.py as a module (tools/ is a scripts folder, not a package)."""

import importlib.util
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "tools" / "route_manager.py"


def load_route_manager():
    if "route_manager" in sys.modules:
        return sys.modules["route_manager"]
    spec = importlib.util.spec_from_file_location("route_manager", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["route_manager"] = module
    spec.loader.exec_module(module)
    return module
