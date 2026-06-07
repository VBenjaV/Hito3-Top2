import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import FlightSearch from './components/FlightSearch';
import FlightList from './components/FlightList';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export default function App() {
  const [flights,  setFlights]  = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const fetchFlights = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.get(`${API_BASE}/flights`);
      setFlights(data);
      setFiltered(data);
    } catch {
      setError('No se pudo conectar con el servidor. Verifica que el backend esté activo.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchFlights(); }, [fetchFlights]);

  function handleSearch({ origin, destination }) {
    const result = flights.filter(f => {
      const matchOrigin = !origin      || f.route.origin      === origin;
      const matchDest   = !destination || f.route.destination === destination;
      return matchOrigin && matchDest;
    });
    setFiltered(result);
  }

  return (
    <div className="container py-4">
      <header className="mb-4">
        <h1 className="h3 fw-bold">
          ✈&nbsp;<span translate="no">SkyConnect Airlines</span>
        </h1>
        <p className="text-muted mb-0">
          Busca y compara vuelos disponibles
        </p>
      </header>

      <main>
        <FlightSearch onSearch={handleSearch} />

        <div className="d-flex justify-content-between align-items-center mb-2">
          <span className="text-muted small">
            {filtered.length} vuelo{filtered.length !== 1 ? 's' : ''} encontrado{filtered.length !== 1 ? 's' : ''}
          </span>
          <button
            type="button"
            className="btn btn-sm btn-outline-secondary"
            onClick={fetchFlights}
            disabled={loading}
            aria-label="Actualizar listado de vuelos"
          >
            {loading ? 'Actualizando…' : 'Actualizar'}
          </button>
        </div>

        <FlightList flights={filtered} loading={loading} error={error} />
      </main>
    </div>
  );
}
