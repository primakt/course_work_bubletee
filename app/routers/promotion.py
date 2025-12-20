from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies import get_db
from models.promotion import Promotion
from models.discount import Discount
from schemas.promotion import PromotionCreate, PromotionResponse
from schemas.discount import DiscountCreate, DiscountResponse
from utils.auth import get_current_user
from models.user import User
from datetime import date

router = APIRouter(prefix="/promotions", tags=["promotions"])

@router.get("/", response_model=list[PromotionResponse])
def get_active_promotions(db: Session = Depends(get_db)):
    today = date.today()
    return db.query(Promotion).filter(Promotion.is_active == True, Promotion.start_date <= today, Promotion.end_date >= today).all()

@router.get("/discounts", response_model=list[DiscountResponse])
def get_discounts(db: Session = Depends(get_db)):
    return db.query(Discount).filter(Discount.is_active == True).all()

@router.post("/", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def create_promotion(promo: PromotionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_promo = Promotion(**promo.model_dump())
    db.add(db_promo)
    db.commit()
    db.refresh(db_promo)
    return db_promo

@router.post("/discounts", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
def create_discount(discount: DiscountCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_discount = Discount(**discount.model_dump())
    db.add(db_discount)
    db.commit()
    db.refresh(db_discount)
    return db_discount