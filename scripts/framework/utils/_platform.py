import os
import shutil
import subprocess
import sys
from typing import Sequence

from ._common import MAX_DIAGNOSTIC_CHARS
from ._logging import get_logger


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    return sys.platform.startswith("darwin")


def is_virtual_environment() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def get_platform_name() -> str:
    if is_windows():
        return "Windows"
    if is_linux():
        return "Linux"
    if is_macos():
        return "macOS"
    return sys.platform


def check_command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def get_python_path() -> str:
    return sys.executable


def get_python_version(python_cmd: str | Sequence[str] | None = None) -> str:
    if python_cmd is None:
        return sys.version.split()[0]

    try:
        result = subprocess.run(
            [*normalize_python_command(python_cmd), "-c", "import sys; print(sys.version.split()[0])"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as exc:
        get_logger().debug("Python version probe failed: %s", exc)
        return "unknown"

    if result.returncode == 0:
        return result.stdout.strip() or "unknown"
    return "unknown"


def command_failure_summary(result: subprocess.CompletedProcess, max_chars: int = MAX_DIAGNOSTIC_CHARS) -> str:
    parts = []
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if stdout:
        parts.append(f"stdout: {stdout}")
    if stderr:
        parts.append(f"stderr: {stderr}")
    if not parts:
        parts.append(f"exit code: {result.returncode}")

    summary = "\n".join(parts)
    if len(summary) > max_chars:
        return summary[: max_chars - 3] + "..."
    return summary


def check_python_runnable(
    python_cmd: str | Sequence[str] | None = None,
    timeout: int = 30,
) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [*normalize_python_command(python_cmd), "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as exc:
        return False, str(exc)

    if result.returncode == 0:
        return True, (result.stdout or "").strip()
    return False, command_failure_summary(result)


def get_env_info() -> dict:
    from ._install import check_playwright_installed

    return {
        "platform": get_platform_name(),
        "python": sys.version,
        "python_path": sys.executable,
        "encoding": sys.stdout.encoding or "unknown",
        "cwd": os.getcwd(),
        "playwright_installed": check_playwright_installed(),
        "pip_available": check_command_exists("pip") or check_command_exists("pip3"),
    }


def get_python_command() -> list[str]:
    if sys.executable:
        return [sys.executable]

    if is_windows():
        python = shutil.which("python")
        if python:
            return [python]
        return ["python"]

    return ["python"]


def get_default_venv_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".venv"))


def get_default_venv_python() -> str:
    if is_windows():
        return os.path.join(get_default_venv_dir(), "Scripts", "python.exe")
    return os.path.join(get_default_venv_dir(), "bin", "python")


def normalize_python_command(python_cmd: str | Sequence[str] | None = None) -> list[str]:
    if python_cmd is None:
        return get_python_command()
    if isinstance(python_cmd, str):
        return [python_cmd]
    return list(python_cmd)
