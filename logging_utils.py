from __future__ import annotations

import logging
import uuid
from pathlib import Path


DEFAULT_LOG_FILE_NAME = "multi_agent_assistant.log"


class _DefaultContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        if not hasattr(record, "domain"):
            record.domain = "system"
        return True


class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = dict(self.extra)
        supplied_extra = kwargs.get("extra")
        if supplied_extra:
            extra.update(supplied_extra)
        kwargs["extra"] = extra
        return msg, kwargs


def build_request_id(prefix: str = "req") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def configure_logging(log_dir: Path, debug: bool = False, request_id: str | None = None) -> str:
    log_dir.mkdir(parents=True, exist_ok=True)

    resolved_request_id = request_id or build_request_id()
    log_file = log_dir / DEFAULT_LOG_FILE_NAME

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | domain=%(domain)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    context_filter = _DefaultContextFilter()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.captureWarnings(True)
    return resolved_request_id


def get_logger(name: str, request_id: str, domain: str = "system") -> RequestLoggerAdapter:
    return RequestLoggerAdapter(logging.getLogger(name), {"request_id": request_id, "domain": domain})
