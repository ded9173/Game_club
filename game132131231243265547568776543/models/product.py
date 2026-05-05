from sqlalchemy import Column, Integer, String, Numeric
from database.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    unit = Column(String(20), nullable=False, default="шт.")