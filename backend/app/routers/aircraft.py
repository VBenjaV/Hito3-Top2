from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Aircraft
from ..schemas import AircraftOut

router = APIRouter(prefix="/aircraft", tags=["aircraft"])


@router.get("", response_model=list[AircraftOut])
def get_aircraft(db: Session = Depends(get_db)):
    return db.query(Aircraft).order_by(Aircraft.id).all()
