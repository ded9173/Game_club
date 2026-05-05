from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QCheckBox
)
from utils.validators import validate_name, validate_inn, validate_phone, validate_address


class CustomerForm(QDialog):
    def __init__(self, customer_id=None, on_saved=None):
        super().__init__()
        self.customer_id = customer_id
        self.on_saved = on_saved
        self.setWindowTitle("➕ Добавить клиента")
        self.resize(400, 350)
        self.setup_ui()
        if customer_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.inn_input = QLineEdit()
        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.is_buyer_check = QCheckBox("Является покупателем")
        self.is_salesman_check = QCheckBox("Является продавцом")

        form.addRow("ФИО:", self.name_input)
        form.addRow("ИНН:", self.inn_input)
        form.addRow("Адрес:", self.address_input)
        form.addRow("Телефон:", self.phone_input)
        form.addRow("", self.is_buyer_check)
        form.addRow("", self.is_salesman_check)

        layout.addLayout(form)

        buttons = QVBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        self.setLayout(layout)

        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)

    def load_data(self):
        try:
            from controllers.customer_controller import CustomerController
            cc = CustomerController()
            customer = cc.get_customer_by_id(self.customer_id)
            cc.close()

            if customer:
                self.name_input.setText(customer.name)
                self.inn_input.setText(customer.inn)
                self.address_input.setText(customer.address)
                self.phone_input.setText(customer.phone)
                self.is_buyer_check.setChecked(customer.is_buyer)
                self.is_salesman_check.setChecked(customer.is_salesman)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {e}")
            self.reject()

    def save(self):
        name = self.name_input.text().strip()
        inn = self.inn_input.text().strip()
        address = self.address_input.text().strip()
        phone = self.phone_input.text().strip()
        is_buyer = self.is_buyer_check.isChecked()
        is_salesman = self.is_salesman_check.isChecked()

        errors = []
        if not validate_name(name): errors.append("ФИО: только кириллица, от 2 символов")
        if not validate_inn(inn): errors.append("ИНН: 10 или 12 цифр")
        if not validate_address(address): errors.append("Адрес: слишком короткий")
        if not validate_phone(phone): errors.append("Телефон: неверный формат")

        if errors:
            QMessageBox.warning(self, "Ошибки ввода", "\n".join(errors))
            return

        try:
            from controllers.customer_controller import CustomerController
            cc = CustomerController()
            data = {
                "name": name, "inn": inn, "address": address, "phone": phone,
                "is_buyer": is_buyer, "is_salesman": is_salesman
            }

            if self.customer_id:
                cc.update_customer(self.customer_id, data)
                msg = "Клиент обновлён"
            else:
                cc.create_customer(**data)
                msg = "Клиент добавлен"

            cc.close()
            QMessageBox.information(self, "Готово", msg)
            if self.on_saved:
                self.on_saved()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")