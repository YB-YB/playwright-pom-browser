"""Common entry-point runner for browser automation scripts.

Provides the boilerplate around Python version checking, asyncio execution,
and graceful error handling with diagnostic context.
"""

import asyncio
import sys
from typing import Any, Awaitable, Optional

from .config import Config
from .utils import print_failure_context, safe_print

MIN_PYTHON = (3, 10)

_page: Any = None
_config: Optional[Config] = None


def check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        sys.exit(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required. "
            f"You are running Python {sys.version_info.major}.{sys.version_info.minor}."
        )


def set_error_context(page: Any = None, config: Optional[Config] = None) -> None:
    global _page, _config
    if page is not None:
        _page = page
    if config is not None:
        _config = config


def run(entry: Awaitable[None]) -> None:
    check_python_version()
    try:
        asyncio.run(entry)
    except KeyboardInterrupt:
        safe_print("\nInterrupted by user.\n")
        sys.exit(0)
    except Exception as exc:
        print_failure_context(exc, page=_page, config=_config)
        sys.exit(1)
