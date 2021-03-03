import os
import sys

VERSION = "{}.{}".format(*sys.version_info)
PY_VERSION = "python{}.{}".format(*sys.version_info)
IS_PYPY = hasattr(sys, "pypy_version_info")
IS_WIN = sys.platform == "win32"
ABI_FLAGS = getattr(sys, "abiflags", "")

OK_ABS_SCRIPTS = [
    "python",
    PY_VERSION,
    "activate",
    "activate.bat",
    "activate_this.py",
    "activate.fish",
    "activate.csh",
    "activate.xsh",
]

