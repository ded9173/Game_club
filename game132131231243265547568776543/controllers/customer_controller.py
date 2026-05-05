from database import SessionLocal
from models import Customer


class CustomerController:
    def __init__(self, session=None):
        self.db_session = session or SessionLocal()

    def create_customer(self, name, inn, address, phone, is_buyer=False, is_salesman=False):
        """Создать нового клиента"""
        if self.get_customer_by_inn(inn):
            raise ValueError("Клиент с таким ИНН уже существует")

        customer = Customer(
            name=name,
            inn=inn,
            address=address,
            phone=phone,
            is_buyer=is_buyer,
            is_salesman=is_salesman
        )
        self.db_session.add(customer)
        self.db_session.commit()
        return customer

    def get_all_customers(self):
        """Получить всех клиентов"""
        return self.db_session.query(Customer).all()

    def get_customer_by_id(self, customer_id):
        """Получить клиента по ID"""
        return self.db_session.query(Customer).filter(Customer.id == customer_id).first()

    def get_customer_by_inn(self, inn):
        """Получить клиента по ИНН"""
        return self.db_session.query(Customer).filter(Customer.inn == inn).first()

    def update_customer(self, customer_id, data):
        """Обновить данные клиента"""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            raise ValueError("Клиент не найден")

        for key, value in data.items():
            setattr(customer, key, value)
        self.db_session.commit()
        return customer

    def delete_customer(self, customer_id):
        """Удалить клиента"""
        customer = self.get_customer_by_id(customer_id)
        if customer:
            self.db_session.delete(customer)
            self.db_session.commit()

    def close(self):
        """Закрыть сессию"""
        if self.db_session:
            self.db_session.close()

    def __del__(self):
        self.close()