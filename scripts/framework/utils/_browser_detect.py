"""检测系统已安装的浏览器及版本信息。

通过注册表（Windows）、应用目录（macOS）、which 命令（Linux）
探测系统中可用的浏览器，返回结构化的检测结果。
"""

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

from ._logging import get_logger
from ._platform import is_windows, is_macos, is_linux


@dataclass
class BrowserInfo:
    """单个浏览器的检测结果。"""

    name: str
    channel: str  # Playwright channel 参数值，如 "chrome", "msedge"
    executable: str = ""
    version: str = ""
    available: bool = False

    @property
    def display(self) -> str:
        if not self.available:
            return f"{self.name}: not found"
        ver = f" ({self.version})" if self.version else ""
        return f"{self.name}{ver} -> {self.executable}"


@dataclass
class DetectionResult:
    """系统浏览器检测汇总结果。"""

    browsers: list[BrowserInfo] = field(default_factory=list)

    @property
    def available_browsers(self) -> list[BrowserInfo]:
        return [b for b in self.browsers if b.available]

    @property
    def has_any(self) -> bool:
        return len(self.available_browsers) > 0

    def get_best(self) -> Optional[BrowserInfo]:
        """按优先级返回最佳可用浏览器。"""
        available = self.available_browsers
        return available[0] if available else None


# --- 优先级顺序：Chrome > Edge > Firefox ---
# Playwright 的 channel 参数支持使用系统浏览器，避免额外下载
_BROWSER_PRIORITY = [
    ("Google Chrome", "chrome"),
    ("Microsoft Edge", "msedge"),
    ("Firefox", "firefox"),
]


def _extract_version(output: str) -> str:
    """从命令输出中提取版本号。"""
    match = re.search(r"(\d+\.\d+[\.\d]*)", output)
    return match.group(1) if match else ""


def _probe_executable(path: str) -> tuple[bool, str]:
    """验证可执行文件是否存在并尝试获取版本。"""
    if not path or not os.path.isfile(path):
        return False, ""

    # Windows 上 Chrome/Edge 的 --version 会启动浏览器窗口，改用目录名获取版本
    if is_windows():
        version = _version_from_app_dir(path)
        if version:
            return True, version

    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = _extract_version(result.stdout + result.stderr)
        return True, version
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        # 文件存在但无法执行 --version，仍视为可用
        return True, ""


def _version_from_app_dir(exe_path: str) -> str:
    """从 Windows 应用安装目录的版本号子文件夹提取版本（Chrome/Edge 通用）。"""
    app_dir = os.path.dirname(exe_path)
    if not os.path.isdir(app_dir):
        return ""

    for item in os.listdir(app_dir):
        if os.path.isdir(os.path.join(app_dir, item)) and re.match(r"\d+\.\d+", item):
            return item
    return ""


def _detect_windows() -> list[BrowserInfo]:
    """Windows 平台：通过注册表和常见路径检测浏览器。"""
    results = []

    # Chrome 常见路径
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    # Edge 常见路径
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    ]

    # Firefox 常见路径
    firefox_paths = [
        os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
    ]

    candidates = [
        ("Google Chrome", "chrome", chrome_paths),
        ("Microsoft Edge", "msedge", edge_paths),
        ("Firefox", "firefox", firefox_paths),
    ]

    for name, channel, paths in candidates:
        info = BrowserInfo(name=name, channel=channel)
        for path in paths:
            found, version = _probe_executable(path)
            if found:
                info.executable = path
                info.version = version
                info.available = True
                break

        # 注册表回退：尝试从注册表获取安装路径
        if not info.available:
            reg_path = _query_windows_registry(channel)
            if reg_path:
                found, version = _probe_executable(reg_path)
                if found:
                    info.executable = reg_path
                    info.version = version
                    info.available = True

        results.append(info)

    return results


def _query_windows_registry(channel: str) -> str:
    """从 Windows 注册表查询浏览器安装路径。"""
    import winreg

    registry_keys = {
        "chrome": [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
        ],
        "msedge": [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
        ],
        "firefox": [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
        ],
    }

    keys = registry_keys.get(channel, [])
    for hive, key_path in keys:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "")
                if value and os.path.isfile(value):
                    return value
        except (OSError, FileNotFoundError):
            continue

    return ""


def _detect_macos() -> list[BrowserInfo]:
    """macOS 平台：通过 Applications 目录检测浏览器。"""
    results = []

    candidates = [
        ("Google Chrome", "chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ("Microsoft Edge", "msedge", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ("Firefox", "firefox", "/Applications/Firefox.app/Contents/MacOS/firefox"),
    ]

    for name, channel, path in candidates:
        info = BrowserInfo(name=name, channel=channel)
        found, version = _probe_executable(path)
        if found:
            info.executable = path
            info.version = version
            info.available = True
        results.append(info)

    return results


def _detect_linux() -> list[BrowserInfo]:
    """Linux 平台：通过 which 命令检测浏览器。"""
    results = []

    candidates = [
        ("Google Chrome", "chrome", ["google-chrome", "google-chrome-stable", "chrome"]),
        ("Microsoft Edge", "msedge", ["microsoft-edge", "microsoft-edge-stable"]),
        ("Firefox", "firefox", ["firefox"]),
    ]

    for name, channel, commands in candidates:
        info = BrowserInfo(name=name, channel=channel)
        for cmd in commands:
            exe = shutil.which(cmd)
            if exe:
                found, version = _probe_executable(exe)
                if found:
                    info.executable = exe
                    info.version = version
                    info.available = True
                    break
        results.append(info)

    return results


def detect_system_browsers() -> DetectionResult:
    """检测当前系统中已安装的浏览器，按优先级排序返回。"""
    log = get_logger()
    log.info("Detecting system browsers...")

    if is_windows():
        browsers = _detect_windows()
    elif is_macos():
        browsers = _detect_macos()
    elif is_linux():
        browsers = _detect_linux()
    else:
        log.warning("Unsupported platform for browser detection: %s", sys.platform)
        browsers = []

    result = DetectionResult(browsers=browsers)

    for b in result.browsers:
        log.info("  %s", b.display)

    if result.has_any:
        best = result.get_best()
        log.info("Best available browser: %s", best.display if best else "none")
    else:
        log.info("No system browsers detected.")

    return result


def get_playwright_channel(browser_info: BrowserInfo) -> Optional[str]:
    """将检测到的浏览器映射为 Playwright launch 的 channel 参数。

    Chrome/Edge 使用 channel 参数启动系统浏览器；
    Firefox 需要使用 Playwright 自带的 firefox 引擎（channel 不适用）。
    """
    # Playwright channel 仅支持 Chromium 系浏览器
    if browser_info.channel in ("chrome", "msedge"):
        return browser_info.channel
    # Firefox 不支持 channel，需要 Playwright 自带的 firefox
    return None
