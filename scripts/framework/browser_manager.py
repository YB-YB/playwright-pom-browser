"""Browser lifecycle management for Playwright automation."""

import os
from typing import TYPE_CHECKING, Any, Optional

from .config import Config
from .utils import get_logger, safe_input, safe_print
from .utils._browser_detect import detect_system_browsers, get_playwright_channel

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright


class BrowserManager:
    """Manage Playwright, browser, context, and page lifecycle."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._playwright: Optional["Playwright"] = None
        self._browser: Optional["Browser"] = None
        self._context: Optional["BrowserContext"] = None
        self._page: Optional["Page"] = None

    @staticmethod
    def ask_headless_mode() -> bool:
        safe_print("\nBrowser run mode")
        safe_print("  [1] Headless - no visible browser window")
        safe_print("  [2] Headed   - show the browser window")

        while True:
            try:
                choice = safe_input("Select [1/2] (default 1): ").strip()
            except (EOFError, KeyboardInterrupt):
                safe_print()
                return True

            if choice in {"", "1"}:
                return True
            if choice == "2":
                return False
            safe_print("Please enter 1 or 2.")

    @staticmethod
    def ask_browser_type() -> str:
        safe_print("\nBrowser type")
        safe_print("  [1] Chromium")
        safe_print("  [2] Firefox")
        safe_print("  [3] WebKit")

        mapping = {"": "chromium", "1": "chromium", "2": "firefox", "3": "webkit"}
        while True:
            try:
                choice = safe_input("Select [1/2/3] (default 1): ").strip()
            except (EOFError, KeyboardInterrupt):
                safe_print()
                return "chromium"

            if choice in mapping:
                return mapping[choice]
            safe_print("Please enter 1, 2, or 3.")

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def start(self) -> "BrowserManager":
        headless = self.config.headless if self.config.headless is not None else True

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Run setup.py --browser chromium or install playwright first."
            ) from exc

        try:
            self._playwright = await async_playwright().start()

            # 优先尝试使用系统已安装的浏览器（通过 channel 参数）
            launched = await self._try_system_browser(headless)

            if not launched:
                # 回退到 Playwright 内置浏览器
                browser_launchers = {
                    "chromium": self._playwright.chromium.launch,
                    "firefox": self._playwright.firefox.launch,
                    "webkit": self._playwright.webkit.launch,
                }

                launcher = browser_launchers.get(self.config.browser_type)
                if launcher is None:
                    raise ValueError(f"Unsupported browser type: {self.config.browser_type}")

                self._browser = await launcher(headless=headless)
                get_logger().info(
                    "Browser started (built-in): %s (%s)",
                    self.config.browser_type,
                    "headless" if headless else "headed",
                )
        except Exception:
            get_logger().exception("Browser startup failed")
            try:
                await self.close()
            except Exception:
                pass
            raise
        return self

    async def _try_system_browser(self, headless: bool) -> bool:
        """尝试使用系统已安装的浏览器启动，成功返回 True。"""
        log = get_logger()
        detection = detect_system_browsers()

        if not detection.has_any:
            log.info("No system browsers detected, will use Playwright built-in browser.")
            return False

        best = detection.get_best()
        if best is None:
            return False

        channel = get_playwright_channel(best)
        if channel is None:
            # Firefox 等不支持 channel 的浏览器，回退到内置引擎
            log.info("System browser %s does not support channel mode, falling back.", best.name)
            return False

        try:
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                channel=channel,
            )
            log.info(
                "Browser started (system): %s via channel=%s (%s)",
                best.name,
                channel,
                "headless" if headless else "headed",
            )
            return True
        except Exception as exc:
            log.warning("Failed to launch system browser %s: %s", best.name, exc)
            return False

    async def create_context(self, **kwargs: Any) -> "BrowserContext":
        if self._browser is None:
            await self.start()

        context_args = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "accept_downloads": self.config.accept_downloads,
        }
        if self.config.locale:
            context_args["locale"] = self.config.locale
        if self.config.user_agent:
            context_args["user_agent"] = self.config.user_agent
        if self.config.storage_state_path:
            storage_state_path = os.path.abspath(self.config.storage_state_path)
            if not os.path.isfile(storage_state_path):
                raise RuntimeError(
                    f"Storage state file not found: {storage_state_path}. "
                    "Log in once and call manager.save_storage_state(path), or pass a valid --storage-state path."
                )
            context_args["storage_state"] = storage_state_path
        context_args.update(kwargs)

        if self._context is not None:
            await self._context.close()

        self._context = await self._browser.new_context(**context_args)
        self._context.set_default_timeout(self.config.timeout)
        self._context.set_default_navigation_timeout(self.config.navigation_timeout)
        self._page = None
        return self._context

    async def create_page(self, context: Optional["BrowserContext"] = None) -> "Page":
        ctx = context or self._context or await self.create_context()
        self._page = await ctx.new_page()
        self._page.set_default_timeout(self.config.timeout)
        self._page.set_default_navigation_timeout(self.config.navigation_timeout)
        return self._page

    async def get_page(self) -> "Page":
        if self._page is None:
            await self.create_page()
        return self._page

    async def save_storage_state(self, path: str) -> None:
        if self._context is None:
            raise RuntimeError("Cannot save storage state before a browser context is created.")
        state_path = os.path.abspath(path)
        state_dir = os.path.dirname(state_path)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
        await self._context.storage_state(path=state_path)
        get_logger().info("Storage state saved: %s", state_path)

    async def close(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._page = None
        get_logger().debug("Browser resources released.")

    @property
    def browser(self) -> Optional["Browser"]:
        return self._browser

    @property
    def context(self) -> Optional["BrowserContext"]:
        return self._context

    @property
    def page(self) -> Optional["Page"]:
        return self._page
