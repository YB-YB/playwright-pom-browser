#!/usr/bin/env python
"""Template for reusable browser automation scripts."""

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from framework.base_page import BrowserPage  # noqa: E402
from framework.browser_manager import BrowserManager  # noqa: E402
from framework.cli import add_common_browser_args, config_from_args, ensure_environment_from_args, warn_for_headed_linux  # noqa: E402
from framework.runner import check_python_version, run, set_error_context  # noqa: E402
from framework.utils import safe_print  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a browser automation task.")
    add_common_browser_args(parser)
    return parser.parse_args()


async def run_task(page, manager: BrowserManager) -> None:
    """Write the browser automation task here."""
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com")
    await browser.wait_for_load_state("domcontentloaded")
    safe_print(f"Page title: {await browser.get_title()}")
    await browser.screenshot("example.png")

    # Use manager.save_storage_state("auth.json") after login if needed.


async def main() -> None:
    args = parse_args()
    config = config_from_args(args)
    set_error_context(config=config)
    ensure_environment_from_args(args, config)
    warn_for_headed_linux(config)

    async with BrowserManager(config) as manager:
        await manager.create_context()
        page = await manager.create_page()
        set_error_context(page=page)
        await run_task(page, manager)

    safe_print("Browser automation task completed.")


if __name__ == "__main__":
    check_python_version()
    run(main())
