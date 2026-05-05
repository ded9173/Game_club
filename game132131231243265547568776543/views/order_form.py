from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from controllers.order_controller import OrderController


class OrderForm(QWidget):
    saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("📦 Создание заказа")
        self.resize(800, 500)
        self.items = []
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Форма создания заказа")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        self.customer_id_input = QLineEdit()
        self.customer_id_input.setPlaceholderText("Введите ID клиента")

        form_layout = QFormLayout()
        form_layout.addRow("ID клиента:", self.customer_id_input)
        layout.addLayout(form_layout)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Товар", "Кол-во", "Цена", "ИТОГО", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.btn_add = QPushButton("+ Добавить товар")
        self.btn_save = QPushButton("✅ Сохранить заказ")
        self.btn_cancel = QPushButton("❌ Отмена")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        self.total_label = QLabel("Общая сумма: 0.00 руб")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")

        layout.addLayout(btn_layout)
        layout.addWidget(self.total_label)
        self.setLayout(layout)

    def connect_signals(self):
        self.btn_add.clicked.connect(self.add_product_row)
        self.btn_save.clicked.connect(self.save_order)
        self.btn_cancel.clicked.connect(self.close)

    def add_product_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name = QLineEdit()
        name.setPlaceholderText("Название товара")
        quantity = QSpinBox()
        quantity.setRange(1, 9999)
        price = QDoubleSpinBox()
        price.setRange(0.01, 1_000_000.00)
        total = QLabel("0.00")
        remove_btn = QPushButton("×")
        remove_btn.setObjectName("delete_btn")
        remove_btn.setFixedSize(30, 30)

        self.table.setCellWidget(row, 0, name)
        self.table.setCellWidget(row, 1, quantity)
        self.table.setCellWidget(row, 2, price)
        self.table.setCellWidget(row, 3, total)
        self.table.setCellWidget(row, 4, remove_btn)

        quantity.valueChanged.connect(lambda: self.update_row_total(row))
        price.valueChanged.connect(lambda: self.update_row_total(row))
        remove_btn.clicked.connect(lambda: self.remove_row(row))

        self.update_row_total(row)

    def update_row_total(self, row):
        qty_w = self.table.cellWidget(row, 1)
        price_w = self.table.cellWidget(row, 2)
        if qty_w and price_w:
            qty = qty_w.value()
            price = price_w.value()
            total = qty * price
            self.table.cellWidget(row, 3).setText(f"{total:.2f}")
            self.update_grand_total()

    def update_grand_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            total_w = self.table.cellWidget(row, 3)
            if total_w:
                total += float(total_w.text())
        self.total_label.setText(f"Общая сумма: {total:.2f} руб")

    def remove_row(self, row):
        self.table.removeRow(row)
        self.update_grand_total()

    def save_order(self):
        customer_id_text = self.customer_id_input.text().strip()
        if not customer_id_text.isdigit():
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите корректный ID клиента")
            return

        customer_id = int(customer_id_text)

        items = []
        for row in range(self.table.rowCount()):
            name_w = self.table.cellWidget(row, 0)
            qty_w = self.table.cellWidget(row, 1)
            price_w = self.table.cellWidget(row, 2)
            if name_w and name_w.text().strip():
                items.append({
                    'name': name_w.text(),
                    'quantity': qty_w.value(),
                    'price': price_w.value()
                })

        if not items:
            QMessageBox.warning(self, "⚠️ Ошибка", "Добавьте хотя бы один товар")
            return

        try:
            controller = OrderController()
            order = controller.create_order(customer_id=customer_id, items=items)
            QMessageBox.information(
                self, "✅ Успех",
                f"Заказ №{order.id} на сумму {order.total_amount:.2f} руб успешно создан!"
            )
            self.saved.emit()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось сохранить заказ:\n{str(e)}")
        finally:
            try:
                controller.close()
            except:
                pass