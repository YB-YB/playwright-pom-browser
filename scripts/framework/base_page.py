"""Common page helper for browser automation scripts."""

import asyncio
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Awaitable, Callable, List, Optional, Pattern, Union
import warnings

from .config import Config
from .utils import get_logger

if TYPE_CHECKING:
    from playwright.async_api import Dialog, Download, FrameLocator, Locator, Page, Response


_NO_EVALUATE_ARG = object()
DEFAULT_TYPE_DELAY_MS = 50


class OutputDirectoryError(OSError):
    pass


class BrowserPage:
    """Thin convenience wrapper around Playwright's async Page API."""

    def __init__(self, page: "Page", config: Optional[Config] = None):
        self.page = page
        self.config = config or Config()
        self._last_dialog_error: Optional[Exception] = None
        self._created_dirs: set[str] = set()

    async def navigate(self, url: str, **kwargs) -> None:
        if self.config.base_url and url.startswith("/"):
            url = self.config.base_url.rstrip("/") + url
        await self.page.goto(url, **kwargs)

    async def go_back(self, **kwargs) -> None:
        await self.page.go_back(**kwargs)

    async def go_forward(self, **kwargs) -> None:
        await self.page.go_forward(**kwargs)

    async def reload(self, **kwargs) -> None:
        await self.page.reload(**kwargs)

    def locator(self, selector: str, **kwargs) -> "Locator":
        return self.page.locator(selector, **kwargs)

    def get_by_role(self, role: str, **kwargs) -> "Locator":
        return self.page.get_by_role(role, **kwargs)

    def get_by_text(self, text: str, **kwargs) -> "Locator":
        return self.page.get_by_text(text, **kwargs)

    def get_by_label(self, label: str, **kwargs) -> "Locator":
        return self.page.get_by_label(label, **kwargs)

    def get_by_placeholder(self, text: str, **kwargs) -> "Locator":
        return self.page.get_by_placeholder(text, **kwargs)

    def get_by_test_id(self, test_id: str) -> "Locator":
        return self.page.get_by_test_id(test_id)

    async def click(self, selector_or_locator: Union[str, "Locator"], **kwargs) -> None:
        await self._resolve_locator(selector_or_locator).click(**kwargs)

    async def click_and_wait_for(
        self,
        selector_or_locator: Union[str, "Locator"],
        wait_selector: str,
        timeout: Optional[int] = None,
        state: Optional[str] = None,
        **kwargs,
    ) -> None:
        wait_kwargs = {}
        if timeout is not None:
            wait_kwargs["timeout"] = timeout
        if state is not None:
            wait_kwargs["state"] = state

        if await self.page.locator(wait_selector).count() > 0:
            raise RuntimeError(
                f"click_and_wait_for: wait_selector '{wait_selector}' already exists before the click. "
                "The wait would resolve immediately, defeating its purpose."
            )

        wait_task = asyncio.create_task(self.page.wait_for_selector(wait_selector, **wait_kwargs))
        await asyncio.sleep(0)
        try:
            await self.click(selector_or_locator, **kwargs)
            await wait_task
        except Exception:
            wait_task.cancel()
            raise

    async def fill_text(self, selector_or_locator: Union[str, "Locator"], text: str, **kwargs) -> None:
        await self._resolve_locator(selector_or_locator).fill(text, **kwargs)

    async def type_text(
        self,
        selector_or_locator: Union[str, "Locator"],
        text: str,
        delay: int = DEFAULT_TYPE_DELAY_MS,
        **kwargs,
    ) -> None:
        await self._resolve_locator(selector_or_locator).press_sequentially(
            text,
            delay=delay,
            **kwargs,
        )

    async def select_option(
        self,
        selector_or_locator: Union[str, "Locator"],
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
    ) -> List[str]:
        return await self._resolve_locator(selector_or_locator).select_option(
            value=value,
            label=label,
            index=index,
        )

    async def hover(self, selector_or_locator: Union[str, "Locator"], **kwargs) -> None:
        await self._resolve_locator(selector_or_locator).hover(**kwargs)

    async def double_click(self, selector_or_locator: Union[str, "Locator"], **kwargs) -> None:
        await self._resolve_locator(selector_or_locator).dblclick(**kwargs)

    async def right_click(self, selector_or_locator: Union[str, "Locator"], **kwargs) -> None:
        await self._resolve_locator(selector_or_locator).click(button="right", **kwargs)

    async def check(self, selector_or_locator: Union[str, "Locator"], **kwargs) -> None:
        await self._resolve_locator(selector_or_locator).check(**kwargs)

    async def uncheck(self, selector_or_locator: Union[str, "Locator"], **kwargs) -> None:
        await self._resolve_locator(selector_or_locator).uncheck(**kwargs)

    async def press_key(self, key: str) -> None:
        await self.page.keyboard.press(key)

    async def scroll_into_view(self, selector_or_locator: Union[str, "Locator"]) -> None:
        await self._resolve_locator(selector_or_locator).scroll_into_view_if_needed()

    async def upload_file(
        self,
        selector_or_locator: Union[str, "Locator"],
        file_paths: Union[str, List[str]],
    ) -> None:
        await self._resolve_locator(selector_or_locator).set_input_files(file_paths)

    async def drag_and_drop(self, source: Union[str, "Locator"], target: Union[str, "Locator"]) -> None:
        await self._resolve_locator(source).drag_to(self._resolve_locator(target))

    async def get_text(self, selector_or_locator: Union[str, "Locator"], **kwargs) -> str:
        return await self._resolve_locator(selector_or_locator).text_content(**kwargs) or ""

    async def get_inner_text(self, selector_or_locator: Union[str, "Locator"]) -> str:
        return await self._resolve_locator(selector_or_locator).inner_text()

    async def get_attribute(self, selector_or_locator: Union[str, "Locator"], name: str) -> Optional[str]:
        return await self._resolve_locator(selector_or_locator).get_attribute(name)

    async def get_value(self, selector_or_locator: Union[str, "Locator"]) -> str:
        """Return the raw ``value`` attribute.

        Prefer ``get_input_value()`` for input, textarea, and select controls because
        it uses Playwright's form-control API.
        """
        warnings.warn(
            "BrowserPage.get_value() returns the raw value attribute; prefer get_input_value() for form controls.",
            FutureWarning,
            stacklevel=2,
        )
        return await self.get_attribute(selector_or_locator, "value") or ""

    async def get_input_value(self, selector_or_locator: Union[str, "Locator"]) -> str:
        return await self._resolve_locator(selector_or_locator).input_value()

    async def is_visible(self, selector_or_locator: Union[str, "Locator"]) -> bool:
        return await self._resolve_locator(selector_or_locator).is_visible()

    async def is_enabled(self, selector_or_locator: Union[str, "Locator"]) -> bool:
        return await self._resolve_locator(selector_or_locator).is_enabled()

    async def is_checked(self, selector_or_locator: Union[str, "Locator"]) -> bool:
        return await self._resolve_locator(selector_or_locator).is_checked()

    async def count_elements(self, selector_or_locator: Union[str, "Locator"]) -> int:
        return await self._resolve_locator(selector_or_locator).count()

    async def get_all_texts(self, selector_or_locator: Union[str, "Locator"]) -> List[str]:
        return await self._resolve_locator(selector_or_locator).all_text_contents()

    async def wait_for_selector(
        self,
        selector: str,
        timeout: Optional[int] = None,
        state: Optional[str] = None,
    ) -> Optional["Locator"]:
        return await self.page.wait_for_selector(selector, timeout=timeout, state=state)

    async def wait_for_load_state(self, state: str = "load", **kwargs) -> None:
        await self.page.wait_for_load_state(state, **kwargs)

    async def wait_for_navigation(
        self,
        action: Optional[Callable[[], Awaitable[Any]]] = None,
        url: Optional[Union[str, Pattern[str], Callable[[str], bool]]] = None,
        **kwargs,
    ) -> None:
        """Run an optional action and wait for a target URL.

        Pass ``url`` when a click or form submit changes location::

            await browser.wait_for_navigation(
                lambda: browser.click("#submit"),
                url="**/dashboard",
            )

        This intentionally waits for URL changes instead of Playwright's legacy
        navigation event because many modern apps update via SPA routing.
        """
        if url is None:
            raise ValueError(
                "wait_for_navigation() requires a target url pattern. "
                "Use wait_for_url(url), wait_for_response(...), or an element assertion for SPA/page updates."
            )

        if action is not None:
            if isinstance(url, str) and self.page.url == url:
                raise RuntimeError(
                    f"wait_for_navigation: current URL already matches '{url}'. "
                    "The wait would resolve immediately, defeating its purpose."
                )
            wait_task = asyncio.create_task(self.page.wait_for_url(url, **kwargs))
            await asyncio.sleep(0)
            try:
                await action()
                await wait_task
            except Exception:
                wait_task.cancel()
                raise
            return

        await self.page.wait_for_url(url, **kwargs)

    async def wait_for_timeout(self, ms: int) -> None:
        await self.page.wait_for_timeout(ms)

    async def wait_for_url(self, url: str, **kwargs) -> None:
        await self.page.wait_for_url(url, **kwargs)

    async def wait_for_function(self, expression: str, **kwargs) -> None:
        await self.page.wait_for_function(expression, **kwargs)

    async def wait_for_page_loaded(self) -> None:
        await self.page.wait_for_load_state("domcontentloaded")

    async def wait_for_network_idle(self, **kwargs) -> None:
        await self.page.wait_for_load_state("networkidle", **kwargs)

    async def get_title(self) -> str:
        return await self.page.title()

    async def get_url(self) -> str:
        return self.page.url

    async def screenshot(
        self,
        name: Optional[str] = None,
        directory: Optional[str] = None,
        full_page: bool = True,
        **kwargs,
    ) -> str:
        name = self._build_filename(name, "screenshot")
        save_dir = directory or self.config.screenshot_dir
        self._ensure_output_dir(save_dir, self._created_dirs)
        filepath = self._safe_output_path(save_dir, name)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        await self.page.screenshot(path=filepath, full_page=full_page, **kwargs)
        return filepath

    async def element_screenshot(
        self,
        selector_or_locator: Union[str, "Locator"],
        name: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> str:
        name = self._build_filename(name, "element")
        save_dir = directory or self.config.screenshot_dir
        self._ensure_output_dir(save_dir, self._created_dirs)
        filepath = self._safe_output_path(save_dir, name)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        await self._resolve_locator(selector_or_locator).screenshot(path=filepath)
        return filepath

    def frame_locator(self, frame_selector: str) -> "FrameLocator":
        return self.page.frame_locator(frame_selector)

    async def accept_alert(self, timeout: Optional[int] = None) -> str:
        """等待下一个 dialog 并接受，返回 dialog 消息文本。

        需要与 asyncio.gather 配合使用，或在触发操作之前调用::

            text, _ = await asyncio.gather(
                browser.accept_alert(),
                browser.click("#trigger-btn"),
            )
        """
        dialog = await self._wait_for_dialog(timeout)
        await dialog.accept()
        return dialog.message

    async def dismiss_alert(self, timeout: Optional[int] = None) -> str:
        """等待下一个 dialog 并关闭，返回 dialog 消息文本。

        需要与 asyncio.gather 配合使用，或在触发操作之前调用::

            text, _ = await asyncio.gather(
                browser.dismiss_alert(),
                browser.click("#cancel-btn"),
            )
        """
        dialog = await self._wait_for_dialog(timeout)
        await dialog.dismiss()
        return dialog.message

    async def prompt_alert(self, text: str, timeout: Optional[int] = None) -> str:
        """等待下一个 prompt dialog，填入 *text* 并接受，返回 dialog 消息文本。

        需要与 asyncio.gather 配合使用，或在触发操作之前调用::

            text, _ = await asyncio.gather(
                browser.prompt_alert("张三"),
                browser.click("#prompt-btn"),
            )
        """
        dialog = await self._wait_for_dialog(timeout)
        await dialog.accept(text)
        return dialog.message

    async def _wait_for_dialog(self, timeout: Optional[int] = None) -> "Dialog":
        kw = {"timeout": timeout} if timeout is not None else {}
        return await self.page.wait_for_event("dialog", **kw)

    def expect_alert(self, action: str = "accept", prompt_text: str = "") -> None:
        """Register a one-shot dialog handler BEFORE the action that triggers it.

        This is the fire-and-forget pattern: call it right before clicking a button
        that you know will open a dialog::

            browser.expect_alert("accept")
            await browser.click("#delete-btn")

        After the dialog is handled, check ``browser.last_dialog_error`` to see if
        the handler encountered an error.

        Args:
            action: "accept" or "dismiss".
            prompt_text: Text to fill if the dialog is a prompt.
        """

        if action not in {"accept", "dismiss"}:
            raise ValueError("action must be 'accept' or 'dismiss'.")

        self._last_dialog_error = None

        async def _handler(dialog) -> None:
            try:
                if action == "dismiss":
                    await dialog.dismiss()
                else:
                    await dialog.accept(prompt_text or None)
            except Exception as exc:
                self._last_dialog_error = exc
                get_logger().error("Dialog handler failed: %s", exc)

        self.page.once("dialog", _handler)

    async def get_cookies(self) -> List[dict]:
        return await self.page.context.cookies()

    async def set_cookies(self, cookies: List[dict]) -> None:
        await self.page.context.add_cookies(cookies)

    async def clear_cookies(self) -> None:
        await self.page.context.clear_cookies()

    async def evaluate(self, expression: str, arg: Any = _NO_EVALUATE_ARG) -> Any:
        """Evaluate JavaScript in the page, optionally passing one Playwright arg.

        安全警告：expression 会被直接注入页面执行，切勿将未经处理的
        用户输入拼接到 expression 中。应始终通过 arg 参数传递外部数据。
        """
        if arg is _NO_EVALUATE_ARG:
            return await self.page.evaluate(expression)
        return await self.page.evaluate(expression, arg)

    async def evaluate_on_all(self, selector: str, expression: str) -> Any:
        """对匹配 selector 的所有元素执行 JavaScript，返回结果列表。

        安全警告：expression 会被直接注入页面执行，切勿将未经处理的
        用户输入拼接到 expression 中。
        """
        return await self.page.eval_on_selector_all(selector, expression)

    async def intercept_request(self, url_pattern: str, handler) -> None:
        await self.page.route(url_pattern, handler)

    async def stop_interception(self, url_pattern: str) -> None:
        await self.page.unroute(url_pattern)

    async def wait_for_response(
        self,
        url_or_predicate: Union[str, Pattern[str], Callable[["Response"], bool]],
        action: Optional[Callable[[], Awaitable[Any]]] = None,
        **kwargs,
    ) -> "Response":
        """Wait for a matching network response.

        Pass an action to register the response listener before the triggering step::

            response = await browser.wait_for_response(
                "**/api/items",
                action=lambda: browser.click("#load-items"),
            )

        Without an action, this waits for the next matching response from now on.
        """
        async with self.page.expect_response(url_or_predicate, **kwargs) as response_info:
            if action is not None:
                await action()

        return await response_info.value

    async def download_by_click(
        self,
        selector_or_locator: Union[str, "Locator"],
        save_as: Optional[str] = None,
        directory: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> str:
        expect_kwargs = {"timeout": timeout} if timeout is not None else {}
        async with self.page.expect_download(**expect_kwargs) as download_info:
            await self.click(selector_or_locator, **kwargs)

        download = await download_info.value
        return await self.save_download(download, save_as=save_as, directory=directory)

    async def save_download(
        self,
        download: "Download",
        save_as: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> str:
        save_dir = directory or self.config.download_dir
        self._ensure_output_dir(save_dir, self._created_dirs)
        filename = save_as or download.suggested_filename
        filepath = self._safe_output_path(save_dir, filename)
        await download.save_as(filepath)
        return filepath

    async def expect_visible(self, selector_or_locator: Union[str, "Locator"]) -> None:
        await self._get_expect(self._resolve_locator(selector_or_locator)).to_be_visible()

    async def expect_hidden(self, selector_or_locator: Union[str, "Locator"]) -> None:
        await self._get_expect(self._resolve_locator(selector_or_locator)).to_be_hidden()

    async def expect_text(self, selector_or_locator: Union[str, "Locator"], text: str) -> None:
        await self._get_expect(self._resolve_locator(selector_or_locator)).to_have_text(text)

    async def expect_contain_text(self, selector_or_locator: Union[str, "Locator"], text: str) -> None:
        await self._get_expect(self._resolve_locator(selector_or_locator)).to_contain_text(text)

    async def expect_value(self, selector_or_locator: Union[str, "Locator"], value: str) -> None:
        await self._get_expect(self._resolve_locator(selector_or_locator)).to_have_value(value)

    async def expect_url(self, url_pattern: str) -> None:
        await self._get_expect(self.page).to_have_url(url_pattern)

    async def expect_title(self, title: str) -> None:
        await self._get_expect(self.page).to_have_title(title)

    async def expect_count(self, selector_or_locator: Union[str, "Locator"], count: int) -> None:
        await self._get_expect(self._resolve_locator(selector_or_locator)).to_have_count(count)

    @staticmethod
    def _get_expect(target):
        from playwright.async_api import expect

        return expect(target)

    @staticmethod
    def _ensure_output_dir(save_dir: str, _created_cache: Optional[set[str]] = None) -> None:
        if _created_cache is not None and save_dir in _created_cache:
            return
        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as exc:
            raise OutputDirectoryError(
                f"Cannot create directory '{save_dir}': {exc}. "
                "Check permissions or set a different directory."
            ) from exc
        if _created_cache is not None:
            _created_cache.add(save_dir)

    @staticmethod
    def _build_filename(name: Optional[str], prefix: str = "screenshot") -> str:
        if not name or not name.strip():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            return f"{prefix}_{timestamp}.png"
        if not os.path.splitext(name)[1]:
            return f"{name}.png"
        return name

    def _resolve_locator(self, selector_or_locator: Union[str, "Locator"]) -> "Locator":
        if isinstance(selector_or_locator, str):
            return self.page.locator(selector_or_locator)
        return selector_or_locator

    @staticmethod
    def _safe_output_path(directory: str, filename: str) -> str:
        if not filename:
            raise ValueError("Output filename cannot be empty.")

        if os.path.isabs(filename):
            raise ValueError("Output filename must be relative to the target directory.")

        save_dir = os.path.abspath(directory)
        filepath = os.path.abspath(os.path.join(save_dir, filename))
        try:
            common_path = os.path.commonpath([save_dir, filepath])
        except ValueError as exc:
            raise ValueError("Output filename must stay inside the target directory.") from exc

        if common_path != save_dir:
            raise ValueError("Output filename must stay inside the target directory.")

        return filepath


    @property
    def last_dialog_error(self) -> Optional[Exception]:
        return self._last_dialog_error


BasePage = BrowserPage  # 向后兼容别名，新脚本请直接使用 BrowserPage
