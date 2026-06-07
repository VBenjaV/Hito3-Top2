from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base


class Aircraft(Base):
    __tablename__ = "aircraft"

    id             = Column(Integer, primary_key=True, index=True)
    model          = Column(String(100), nullable=False)
    capacity       = Column(Integer, nullable=False)
    operation_type = Column(String(30), nullable=False)

    flights = relationship("Flight", back_populates="aircraft")


class Route(Base):
    __tablename__ = "routes"

    id               = Column(Integer, primary_key=True, index=True)
    origin           = Column(String(100), nullable=False)
    destination      = Column(String(100), nullable=False)
    duration_min     = Column(Integer, nullable=False)
    is_international = Column(Boolean, nullable=False, default=False)

    flights = relationship("Flight", back_populates="route")


class Flight(Base):
    __tablename__ = "flights"

    id             = Column(Integer, primary_key=True, index=True)
    route_id       = Column(Integer, ForeignKey("routes.id"), nullable=False)
    aircraft_id    = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    departure_date = Column(DateTime(timezone=True), nullable=False)
    arrival_date   = Column(DateTime(timezone=True), nullable=False)
    price          = Column(Numeric(10, 2), nullable=False)
    status         = Column(String(20), nullable=False, default="scheduled")

    route    = relationship("Route", back_populates="flights")
    aircraft = relationship("Aircraft", back_populates="flights")
    bookings = relationship("Booking", back_populates="flight")


class Booking(Base):
    __tablename__ = "bookings"

    id               = Column(Integer, primary_key=True, index=True)
    flight_id        = Column(Integer, ForeignKey("flights.id"), nullable=False)
    passenger_name   = Column(String(120), nullable=False)
    passenger_email  = Column(String(120), nullable=False)
    seat_number      = Column(String(6), nullable=False)
    booking_date     = Column(DateTime(timezone=True), nullable=False)
    status           = Column(String(20), nullable=False, default="confirmed")

    flight = relationship("Flight", back_populates="bookings")
