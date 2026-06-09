import time
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from prometheus_fastapi_instrumentator import Instrumentator

from .cache import is_cache_enabled, ping_redis
from .database import engine, Base
from .routers import flights, routes, aircraft

logger = logging.getLogger("skyconnect")

app = FastAPI(
    title="SkyConnect Airlines API",
    description=(
        "API de SkyConnect Airlines — Hito 3.\n\n"
        "Capa de caché **Redis** (cache-aside) en `GET /flights`, "
        "`GET /routes` y `GET /aircraft`. Métricas Prometheus en `/metrics`.\n\n"
        "Variable `CACHE_ENABLED=false` desactiva la caché para pruebas baseline (before)."
    ),
    version="2.1.0",
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


@app.exception_handler(OperationalError)
async def database_unavailable_handler(_request: Request, exc: OperationalError):
    """Evita HTTP 500 genéricos cuando PostgreSQL está saturado o no responde."""
    logger.error("Error de base de datos bajo carga: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Base de datos temporalmente no disponible. Reintentar."},
    )


@app.on_event("startup")
def startup() -> None:
    """Espera a PostgreSQL (y Redis si caché activa); crea tablas si no existen."""
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            if is_cache_enabled() and not ping_redis():
                raise RuntimeError("Redis no respondió al ping.")
            logger.info(
                "Servicios listos. cache_enabled=%s",
                is_cache_enabled(),
            )
            return
        except (OperationalError, RuntimeError) as exc:
            logger.warning("Esperando servicios… intento %d/%d (%s)", attempt, retries, exc)
            time.sleep(2)
    raise RuntimeError("No se pudo conectar a PostgreSQL o Redis después de %d intentos." % retries)


@app.get("/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "cache_enabled": is_cache_enabled(),
        "redis": ping_redis() if is_cache_enabled() else None,
    }
