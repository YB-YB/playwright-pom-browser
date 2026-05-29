"""Framework helpers for Python browser automation."""

from .base_page import BasePage, BrowserPage
from .browser_manager import BrowserManager
from .config import Config
from .runner import check_python_version, run, set_error_context
from .utils import (
    ensure_playwright_environment,
    get_platform_name,
    logger,
    safe_input,
    safe_print,
    setup_logging,
)

__all__ = [
    "BasePage",
    "BrowserManager",
    "BrowserPage",
    "check_python_version",
    "Config",
    "ensure_playwright_environment",
    "get_platform_name",
    "logger",
    "run",
    "safe_input",
    "safe_print",
    "set_error_context",
    "setup_logging",
]
