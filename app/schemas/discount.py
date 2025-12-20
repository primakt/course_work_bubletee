from pydantic import BaseModel
from decimal import Decimal
from datetime import date

class DiscountBase(BaseModel):
    code: str
    percentage: Decimal | None = None
    value: Decimal | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool = True

class DiscountCreate(DiscountBase):
    pass

class DiscountResponse(DiscountBase):
    id: int
    used_count: int

    class Config:
        from_attributes = True