import os
import sys

from .common import PY_VERSION, IS_PYPY, IS_WIN, ABI_FLAGS
from .logger import LoggerInstance as _LoggerInstance


def mkdir(at_path):
    if not os.path.exists(at_path):
        _LoggerInstance.info("Creating %s", at_path)
        os.makedirs(at_path)
    else:
        _LoggerInstance.info("Directory %s already exists", at_path)


def is_executable(exe):
    """Checks a file is executable"""
    return os.path.isfile(exe) and os.access(exe, os.X_OK)


def path_locations(home_dir, dry_run=False):
    """Return the path locations for the environment (where libraries are,
    where scripts go, etc)"""
    home_dir = os.path.abspath(home_dir)
    lib_dir, inc_dir, bin_dir = None, None, None
    # XXX: We'd use distutils.sysconfig.get_python_inc/lib but its
    # prefix arg is broken: http://bugs.python.org/issue3386
    if IS_WIN:
        # Windows has lots of problems with executables with spaces in
        # the name; this function will remove them (using the ~1
        # format):
        if not dry_run:
            mkdir(home_dir)
        if " " in home_dir:
            import ctypes

            get_short_path_name = ctypes.windll.kernel32.GetShortPathNameW
            size = max(len(home_dir) + 1, 256)
            buf = ctypes.create_unicode_buffer(size)
            try:
                # noinspection PyUnresolvedReferences
                u = unicode
            except NameError:
                u = str
            ret = get_short_path_name(u(home_dir), buf, size)
            if not ret:
                print('Error: the path "{}" has a space in it'.format(home_dir))
                print("We could not determine the short pathname for it.")
                print("Exiting.")
                sys.exit(3)
            home_dir = str(buf.value)
        lib_dir = os.path.join(home_dir, "Lib")
        inc_dir = os.path.join(home_dir, "Include")
        bin_dir = os.path.join(home_dir, "Scripts")
    if IS_PYPY:
        lib_dir = home_dir
        inc_dir = os.path.join(home_dir, "include")
        bin_dir = os.path.join(home_dir, "bin")
    elif not IS_WIN:
        lib_dir = os.path.join(home_dir, "lib", PY_VERSION)
        inc_dir = os.path.join(home_dir, "include", PY_VERSION + ABI_FLAGS)
        bin_dir = os.path.join(home_dir, "bin")
    return home_dir, lib_dir, inc_dir, bin_dir



