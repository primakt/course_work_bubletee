from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from base import Base
from datetime import datetime

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    subscribed = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")