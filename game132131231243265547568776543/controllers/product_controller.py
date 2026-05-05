from database.db import SessionLocal
from models import Product


class ProductController:
    def __init__(self, session=None):
        self.db_session = session or SessionLocal()

    def create_product(self, name, price, description="", stock_quantity=0, unit="шт."):
        product = Product(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            unit=unit
        )
        self.db_session.add(product)
        try:
            self.db_session.commit()
            return product
        except Exception as e:
            self.db_session.rollback()
            raise e

    def get_all_products(self):
        return self.db_session.query(Product).all()

    def close(self):
        if self.db_session:
            self.db_session.close()

    def __del__(self):
        self.close()