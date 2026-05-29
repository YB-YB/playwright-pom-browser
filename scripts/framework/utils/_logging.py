import logging
import os
import sys
import traceback


logger = logging.getLogger("browser-automation")
_LOGGING_READY = False


def setup_logging(level: int = logging.INFO, fmt: str | None = None) -> None:
    global _LOGGING_READY
    if fmt is None:
        fmt = "  [%(levelname)s] %(message)s"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    _LOGGING_READY = True


def get_logger() -> logging.Logger:
    if not _LOGGING_READY:
        setup_logging(logging.INFO)
    return logger


def safe_print(text: str = "", **kwargs) -> None:
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        cleaned = str(text).encode(encoding, errors="replace").decode(encoding)
        print(cleaned, **kwargs)


def safe_input(prompt: str = "") -> str:
    try:
        return input(prompt)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        cleaned = prompt.encode(encoding, errors="replace").decode(encoding)
        return input(cleaned)


def print_failure_context(exc: BaseException, *, page=None, config=None, show_traceback: bool = False) -> None:
    safe_print(f"\nExecution failed: {type(exc).__name__}: {exc}")

    current_url = getattr(page, "url", None) if page is not None else None
    if current_url:
        safe_print(f"Current URL: {current_url}")

    if config is not None:
        safe_print(
            "Config: "
            f"browser={getattr(config, 'browser_type', 'unknown')}, "
            f"headless={getattr(config, 'headless', 'unknown')}, "
            f"timeout={getattr(config, 'timeout', 'unknown')}ms, "
            f"navigation_timeout={getattr(config, 'navigation_timeout', 'unknown')}ms"
        )
        screenshot_dir = getattr(config, "screenshot_dir", "")
        if screenshot_dir:
            safe_print(f"Screenshot directory: {os.path.abspath(screenshot_dir)}")

    if show_traceback or os.environ.get("BROWSER_DEBUG") == "1":
        safe_print("\nTraceback:")
        safe_print("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).rstrip())

    safe_print()
