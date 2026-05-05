from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox,
    QTextEdit
)


class ProductForm(QDialog):
    def __init__(self, on_saved=None):
        super().__init__()
        self.on_saved = on_saved
        self.setWindowTitle("📦 Добавить товар")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите название товара")

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Цена (например: 999.99)")

        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Количество на складе (по желанию)")
        self.stock_input.setText("0")

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Описание товара (необязательно)")

        form.addRow("Название:", self.name_input)
        form.addRow("Цена:", self.price_input)
        form.addRow("Кол-во:", self.stock_input)
        form.addRow("Описание:", self.desc_input)

        layout.addLayout(form)

        buttons = QVBoxLayout()
        self.save_btn = QPushButton("✅ Сохранить")
        self.cancel_btn = QPushButton("❌ Отмена")
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        self.setLayout(layout)

        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)

    def validate_inputs(self):
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        stock_text = self.stock_input.text().strip()

        errors = []

        if not name:
            errors.append("Название обязательно")
        elif len(name) < 2:
            errors.append("Название должно быть не менее 2 символов")

        if not price_text:
            errors.append("Цена обязательна")
        else:
            try:
                price = float(price_text)
                if price <= 0:
                    errors.append("Цена должна быть больше 0")
            except ValueError:
                errors.append("Цена должна быть числом")

        if stock_text:
            try:
                stock = int(stock_text)
                if stock < 0:
                    errors.append("Количество не может быть отрицательным")
            except ValueError:
                errors.append("Количество должно быть целым числом")

        return name, price_text, stock_text, errors

    def save(self):
        name, price_text, stock_text, errors = self.validate_inputs()

        if errors:
            QMessageBox.warning(self, "Ошибки ввода", "\n".join(errors))
            return

        try:
            price = float(price_text)
            stock = int(stock_text) if stock_text.strip() else 0

            from controllers.product_controller import ProductController
            pc = ProductController()
            pc.create_product(
                name=name,
                price=price,
                description=self.desc_input.toPlainText().strip(),
                stock_quantity=stock
            )
            pc.close()
            QMessageBox.information(self, "Успех", "Товар успешно добавлен!")
            if self.on_saved:
                self.on_saved()
            self.accept()
        except Exception as e:
            import traceback
            print("Ошибка при сохранении товара:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить товар:\n{e}")