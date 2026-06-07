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
| Locust      | http://localhost:8089        |
| Prometheus  | http://localhost:9090        |
| Grafana     | http://localhost:3001 (admin/admin) |

## Ejecutar prueba de carga (modo headless)

```bash
mkdir -p locust/results

docker compose run --rm locust \
  locust -f locustfile.py \
  --host=http://backend:8000 \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 5m \
  --headless \
  --csv=results/before
```

Los resultados quedan en `locust/results/before_stats.csv`.

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
