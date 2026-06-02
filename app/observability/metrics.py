from prometheus_client import Counter, Histogram, Gauge, generate_latest
from sqlalchemy import func
from sqlmodel import select
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.db.models import User, Route, Impression
from app.db.engine import sync_session

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency",
    ["endpoint"],
)

USERS_TOTAL = Gauge("app_users_total", "Total number of users in system")

ROUTES_TOTAL = Gauge("app_routes_total", "Total number of routes in system")

IMPRESSIONS_TOTAL = Gauge(
    "app_impressions_total", "Total number of impressions in system"
)


def refresh_business_metrics() -> None:
    with sync_session() as session:
        total_users = session.exec(select(func.count()).select_from(User)).one()
        total_routes = session.exec(select(func.count()).select_from(Route)).one()
        total_impressions = session.exec(
            select(func.count()).select_from(Impression)
        ).one()

        USERS_TOTAL.set(total_users)
        ROUTES_TOTAL.set(total_routes)
        IMPRESSIONS_TOTAL.set(total_impressions)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next) -> None:
        start = time.time()

        response = await call_next(request)

        duration = time.time() - start

        endpoint = request.url.path

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

        return response


def metrics_endpoint():
    return generate_latest()
