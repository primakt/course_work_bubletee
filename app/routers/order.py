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
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    min_pickup_time = datetime.utcnow() + timedelta(minutes=15)
    pickup_time_naive = order_data.pickup_time.replace(tzinfo=None)  # убираем timezone

    if pickup_time_naive < min_pickup_time:
        raise HTTPException(status_code=400, detail="Время самовывоза должно быть не менее чем через 15 минут")

    if not order_data.items:
        raise HTTPException(status_code=400, detail="Корзина пуста")
    
    item_ids = [item.menu_item_id for item in order_data.items]
    items = db.query(MenuItem).filter(MenuItem.id.in_(item_ids)).all()
    
    if len(items) != len(order_data.items):
        raise HTTPException(
            status_code=404,
            detail="Один или несколько товаров не найдены"
        )

    total_price = Decimal("0")
    order_items_data = []
    
    for req_item in order_data.items:
        menu_item = next((i for i in items if i.id == req_item.menu_item_id), None)
        
        if not menu_item.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"Товар '{menu_item.name}' недоступен"
            )
        
        if req_item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Количество должно быть больше 0"
            )
        
        subtotal = menu_item.price * req_item.quantity
        total_price += subtotal
        
        order_items_data.append({
            "menu_item": menu_item,
            "quantity": req_item.quantity,
            "price": menu_item.price
        })

    discount_amount = Decimal("0")
    discount_code_used = None
    
    if order_data.discount_code:
        discount = db.query(Discount).filter(
            Discount.code == order_data.discount_code.upper(),
            Discount.is_active == True
        ).first()
        
        if not discount:
            raise HTTPException(
                status_code=400,
                detail="Неверный или неактивный промокод"
            )
        
        today = datetime.utcnow().date()
        if discount.valid_from and discount.valid_from > today:
            raise HTTPException(
                status_code=400,
                detail=f"Промокод будет действовать с {discount.valid_from}"
            )
        if discount.valid_to and discount.valid_to < today:
            raise HTTPException(
                status_code=400,
                detail="Промокод истёк"
            )
        
        if discount.usage_limit and discount.used_count >= discount.usage_limit:
            raise HTTPException(
                status_code=400,
                detail="Промокод исчерпан"
            )
        
        if discount.percentage:
            discount_amount = total_price * (discount.percentage / 100)
        elif discount.value:
            discount_amount = min(discount.value, total_price)
        
        discount_code_used = discount.code
        total_price -= discount_amount
        
        discount.used_count += 1
        db.add(discount)

    db_order = Order(
        user_id=current_user.id,
        status="new",
        total_price=total_price,
        pickup_time=order_data.pickup_time,
    )
    db.add(db_order)
    db.flush()

    for item_data in order_items_data:
        db_order_item = OrderItem(
            order_id=db_order.id,
            menu_item_id=item_data["menu_item"].id,
            quantity=item_data["quantity"],
            price_at_purchase=item_data["price"]
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
        db.add(current_user)

    db.commit()
    db.refresh(db_order)

    return db_order


@router.get("/my", response_model=list[OrderResponse])
async def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).all()
    
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if order.user_id != current_user.id and current_user.role_name != "admin":
        raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")
    
    return order