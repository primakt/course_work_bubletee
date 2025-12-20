from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from base import Base
from datetime import datetime, timezone

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="new")
    total_price = Column(Numeric(10, 2), nullable=False)
    pickup_time = Column(DateTime(timezone=True), nullable=False)  # aware datetime
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    user = relationship("User")
    items = relationship("OrderItem", back_populates="order")  # <-- ОБЯЗАТЕЛЬНО!