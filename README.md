# SkyConnect Airlines — Sistema Base (Hito 3)

Sistema base para el Hito 3 del curso Ingeniería de Software.
El objetivo es analizar, medir y optimizar el rendimiento bajo alta concurrencia
implementando Redis como capa de caché, Prometheus y Grafana como observabilidad.

## Requisitos

- Docker Desktop ≥ 4.x
- Docker Compose v2

## Levantar el entorno

```bash
docker compose up --build
```

| Servicio    | URL                          |
|-------------|------------------------------|
| Frontend    | http://localhost:3000        |
| Backend API | http://localhost:8000        |
| API Docs    | http://localhost:8000/docs   |
| Redis       | localhost:6379               |
| Locust      | http://localhost:8089        |
| Prometheus  | http://localhost:9090        |
| Grafana     | http://localhost:3001 (admin/admin) |

## Redis (capa de caché)

Estrategia **cache-aside** en `GET /flights`, `GET /routes` y `GET /aircraft`.

| Endpoint      | Clave Redis                  | TTL   | Justificación                          |
|---------------|------------------------------|-------|----------------------------------------|
| GET /flights  | `skyconnect:flights:all`     | 60 s  | Asientos disponibles cambian con reservas |
| GET /routes   | `skyconnect:routes:all`      | 300 s | Catálogo estático de rutas             |
| GET /aircraft | `skyconnect:aircraft:all`    | 300 s | Catálogo estático de aeronaves         |

**Invalidación:** las claves expiran por TTL y se refrescan en el próximo cache miss.
Funciones `invalidate_*_cache()` en `backend/app/cache.py` permiten borrado explícito
(p. ej. tras confirmar una reserva futura).

**Métricas Prometheus** (expuestas en `/metrics`):

- `cache_hits_total` — respuestas servidas desde Redis
- `cache_misses_total` — consultas a PostgreSQL

Cache Hit Ratio en Grafana: `hits / (hits + misses)` — objetivo **> 70%** bajo carga.

## Ejecutar prueba de carga (modo headless)

**Linux / macOS / Git Bash:**

```bash
mkdir -p locust/results

docker compose run --rm locust \
  -f locustfile.py \
  --host=http://backend:8000 \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 5m \
  --headless \
  --csv=results/before
```

**Windows PowerShell** (todo en una línea):

```powershell
New-Item -ItemType Directory -Force -Path locust\results

docker compose run --rm locust -f locustfile.py --host=http://backend:8000 --users 1000 --spawn-rate 50 --run-time 5m --headless --csv=results/before
```

> **Nota:** la imagen `locustio/locust` ya usa `locust` como entrypoint. No repitas
> `locust` en el comando (`docker compose run --rm locust locust ...` falla con
> `Unknown User(s): locust`).

Los resultados quedan en `locust/results/before_stats.csv` (baseline) o
`locust/results/after_stats.csv` (post-Redis).

Para la prueba **después** de implementar Redis, cambia el prefijo CSV:

```powershell
docker compose run --rm locust -f locustfile.py --host=http://backend:8000 --users 1000 --spawn-rate 50 --run-time 5m --headless --csv=results/after
```

## Estructura del proyecto

```
skyconnect/
  backend/          FastAPI + SQLAlchemy
  frontend/         React + Vite + Bootstrap
  db/
    init.sql        Esquema + seed (3 aviones, 8 rutas, 200 vuelos, 500 reservas)
  locust/
    locustfile.py   Script de pruebas de carga
    results/        Resultados CSV de Locust (generado al ejecutar)
  monitoring/
    prometheus/     prometheus.yml
    grafana/        Provisioning de dashboards
  docker-compose.yml
```

## Endpoint crítico a optimizar

```
GET /flights
```

Ejecuta un JOIN sobre `flights`, `routes`, `aircraft` y `bookings` para calcular
asientos disponibles. Bajo 1.000 usuarios concurrentes es el principal cuello de
botella del sistema.

## Datos precargados

| Tabla     | Registros |
|-----------|-----------|
| aircraft  | 3         |
| routes    | 8         |
| flights   | 200       |
| bookings  | ~500      |

La ocupación de los vuelos varía según proximidad:
vuelos próximos (≤7 días) tienen entre 50–85% de asientos ocupados,
vuelos lejanos (>30 días) entre 2–12%.

---

> **Instrucciones completas** en el documento `hito3.tex` / `hito3.pdf`.
