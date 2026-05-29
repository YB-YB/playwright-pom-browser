"""Configuration for browser automation scripts."""

import os
from dataclasses import dataclass
from typing import Optional

from .utils import get_logger


SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}


def _env_bool(name: str) -> Optional[bool]:
    raw = os.getenv(name)
    if raw is None:
        return None

    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    get_logger().warning(
        "Ignoring invalid boolean value for %s: %r. Expected true/false, 1/0, yes/no, or on/off.",
        name,
        raw,
    )
    return None


def _env_int(name: str, default: int, *, positive: bool = False) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        value = int(raw)
    except ValueError:
        get_logger().warning("Ignoring invalid integer value for %s: %r.", name, raw)
        return default

    if positive and value <= 0:
        get_logger().warning("Ignoring non-positive integer value for %s: %r.", name, raw)
        return default
    return value


def _env_str(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    return raw if raw is not None else default


@dataclass
class Config:
    """Runtime configuration for Playwright browser automation."""

    headless: Optional[bool] = None
    browser_type: str = "chromium"
    timeout: int = 30000
    navigation_timeout: int = 60000
    screenshot_dir: str = ""
    download_dir: str = ""
    viewport_width: int = 1280
    viewport_height: int = 800
    base_url: str = ""
    locale: str = ""
    user_agent: str = ""
    storage_state_path: str = ""
    accept_downloads: bool = True
    browser_probe_timeout: int = 120

    def __post_init__(self) -> None:
        self._set_defaults()
        self.validate()

    def _set_defaults(self) -> None:
        if not self.screenshot_dir:
            self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        if not self.download_dir:
            self.download_dir = os.path.join(os.getcwd(), "downloads")

    def validate(self) -> None:
        if self.browser_type not in SUPPORTED_BROWSERS:
            supported = ", ".join(sorted(SUPPORTED_BROWSERS))
            raise ValueError(f"Unsupported browser type: {self.browser_type!r}. Expected one of: {supported}.")
        if self.timeout <= 0:
            raise ValueError(f"timeout must be a positive integer, got {self.timeout}.")
        if self.navigation_timeout <= 0:
            raise ValueError(f"navigation_timeout must be a positive integer, got {self.navigation_timeout}.")
        if self.viewport_width <= 0 or self.viewport_height <= 0:
            raise ValueError(f"viewport_width and viewport_height must be positive integers, got ({self.viewport_width}, {self.viewport_height}).")
        if self.browser_probe_timeout <= 0:
            raise ValueError(f"browser_probe_timeout must be a positive integer, got {self.browser_probe_timeout}.")

    @property
    def is_configured(self) -> bool:
        """Return True when headless mode and browser_type have been explicitly set for the current session."""
        return (
            self.headless is not None
            and self.browser_type in SUPPORTED_BROWSERS
        )

    @classmethod
    def from_env(cls) -> "Config":
        accept_downloads = _env_bool("BROWSER_ACCEPT_DOWNLOADS")
        return cls(
            headless=_env_bool("BROWSER_HEADLESS"),
            browser_type=_env_str("BROWSER_TYPE", "chromium"),
            timeout=_env_int("BROWSER_TIMEOUT", 30000, positive=True),
            navigation_timeout=_env_int("BROWSER_NAVIGATION_TIMEOUT", 60000, positive=True),
            viewport_width=_env_int("BROWSER_VIEWPORT_WIDTH", 1280, positive=True),
            viewport_height=_env_int("BROWSER_VIEWPORT_HEIGHT", 800, positive=True),
            base_url=_env_str("BROWSER_BASE_URL"),
            screenshot_dir=_env_str("BROWSER_SCREENSHOT_DIR"),
            download_dir=_env_str("BROWSER_DOWNLOAD_DIR"),
            locale=_env_str("BROWSER_LOCALE"),
            user_agent=_env_str("BROWSER_USER_AGENT"),
            storage_state_path=_env_str("BROWSER_STORAGE_STATE"),
            browser_probe_timeout=_env_int("BROWSER_PROBE_TIMEOUT", 120, positive=True),
            accept_downloads=True if accept_downloads is None else accept_downloads,
        )
