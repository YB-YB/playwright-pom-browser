#!/usr/bin/env python
"""Smoke test for the browser automation skill."""

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from framework.base_page import BrowserPage  # noqa: E402
from framework.browser_manager import BrowserManager  # noqa: E402
from framework.cli import add_common_browser_args, config_from_args, ensure_environment_from_args, warn_for_headed_linux  # noqa: E402
from framework.runner import check_python_version, run, set_error_context  # noqa: E402
from framework.utils import (  # noqa: E402
    get_platform_name,
    safe_print,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a browser automation smoke test.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_test.py --headless
  python run_test.py --headed --browser firefox
  python run_test.py --headless --install-missing
        """,
    )
    add_common_browser_args(parser)
    parser.add_argument(
        "--url",
        default="data:text/html,<title>Browser automation smoke test</title><h1>ready</h1>",
        help="URL to open for the smoke test.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    config = config_from_args(args)
    set_error_context(config=config)
    ensure_environment_from_args(args, config)
    warn_for_headed_linux(config)

    safe_print(
        f"\nSmoke test: {config.browser_type} | "
        f"{'headless' if config.headless else 'headed'} | "
        f"{get_platform_name()}\n"
    )

    async with BrowserManager(config) as manager:
        await manager.create_context()
        page = await manager.create_page()
        set_error_context(page=page)
        browser = BrowserPage(page, manager.config)

        await browser.navigate(args.url)
        await browser.wait_for_load_state("domcontentloaded")

        title = await browser.get_title()
        safe_print(f"Page title: {title}")

        screenshot_path = await browser.screenshot("demo_example_com.png")
        safe_print(f"Screenshot saved: {screenshot_path}")

    safe_print("\nSmoke test passed.\n")


if __name__ == "__main__":
    check_python_version()
    run(main())
