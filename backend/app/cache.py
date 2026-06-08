"""
Capa de caché Redis (estrategia cache-aside) para SkyConnect Hito 3.

Invalidación:
  - TTL: cada clave expira automáticamente y se refresca en el próximo miss.
  - /flights (60 s): asientos disponibles cambian con reservas; TTL corto
    equilibra frescura y rendimiento.
  - /routes y /aircraft (300 s): catálogos estáticos; TTL largo reduce carga
    en PostgreSQL sin impacto relevante en consistencia.
  - Invalidación explícita: invalidate_flights_cache() borra la clave de vuelos;
    útil si se añade un endpoint POST de reservas (no presente en el hito).
"""

import json
import logging
import os
from collections.abc import Callable
from typing import Any

import redis
from prometheus_client import Counter

logger = logging.getLogger("skyconnect")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Claves Redis
CACHE_KEY_FLIGHTS = "skyconnect:flights:all"
CACHE_KEY_ROUTES = "skyconnect:routes:all"
CACHE_KEY_AIRCRAFT = "skyconnect:aircraft:all"

# TTL en segundos
TTL_FLIGHTS = int(os.getenv("CACHE_TTL_FLIGHTS", "60"))
TTL_ROUTES = int(os.getenv("CACHE_TTL_ROUTES", "300"))
TTL_AIRCRAFT = int(os.getenv("CACHE_TTL_AIRCRAFT", "300"))

cache_hits_total = Counter(
    "cache_hits_total",
    "Total de respuestas servidas desde Redis",
)
cache_misses_total = Counter(
    "cache_misses_total",
    "Total de respuestas obtenidas desde PostgreSQL (cache miss)",
)

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def ping_redis() -> bool:
    return bool(get_redis().ping())


def get_cached_or_fetch(key: str, ttl: int, fetch_fn: Callable[[], Any]) -> Any:
    """Cache-aside: hit → JSON desde Redis; miss → PostgreSQL → setex."""
    client = get_redis()
    cached = client.get(key)
    if cached is not None:
        cache_hits_total.inc()
        return json.loads(cached)

    cache_misses_total.inc()
    data = fetch_fn()
    client.setex(key, ttl, json.dumps(data))
    return data


def invalidate_flights_cache() -> None:
    """Invalidación explícita tras una reserva confirmada (extensión futura)."""
    get_redis().delete(CACHE_KEY_FLIGHTS)


def invalidate_routes_cache() -> None:
    get_redis().delete(CACHE_KEY_ROUTES)


def invalidate_aircraft_cache() -> None:
    get_redis().delete(CACHE_KEY_AIRCRAFT)
