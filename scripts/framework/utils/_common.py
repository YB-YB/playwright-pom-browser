import os


SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REQUIREMENTS_FILE = os.path.join(SCRIPT_DIR, "requirements.txt")
DEFAULT_BROWSER_PROBE_TIMEOUT = 120
MAX_DIAGNOSTIC_CHARS = 1200
SETUP_SCRIPT = os.path.join(SCRIPT_DIR, "setup.py")
RUN_TEST_SCRIPT = os.path.join(SCRIPT_DIR, "run_test.py")
