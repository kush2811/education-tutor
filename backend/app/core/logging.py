"""Structured logging configuration for backend services with sensitive data masking."""

import logging
import re
import sys
from app.core.config import settings


class SensitiveDataFilter(logging.Filter):
    """Masks API keys, JWT bearer tokens, and credentials from log outputs."""

    # Patterns for sensitive credentials
    PATTERNS = [
        (re.compile(r'AIza[0-9A-Za-z-_]{35}'), 'AIza***[REDACTED_API_KEY]'),
        (re.compile(r'sk-[0-9A-Za-z-_]{20,}'), 'sk-***[REDACTED_API_KEY]'),
        (re.compile(r'Bearer\s+[A-Za-z0-9\-_\.]+', re.IGNORECASE), 'Bearer [REDACTED_TOKEN]'),
        (re.compile(r'(password|secret|key)["\']?\s*[:=]\s*["\']?[^"\',\s]+', re.IGNORECASE), r'\1=[REDACTED]'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            masked = record.msg
            for pattern, replacement in self.PATTERNS:
                masked = pattern.sub(replacement, masked)
            record.msg = masked
        return True


def setup_logging() -> logging.Logger:
    """Configure and return root application logger with sensitive data protection."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(logging.Formatter(log_format))

    logger = logging.getLogger("ai_tutor")
    logger.setLevel(log_level)
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.addHandler(handler)

    # Optional Production File Logging with Rotation
    if settings.ENABLE_FILE_LOGGING and settings.LOG_FILE_PATH:
        try:
            import os
            from logging.handlers import RotatingFileHandler
            log_dir = os.path.dirname(settings.LOG_FILE_PATH)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                settings.LOG_FILE_PATH,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.addFilter(SensitiveDataFilter())
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to initialize rotating file logger: {e}\n")

    logger.propagate = False

    return logger


logger = setup_logging()
