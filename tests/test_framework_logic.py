import asyncio
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_setup_module():
    spec = importlib.util.spec_from_file_location("skill_setup", SCRIPTS / "setup.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SetupVenvTests(unittest.TestCase):
    def setUp(self):
        self.setup = load_setup_module()

    def test_rejects_venv_inside_skill_directory(self):
        skill_venv = ROOT / "task" / ".venv"
        with self.assertRaisesRegex(RuntimeError, "inside the skill directory"):
            self.setup.validate_venv_location(str(skill_venv))

    def test_allows_venv_outside_skill_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.setup.validate_venv_location(os.path.join(tmp, ".venv"))

    def test_existing_unrunnable_venv_reports_recreate_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            venv_dir = Path(tmp) / ".venv"
            scripts_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
            scripts_dir.mkdir(parents=True)
            python_path = scripts_dir / ("python.exe" if os.name == "nt" else "python")
            python_path.write_text("", encoding="utf-8")

            with mock.patch.object(self.setup, "check_python_runnable", return_value=(False, "broken launcher")):
                with self.assertRaisesRegex(RuntimeError, "--recreate-venv"):
                    self.setup.create_venv_if_needed(str(venv_dir))


class UtilsDiagnosticsTests(unittest.TestCase):
    def test_command_failure_summary_includes_stderr(self):
        from framework.utils import command_failure_summary

        result = subprocess.CompletedProcess(["python"], 1, stdout="", stderr="browser missing")
        self.assertEqual(command_failure_summary(result), "stderr: browser missing")


class FakePage:
    def __init__(self):
        self.calls = []

    async def evaluate(self, *args):
        self.calls.append(args)
        return args


class BrowserPageEvaluateTests(unittest.IsolatedAsyncioTestCase):
    async def test_evaluate_without_arg_uses_one_argument(self):
        from framework.base_page import BrowserPage

        page = FakePage()
        browser = BrowserPage(page)
        result = await browser.evaluate("() => 1")

        self.assertEqual(result, ("() => 1",))
        self.assertEqual(page.calls, [("() => 1",)])

    async def test_evaluate_with_arg_forwards_playwright_arg(self):
        from framework.base_page import BrowserPage

        page = FakePage()
        browser = BrowserPage(page)
        result = await browser.evaluate("(value) => value.answer", {"answer": 42})

        self.assertEqual(result, ("(value) => value.answer", {"answer": 42}))
        self.assertEqual(page.calls, [("(value) => value.answer", {"answer": 42})])

    async def test_evaluate_can_pass_none_as_explicit_arg(self):
        from framework.base_page import BrowserPage

        page = FakePage()
        browser = BrowserPage(page)
        result = await browser.evaluate("(value) => value", None)

        self.assertEqual(result, ("(value) => value", None))
        self.assertEqual(page.calls, [("(value) => value", None)])


class ConfigEnvTests(unittest.TestCase):
    def test_from_env_uses_defaults_when_no_env_vars(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = Config.from_env()
            self.assertIsNone(cfg.headless)
            self.assertEqual(cfg.browser_type, "chromium")
            self.assertEqual(cfg.timeout, 30000)
            self.assertEqual(cfg.navigation_timeout, 60000)
            self.assertEqual(cfg.viewport_width, 1280)
            self.assertEqual(cfg.viewport_height, 800)
            self.assertTrue(cfg.accept_downloads)

    def test_from_env_reads_browser_headless_true(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {"BROWSER_HEADLESS": "true"}, clear=True):
            cfg = Config.from_env()
            self.assertTrue(cfg.headless)

    def test_from_env_reads_browser_headless_false(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {"BROWSER_HEADLESS": "false"}, clear=True):
            cfg = Config.from_env()
            self.assertFalse(cfg.headless)

    def test_from_env_reads_browser_type(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {"BROWSER_TYPE": "firefox"}, clear=True):
            cfg = Config.from_env()
            self.assertEqual(cfg.browser_type, "firefox")

    def test_from_env_reads_timeout(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {"BROWSER_TIMEOUT": "45000"}, clear=True):
            cfg = Config.from_env()
            self.assertEqual(cfg.timeout, 45000)

    def test_from_env_rejects_negative_timeout(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {"BROWSER_TIMEOUT": "-100"}, clear=True):
            cfg = Config.from_env()
            self.assertEqual(cfg.timeout, 30000)

    def test_from_env_reads_storage_state(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {"BROWSER_STORAGE_STATE": "auth.json"}, clear=True):
            cfg = Config.from_env()
            self.assertEqual(cfg.storage_state_path, "auth.json")

    def test_from_env_reads_accept_downloads(self):
        from framework.config import Config

        with mock.patch.dict(os.environ, {"BROWSER_ACCEPT_DOWNLOADS": "false"}, clear=True):
            cfg = Config.from_env()
            self.assertFalse(cfg.accept_downloads)

    def test_post_init_rejects_invalid_browser_type(self):
        from framework.config import Config

        with self.assertRaises(ValueError):
            Config(browser_type="invalid_browser")

    def test_post_init_rejects_zero_timeout(self):
        from framework.config import Config

        with self.assertRaises(ValueError):
            Config(timeout=0)


class CliParsingTests(unittest.TestCase):
    def test_parse_viewport_standard_format(self):
        from framework.cli import _parse_viewport

        width, height = _parse_viewport("1280x800")
        self.assertEqual(width, 1280)
        self.assertEqual(height, 800)

    def test_parse_viewport_widthxheight(self):
        from framework.cli import _parse_viewport

        width, height = _parse_viewport("1920*1080")
        self.assertEqual(width, 1920)
        self.assertEqual(height, 1080)

    def test_parse_viewport_rejects_invalid_format(self):
        from framework.cli import _parse_viewport

        with self.assertRaises(Exception):
            _parse_viewport("1280")

    def test_parse_viewport_rejects_negative_values(self):
        from framework.cli import _parse_viewport

        with self.assertRaises(Exception):
            _parse_viewport("-1280x800")

    def test_config_from_args_headless_flag(self):
        import argparse
        from framework.cli import config_from_args

        ns = argparse.Namespace(
            headless=True, headed=False, interactive=False,
            browser=None, timeout=None, navigation_timeout=None,
            base_url=None, screenshot_dir=None, storage_state=None,
            viewport=None, viewport_width=None, viewport_height=None,
            browser_probe_timeout=None, skip_env_check=False, install_missing=False,
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = config_from_args(ns)
            self.assertTrue(cfg.headless)


class BrowserManagerTests(unittest.TestCase):
    def test_ask_headless_returns_true_for_default(self):
        from framework.browser_manager import BrowserManager

        with mock.patch("framework.browser_manager.safe_input", return_value=""):
            result = BrowserManager.ask_headless_mode()
            self.assertTrue(result)

    def test_ask_headless_returns_false_for_option_2(self):
        from framework.browser_manager import BrowserManager

        with mock.patch("framework.browser_manager.safe_input", return_value="2"):
            result = BrowserManager.ask_headless_mode()
            self.assertFalse(result)

    def test_ask_browser_type_returns_chromium_by_default(self):
        from framework.browser_manager import BrowserManager

        with mock.patch("framework.browser_manager.safe_input", return_value=""):
            result = BrowserManager.ask_browser_type()
            self.assertEqual(result, "chromium")

    def test_ask_browser_type_returns_firefox_for_option_2(self):
        from framework.browser_manager import BrowserManager

        with mock.patch("framework.browser_manager.safe_input", return_value="2"):
            result = BrowserManager.ask_browser_type()
            self.assertEqual(result, "firefox")

    def test_browser_manager_default_config(self):
        from framework.browser_manager import BrowserManager

        mgr = BrowserManager()
        self.assertIsNotNone(mgr.config)
        self.assertIsNone(mgr.browser)
        self.assertIsNone(mgr.context)
        self.assertIsNone(mgr.page)

    def test_browser_manager_custom_config(self):
        from framework.config import Config
        from framework.browser_manager import BrowserManager

        cfg = Config(browser_type="firefox", headless=False)
        mgr = BrowserManager(cfg)
        self.assertEqual(mgr.config.browser_type, "firefox")
        self.assertFalse(mgr.config.headless)


if __name__ == "__main__":
    unittest.main()
