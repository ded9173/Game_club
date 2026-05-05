from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
)
from .product_form import ProductForm


class ProductManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📦 Управление товарами")
        self.resize(900, 600)
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.product_table = QTableWidget(0, 5)
        self.product_table.setHorizontalHeaderLabels(["ID", "Название", "Цена", "На складе", "Ед."])
        self.product_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.product_table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Добавить товар")
        self.btn_refresh = QPushButton("🔄 Обновить")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_product)
        self.btn_refresh.clicked.connect(self.load_products)

    def load_products(self):
        try:
            from controllers.product_controller import ProductController
            pc = ProductController()
            products = pc.get_all_products()
            self.product_table.setRowCount(0)

            for p in products:
                row = self.product_table.rowCount()
                self.product_table.insertRow(row)
                self.product_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.product_table.setItem(row, 1, QTableWidgetItem(p.name))
                self.product_table.setItem(row, 2, QTableWidgetItem(f"{float(p.price):.2f}"))
                self.product_table.setItem(row, 3, QTableWidgetItem(str(p.stock_quantity)))
                self.product_table.setItem(row, 4, QTableWidgetItem(p.unit))

            pc.close()
        except Exception as e:
            import traceback
            print("❌ Ошибка при загрузке товаров:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить товары:\n{e}")

    def add_product(self):
        dialog = ProductForm(on_saved=self.load_products)
        dialog.exec()