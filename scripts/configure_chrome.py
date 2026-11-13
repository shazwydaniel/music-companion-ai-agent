"""Make this project's activated virtualenv open local Streamlit URLs in Chrome."""

# 1. Limit the installer to macOS and this repository's own .venv.
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
CHROME = Path("/Applications/Google Chrome.app")
CHROME_USER = Path.home() / "Applications" / "Google Chrome.app"


# 2. Streamlit 1.67 calls `open URL` on macOS; an activated venv puts this shim
#    first on PATH. Other `open` arguments continue to use the system command.
SHIM = """#!/bin/sh
# Riffin local Chrome opener; installed only in this project's ignored .venv.
case "$1" in
  http://localhost:*|https://localhost:*|http://127.0.0.1:*|https://127.0.0.1:*)
    exec /usr/bin/open -a 'Google Chrome' "$@"
    ;;
esac
exec /usr/bin/open "$@"
"""


def main() -> int:
    """Install an idempotent local shim without changing the OS default browser."""
    if sys.platform != "darwin":
        print("Chrome auto-open setup is for macOS only.")
        return 1
    if Path(sys.prefix).resolve() != VENV.resolve():
        print("Run this script with this repository's .venv/bin/python.")
        return 1
    if not (CHROME.is_dir() or CHROME_USER.is_dir()):
        print("Google Chrome is not installed in Applications.")
        return 1
    target = VENV / "bin" / "open"
    if target.exists() and target.read_text(encoding="utf-8") != SHIM:
        print("An existing .venv/bin/open was left unchanged.")
        return 1
    target.write_text(SHIM, encoding="utf-8")
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("Configured this .venv to open local Streamlit URLs in Google Chrome.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
