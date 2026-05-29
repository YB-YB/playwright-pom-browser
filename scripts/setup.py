#!/usr/bin/env python
"""Environment setup for the browser automation skill."""

import argparse
import os
import shutil
import subprocess
import sys
import venv

# --- Python version guard ---
_MIN_PYTHON = (3, 10)
if sys.version_info < _MIN_PYTHON:
    sys.exit(
        f"Python {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}+ is required. "
        f"You are running Python {sys.version_info.major}.{sys.version_info.minor}."
    )

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from framework.utils import (  # noqa: E402
    check_playwright_browsers,
    check_playwright_installed,
    check_python_runnable,
    DEFAULT_BROWSER_PROBE_TIMEOUT,
    get_platform_name,
    get_python_path,
    get_python_command,
    get_python_version,
    install_playwright_browsers,
    install_requirements,
    is_linux,
    RUN_TEST_SCRIPT,
    safe_input,
    safe_print,
    SCRIPT_DIR,
    SETUP_SCRIPT,
)

SKILL_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_VENV_DIR = os.path.abspath(os.path.join(os.getcwd(), ".venv"))


def venv_python_path(venv_dir: str) -> str:
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def path_is_within(path: str, parent: str) -> bool:
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(parent)]) == os.path.abspath(parent)
    except ValueError:
        return False


def validate_venv_location(venv_dir: str) -> None:
    if path_is_within(venv_dir, SKILL_DIR):
        raise RuntimeError(
            "Refusing to create or use a virtual environment inside the skill directory: "
            f"{venv_dir}\n"
            "Create a task/project directory first and pass that environment explicitly, for example:\n"
            f"  {' '.join(get_python_command())} {SETUP_SCRIPT} --browser chromium --venv C:\\path\\to\\browser-task\\.venv"
        )


def recreate_venv_dir(venv_dir: str) -> None:
    if not os.path.isdir(venv_dir):
        return
    if not os.path.isfile(os.path.join(venv_dir, "pyvenv.cfg")):
        raise RuntimeError(f"Refusing to recreate {venv_dir}: pyvenv.cfg was not found.")
    safe_print(f"Recreating virtual environment: {venv_dir}")
    shutil.rmtree(venv_dir)


def create_venv_if_needed(venv_dir: str, recreate: bool = False) -> str:
    validate_venv_location(venv_dir)
    if recreate:
        recreate_venv_dir(venv_dir)

    python_path = venv_python_path(venv_dir)
    if os.path.exists(python_path):
        ok, detail = check_python_runnable(python_path)
        if not ok:
            raise RuntimeError(
                f"Virtual environment Python exists but is not runnable: {python_path}\n"
                f"{detail}\n"
                "Recreate this environment with --recreate-venv, or delete it and rerun setup."
            )
        return python_path

    safe_print(f"Creating virtual environment: {venv_dir}")
    try:
        venv.EnvBuilder(with_pip=True).create(venv_dir)
    except Exception as exc:
        raise RuntimeError(f"Failed to create virtual environment at {venv_dir}: {exc}") from exc

    if not os.path.exists(python_path):
        raise RuntimeError(f"Virtual environment was created, but Python was not found at {python_path}")
    return python_path


def ensure_venv_pip_ready(python_path: str) -> bool:
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        safe_print(f"Unable to check venv pip: {exc}")
        return False

    if result.returncode == 0:
        return True

    safe_print("Virtual environment exists but pip is not available.")
    if result.stdout.strip():
        safe_print(result.stdout.strip())
    if result.stderr.strip():
        safe_print(result.stderr.strip())
    safe_print("Recreate this environment with --recreate-venv, or delete it and rerun setup.")
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set up Python Playwright for browser automation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py --check --venv C:\\path\\to\\browser-task\\.venv
  python setup.py --check --no-venv
  python setup.py --browser chromium --venv C:\\path\\to\\browser-task\\.venv
  python setup.py --browser chromium --with-deps --venv /path/to/browser-task/.venv
  python /path/to/playwright-pom-browser/scripts/setup.py --browser chromium --venv .venv
  python /path/to/playwright-pom-browser/scripts/setup.py --browser chromium --venv .venv --recreate-venv
  python setup.py --browser chromium --no-venv
  python setup.py --all --venv C:\\path\\to\\browser-task\\.venv
        """,
    )
    parser.add_argument("--check", action="store_true", help="Check only; do not install anything.")
    parser.add_argument(
        "--venv",
        default=None,
        help="Task/project virtual environment directory to create/use. Defaults to current working directory/.venv.",
    )
    parser.add_argument(
        "--recreate-venv",
        action="store_true",
        help="Delete and recreate the target virtual environment before installing. The target must be a venv.",
    )
    parser.add_argument(
        "--no-venv",
        action="store_true",
        help="Install into the current Python environment instead of an isolated virtual environment.",
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        help="Browser to install or verify.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="install_all",
        help="Install all supported browsers.",
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help="Install Playwright system dependencies on Linux when installing browsers.",
    )
    parser.add_argument(
        "--browser-probe-timeout",
        type=int,
        default=DEFAULT_BROWSER_PROBE_TIMEOUT,
        help="Timeout in seconds for verifying Playwright browser launch. Defaults to 120.",
    )
    return parser.parse_args()


def show_env_info(
    browser: str = "chromium",
    python_cmd: str | None = None,
    browser_probe_timeout: int = DEFAULT_BROWSER_PROBE_TIMEOUT,
) -> tuple[bool, bool]:
    python_label = python_cmd or get_python_path()
    safe_print("\n" + "=" * 58)
    safe_print("  Browser Automation - Environment Check")
    safe_print("=" * 58)
    safe_print(f"  Platform:       {get_platform_name()}")
    safe_print(f"  Python version: {get_python_version(python_cmd)}")
    safe_print(f"  Python path:    {python_label}")
    safe_print(f"  Console codec:  {sys.stdout.encoding or 'unknown'}")

    python_ok = True
    if python_cmd:
        python_ok, python_detail = check_python_runnable(python_cmd)
        safe_print(f"  Python runnable:{' yes' if python_ok else ' no'}")
        if not python_ok:
            safe_print(f"  Python error:   {python_detail}")

    package_ok = check_playwright_installed(python_cmd) if python_ok else False
    browser_ok = (
        check_playwright_browsers(browser, python_cmd, timeout=browser_probe_timeout, log_failure=True)
        if package_ok
        else False
    )
    safe_print(f"  Playwright:     {'installed' if package_ok else 'missing'}")
    safe_print(f"  {browser}:      {'installed' if browser_ok else 'missing or not verified'}")
    safe_print("=" * 58 + "\n")
    return package_ok, browser_ok


def prompt_browser_choice() -> tuple[str, ...]:
    if not sys.stdin.isatty():
        safe_print("No interactive stdin detected; defaulting to Chromium.")
        return ("chromium",)

    safe_print("Choose browsers to install:")
    safe_print("  [1] Chromium (recommended)")
    safe_print("  [2] Firefox")
    safe_print("  [3] WebKit")
    safe_print("  [4] All browsers")
    safe_print("  [5] Skip")

    try:
        choice = safe_input("Select [1/2/3/4/5] (default 1): ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        safe_print()
        return ()

    mapping = {
        "1": ("chromium",),
        "2": ("firefox",),
        "3": ("webkit",),
        "4": ("chromium", "firefox", "webkit"),
        "5": (),
    }
    return mapping.get(choice, ("chromium",))


def install_environment(
    browsers: tuple[str, ...],
    python_cmd: str | None = None,
    with_deps: bool = False,
) -> bool:
    if not check_playwright_installed(python_cmd):
        if not install_requirements(python_cmd=python_cmd):
            requirements_file = os.path.join(SCRIPT_DIR, "requirements.txt")
            safe_print("\nDependency installation failed. Try:")
            safe_print(f"  {(python_cmd or sys.executable)} -m pip install -r {requirements_file}")
            return False

    if not browsers:
        safe_print("Skipped browser installation.")
        return True

    return install_playwright_browsers(*browsers, python_cmd=python_cmd, with_deps=with_deps)


def main() -> None:
    args = parse_args()
    if args.browser_probe_timeout <= 0:
        safe_print("--browser-probe-timeout must be a positive integer.")
        sys.exit(1)
    if args.no_venv and args.recreate_venv:
        safe_print("--recreate-venv cannot be used with --no-venv.")
        sys.exit(1)
    selected_browser = args.browser or "chromium"
    if args.with_deps and not is_linux():
        safe_print("--with-deps is only used on Linux; continuing without system dependency installation.")

    venv_dir = os.path.abspath(args.venv or DEFAULT_VENV_DIR)
    target_python = None if args.no_venv else venv_python_path(venv_dir)

    if args.check and not args.no_venv and args.venv is None and path_is_within(venv_dir, SKILL_DIR):
        safe_print(
            f"The default virtual environment path ({venv_dir}) is inside the skill directory "
            "and cannot be used.\n"
            "--check will inspect the current Python environment instead.\n"
            "To check a specific isolated environment, use --venv to specify a path outside "
            "the skill directory.\n"
        )
        args.no_venv = True
        target_python = None

    if not args.no_venv:
        try:
            validate_venv_location(venv_dir)
        except RuntimeError as exc:
            safe_print(str(exc))
            sys.exit(1)

    if args.check and not args.no_venv and not os.path.exists(target_python):
        safe_print(f"Virtual environment is missing: {venv_dir}")
        safe_print("--check verifies the selected isolated virtual environment, not the current Python.")
        safe_print("Create the isolated environment with:")
        safe_print(f"  {' '.join(get_python_command())} {SETUP_SCRIPT} --browser {selected_browser} --venv {venv_dir}\n")
        safe_print("Or check the current Python explicitly with:")
        safe_print(f"  {' '.join(get_python_command())} {SETUP_SCRIPT} --check --no-venv\n")
        sys.exit(1)

    package_ok, browser_ok = show_env_info(selected_browser, target_python, args.browser_probe_timeout)

    if args.check:
        if package_ok and browser_ok:
            if args.no_venv:
                safe_print("Current Python environment is ready.")
            else:
                safe_print("Isolated virtual environment is ready.")
            return

        safe_print("Environment is incomplete. Suggested commands:")
        python_cmd = target_python or " ".join(get_python_command())
        if not package_ok:
            safe_print(f"  {python_cmd} -m pip install playwright")
        safe_print(f"  {python_cmd} -m playwright install {selected_browser}")
        sys.exit(1)

    if args.install_all:
        browsers = ("chromium", "firefox", "webkit")
    elif args.browser:
        browsers = (args.browser,)
    else:
        browsers = prompt_browser_choice()

    if not args.no_venv:
        try:
            target_python = create_venv_if_needed(venv_dir, recreate=args.recreate_venv)
        except RuntimeError as exc:
            safe_print(str(exc))
            sys.exit(1)
        if not ensure_venv_pip_ready(target_python):
            sys.exit(1)
        safe_print(f"Using virtual environment Python: {target_python}")

    if install_environment(browsers, target_python, with_deps=args.with_deps):
        safe_print("\nSetup complete. Run:")
        run_python = target_python or " ".join(get_python_command())
        safe_print(f"  {run_python} {RUN_TEST_SCRIPT} --headless\n")
    else:
        safe_print("\nSetup did not complete successfully.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
