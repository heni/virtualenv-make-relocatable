import os
import sys

from .common import IS_WIN, VERSION, OK_ABS_SCRIPTS
from .logger import LoggerInstance as _LoggerInstance
from .utils import path_locations


def make_environment_relocatable(home_dir):
    """
    Makes the already-existing environment use relative paths, and takes out
    the #!-based environment selection in scripts.
    """
    home_dir, lib_dir, inc_dir, bin_dir = path_locations(home_dir)
    activate_this = os.path.join(bin_dir, "activate_this.py")
    if not os.path.exists(activate_this):
        _LoggerInstance.fatal(
            "The environment doesn't have a file %s -- please re-run virtualenv " "on this environment to update it",
            activate_this,
        )
    fixup_scripts(home_dir, bin_dir)
    fixup_pth_and_egg_link(home_dir)



def fixup_scripts(_, bin_dir):
    if IS_WIN:
        new_shebang_args = ("{} /c".format(os.path.normcase(os.environ.get("COMSPEC", "cmd.exe"))), "", ".exe")
    else:
        new_shebang_args = ("/usr/bin/env", VERSION, "")

    # This is what we expect at the top of scripts:
    shebang = "#!{}".format(
        os.path.normcase(os.path.join(os.path.abspath(bin_dir), "python{}".format(new_shebang_args[2])))
    )
    # This is what we'll put:
    new_shebang = "#!{} python{}{}".format(*new_shebang_args)

    for filename in os.listdir(bin_dir):
        filename = os.path.join(bin_dir, filename)
        if not os.path.isfile(filename):
            # ignore child directories, e.g. .svn ones.
            continue
        with open(filename, "rb") as f:
            try:
                lines = f.read().decode("utf-8").splitlines()
            except UnicodeDecodeError:
                # This is probably a binary program instead
                # of a script, so just ignore it.
                continue
        if not lines:
            _LoggerInstance.warn("Script %s is an empty file", filename)
            continue

        old_shebang = lines[0].strip()
        old_shebang = old_shebang[0:2] + os.path.normcase(old_shebang[2:])

        if not old_shebang.startswith(shebang):
            if os.path.basename(filename) in OK_ABS_SCRIPTS:
                _LoggerInstance.debug("Cannot make script %s relative", filename)
            elif lines[0].strip() == new_shebang:
                _LoggerInstance.info("Script %s has already been made relative", filename)
            else:
                _LoggerInstance.warn(
                    "Script %s cannot be made relative (it's not a normal script that starts with %s)",
                    filename,
                    shebang,
                )
            continue
        _LoggerInstance.notify("Making script %s relative", filename)
        script = relative_script([new_shebang] + lines[1:])
        with open(filename, "wb") as f:
            f.write("\n".join(script).encode("utf-8"))



def relative_script(lines):
    """Return a script that'll work in a relocatable environment."""
    activate = (
        "import os; "
        "activate_this=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'activate_this.py'); "
        "exec(compile(open(activate_this).read(), activate_this, 'exec'), { '__file__': activate_this}); "
        "del os, activate_this"
    )
    # Find the last future statement in the script. If we insert the activation
    # line before a future statement, Python will raise a SyntaxError.
    activate_at = None
    for idx, line in reversed(list(enumerate(lines))):
        if line.split()[:3] == ["from", "__future__", "import"]:
            activate_at = idx + 1
            break
    if activate_at is None:
        # Activate after the shebang.
        activate_at = 1
    return lines[:activate_at] + ["", activate, ""] + lines[activate_at:]



def fixup_pth_and_egg_link(home_dir, sys_path=None):
    """Makes .pth and .egg-link files use relative paths"""
    home_dir = os.path.normcase(os.path.abspath(home_dir))
    if sys_path is None:
        sys_path = sys.path
    for a_path in sys_path:
        if not a_path:
            a_path = "."
        if not os.path.isdir(a_path):
            continue
        a_path = os.path.normcase(os.path.abspath(a_path))
        if not a_path.startswith(home_dir):
            _LoggerInstance.debug("Skipping system (non-environment) directory %s", a_path)
            continue
        for filename in os.listdir(a_path):
            filename = os.path.join(a_path, filename)
            if filename.endswith(".pth"):
                if not os.access(filename, os.W_OK):
                    _LoggerInstance.warn("Cannot write .pth file %s, skipping", filename)
                else:
                    fixup_pth_file(filename)
            if filename.endswith(".egg-link"):
                if not os.access(filename, os.W_OK):
                    _LoggerInstance.warn("Cannot write .egg-link file %s, skipping", filename)
                else:
                    fixup_egg_link(filename)



def fixup_pth_file(filename):
    lines = []
    with open(filename) as f:
        prev_lines = f.readlines()
    for line in prev_lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("import ") or os.path.abspath(line) != line:
            lines.append(line)
        else:
            new_value = make_relative_path(filename, line)
            if line != new_value:
                _LoggerInstance.debug("Rewriting path {} as {} (in {})".format(line, new_value, filename))
            lines.append(new_value)
    if lines == prev_lines:
        _LoggerInstance.info("No changes to .pth file %s", filename)
        return
    _LoggerInstance.notify("Making paths in .pth file %s relative", filename)
    with open(filename, "w") as f:
        f.write("\n".join(lines) + "\n")


def fixup_egg_link(filename):
    with open(filename) as f:
        link = f.readline().strip()
    if os.path.abspath(link) != link:
        _LoggerInstance.debug("Link in %s already relative", filename)
        return
    new_link = make_relative_path(filename, link)
    _LoggerInstance.notify("Rewriting link {} in {} as {}".format(link, filename, new_link))
    with open(filename, "w") as f:
        f.write(new_link)


def make_relative_path(source, dest, dest_is_directory=True):
    """
    Make a filename relative, where the filename is dest, and it is
    being referred to from the filename source.
        >>> make_relative_path('/usr/share/something/a-file.pth',
        ...                    '/usr/share/another-place/src/Directory')
        '../another-place/src/Directory'
        >>> make_relative_path('/usr/share/something/a-file.pth',
        ...                    '/home/user/src/Directory')
        '../../../home/user/src/Directory'
        >>> make_relative_path('/usr/share/a-file.pth', '/usr/share/')
        './'
    """
    source = os.path.dirname(source)
    if not dest_is_directory:
        dest_filename = os.path.basename(dest)
        dest = os.path.dirname(dest)
    else:
        dest_filename = None
    dest = os.path.normpath(os.path.abspath(dest))
    source = os.path.normpath(os.path.abspath(source))
    dest_parts = dest.strip(os.path.sep).split(os.path.sep)
    source_parts = source.strip(os.path.sep).split(os.path.sep)
    while dest_parts and source_parts and dest_parts[0] == source_parts[0]:
        dest_parts.pop(0)
        source_parts.pop(0)
    full_parts = [".."] * len(source_parts) + dest_parts
    if not dest_is_directory and dest_filename is not None:
        full_parts.append(dest_filename)
    if not full_parts:
        # Special case for the current directory (otherwise it'd be '')
        return "./"
    return os.path.sep.join(full_parts)

