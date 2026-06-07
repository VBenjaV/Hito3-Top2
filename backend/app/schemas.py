from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class AircraftOut(BaseModel):
    id: int
    model: str
    capacity: int
    operation_type: str

    class Config:
        from_attributes = True


class RouteOut(BaseModel):
    id: int
    origin: str
    destination: str
    duration_min: int
    is_international: bool

    class Config:
        from_attributes = True


class FlightOut(BaseModel):
    id: int
    departure_date: datetime
    arrival_date: datetime
    price: Decimal
    status: str
    available_seats: int
    route: RouteOut
    aircraft: AircraftOut

    class Config:
        from_attributes = True


class BookingOut(BaseModel):
    id: int
    flight_id: int
    passenger_name: str
    passenger_email: str
    seat_number: str
    booking_date: datetime
    status: str

    class Config:
        from_attributes = True
