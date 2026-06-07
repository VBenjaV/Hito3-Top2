-- ============================================================
--  SkyConnect Airlines — Esquema y Datos Iniciales
--  Sistema base para Hito 3 (Optimización con Redis)
-- ============================================================

-- --------------------------------------------------------
-- TABLAS
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS aircraft (
    id              SERIAL PRIMARY KEY,
    model           VARCHAR(100)  NOT NULL,
    capacity        INTEGER       NOT NULL CHECK (capacity > 0),
    -- 'nacional' | 'internacional' | 'nacional e internacional'
    operation_type  VARCHAR(30)   NOT NULL
);

CREATE TABLE IF NOT EXISTS routes (
    id               SERIAL PRIMARY KEY,
    origin           VARCHAR(100) NOT NULL,
    destination      VARCHAR(100) NOT NULL,
    duration_min     INTEGER      NOT NULL,
    is_international BOOLEAN      NOT NULL DEFAULT FALSE,
    UNIQUE (origin, destination)
);

CREATE TABLE IF NOT EXISTS flights (
    id             SERIAL PRIMARY KEY,
    route_id       INTEGER        NOT NULL REFERENCES routes(id),
    aircraft_id    INTEGER        NOT NULL REFERENCES aircraft(id),
    departure_date TIMESTAMPTZ    NOT NULL,
    arrival_date   TIMESTAMPTZ    NOT NULL,
    price          NUMERIC(10, 2) NOT NULL CHECK (price > 0),
    -- 'scheduled' | 'boarding' | 'departed' | 'cancelled'
    status         VARCHAR(20)    NOT NULL DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS bookings (
    id               SERIAL PRIMARY KEY,
    flight_id        INTEGER      NOT NULL REFERENCES flights(id),
    passenger_name   VARCHAR(120) NOT NULL,
    passenger_email  VARCHAR(120) NOT NULL,
    seat_number      VARCHAR(6)   NOT NULL,
    booking_date     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    -- 'confirmed' | 'cancelled' | 'pending'
    status           VARCHAR(20)  NOT NULL DEFAULT 'confirmed'
);

-- Índices básicos del sistema base.
-- El alumno deberá identificar índices adicionales que mejoren el rendimiento.
CREATE INDEX idx_flights_route    ON flights(route_id);
CREATE INDEX idx_flights_aircraft ON flights(aircraft_id);
CREATE INDEX idx_bookings_flight  ON bookings(flight_id);

-- --------------------------------------------------------
-- AERONAVES (3 modelos)
-- --------------------------------------------------------
INSERT INTO aircraft (model, capacity, operation_type) VALUES
    ('Airbus A320',           180, 'nacional'),
    ('Boeing 737-800',        189, 'nacional e internacional'),
    ('Boeing 787 Dreamliner', 296, 'internacional');

-- --------------------------------------------------------
-- RUTAS (4 nacionales + 4 internacionales)
-- --------------------------------------------------------
INSERT INTO routes (origin, destination, duration_min, is_international) VALUES
    ('Santiago', 'Antofagasta',   90,  FALSE),
    ('Santiago', 'Concepción',    60,  FALSE),
    ('Santiago', 'Puerto Montt',  95,  FALSE),
    ('Santiago', 'Punta Arenas', 210,  FALSE),
    ('Santiago', 'Buenos Aires', 195,  TRUE),
    ('Santiago', 'Lima',         240,  TRUE),
    ('Santiago', 'São Paulo',    270,  TRUE),
    ('Santiago', 'Miami',        600,  TRUE);

-- --------------------------------------------------------
-- VUELOS (200 en total — 25 por ruta)
--
-- Fechas : próximos ~90 días desde el momento del seed
-- Horarios: 07:00 | 12:00 | 16:00 | 20:00 (rotando)
-- Aeronaves:
--   Nacionales    → A320 (id=1) o B737-800 (id=2)
--   Internacionales → B737-800 (id=2) o B787 (id=3)
-- Precios base (CLP) con variación ±15 %:
--   Antofagasta $65k | Concepción $55k | Pto. Montt $70k | Pta. Arenas $110k
--   Bs. Aires $320k  | Lima $380k      | São Paulo $450k  | Miami $720k
-- --------------------------------------------------------
DO $$
DECLARE
    v_route        RECORD;
    v_aircraft_id  INTEGER;
    v_base_ts      TIMESTAMP;
    v_departure    TIMESTAMPTZ;
    v_arrival      TIMESTAMPTZ;
    v_price        NUMERIC(10, 2);
    v_day_offset   INTEGER;
    v_hour         INTEGER;
    v_i            INTEGER;
    price_bases    NUMERIC[] := ARRAY[
         65000,   -- ruta id=1  Santiago→Antofagasta
         55000,   -- ruta id=2  Santiago→Concepción
         70000,   -- ruta id=3  Santiago→Puerto Montt
        110000,   -- ruta id=4  Santiago→Punta Arenas
        320000,   -- ruta id=5  Santiago→Buenos Aires
        380000,   -- ruta id=6  Santiago→Lima
        450000,   -- ruta id=7  Santiago→São Paulo
        720000    -- ruta id=8  Santiago→Miami
    ];
BEGIN
    -- Fecha base: medianoche del día actual (sin componente de hora)
    v_base_ts := DATE_TRUNC('day', NOW()::TIMESTAMP);

    FOR v_route IN SELECT * FROM routes ORDER BY id LOOP

        -- Seleccionar aeronave según tipo de ruta
        IF v_route.is_international THEN
            v_aircraft_id := CASE WHEN v_route.id % 2 = 0 THEN 3 ELSE 2 END;
        ELSE
            v_aircraft_id := CASE WHEN v_route.id % 2 = 0 THEN 2 ELSE 1 END;
        END IF;

        FOR v_i IN 0..24 LOOP
            -- Distribuir 25 vuelos en ~90 días (cada 3-4 días)
            v_day_offset := (v_i * 3) + (v_route.id - 1);

            -- Horarios rotativos: 07:00 | 12:00 | 16:00 | 20:00
            v_hour := CASE (v_i % 4)
                WHEN 0 THEN 7
                WHEN 1 THEN 12
                WHEN 2 THEN 16
                ELSE        20
            END;

            -- Construir timestamp sumando intervalos (evita literals de zona horaria)
            v_departure := (
                v_base_ts
                + (v_day_offset || ' days')::INTERVAL
                + (v_hour       || ' hours')::INTERVAL
            )::TIMESTAMPTZ;

            v_arrival := v_departure + (v_route.duration_min || ' minutes')::INTERVAL;

            -- Precio con variación ±15 %, redondeado a miles de pesos
            v_price := ROUND(
                (price_bases[v_route.id] * (0.85 + random() * 0.30)) / 1000.0
            ) * 1000;

            INSERT INTO flights (route_id, aircraft_id, departure_date, arrival_date, price, status)
            VALUES (
                v_route.id,
                v_aircraft_id,
                v_departure,
                v_arrival,
                v_price,
                CASE WHEN v_day_offset = 0 THEN 'boarding' ELSE 'scheduled' END
            );
        END LOOP;
    END LOOP;
END $$;

-- --------------------------------------------------------
-- RESERVAS (~500 en total)
--
-- Ocupación realista según proximidad del vuelo:
--   ≤ 7 días  → 50–85 % lleno
--   ≤15 días  → 30–60 % lleno
--   ≤30 días  → 10–30 % lleno
--   > 30 días →  2–12 % lleno
--
-- 50 pasajeros ficticios rotan entre los vuelos.
-- --------------------------------------------------------
DO $$
DECLARE
    names  TEXT[] := ARRAY[
        'Ana García',        'Luis Martínez',    'Sofía López',      'Carlos Rodríguez',  'Valentina Torres',
        'Matías Flores',     'Camila Díaz',       'Sebastián Muñoz',  'Isabella Reyes',    'Nicolás Herrera',
        'Javiera Morales',   'Felipe Jiménez',    'Constanza Ruiz',   'Andrés Castro',     'Daniela Vega',
        'Diego Romero',      'Catalina Vargas',   'Tomás Aguirre',    'Natalia Rojas',     'Rodrigo Fuentes',
        'Francisca Molina',  'Ignacio Medina',    'Alejandra Soto',   'Maximiliano Arce',  'Fernanda Ríos',
        'Pablo Salinas',     'Antonia Bravo',     'Joaquín Pinto',    'Renata Espinoza',   'Emilio Cortés',
        'Lucía Sandoval',    'Gabriel Contreras', 'Martina Ibáñez',   'Cristóbal Tapia',   'Victoria Peña',
        'Ricardo Lara',      'Alicia Zamora',     'Benjamín Paredes', 'Ximena Quezada',    'Esteban Navarro',
        'Paola Gutiérrez',   'Patricio Vera',     'Simone Campos',    'Eduardo Sepúlveda', 'Loreto Cifuentes',
        'Claudio Riquelme',  'Andrea Moya',       'Hernán Acosta',    'Pamela Núñez',      'Sergio Cárdenas'
    ];
    emails TEXT[] := ARRAY[
        'ana.garcia@mail.cl',        'luis.martinez@mail.cl',    'sofia.lopez@mail.cl',      'carlos.rodriguez@mail.cl',  'valentina.torres@mail.cl',
        'matias.flores@mail.cl',     'camila.diaz@mail.cl',      'sebastian.munoz@mail.cl',  'isabella.reyes@mail.cl',    'nicolas.herrera@mail.cl',
        'javiera.morales@mail.cl',   'felipe.jimenez@mail.cl',   'constanza.ruiz@mail.cl',   'andres.castro@mail.cl',     'daniela.vega@mail.cl',
        'diego.romero@mail.cl',      'catalina.vargas@mail.cl',  'tomas.aguirre@mail.cl',    'natalia.rojas@mail.cl',     'rodrigo.fuentes@mail.cl',
        'francisca.molina@mail.cl',  'ignacio.medina@mail.cl',   'alejandra.soto@mail.cl',   'maximo.arce@mail.cl',       'fernanda.rios@mail.cl',
        'pablo.salinas@mail.cl',     'antonia.bravo@mail.cl',    'joaquin.pinto@mail.cl',    'renata.espinoza@mail.cl',   'emilio.cortes@mail.cl',
        'lucia.sandoval@mail.cl',    'gabriel.contreras@mail.cl','martina.ibanez@mail.cl',   'cristobal.tapia@mail.cl',   'victoria.pena@mail.cl',
        'ricardo.lara@mail.cl',      'alicia.zamora@mail.cl',    'benjamin.paredes@mail.cl', 'ximena.quezada@mail.cl',    'esteban.navarro@mail.cl',
        'paola.gutierrez@mail.cl',   'patricio.vera@mail.cl',    'simone.campos@mail.cl',    'eduardo.sepulveda@mail.cl', 'loreto.cifuentes@mail.cl',
        'claudio.riquelme@mail.cl',  'andrea.moya@mail.cl',      'hernan.acosta@mail.cl',    'pamela.nunez@mail.cl',      'sergio.cardenas@mail.cl'
    ];

    v_flight       RECORD;
    v_n_bookings   INTEGER;
    v_booked       INTEGER;
    v_total        INTEGER := 0;
    v_retries      INTEGER;
    v_passenger    INTEGER;
    v_seat_row     INTEGER;
    v_seat_col     TEXT;
    v_seat         TEXT;
    v_days_ahead   DOUBLE PRECISION;
BEGIN
    FOR v_flight IN
        SELECT f.id AS flight_id,
               a.capacity,
               f.departure_date
        FROM flights f
        JOIN aircraft a ON a.id = f.aircraft_id
        ORDER BY f.id
    LOOP
        -- Días hasta el vuelo (puede ser negativo si ya pasó)
        v_days_ahead := EXTRACT(EPOCH FROM (v_flight.departure_date - NOW())) / 86400.0;

        IF    v_days_ahead <= 7  THEN v_n_bookings := FLOOR(v_flight.capacity * (0.50 + random() * 0.35));
        ELSIF v_days_ahead <= 15 THEN v_n_bookings := FLOOR(v_flight.capacity * (0.30 + random() * 0.30));
        ELSIF v_days_ahead <= 30 THEN v_n_bookings := FLOOR(v_flight.capacity * (0.10 + random() * 0.20));
        ELSE                          v_n_bookings := FLOOR(v_flight.capacity * (0.02 + random() * 0.10));
        END IF;

        -- No superar el límite total de 500 reservas
        IF v_total + v_n_bookings > 500 THEN
            v_n_bookings := 500 - v_total;
        END IF;
        EXIT WHEN v_n_bookings <= 0;

        v_booked  := 0;
        v_retries := 0;

        WHILE v_booked < v_n_bookings AND v_retries < v_n_bookings * 5 LOOP
            v_seat_row := 1 + FLOOR(random() * 40)::INTEGER;
            v_seat_col := chr(65 + FLOOR(random() * 6)::INTEGER);  -- A–F
            v_seat     := v_seat_row::TEXT || v_seat_col;
            v_passenger := 1 + ((v_total + v_booked) % 50);

            BEGIN
                INSERT INTO bookings
                    (flight_id, passenger_name, passenger_email, seat_number, booking_date, status)
                VALUES (
                    v_flight.flight_id,
                    names[v_passenger],
                    emails[v_passenger],
                    v_seat,
                    NOW() - (FLOOR(random() * 30)::TEXT || ' days')::INTERVAL,
                    CASE WHEN random() < 0.04 THEN 'cancelled' ELSE 'confirmed' END
                );
                v_booked := v_booked + 1;
            EXCEPTION WHEN OTHERS THEN
                -- Asiento duplicado → incrementar retries y volver a intentar
                NULL;
            END;

            v_retries := v_retries + 1;
        END LOOP;

        v_total := v_total + v_booked;
        EXIT WHEN v_total >= 500;
    END LOOP;

    RAISE NOTICE '==========================================';
    RAISE NOTICE 'SkyConnect Airlines — Seed completado';
    RAISE NOTICE '  Aeronaves : %', (SELECT COUNT(*) FROM aircraft);
    RAISE NOTICE '  Rutas     : %', (SELECT COUNT(*) FROM routes);
    RAISE NOTICE '  Vuelos    : %', (SELECT COUNT(*) FROM flights);
    RAISE NOTICE '  Reservas  : %', v_total;
    RAISE NOTICE '==========================================';
END $$;
