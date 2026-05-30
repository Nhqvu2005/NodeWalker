"""
Browser Launcher — Auto-detect, select, and launch browsers with debug port.

Supports Chrome, Edge, Brave, Firefox, Opera, Chromium, and custom paths.
Uses the user's default profile (no clean/temp profile).
Reads browser_config.json to decide which browser to use.
"""

import json
import os
import platform
import random
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

# ── Known browser paths per OS ─────────────────────────────────

_BROWSER_PATHS: dict[str, dict[str, list[str]]] = {
    "windows": {
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        "brave": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
        "opera": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\opera.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe"),
        ],
        "chromium": [
            r"C:\Program Files\Chromium\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Chromium\Application\chrome.exe"),
        ],
    },
    "darwin": {
        "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
        "edge": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
        "brave": ["/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
        "firefox": ["/Applications/Firefox.app/Contents/MacOS/firefox"],
        "opera": ["/Applications/Opera.app/Contents/MacOS/Opera"],
        "chromium": ["/Applications/Chromium.app/Contents/MacOS/Chromium"],
    },
    "linux": {
        "chrome": ["google-chrome", "google-chrome-stable"],
        "edge": ["microsoft-edge", "microsoft-edge-stable"],
        "brave": ["brave-browser", "brave-browser-stable"],
        "firefox": ["firefox"],
        "opera": ["opera"],
        "chromium": ["chromium", "chromium-browser"],
    },
}

# Process names for killing (Windows)
_PROCESS_NAMES: dict[str, str] = {
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "brave": "brave.exe",
    "firefox": "firefox.exe",
    "opera": "opera.exe",
    "chromium": "chrome.exe",
}


def _get_os_key() -> str:
    """Get the OS key for path lookup."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "darwin"
    return "linux"


def _find_browser_exe(browser_name: str) -> str | None:
    """Find the executable path for a browser on the current OS."""
    os_key = _get_os_key()
    paths = _BROWSER_PATHS.get(os_key, {}).get(browser_name, [])

    for path in paths:
        if os_key == "linux":
            # On Linux, check if command is in PATH
            found = shutil.which(path)
            if found:
                return found
        else:
            if os.path.isfile(path):
                return path

    return None


def load_config(config_path: str | None = None) -> dict:
    """Load browser_config.json. Creates default if not found.

    Args:
        config_path: Path to config file. If None, looks in project root.

    Returns:
        Config dict with browser selection values.
    """
    if config_path is None:
        # Look relative to this file's project root
        # __file__ is nodewalker/core/browser_launcher.py
        # project root is 3 levels up: core -> nodewalker -> NodeWalker
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "browser_config.json"
    else:
        config_path = Path(config_path)

    if config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Create default config
    default_config = {
        "chrome": 1,
        "edge": 0,
        "brave": 0,
        "firefox": 0,
        "opera": 0,
        "chromium": 0,
        "other": "",
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=4)

    return default_config


def select_browser(config: dict) -> tuple[str, str]:
    """Select which browser to use based on config.

    Returns:
        (browser_name, exe_path) tuple.

    Raises:
        RuntimeError: If no browser could be found.
    """
    known_browsers = ["chrome", "edge", "brave", "firefox", "opera", "chromium"]

    # Collect browsers with value=1
    enabled = [b for b in known_browsers if config.get(b) == 1]

    if enabled:
        # If multiple enabled, pick random
        if len(enabled) > 1:
            random.shuffle(enabled)

        for browser_name in enabled:
            exe = _find_browser_exe(browser_name)
            if exe:
                return browser_name, exe

        # Enabled browsers not found on system
        tried = ", ".join(enabled)
        raise RuntimeError(
            f"Enabled browser(s) [{tried}] not found on this system. "
            f"Install one or set 'other' in browser_config.json."
        )

    # All 0 → use "other"
    other_path = config.get("other", "").strip()
    if other_path and os.path.isfile(other_path):
        return "other", other_path

    raise RuntimeError(
        "No browser selected. Set at least one browser to 1 in browser_config.json, "
        "or provide a path in the 'other' field."
    )


def _is_debug_port_open(port: int) -> bool:
    """Check if a debug port is already responding to CDP."""
    try:
        resp = urllib.request.urlopen(
            f"http://localhost:{port}/json/version", timeout=2
        )
        data = json.loads(resp.read())
        return "Browser" in data
    except Exception:
        return False


def _kill_browser(browser_name: str) -> bool:
    """Kill all processes of a browser. Returns True if killed anything."""
    os_key = _get_os_key()

    if os_key == "windows":
        proc_name = _PROCESS_NAMES.get(browser_name, f"{browser_name}.exe")
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/T", "/IM", proc_name],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
    else:
        # Linux/Mac: pkill
        proc_name = _PROCESS_NAMES.get(browser_name, browser_name)
        proc_name_no_ext = proc_name.replace(".exe", "")
        try:
            result = subprocess.run(
                ["pkill", "-f", proc_name_no_ext],
                capture_output=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False


def _get_default_profile_dir(browser_name: str) -> Path | None:
    """Get the default user data directory for a browser."""
    os_key = _get_os_key()

    if os_key == "windows":
        appdata = os.environ.get("LOCALAPPDATA", "")
        dirs = {
            "chrome": Path(appdata) / "Google" / "Chrome" / "User Data",
            "edge": Path(appdata) / "Microsoft" / "Edge" / "User Data",
            "brave": Path(appdata) / "BraveSoftware" / "Brave-Browser" / "User Data",
            "chromium": Path(appdata) / "Chromium" / "User Data",
            "opera": Path(appdata) / "Opera Software" / "Opera Stable",
        }
    elif os_key == "darwin":
        home = Path.home()
        dirs = {
            "chrome": home / "Library/Application Support/Google/Chrome",
            "edge": home / "Library/Application Support/Microsoft Edge",
            "brave": home / "Library/Application Support/BraveSoftware/Brave-Browser",
            "chromium": home / "Library/Application Support/Chromium",
        }
    else:
        home = Path.home()
        dirs = {
            "chrome": home / ".config/google-chrome",
            "edge": home / ".config/microsoft-edge",
            "brave": home / ".config/BraveSoftware/Brave-Browser",
            "chromium": home / ".config/chromium",
        }

    profile_dir = dirs.get(browser_name)
    if profile_dir and profile_dir.is_dir():
        return profile_dir
    return None


def _clear_crash_sentinels(browser_name: str) -> None:
    """Remove crash recovery sentinel files from the browser's default profile.

    After force-killing a browser, these files tell Chrome to show the
    'Restore pages?' dialog on next launch, which blocks CDP initialization.
    """
    profile_dir = _get_default_profile_dir(browser_name)
    if not profile_dir:
        return

    # Files that trigger crash recovery dialog
    sentinels = [
        "SingletonLock",
        "SingletonSocket",
        "SingletonCookie",
        "lockfile",
    ]

    for sentinel in sentinels:
        target = profile_dir / sentinel
        try:
            if target.exists():
                target.unlink(missing_ok=True)
        except Exception:
            pass

    # Also clean the "exit_type" in Preferences to prevent "crashed" notification
    prefs_file = profile_dir / "Default" / "Preferences"
    if prefs_file.is_file():
        try:
            with open(prefs_file, "r", encoding="utf-8") as f:
                prefs = json.load(f)

            # Set exit_type to "Normal" so Chrome doesn't think it crashed
            if prefs.get("profile", {}).get("exit_type") == "Crashed":
                prefs["profile"]["exit_type"] = "Normal"
                prefs["profile"]["exited_cleanly"] = True
                with open(prefs_file, "w", encoding="utf-8") as f:
                    json.dump(prefs, f)
        except Exception:
            pass


def launch_browser(
    exe_path: str,
    browser_name: str,
    debug_port: int = 9222,
) -> subprocess.Popen:
    """Launch browser with remote debugging enabled.

    Chrome v141+ requires --user-data-dir pointing to a NON-default directory
    for remote debugging. We create a dedicated debug profile dir and symlink
    the 'Default' subfolder from the user's real profile so cookies/login/
    history are preserved.

    Args:
        exe_path: Path to browser executable.
        browser_name: Name of the browser (for logging).
        debug_port: CDP debug port.

    Returns:
        Popen process handle.
    """
    # Firefox uses a different flag format
    if browser_name == "firefox":
        args = [exe_path, "--remote-debugging-port", str(debug_port)]
    else:
        # Build the debug profile directory
        debug_profile_dir = _prepare_debug_profile(browser_name)

        args = [
            exe_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={debug_profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-session-crashed-bubble",
            "--hide-crash-restore-bubble",
            "--disable-features=TranslateUI",
            "about:blank",
        ]

    # Launch detached (Chrome is a GUI app, needs its own window)
    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def _prepare_debug_profile(browser_name: str) -> Path:
    """Create a debug profile dir that shares ALL data with the real profile.

    Strategy:
    1. Get the real User Data directory (e.g. AppData/Local/Microsoft/Edge/User Data)
    2. Create an NTFS junction at ~/.nodewalker/<browser>/ → real User Data
       (NTFS junctions don't need admin on Windows, unlike symlinks)
    3. If junction already exists, reuse it
    4. If junction fails, return the real profile path directly

    This way the browser opens with the user's real cookies, sessions, etc.
    but Chrome v141+ sees it as a "non-default" path, satisfying its requirement.

    Returns:
        Path to use as --user-data-dir.
    """
    real_profile = _get_default_profile_dir(browser_name)
    if not real_profile:
        # No real profile found, just use a blank one
        home = Path.home()
        debug_dir = home / ".nodewalker" / browser_name
        debug_dir.mkdir(parents=True, exist_ok=True)
        return debug_dir

    home = Path.home()
    debug_dir = home / ".nodewalker" / browser_name

    # If debug_dir already exists and is a junction/symlink to the right place, reuse
    if debug_dir.exists():
        try:
            # Check if it's a junction/symlink pointing to the real profile
            if debug_dir.is_symlink() or _is_junction(debug_dir):
                resolved = debug_dir.resolve()
                if resolved == real_profile.resolve():
                    return debug_dir
                # Points to wrong place, remove and recreate
                os.remove(str(debug_dir))
            elif debug_dir.is_dir():
                # Regular directory from old approach, remove it
                import shutil
                shutil.rmtree(debug_dir, ignore_errors=True)
        except Exception:
            pass

    # Create parent directory
    debug_dir.parent.mkdir(parents=True, exist_ok=True)

    # Try creating NTFS junction (Windows) or symlink (Unix)
    os_key = _get_os_key()
    try:
        if os_key == "windows":
            # NTFS junction: doesn't need admin privileges!
            import subprocess
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(debug_dir), str(real_profile)],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                print(f"[Browser] Profile junction: {debug_dir} → {real_profile}")
                return debug_dir
            else:
                print(f"[Browser] Junction failed: {result.stderr.strip()}")
        else:
            # Unix: symlinks work without admin
            os.symlink(real_profile, debug_dir, target_is_directory=True)
            print(f"[Browser] Profile symlink: {debug_dir} → {real_profile}")
            return debug_dir
    except Exception as e:
        print(f"[Browser] Could not create profile link: {e}")

    # Fallback: use real profile path directly
    # This works for Edge/Brave/etc. Chrome v141+ may reject it.
    print(f"[Browser] Using real profile directly: {real_profile}")
    return real_profile


def _is_junction(path: Path) -> bool:
    """Check if a path is an NTFS junction point (Windows)."""
    try:
        import ctypes
        FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False


def ensure_browser_ready(
    config_path: str | None = None,
    debug_port: int = 9222,
    timeout: int = 30,
) -> dict:
    """Main entry point: ensure a browser is running with CDP debug port.

    Logic:
    1. If debug port is already open → reuse (no restart)
    2. Else → read config, select browser, kill existing, relaunch with debug port
    3. Wait for debug port to respond

    Args:
        config_path: Path to browser_config.json.
        debug_port: CDP remote debugging port.
        timeout: Max seconds to wait for browser to start.

    Returns:
        {"browser": name, "exe": path, "port": port, "reused": bool}
    """
    # Step 1: Check if debug port is already open
    if _is_debug_port_open(debug_port):
        try:
            resp = urllib.request.urlopen(
                f"http://localhost:{debug_port}/json/version", timeout=2
            )
            info = json.loads(resp.read())
            browser_str = info.get("Browser", "Unknown")
            return {
                "browser": browser_str,
                "exe": "(already running)",
                "port": debug_port,
                "reused": True,
            }
        except Exception:
            pass

    # Step 2: Read config and select browser
    config = load_config(config_path)
    browser_name, exe_path = select_browser(config)

    print(f"[Browser] Selected: {browser_name} ({exe_path})")

    # Step 3: Kill existing browser processes (so we can relaunch with debug port)
    print(f"[Browser] Closing existing {browser_name} processes...")
    killed = _kill_browser(browser_name)
    # Give OS time to fully release resources (especially on Windows)
    time.sleep(4 if killed else 1)

    # Step 3.5: Clear crash recovery sentinels so Chrome doesn't show
    # "Restore pages?" dialog which blocks CDP init
    print(f"[Browser] Clearing crash recovery markers...")
    _clear_crash_sentinels(browser_name)

    # Step 4: Launch with debug port (uses default profile automatically)
    print(f"[Browser] Launching with --remote-debugging-port={debug_port}...")
    proc = launch_browser(exe_path, browser_name, debug_port)

    # Step 5: Wait for debug port to respond
    print(f"[Browser] Waiting for CDP port {debug_port}...")
    start = time.time()
    while time.time() - start < timeout:
        if _is_debug_port_open(debug_port):
            elapsed = time.time() - start
            print(f"[Browser] Ready! CDP responding ({elapsed:.1f}s)")
            return {
                "browser": browser_name,
                "exe": exe_path,
                "port": debug_port,
                "pid": proc.pid,
                "reused": False,
            }
        time.sleep(1)

    raise RuntimeError(
        f"Browser failed to start within {timeout}s. "
        f"Tried: {exe_path} --remote-debugging-port={debug_port}"
    )
