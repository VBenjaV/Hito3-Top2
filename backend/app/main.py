import time
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from prometheus_fastapi_instrumentator import Instrumentator

from .cache import ping_redis
from .database import engine, Base
from .routers import flights, routes, aircraft

logger = logging.getLogger("skyconnect")

app = FastAPI(
    title="SkyConnect Airlines API",
    description=(
        "API de SkyConnect Airlines — Hito 3.\n\n"
        "Capa de caché **Redis** (cache-aside) en `GET /flights`, "
        "`GET /routes` y `GET /aircraft`. Métricas Prometheus en `/metrics`."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(flights.router)
app.include_router(routes.router)
app.include_router(aircraft.router)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
def startup() -> None:
    """Espera a PostgreSQL y Redis; crea tablas si no existen."""
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            if not ping_redis():
                raise RuntimeError("Redis no respondió al ping.")
            logger.info("Conexión a PostgreSQL y Redis exitosa.")
            return
        except (OperationalError, RuntimeError) as exc:
            logger.warning("Esperando servicios… intento %d/%d (%s)", attempt, retries, exc)
            time.sleep(2)
    raise RuntimeError("No se pudo conectar a PostgreSQL o Redis después de %d intentos." % retries)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "redis": ping_redis()}
