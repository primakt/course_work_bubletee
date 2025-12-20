from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from base import get_db
from models.order import Order
from models.order_item import OrderItem
from models.menu_item import MenuItem
from models.discount import Discount
from models.loyalty_point import LoyaltyPoint
from models.user import User
from schemas.order import OrderCreate, OrderResponse
from utils.auth import get_current_user
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if order_data.pickup_time < datetime.utcnow() + timedelta(minutes=15):
        raise HTTPException(status_code=400, detail="Время самовывоза должно быть не менее чем через 15 минут")

    items = db.query(MenuItem).filter(MenuItem.id.in_([item.menu_item_id for item in order_data.items])).all()
    if len(items) != len(order_data.items):
        raise HTTPException(status_code=404, detail="Один или несколько товаров не найдены")

    total_price = Decimal("0")
    order_items = []
    for req_item in order_data.items:
        menu_item = next((i for i in items if i.id == req_item.menu_item_id), None)
        if not menu_item.is_available:
            raise HTTPException(status_code=400, detail=f"Товар {menu_item.name} недоступен")
        subtotal = menu_item.price * req_item.quantity
        total_price += subtotal
        order_items.append({
            "menu_item": menu_item,
            "quantity": req_item.quantity,
            "price": menu_item.price
        })

    discount_amount = Decimal("0")
    if order_data.discount_code:
        discount = db.query(Discount).filter(Discount.code == order_data.discount_code, Discount.is_active == True).first()
        if not discount:
            raise HTTPException(status_code=400, detail="Неверный или неактивный промокод")
        if discount.valid_from and discount.valid_from > datetime.utcnow().date():
            raise HTTPException(status_code=400, detail="Промокод ещё не действует")
        if discount.valid_to and discount.valid_to < datetime.utcnow().date():
            raise HTTPException(status_code=400, detail="Промокод истёк")
        
        if discount.percentage:
            discount_amount = total_price * (discount.percentage / 100)
        elif discount.value:
            discount_amount = discount.value
        
        total_price -= discount_amount
        discount.used_count += 1
        db.add(discount)

    db_order = Order(
        user_id=current_user.id,
        status="new",
        total_price=total_price,
        pickup_time=order_data.pickup_time
    )
    db.add(db_order)
    db.flush()

    for oi in order_items:
        db_order_item = OrderItem(
            order_id=db_order.id,
            menu_item_id=oi["menu_item"].id,
            quantity=oi["quantity"],
            price_at_purchase=oi["price"]
        )
        db.add(db_order_item)

    points_earned = int(total_price // 100)
    if points_earned > 0:
        loyalty = LoyaltyPoint(
            user_id=current_user.id,
            points_earned=points_earned,
            reason="purchase",
            order_id=db_order.id
        )
        db.add(loyalty)
        current_user.points += points_earned

    db.commit()
    db.refresh(db_order)

    return db_order

@router.get("/my", response_model=list[OrderResponse])
def get_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()