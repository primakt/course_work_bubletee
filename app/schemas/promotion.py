from pydantic import BaseModel
from datetime import date

class PromotionBase(BaseModel):
    title: str
    description: str
    image_url: str | None = None
    start_date: date
    end_date: date
    is_active: bool = True

class PromotionCreate(PromotionBase):
    pass

class PromotionResponse(PromotionBase):
    id: int

    class Config:
        from_attributes = True