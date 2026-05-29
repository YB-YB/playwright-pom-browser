import os
import subprocess
import sys
from typing import Sequence

from ._common import DEFAULT_BROWSER_PROBE_TIMEOUT, REQUIREMENTS_FILE
from ._logging import get_logger
from ._platform import (
    command_failure_summary,
    get_platform_name,
    get_python_version,
    is_linux,
    normalize_python_command,
)
from ._browser_detect import detect_system_browsers, get_playwright_channel


def check_playwright_installed(python_cmd: str | Sequence[str] | None = None) -> bool:
    if python_cmd is None:
        try:
            import playwright  # noqa: F401

            return True
        except ImportError:
            return False

    try:
        result = subprocess.run(
            [*normalize_python_command(python_cmd), "-c", "import playwright"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as exc:
        get_logger().debug("Playwright package probe failed: %s", exc)
        return False

    return result.returncode == 0


def check_playwright_browsers(
    browser_type: str = "chromium",
    python_cmd: str | Sequence[str] | None = None,
    timeout: int = DEFAULT_BROWSER_PROBE_TIMEOUT,
    log_failure: bool = False,
) -> bool:
    if not check_playwright_installed(python_cmd):
        return False

    code = """
import asyncio
import sys

from playwright.async_api import async_playwright


async def main():
    browser_type = sys.argv[1]
    playwright = await async_playwright().start()
    browser = None
    try:
        launcher = getattr(playwright, browser_type)
        browser = await launcher.launch(headless=True)
    finally:
        if browser is not None:
            await browser.close()
        await playwright.stop()


asyncio.run(main())
"""
    try:
        result = subprocess.run(
            [*normalize_python_command(python_cmd), "-c", code, browser_type],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as exc:
        log = get_logger()
        if log_failure:
            log.warning("Browser probe failed for %s: %s", browser_type, exc)
        else:
            log.debug("Browser probe failed for %s: %s", browser_type, exc)
        return False

    if result.returncode == 0:
        return True

    log = get_logger()
    message = command_failure_summary(result)
    if log_failure:
        log.warning("Browser probe failed for %s:\n%s", browser_type, message)
    else:
        log.debug("Browser probe failed for %s: %s", browser_type, message)
    return False


def install_package(
    package: str,
    upgrade: bool = False,
    timeout: int = 300,
    python_cmd: str | Sequence[str] | None = None,
) -> bool:
    cmd = [*normalize_python_command(python_cmd), "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(package)

    try:
        get_logger().info("Installing %s ...", package)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        get_logger().error("%s installation timed out.", package)
        return False
    except (subprocess.SubprocessError, OSError) as exc:
        get_logger().error("Installation failed: %s", exc)
        return False

    if result.returncode == 0:
        get_logger().info("%s installed successfully.", package)
        return True

    get_logger().error("%s installation failed: %s", package, result.stderr.strip())
    return False


def install_requirements(
    requirements_file: str = REQUIREMENTS_FILE,
    timeout: int = 300,
    python_cmd: str | Sequence[str] | None = None,
) -> bool:
    if not os.path.exists(requirements_file):
        return install_package("playwright", timeout=timeout, python_cmd=python_cmd)

    cmd = [*normalize_python_command(python_cmd), "-m", "pip", "install", "-r", requirements_file]
    try:
        get_logger().info("Installing dependencies from %s ...", requirements_file)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        get_logger().error("Dependency installation timed out.")
        return False
    except (subprocess.SubprocessError, OSError) as exc:
        get_logger().error("Dependency installation failed: %s", exc)
        return False

    if result.returncode == 0:
        get_logger().info("Dependencies installed successfully.")
        return True

    get_logger().error("Dependency installation failed: %s", result.stderr.strip())
    return False


def install_playwright_browsers(
    *browsers: str,
    with_deps: bool = False,
    timeout: int = 900,
    python_cmd: str | Sequence[str] | None = None,
) -> bool:
    if not browsers:
        browsers = ("chromium",)

    cmd = [*normalize_python_command(python_cmd), "-m", "playwright", "install"]
    if with_deps and is_linux():
        cmd.append("--with-deps")
    cmd.extend(browsers)

    browser_names = ", ".join(browsers)
    try:
        get_logger().info("Installing Playwright browser(s): %s ...", browser_names)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        get_logger().error("Browser installation timed out.")
        return False
    except (subprocess.SubprocessError, OSError) as exc:
        get_logger().error("Browser installation failed: %s", exc)
        return False

    if result.returncode == 0:
        get_logger().info("Browser installation completed: %s", browser_names)
        return True

    get_logger().error("Browser installation failed: %s", result.stderr.strip())
    return False


def ensure_playwright_environment(
    browsers: tuple[str, ...] = ("chromium",),
    auto_install: bool = False,
    python_cmd: str | Sequence[str] | None = None,
    browser_probe_timeout: int = DEFAULT_BROWSER_PROBE_TIMEOUT,
) -> bool:
    log = get_logger()
    log.info("Platform: %s", get_platform_name())
    log.info("Python: %s", get_python_version(python_cmd))

    package_ok = check_playwright_installed(python_cmd)
    log.info("Playwright package: %s", "installed" if package_ok else "missing")

    if not package_ok:
        if not auto_install:
            log.warning(
                "Install Playwright first: %s -m pip install playwright",
                " ".join(normalize_python_command(python_cmd)),
            )
            return False
        if not install_requirements(python_cmd=python_cmd):
            return False

    # 优先检测系统浏览器：如果有可用的系统浏览器（支持 channel 模式），跳过下载
    detection = detect_system_browsers()
    if detection.has_any:
        best = detection.get_best()
        if best and get_playwright_channel(best):
            log.info(
                "System browser available: %s. "
                "Playwright will use it via channel='%s', skipping browser download.",
                best.display,
                get_playwright_channel(best),
            )
            return True

    # 无可用系统浏览器，检查 Playwright 内置浏览器
    missing_browsers = [
        browser
        for browser in browsers
        if not check_playwright_browsers(browser, python_cmd, timeout=browser_probe_timeout, log_failure=True)
    ]
    if not missing_browsers:
        log.info("Requested browser(s) are available.")
        return True

    log.warning("No system browsers detected. Missing Playwright browser(s): %s", ", ".join(missing_browsers))
    if not auto_install:
        log.warning(
            "Install browsers with: %s -m playwright install %s",
            " ".join(normalize_python_command(python_cmd)),
            " ".join(missing_browsers),
        )
        return False

    log.info("Downloading Playwright browser(s): %s ...", ", ".join(missing_browsers))
    return install_playwright_browsers(*missing_browsers, python_cmd=python_cmd)
