import { useState } from 'react';

export default function FlightSearch({ onSearch }) {
  const [origin, setOrigin]      = useState('');
  const [destination, setDest]   = useState('');

  const cities = [
    'Santiago', 'Antofagasta', 'Concepción', 'Puerto Montt', 'Punta Arenas',
    'Buenos Aires', 'Lima', 'São Paulo', 'Miami',
  ];

  function handleSubmit(e) {
    e.preventDefault();
    onSearch({ origin, destination });
  }

  return (
    <form className="row g-2 mb-4" onSubmit={handleSubmit}>
      <div className="col-md-4">
        <label htmlFor="origin" className="form-label">Origen</label>
        <select
          id="origin"
          className="form-select"
          value={origin}
          onChange={e => setOrigin(e.target.value)}
          autoComplete="off"
        >
          <option value="">Todos</option>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="col-md-4">
        <label htmlFor="destination" className="form-label">Destino</label>
        <select
          id="destination"
          className="form-select"
          value={destination}
          onChange={e => setDest(e.target.value)}
          autoComplete="off"
        >
          <option value="">Todos</option>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="col-md-4 d-flex align-items-end">
        <button type="submit" className="btn btn-primary w-100">
          Buscar vuelos
        </button>
      </div>
    </form>
  );
}
