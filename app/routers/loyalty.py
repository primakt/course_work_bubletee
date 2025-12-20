from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from base import get_db
from models.favorite_order import FavoriteOrder
from models.user import User
from schemas.loyalty import FavoriteOrderCreate, FavoriteOrderResponse, LoyaltyResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/loyalty", tags=["loyalty"])

@router.get("/balance", response_model=LoyaltyResponse)
def get_balance(current_user: User = Depends(get_current_user)):
    return {"points": current_user.points}

@router.post("/favorite", response_model=FavoriteOrderResponse)
def save_favorite_order(
    fav: FavoriteOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorite = db.query(FavoriteOrder).filter(FavoriteOrder.user_id == current_user.id).first()
    if favorite:
        favorite.order_details = fav.items
        favorite.name = fav.name
    else:
        favorite = FavoriteOrder(
            user_id=current_user.id,
            order_details=fav.items,
            name=fav.name
        )
        db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite

@router.get("/favorite", response_model=FavoriteOrderResponse | None)
def get_favorite_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorite = db.query(FavoriteOrder).filter(FavoriteOrder.user_id == current_user.id).first()
    if not favorite:
        return None
    return favorite