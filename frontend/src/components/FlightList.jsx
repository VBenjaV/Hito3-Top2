const STATUS_LABELS = {
  scheduled: { label: 'Programado', badge: 'bg-secondary' },
  boarding:  { label: 'Abordando',  badge: 'bg-success'   },
  departed:  { label: 'Despegado',  badge: 'bg-primary'   },
  cancelled: { label: 'Cancelado',  badge: 'bg-danger'    },
};

function formatDate(iso) {
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'America/Santiago',
  }).format(new Date(iso));
}

function formatPrice(price) {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    maximumFractionDigits: 0,
  }).format(price);
}

export default function FlightList({ flights, loading, error }) {
  if (loading) {
    return (
      <p className="text-center text-muted" aria-live="polite">
        Cargando vuelos…
      </p>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert" aria-live="polite">
        {error}
      </div>
    );
  }

  if (flights.length === 0) {
    return (
      <p className="text-center text-muted">
        No hay vuelos disponibles para los criterios seleccionados.
      </p>
    );
  }

  return (
    <div className="table-responsive">
      <table className="table table-hover align-middle">
        <thead className="table-dark">
          <tr>
            <th scope="col">Origen</th>
            <th scope="col">Destino</th>
            <th scope="col">Salida</th>
            <th scope="col">Llegada</th>
            <th scope="col">Aeronave</th>
            <th scope="col" style={{ fontVariantNumeric: 'tabular-nums' }}>Asientos disp.</th>
            <th scope="col" style={{ fontVariantNumeric: 'tabular-nums' }}>Precio</th>
            <th scope="col">Estado</th>
          </tr>
        </thead>
        <tbody>
          {flights.map(f => {
            const st = STATUS_LABELS[f.status] ?? { label: f.status, badge: 'bg-secondary' };
            return (
              <tr key={f.id}>
                <td>{f.route.origin}</td>
                <td>{f.route.destination}</td>
                <td style={{ fontVariantNumeric: 'tabular-nums' }}>{formatDate(f.departure_date)}</td>
                <td style={{ fontVariantNumeric: 'tabular-nums' }}>{formatDate(f.arrival_date)}</td>
                <td>{f.aircraft.model}</td>
                <td style={{ fontVariantNumeric: 'tabular-nums' }}>{f.available_seats}</td>
                <td style={{ fontVariantNumeric: 'tabular-nums' }}>{formatPrice(f.price)}</td>
                <td>
                  <span className={`badge ${st.badge}`}>{st.label}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
