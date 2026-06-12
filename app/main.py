from fastapi import FastAPI, Response
from sqlmodel import SQLModel

from app.observability.logging import setup_logging
from app.observability.middleware import LoggingMiddleware
from app.user.routes import auth_router
from app.user.routes import users_router
from app.observability.metrics import PrometheusMiddleware, metrics_endpoint
from app.routes.routes import router as route_router
from app.impressions.routes import router as impression_router
from app.reactions.routes import router as reactions_router
from app.observability.healthchecks import router as healthchecks_router
from app.db.engine import get_engine


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Routes API")

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(route_router)
    app.include_router(impression_router)
    app.include_router(reactions_router)
    app.include_router(healthchecks_router)

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(PrometheusMiddleware)

    @app.on_event("startup")
    def on_startup():
        SQLModel.metadata.create_all(get_engine())

    @app.get("/metrics")
    def metrics():
        return Response(content=metrics_endpoint(), media_type="text/plain")

    return app


app = create_app()
