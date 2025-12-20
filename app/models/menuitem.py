from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean
from base import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)