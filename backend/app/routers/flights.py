from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..cache import CACHE_KEY_FLIGHTS, TTL_FLIGHTS, get_cached_or_fetch
from ..database import get_db
from ..models import Booking, Flight
from ..schemas import FlightOut

router = APIRouter(prefix="/flights", tags=["flights"])


def _fetch_flights_from_db(db: Session) -> list[dict]:
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
        ).model_dump(mode="json")
        for flight, booked in rows
    ]


@router.get("", response_model=list[FlightOut])
def get_flights(db: Session = Depends(get_db)):
    """
    Listado de vuelos con caché Redis (TTL 60 s).

    Cache-aside: bajo alta concurrencia las lecturas repetidas se sirven desde
    Redis, reduciendo la presión sobre PostgreSQL.
    """
    return get_cached_or_fetch(
        CACHE_KEY_FLIGHTS,
        TTL_FLIGHTS,
        lambda: _fetch_flights_from_db(db),
    )
