from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from base import get_db
from models.promotion import Promotion
from models.discount import Discount
from models.user import User
from schemas.promotion import PromotionCreate, PromotionResponse
from schemas.discount import DiscountCreate, DiscountResponse
from utils.auth import get_current_user, get_current_admin
from datetime import date

router = APIRouter(prefix="/promotions", tags=["promotions"])

@router.get("/", response_model=list[PromotionResponse])
async def get_active_promotions(db: Session = Depends(get_db)):
    today = date.today()
    
    promotions = db.query(Promotion).filter(
        Promotion.is_active == True,
        Promotion.start_date <= today,
        Promotion.end_date >= today
    ).all()
    
    return promotions


@router.get("/discounts", response_model=list[DiscountResponse])
async def get_discounts(db: Session = Depends(get_db)):
    today = date.today()
    
    discounts = db.query(Discount).filter(
        Discount.is_active == True
    ).filter(
        (Discount.valid_from.is_(None)) | (Discount.valid_from <= today)
    ).filter(
        (Discount.valid_to.is_(None)) | (Discount.valid_to >= today)
    ).filter(
        (Discount.usage_limit.is_(None)) | (Discount.used_count < Discount.usage_limit)
    ).all()
    
    return discounts


@router.post("/", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    promo: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if promo.end_date < promo.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата окончания должна быть позже даты начала"
        )
    
    db_promo = Promotion(**promo.model_dump())
    db.add(db_promo)
    db.commit()
    db.refresh(db_promo)
    
    return db_promo


@router.post("/discounts", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
async def create_discount(
    discount: DiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    existing = db.query(Discount).filter(
        Discount.code == discount.code.upper()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Промокод '{discount.code}' уже существует"
        )
    
    if not discount.percentage and not discount.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите процент или фиксированную скидку"
        )
    
    if discount.percentage and discount.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите либо процент, либо фиксированную скидку"
        )
    
    if discount.valid_to and discount.valid_from and discount.valid_to < discount.valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата окончания должна быть позже даты начала"
        )
    
    discount_data = discount.model_dump()
    discount_data['code'] = discount_data['code'].upper()
    
    db_discount = Discount(**discount_data)
    db.add(db_discount)
    db.commit()
    db.refresh(db_discount)
    
    return db_discount


@router.put("/discounts/{discount_id}", response_model=DiscountResponse)
async def update_discount(
    discount_id: int,
    discount: DiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    
    db_discount = db.query(Discount).filter(Discount.id == discount_id).first()
    
    if not db_discount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Промокод не найден"
        )
    
    for key, value in discount.model_dump(exclude_unset=True).items():
        if key == 'code':
            value = value.upper()
        setattr(db_discount, key, value)
    
    db.commit()
    db.refresh(db_discount)
    
    return db_discount