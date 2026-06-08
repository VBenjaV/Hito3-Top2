from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..cache import CACHE_KEY_ROUTES, TTL_ROUTES, get_cached_or_fetch
from ..database import get_db
from ..models import Route
from ..schemas import RouteOut

router = APIRouter(prefix="/routes", tags=["routes"])


def _fetch_routes_from_db(db: Session) -> list[dict]:
    routes = db.query(Route).order_by(Route.id).all()
    return [RouteOut.model_validate(r).model_dump(mode="json") for r in routes]


@router.get("", response_model=list[RouteOut])
def get_routes(db: Session = Depends(get_db)):
    """Catálogo de rutas con caché Redis (TTL 300 s)."""
    return get_cached_or_fetch(
        CACHE_KEY_ROUTES,
        TTL_ROUTES,
        lambda: _fetch_routes_from_db(db),
    )
