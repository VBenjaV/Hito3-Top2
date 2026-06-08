from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..cache import CACHE_KEY_AIRCRAFT, TTL_AIRCRAFT, get_cached_or_fetch
from ..database import get_db
from ..models import Aircraft
from ..schemas import AircraftOut

router = APIRouter(prefix="/aircraft", tags=["aircraft"])


def _fetch_aircraft_from_db(db: Session) -> list[dict]:
    aircraft = db.query(Aircraft).order_by(Aircraft.id).all()
    return [AircraftOut.model_validate(a).model_dump(mode="json") for a in aircraft]


@router.get("", response_model=list[AircraftOut])
def get_aircraft(db: Session = Depends(get_db)):
    """Catálogo de aeronaves con caché Redis (TTL 300 s)."""
    return get_cached_or_fetch(
        CACHE_KEY_AIRCRAFT,
        TTL_AIRCRAFT,
        lambda: _fetch_aircraft_from_db(db),
    )
