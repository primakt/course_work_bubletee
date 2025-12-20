from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    discount_code: str | None = None
    pickup_time: datetime
    store_id: int

class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    price_at_purchase: Decimal

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    status: str
    total_price: Decimal
    pickup_time: datetime
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True