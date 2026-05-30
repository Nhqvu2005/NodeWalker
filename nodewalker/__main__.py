"""
NodeWalker CLI entry point.

Usage:
    python -m nodewalker                          # Auto-detect browser, default ports
    python -m nodewalker --port 9000              # Custom server port
    python -m nodewalker --debug-port 9333        # Custom browser debugging port
    python -m nodewalker --host 0.0.0.0           # Listen on all interfaces
    python -m nodewalker --no-launch              # Don't auto-launch browser
    python -m nodewalker --config path/to/cfg     # Custom browser config file
"""

import argparse
import uvicorn
from nodewalker.server import create_app
from nodewalker.core.browser_launcher import ensure_browser_ready


def main():
    parser = argparse.ArgumentParser(
        prog="nodewalker",
        description="NodeWalker - Browser Control Tool for AI Agents",
    )
    parser.add_argument(
        "--port", type=int, default=8585,
        help="HTTP server port (default: 8585)"
    )
    parser.add_argument(
        "--debug-port", type=int, default=9222,
        help="Browser remote debugging port (default: 9222)"
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--no-launch", action="store_true",
        help="Don't auto-launch browser (assume it's already running)"
    )
    parser.add_argument(
        "--reload", action="store_true",
        help="Enable hot-reload: auto-restart server when code changes"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to browser_config.json (default: auto-detect)"
    )
    # Keep backward compat
    parser.add_argument(
        "--chrome-port", type=int, default=None,
        help=argparse.SUPPRESS  # Hidden, backward compat
    )
    args = parser.parse_args()

    # Backward compat: --chrome-port maps to --debug-port
    debug_port = args.chrome_port or args.debug_port

    # ── Auto-launch browser ────────────────────────────────────
    browser_info = None
    if not args.no_launch:
        try:
            browser_info = ensure_browser_ready(
                config_path=args.config,
                debug_port=debug_port,
            )
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            print("        Use --no-launch to skip auto-launch")
            return

    browser_label = "Unknown"
    if browser_info:
        if browser_info["reused"]:
            browser_label = f"{browser_info['browser']} (reused)"
        else:
            browser_label = browser_info["browser"]

    reload_label = "ON" if args.reload else "OFF"
    print(f"""
+==================================================+
|              NodeWalker v0.2.0                   |
|       Browser Control Tool for AI Agents         |
+==================================================+
|  Server:   http://{args.host}:{args.port:<23}|
|  Browser:  {browser_label:<37}|
|  CDP Port: {debug_port:<37}|
|  Reload:   {reload_label:<37}|
+--------------------------------------------------+
|  GET  /tools      - Tool schemas                 |
|  POST /execute    - Run a tool                   |
|  GET  /health     - Status check                 |
+==================================================+
""")

    # For hot-reload, uvicorn needs the app as an import string
    if args.reload:
        # Set chrome_port via env var so the app factory picks it up
        import os
        os.environ["NODEWALKER_CHROME_PORT"] = str(debug_port)
        uvicorn.run(
            "nodewalker.server:app",
            host=args.host,
            port=args.port,
            log_level="info",
            reload=True,
            reload_dirs=["nodewalker"],
        )
    else:
        app = create_app(chrome_port=debug_port)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
