from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Route
from ..schemas import RouteOut

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
def get_routes(db: Session = Depends(get_db)):
    return db.query(Route).order_by(Route.id).all()
