import json
import logging
from datetime import datetime, timezone
from contextvars import ContextVar

request_id_var = ContextVar("request_id", default=None)
session_id_var = ContextVar("session_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        log_record = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
            "session_id": session_id_var.get(),
            "extra": getattr(record, "extra", None),
            "traceback": self.formatException(record.exc_info)
            if record.exc_info
            else None,
        }

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
