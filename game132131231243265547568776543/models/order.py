from sqlalchemy import Column, Integer, DateTime, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    status = Column(String(50), nullable=False, default="Новый")

    customer = relationship("Customer", back_populates="orders")