from pydantic import BaseModel
from typing import List

class FavoriteOrderCreate(BaseModel):
    items: List[dict]
    name: str | None = None

class FavoriteOrderResponse(BaseModel):
    order_details: dict
    name: str | None

    class Config:
        from_attributes = True

class LoyaltyResponse(BaseModel):
    points: int