#!/usr/bin/env python3
from __future__ import annotations
import sys
import platform

mods = [
    ("python", platform.python_version()),
]

try:
    import numpy as np  # type: ignore
    mods.append(("numpy", np.__version__))
except Exception:
    mods.append(("numpy", "missing"))

try:
    import matplotlib  # type: ignore
    ver = getattr(matplotlib, "__version__", "unknown")
    mods.append(("matplotlib", ver))
except Exception:
    mods.append(("matplotlib", "missing"))

print("\n".join(f"{k}: {v}" for k,v in mods))
