from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database.db import Base


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    inn = Column(String(12), unique=True, nullable=False)
    address = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    is_buyer = Column(Boolean, default=False)
    is_salesman = Column(Boolean, default=False)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")