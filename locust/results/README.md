# Resultados de pruebas Locust

Exportar con `--csv=results/before` (AS-IS, sin caché) y `--csv=results/after` (To-Be, con Redis).

## Parámetros del escenario (informe)

| Parámetro | Valor |
|-----------|-------|
| Usuarios concurrentes | 1.000 |
| Spawn rate | 50 usuarios/seg |
| Duración | 5 minutos |
| Host | http://backend:8000 |
| Distribución | 70% GET /flights, 20% GET /routes, 10% GET /aircraft |

## Métricas recolectadas (08/06/2026)

### AS-IS — `before` (`CACHE_ENABLED=false`)

| Métrica | Valor |
|---------|-------|
| GET /flights | 1.060 req · 478 fallos (45 %) |
| GET /routes | 297 req · 126 fallos (42 %) |
| GET /aircraft | 163 req · 76 fallos (47 %) |
| Latencia promedio | 2,61 s |
| Latencia P95 | ~262 s (/flights, /routes); ~261 s (/aircraft) |
| RPS | 5,4 req/s |
| CPU backend | 47 % |
| Memoria backend | 128 MiB |
| Cache Hit Ratio | N/A |
| Errores | HTTP 500 (saturación PostgreSQL) |

### To-Be — `after` (`CACHE_ENABLED=true`, Redis activo)

| Métrica | Valor |
|---------|-------|
| GET /flights | 31.565 req · 44 fallos (0,14 %) |
| GET /routes | 9.028 req · 12 fallos (0,13 %) |
| GET /aircraft | 4.520 req · 4 fallos (0,09 %) |
| Latencia promedio | ~179 ms |
| Latencia P95 | 7,5 s |
| RPS | 150,8 req/s |
| CPU backend | 100 % |
| Memoria backend | 193 MiB |
| Cache Hit Ratio | 99,8 % |

## Archivos esperados

- `before_stats.csv`, `before_failures.csv`, `before_stats_history.csv`
- `after_stats.csv`, `after_failures.csv`, `after_stats_history.csv`
