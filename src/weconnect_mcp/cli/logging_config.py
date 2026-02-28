"""Centralized logging configuration.

Single entry point: call ``configure_logging()`` once at startup (in the CLI).
All other modules just do ``logging.getLogger(__name__)`` — no setup of their
own.  This module also provides the uvicorn log-config dict used in HTTP mode
and a helper to re-apply third-party log levels after the carconnectivity
library resets them during initialisation.

Transport behaviour
-------------------
* **stdio**  – MCP protocol runs over stdout, so *no* log output must ever
  reach stdout.  We log to stderr (default) or to a file if ``--log-file`` is
  given.  When a log file is used we additionally silence stderr so that
  nothing leaks into the MCP stream.
* **http**   – stdout is free.  We log to stdout so that cloud platforms
  (Railway etc.) show INFO/WARNING as normal lines instead of colouring
  everything red (which they do for stderr).

Third-party library levels
--------------------------
The ``carconnectivity`` library is very verbose at DEBUG / INFO.  We always
clamp it to ``max(user_level, WARNING)`` to avoid noise, unless the user
explicitly asks for DEBUG.  The same clamping applies to ``urllib3`` and
``httpx``.

Note: ``CarConnectivity.__init__()`` internally calls ``LOG.setLevel()`` based
on its own config, potentially overriding what we set here.  For that reason
``apply_third_party_levels()`` must be called *again* after the adapter has
finished connecting (see ``_connect_vw`` in the CLI).
"""

import logging
import os
import sys
from typing import Optional

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Names of noisy third-party loggers we want to keep quiet.
_THIRD_PARTY_LOGGERS = (
    "carconnectivity",
    "carconnectivity.connectors.volkswagen-api-debug",
    "carconnectivity.connectors",
    "urllib3",
    "httpx",
)

LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def configure_logging(
    transport: str,
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
) -> None:
    """Configure the root logger for the whole application.

    Must be called **once**, as early as possible in the CLI entry-point,
    before any other module imports trigger logging calls.

    Args:
        transport: ``"stdio"`` or ``"http"``.  Controls which stream is used.
        level:     Numeric log level (e.g. ``logging.INFO``).
        log_file:  Optional path to a log file.  When given, all output goes
                   to the file.  In stdio mode stderr is additionally silenced.
    """
    fmt = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
    root = logging.getLogger()
    # Remove any handlers that third-party imports may have already installed.
    root.handlers.clear()
    root.setLevel(level)

    if log_file:
        # ── File output (works for both transports) ──────────────────────────
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(log_file, mode="a")
        fh.setFormatter(fmt)
        root.addHandler(fh)
        if transport == "stdio":
            # Silence stderr completely so nothing leaks into the MCP stream.
            sys.stderr = open(os.devnull, "w")
    elif transport == "http":
        # ── HTTP / cloud: log to stdout ───────────────────────────────────────
        # Railway (and most cloud platforms) colour stderr lines red, making
        # normal INFO output look like errors.  stdout stays neutral.
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        root.addHandler(sh)
    else:
        # ── stdio / local: log to stderr ──────────────────────────────────────
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        root.addHandler(sh)

    apply_third_party_levels(level)


def apply_third_party_levels(user_level: int = DEFAULT_LOG_LEVEL) -> None:
    """Set log levels for noisy third-party libraries.

    Clamps each third-party logger to ``max(user_level, WARNING)`` so that
    debug/info noise from those libraries is suppressed unless the user
    explicitly chose DEBUG.  Always at minimum ERROR for the carconnectivity
    api-debug logger (extremely spammy).

    This function is intentionally callable multiple times — the CLI calls it
    once during initial setup and once more *after* the VW adapter has
    connected, because ``CarConnectivity.__init__()`` resets the carconnectivity
    logger level from its config file.

    Args:
        user_level: The log level the user selected for the application.
    """
    # Minimum level for third-party libs: no noisier than WARNING.
    third_party_level = max(user_level, logging.WARNING)
    # The api-debug sub-logger spams WARNING messages about unknown capability
    # codes; clamp it further to ERROR.
    api_debug_level = max(user_level, logging.ERROR)

    for name in _THIRD_PARTY_LOGGERS:
        lvl = api_debug_level if "api-debug" in name or name == "carconnectivity.connectors" else third_party_level
        logging.getLogger(name).setLevel(lvl)


def get_logger(name: str) -> logging.Logger:
    """Return the logger for a module.

    Thin wrapper around ``logging.getLogger(name)``.  Modules should call this
    (or ``logging.getLogger(__name__)`` directly) — no handler setup here.

    Args:
        name: Logger name, typically ``__name__``.

    Returns:
        The standard Python logger for that name.
    """
    return logging.getLogger(name)


def get_uvicorn_log_config(stream: str = "ext://sys.stdout") -> dict:
    """Return a uvicorn-compatible log_config dict.

    Redirects uvicorn's own loggers to the given stream so that cloud
    platforms (Railway etc.) see access logs and startup messages as normal
    output rather than errors.

    Pass this dict as ``uvicorn_config={"log_config": ...}`` when calling
    ``server.run()``.

    Args:
        stream: Python logging stream reference, e.g. ``"ext://sys.stdout"``
                or ``"ext://sys.stderr"``.

    Returns:
        A logging dictConfig-compatible dictionary.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": False,
                "()": "uvicorn.logging.DefaultFormatter",
            },
            "access": {
                "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
                "use_colors": False,
                "()": "uvicorn.logging.AccessFormatter",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "stream": stream,
                "formatter": "default",
            },
            "access": {
                "class": "logging.StreamHandler",
                "stream": stream,
                "formatter": "access",
            },
        },
        "loggers": {
            "uvicorn":        {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error":  {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["access"],  "level": "INFO", "propagate": False},
        },
    }
