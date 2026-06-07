import time
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .database import engine, Base
from .routers import flights, routes, aircraft

logger = logging.getLogger("skyconnect")

app = FastAPI(
    title="SkyConnect Airlines API",
    description=(
        "Sistema base para Hito 3 — Optimización con Redis.\n\n"
        "**NOTA PARA EL ALUMNO:** este es el sistema base sin caché. "
        "El endpoint `GET /flights` es el cuello de botella a optimizar."
    ),
    version="1.0.0",
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


@app.on_event("startup")
def startup() -> None:
    """
    Espera a que PostgreSQL esté listo y crea las tablas si aún no existen.
    El init.sql ya las crea con datos; este create_all es un fallback para
    entornos locales sin Docker.
    """
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            logger.info("Conexión a PostgreSQL exitosa.")
            return
        except OperationalError:
            logger.warning("Esperando a PostgreSQL… intento %d/%d", attempt, retries)
            time.sleep(2)
    raise RuntimeError("No se pudo conectar a PostgreSQL después de %d intentos." % retries)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
