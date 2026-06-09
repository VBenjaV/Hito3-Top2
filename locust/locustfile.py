"""
SkyConnect Airlines — Script de pruebas de carga (Locust)
=========================================================

Escenario Cyber Day (enunciado Hito 3):
  - 1.000 usuarios concurrentes
  - Spawn rate: 50 usuarios/seg
  - Duración: 5 minutos
  - Distribución: 70% /flights, 20% /routes, 10% /aircraft

Uso — prueba BEFORE (sin caché Redis):
  1. docker compose up -d --build
  2. docker compose stop backend && docker compose run -d --service-ports --name backend \
       -e CACHE_ENABLED=false backend
  3. docker compose run --rm locust -f locustfile.py --host=http://backend:8000 \
       --users 1000 --spawn-rate 50 --run-time 5m --headless --csv=results/before

Uso — prueba AFTER (con Redis):
  1. docker compose up -d --build   # CACHE_ENABLED=true por defecto
  2. docker compose run --rm locust -f locustfile.py --host=http://backend:8000 \
       --users 1000 --spawn-rate 50 --run-time 5m --headless --csv=results/after

Archivos generados por --csv:
  results/before_stats.csv / after_stats.csv
  results/before_failures.csv / after_failures.csv
"""

from locust import HttpUser, task, between

# Pesos alineados con el informe: 70 / 20 / 10
WEIGHT_FLIGHTS = 7
WEIGHT_ROUTES = 2
WEIGHT_AIRCRAFT = 1


class SkyConnectUser(HttpUser):
    """
    Simula un usuario buscando vuelos durante Cyber Day.
    wait_time entre 1 y 3 s simula pausa humana entre búsquedas.
    """

    wait_time = between(1, 3)

    @task(WEIGHT_FLIGHTS)
    def search_flights(self):
        with self.client.get("/flights", name="/flights", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"/flights → HTTP {response.status_code}")

    @task(WEIGHT_ROUTES)
    def get_routes(self):
        with self.client.get("/routes", name="/routes", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"/routes → HTTP {response.status_code}")

    @task(WEIGHT_AIRCRAFT)
    def get_aircraft(self):
        with self.client.get("/aircraft", name="/aircraft", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"/aircraft → HTTP {response.status_code}")
