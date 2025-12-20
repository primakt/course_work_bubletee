from sqlalchemy import Column, Integer, ForeignKey, JSON, String, DateTime
from sqlalchemy.orm import relationship
from base import Base
from datetime import datetime

class FavoriteOrder(Base):
    __tablename__ = "favorite_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    order_details = Column(JSON, nullable=False)
    name = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")