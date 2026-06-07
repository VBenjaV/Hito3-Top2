from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Aircraft, Booking, Flight
from ..schemas import FlightOut

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("", response_model=list[FlightOut])
def get_flights(db: Session = Depends(get_db)):
    """
    Endpoint crítico del sistema base.

    Realiza un JOIN entre flights, routes, aircraft y una subconsulta sobre
    bookings para calcular asientos disponibles. Bajo alta concurrencia esta
    consulta se convierte en el principal cuello de botella del sistema.

    NOTA PARA EL ALUMNO: este endpoint NO usa caché. Mide la latencia en su
    estado actual con Locust y luego implementa Redis para reducirla.
    """
    # Subconsulta: reservas confirmadas por vuelo
    booked_subq = (
        select(
            Booking.flight_id,
            func.count(Booking.id).label("booked_count"),
        )
        .where(Booking.status == "confirmed")
        .group_by(Booking.flight_id)
        .subquery()
    )

    rows = (
        db.query(Flight, func.coalesce(booked_subq.c.booked_count, 0).label("booked"))
        .options(joinedload(Flight.route), joinedload(Flight.aircraft))
        .outerjoin(booked_subq, Flight.id == booked_subq.c.flight_id)
        .filter(Flight.status != "cancelled")
        .order_by(Flight.departure_date)
        .all()
    )

    return [
        FlightOut(
            id=flight.id,
            departure_date=flight.departure_date,
            arrival_date=flight.arrival_date,
            price=flight.price,
            status=flight.status,
            available_seats=max(flight.aircraft.capacity - int(booked), 0),
            route=flight.route,
            aircraft=flight.aircraft,
        )
        for flight, booked in rows
    ]
