import os
import sys
import time
import atexit
import signal
import subprocess
import urllib.request
from typing import List, Optional
from src.logger import get_logger

logger = get_logger("process_mgr")

class ProcessManager:
    """Manages process lifecycle, auto-launches Chrome CDP, and cleans up sub-processes on exit."""

    _instance = None
    child_processes: List[subprocess.Popen] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance._register_signals()
        return cls._instance

    def _register_signals(self):
        atexit.register(self.cleanup)
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except Exception:
            pass

    def _handle_signal(self, signum, frame):
        logger.info(f"Received exit signal ({signum}). Cleaning up processes...")
        self.cleanup()
        sys.exit(0)

    def register_process(self, proc: subprocess.Popen):
        if proc and proc not in self.child_processes:
            self.child_processes.append(proc)

    def cleanup(self):
        """Terminates all registered child processes cleanly."""
        for proc in self.child_processes:
            try:
                if proc.poll() is None:
                    logger.info(f"Terminating child process PID {proc.pid}...")
                    proc.terminate()
                    proc.wait(timeout=2)
            except Exception as e:
                logger.warning(f"Failed to gracefully terminate PID {proc.pid}: {e}")
                try:
                    proc.kill()
                except Exception:
                    pass
        self.child_processes.clear()

def is_cdp_available(cdp_url: str = "http://localhost:9222") -> bool:
    """Checks if Chrome DevTools Protocol is responsive on port 9222."""
    try:
        req = urllib.request.urlopen(f"{cdp_url}/json/version", timeout=2)
        return req.getcode() == 200
    except Exception:
        return False

def find_chrome_executable() -> Optional[str]:
    """Finds the Google Chrome executable path on Windows."""
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        paths.append(os.path.join(local_appdata, r"Google\Chrome\Application\chrome.exe"))

    for p in paths:
        if os.path.exists(p):
            return p
    return None

def ensure_chrome_running(cdp_port: int = 9222, default_url: str = "https://www.naukri.com") -> bool:
    """Checks if Chrome is running on debug port 9222; if not, launches Chrome automatically."""
    cdp_url = f"http://localhost:{cdp_port}"
    if is_cdp_available(cdp_url):
        logger.info(f"✅ Chrome CDP already active on port {cdp_port}.")
        return True

    logger.info(f"⚠️ Chrome CDP port {cdp_port} not detected. Auto-launching Chrome...")
    chrome_path = find_chrome_executable()
    if not chrome_path:
        logger.error("❌ Google Chrome executable not found on system!")
        return False

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_data_dir = os.path.join(project_dir, "chrome_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    cmd = [
        chrome_path,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        default_url
    ]

    try:
        proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        ProcessManager().register_process(proc)
        logger.info(f"🚀 Launched Chrome (PID {proc.pid}) with CDP port {cdp_port}.")

        # Wait up to 8s for CDP to become active
        for _ in range(16):
            time.sleep(0.5)
            if is_cdp_available(cdp_url):
                logger.info(f"✅ Connected to Chrome CDP on port {cdp_port} successfully!")
                return True

        logger.warning(f"Chrome launched (PID {proc.pid}) but CDP port {cdp_port} took longer to respond.")
        return True
    except Exception as e:
        logger.error(f"Failed to auto-launch Chrome: {e}")
        return False
