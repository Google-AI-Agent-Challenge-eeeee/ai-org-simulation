import logging
import sys

from backend.core.config.settings import get_settings
from backend.core.constants.enums import Environment

_LOGGER_INITIALIZED = False

_DEV_FORMAT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"
_PROD_FORMAT = (
    '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
)


def setup_logger() -> None:
    """Configure the root logger exactly once per process.

    Dev environments get a human-readable format; everything else uses JSON-ish lines
    suitable for Cloud Run / Cloud Logging.
    """
    global _LOGGER_INITIALIZED
    if _LOGGER_INITIALIZED:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level)

    fmt = _DEV_FORMAT if settings.env is Environment.DEVELOPMENT else _PROD_FORMAT

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    _LOGGER_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
