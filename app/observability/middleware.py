import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.logging import (
    request_id_var,
    session_id_var,
)

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()

        request_id = str(uuid.uuid4())

        session_id = request.cookies.get(
            "session_id", "00000000-0000-0000-0000-000000000000"
        )

        request_id_var.set(request_id)
        session_id_var.set(session_id)

        try:
            response = await call_next(request)

            logger.info(
                f"{request.method} {request.url.path}",
                extra={
                    "status_code": response.status_code,
                    "duration": time.time() - start,
                },
            )

            return response

        except Exception as e:
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={"error": str(e)},
            )
            raise
