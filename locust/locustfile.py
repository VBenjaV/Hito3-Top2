"""
SkyConnect Airlines — Script de pruebas de carga (Locust)
=========================================================

Uso:
  # Modo web (interfaz en http://localhost:8089)
  locust -f locustfile.py --host=http://backend:8000

  # Modo headless — guardar resultados en CSV
  locust -f locustfile.py \
    --host=http://backend:8000 \
    --users 1000 \
    --spawn-rate 50 \
    --run-time 5m \
    --headless \
    --csv=results/before

Archivos generados por --csv:
  results/before_stats.csv          — estadísticas por endpoint
  results/before_stats_history.csv  — historial en el tiempo
  results/before_failures.csv       — errores registrados
"""

from locust import HttpUser, task, between


class SkyConnectUser(HttpUser):
    """
    Simula el comportamiento de un usuario buscando vuelos en Cyber Day.

    Distribución de tareas:
      - GET /flights  → 70% de las peticiones (endpoint crítico)
      - GET /routes   → 20% de las peticiones
      - GET /aircraft → 10% de las peticiones
    """
    wait_time = between(1, 3)   # pausa entre requests (segundos)

    @task(7)
    def search_flights(self):
        """Consulta el listado completo de vuelos — endpoint más costoso."""
        with self.client.get("/flights", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(2)
    def get_routes(self):
        """Consulta el catálogo de rutas disponibles."""
        self.client.get("/routes")

    @task(1)
    def get_aircraft(self):
        """Consulta el catálogo de aeronaves."""
        self.client.get("/aircraft")
