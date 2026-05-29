"""Shared command-line helpers for browser automation scripts."""

import argparse
import os
import sys
from typing import Tuple

from .browser_manager import BrowserManager
from .config import Config
from .utils import ensure_playwright_environment, get_logger, get_python_command, is_linux, is_virtual_environment, safe_print, SETUP_SCRIPT


def add_common_browser_args(parser: argparse.ArgumentParser) -> None:
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--headless", action="store_true", help="Run without showing a browser window.")
    mode_group.add_argument("--headed", action="store_true", help="Show the browser window.")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Ask for browser run mode when neither --headless nor --headed is provided.",
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default=None,
        help="Browser type. Defaults to BROWSER_TYPE or chromium.",
    )
    parser.add_argument("--timeout", type=int, default=None, help="Global timeout in milliseconds.")
    parser.add_argument(
        "--navigation-timeout",
        type=int,
        default=None,
        help="Navigation timeout in milliseconds.",
    )
    parser.add_argument("--base-url", default=None, help="Base URL used when navigating to paths like /dashboard.")
    parser.add_argument("--screenshot-dir", default=None, help="Directory for screenshots.")
    parser.add_argument("--storage-state", default=None, help="Path to a Playwright storage_state JSON file.")
    parser.add_argument("--viewport", default=None, help="Viewport size as WIDTHxHEIGHT, for example 1280x800.")
    parser.add_argument("--viewport-width", type=int, default=None, help="Viewport width in pixels.")
    parser.add_argument("--viewport-height", type=int, default=None, help="Viewport height in pixels.")
    parser.add_argument(
        "--browser-probe-timeout",
        type=int,
        default=None,
        help="Timeout in seconds for verifying Playwright browser launch. Defaults to BROWSER_PROBE_TIMEOUT or 120.",
    )
    parser.add_argument("--skip-env-check", action="store_true", help="Skip Playwright environment check.")
    parser.add_argument(
        "--install-missing",
        action="store_true",
        help="Install missing Python dependencies from requirements.txt and missing Playwright browsers.",
    )


def _parse_viewport(value: str) -> Tuple[int, int]:
    normalized = value.lower().replace("*", "x")
    parts = normalized.split("x", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Viewport must be in WIDTHxHEIGHT format, for example 1280x800.")

    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Viewport width and height must be integers.") from exc

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Viewport width and height must be positive integers.")

    return width, height


def config_from_args(args: argparse.Namespace) -> Config:
    config = Config.from_env()

    if args.headless:
        config.headless = True
    elif args.headed:
        config.headless = False
    elif config.headless is None:
        config.headless = BrowserManager.ask_headless_mode() if args.interactive else True

    if args.browser:
        config.browser_type = args.browser
    if args.timeout is not None:
        config.timeout = args.timeout
    if args.navigation_timeout is not None:
        config.navigation_timeout = args.navigation_timeout
    if args.base_url is not None:
        config.base_url = args.base_url
    if args.screenshot_dir is not None:
        config.screenshot_dir = args.screenshot_dir
    if args.storage_state is not None:
        config.storage_state_path = args.storage_state
    if args.viewport:
        config.viewport_width, config.viewport_height = _parse_viewport(args.viewport)
    if args.viewport_width is not None:
        config.viewport_width = args.viewport_width
    if args.viewport_height is not None:
        config.viewport_height = args.viewport_height
    if args.browser_probe_timeout is not None:
        config.browser_probe_timeout = args.browser_probe_timeout

    config.validate()
    return config


def ensure_environment_from_args(args: argparse.Namespace, config: Config) -> None:
    should_skip = args.skip_env_check or os.environ.get("BROWSER_SKIP_ENV_CHECK") == "1"
    if should_skip:
        get_logger().info("Environment check skipped.")
        return

    if args.install_missing and not is_virtual_environment():
        env_ok = ensure_playwright_environment(
            browsers=(config.browser_type,),
            auto_install=False,
            browser_probe_timeout=config.browser_probe_timeout,
        )
        if env_ok:
            return

        safe_print("\nRefusing to auto-install into the current non-venv Python environment.")
        safe_print("Create/use the isolated environment first:")
        setup_script = os.path.abspath(SETUP_SCRIPT)
        safe_print(f"  {' '.join(get_python_command())} {setup_script} --browser {config.browser_type} --venv C:\\path\\to\\browser-task\\.venv")
        safe_print("Then rerun with the venv Python.\n")
        sys.exit(1)

    env_ok = ensure_playwright_environment(
        browsers=(config.browser_type,),
        auto_install=args.install_missing,
        browser_probe_timeout=config.browser_probe_timeout,
    )
    if env_ok:
        return

    python_cmd = " ".join(get_python_command())
    setup_script = os.path.abspath(SETUP_SCRIPT)
    safe_print("\nEnvironment check failed. To install dependencies, run:")
    safe_print(f"  {python_cmd} {setup_script} --browser {config.browser_type}")
    safe_print("Or rerun this command with --install-missing.\n")
    sys.exit(1)


def warn_for_headed_linux(config: Config) -> None:
    if is_linux() and not config.headless and not os.environ.get("DISPLAY"):
        get_logger().warning("Linux headed mode usually requires DISPLAY to be set.")
