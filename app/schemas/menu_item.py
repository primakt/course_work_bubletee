from pydantic import BaseModel
from decimal import Decimal

class MenuItemBase(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    category: str
    image_url: str | None = None
    is_available: bool = True

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemUpdate(MenuItemBase):
    pass

class MenuItemResponse(MenuItemBase):
    id: int

    class Config:
        from_attributes = True