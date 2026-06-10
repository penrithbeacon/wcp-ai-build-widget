"""
wcp_bonjour.py — WCP Bonjour Agent discovery and notification client.
Widget Context Protocol 2.2.0  |  https://widgetcontextprotocol.com

Drop this file into any WCP widget container alongside app.py.

Responsibilities:
  - Discover the Bonjour agent port at startup (reads the port advertisement file)
  - Cache the port in memory for zero-overhead lookups
  - Register this container with the Bonjour agent via POST /agent/register
  - Retry registration in the background if the agent is not yet running
  - Receive port-change push notifications via POST /widget/bonjour
  - Re-register automatically when the agent changes its port

Usage in app.py
---------------
    import wcp_bonjour

    # 1. Register the notification endpoint on your Flask app (before app.run):
    wcp_bonjour.flask_route(app)

    # 2. Kick off discovery + registration at startup.
    #    Run this in a daemon thread so it does not block app.run:
    threading.Thread(
        target=wcp_bonjour.init,
        kwargs=dict(
            name="wcp-widget-cloudflare",
            port=3742,
            companion_widget="wcp-widget-cloudflare",
            version="2.3.1",
        ),
        daemon=True,
    ).start()

This module is stdlib-only except for the optional Flask integration in flask_route().
Flask is only imported inside that function, never at module level.
"""

import json
import logging
import pathlib
import threading
import time
import urllib.request

log = logging.getLogger(__name__)

# ── Environment detection ─────────────────────────────────────────────────────
# Running inside a Docker container if /.dockerenv exists (set by Docker runtime).
_IN_DOCKER = pathlib.Path("/.dockerenv").exists()

# Port advertisement file written by the Bonjour agent on startup.
# Inside Docker: mounted read-only from ~/Library/Application Support/penrithbeacon/
# Outside Docker: native macOS path (dev mode, or the agent itself).
AGENT_PORT_FILE: pathlib.Path = (
    pathlib.Path("/host-support/bonjour-agent.port") if _IN_DOCKER
    else pathlib.Path.home() / "Library" / "Application Support"
         / "penrithbeacon" / "bonjour-agent.port"
)

# Hostname used to reach the Bonjour agent from this process.
# Docker Desktop for Mac routes host.docker.internal → host, including loopback services.
_AGENT_HOST: str = "host.docker.internal" if _IN_DOCKER else "127.0.0.1"

# ── In-memory port cache ──────────────────────────────────────────────────────
_bonjour_port: int | None = None
_port_lock = threading.Lock()

# ── Registration state (set by init()) ───────────────────────────────────────
_reg_name:      str = ""
_reg_port:      int = 0
_reg_companion: str = ""
_reg_version:   str = ""
_reg_health:    str = "/widget/health"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _read_port_file() -> int | None:
    """Read the agent port from the advertisement file. Returns None on any error."""
    try:
        return int(AGENT_PORT_FILE.read_text().strip())
    except Exception:
        return None


def _do_register(agent_port: int) -> bool:
    """
    POST /agent/register to the Bonjour agent.
    Returns True on HTTP 200, False on any error.
    """
    try:
        payload = json.dumps({
            "name":             _reg_name,
            "port":             _reg_port,
            "companion_widget": _reg_companion,
            "version":          _reg_version,
            "health":           _reg_health,
            "platform":         "docker",
        }).encode()
        req = urllib.request.Request(
            f"http://{_AGENT_HOST}:{agent_port}/agent/register",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status == 200:
                log.info(
                    f"[wcp_bonjour] Registered '{_reg_name}' (port {_reg_port}) "
                    f"with Bonjour agent on port {agent_port}"
                )
                return True
            return False
    except Exception as exc:
        log.warning(f"[wcp_bonjour] Registration failed (agent port {agent_port}): {exc}")
        return False


def _retry_loop(retry_seconds: int) -> None:
    """
    Background thread: periodically re-reads the port file and retries
    registration until it succeeds.  Exits silently on first success.
    """
    global _bonjour_port
    while True:
        time.sleep(retry_seconds)
        agent_port = _read_port_file()
        if agent_port is None:
            continue
        with _port_lock:
            _bonjour_port = agent_port
        if _do_register(agent_port):
            log.info("[wcp_bonjour] Retry registration succeeded.")
            return


# ── Public API ────────────────────────────────────────────────────────────────

def get_port() -> int | None:
    """
    Return the current Bonjour agent port.
    Checks the in-memory cache first; falls back to reading the port file.
    """
    with _port_lock:
        if _bonjour_port is not None:
            return _bonjour_port
    return _read_port_file()


def set_port(port: int) -> None:
    """
    Update the cached port and immediately re-register.
    Called internally by the /widget/bonjour notification handler.
    """
    global _bonjour_port
    with _port_lock:
        _bonjour_port = port
    log.info(f"[wcp_bonjour] Agent port changed to {port} — re-registering.")
    if _reg_name:
        _do_register(port)


def init(
    name:             str,
    port:             int,
    companion_widget: str = "",
    version:          str = "",
    health:           str = "/widget/health",
    retry_seconds:    int = 30,
) -> None:
    """
    Initialise Bonjour discovery and registration for this container.

    Call once at startup (in a daemon thread so it does not block Flask).
    Reads the port advertisement file, populates the in-memory cache, and
    registers this container with the agent.  If the agent is not yet running
    (port file absent or registration fails), retries every `retry_seconds`
    in the background until it succeeds.

    Parameters
    ----------
    name             : unique container/agent name (e.g. "wcp-widget-cloudflare")
    port             : the port this container's Flask app is listening on
    companion_widget : Docker image name of the companion widget (if any)
    version          : semver string of this container's version
    health           : health-check path (default "/widget/health")
    retry_seconds    : seconds between registration retry attempts
    """
    global _bonjour_port, _reg_name, _reg_port, _reg_companion, _reg_version, _reg_health

    _reg_name      = name
    _reg_port      = port
    _reg_companion = companion_widget
    _reg_version   = version
    _reg_health    = health

    agent_port = _read_port_file()
    if agent_port is not None:
        with _port_lock:
            _bonjour_port = agent_port
        log.info(f"[wcp_bonjour] Discovered Bonjour agent on port {agent_port}")
        if not _do_register(agent_port):
            log.warning("[wcp_bonjour] Initial registration failed — starting retry loop")
            threading.Thread(target=_retry_loop, args=(retry_seconds,), daemon=True).start()
    else:
        log.warning(
            f"[wcp_bonjour] Port file not found at {AGENT_PORT_FILE} "
            f"— Bonjour agent may not be running.  Retrying every {retry_seconds}s."
        )
        threading.Thread(target=_retry_loop, args=(retry_seconds,), daemon=True).start()


# ── Flask integration ─────────────────────────────────────────────────────────

def flask_route(app) -> None:
    """
    Register the mandatory WCP 2.2.0 notification endpoint on a Flask app.

        POST /widget/bonjour
        {"agent_port": <int>}
        → 200 {"status": "ok"}

    The Bonjour agent calls this endpoint on every registered container when
    its own port changes.  The handler updates the in-memory cache and
    re-registers with the agent on the new port.

    Call this once, after creating the Flask app object and before app.run():

        wcp_bonjour.flask_route(app)
    """
    from flask import request as _req, jsonify as _jsonify

    @app.route("/widget/bonjour", methods=["POST"])
    def _wcp_bonjour_notify():
        body     = _req.get_json(force=True, silent=True) or {}
        new_port = body.get("agent_port")
        if new_port is None:
            return _jsonify({"error": "agent_port required"}), 400
        set_port(int(new_port))
        return _jsonify({"status": "ok"})
