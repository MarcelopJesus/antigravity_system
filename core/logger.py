import logging
import os
import re
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

# Patterns to mask in logs
_SENSITIVE_PATTERNS = [
    (re.compile(r'(key=)[A-Za-z0-9_-]{10,}'), r'\1****'),
    (re.compile(r'(password["\s:=]+)[^\s,"]+', re.IGNORECASE), r'\1****'),
    (re.compile(r'(Authorization:\s*Basic\s+)[A-Za-z0-9+/=]+', re.IGNORECASE), r'\1****'),
    (re.compile(r'(api_key["\s:=]+)[^\s,"]+', re.IGNORECASE), r'\1****'),
]


class SensitiveFilter(logging.Filter):
    """Masks API keys, passwords and tokens from log output."""

    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in _SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args:
            args = list(record.args) if isinstance(record.args, tuple) else [record.args]
            for i, arg in enumerate(args):
                if isinstance(arg, str):
                    for pattern, replacement in _SENSITIVE_PATTERNS:
                        args[i] = pattern.sub(replacement, args[i])
            record.args = tuple(args)
        return True


def setup_logger(name="fabrica_seo", log_dir="logs"):
    """
    Configures structured logging with console + file output.

    Args:
        name: Logger name
        log_dir: Directory for log files

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers on re-init
    if logger.handlers:
        return logger

    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s.%(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sensitive_filter = SensitiveFilter()

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    console.addFilter(sensitive_filter)
    logger.addHandler(console)

    # File handler with daily rotation
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"pipeline-{today}.log")

    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(sensitive_filter)
    logger.addHandler(file_handler)

    return logger


def get_logger(module_name):
    """
    Returns a child logger for a specific module.

    Usage:
        from core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Message here")
    """
    parent = logging.getLogger("fabrica_seo")
    if not parent.handlers:
        setup_logger()
    return logging.getLogger(f"fabrica_seo.{module_name}")
