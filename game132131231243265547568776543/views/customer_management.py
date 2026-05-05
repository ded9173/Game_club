from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout,
    QMessageBox, QLineEdit, QLabel, QFormLayout, QDialog
)
from PyQt6.QtCore import Qt
from .customer_form import CustomerForm


class CustomerManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📞 Управление клиентами")
        self.resize(900, 600)
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по ИНН или ФИО...")
        self.btn_search = QPushButton("🔍 Найти")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        layout.addLayout(search_layout)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "ИНН", "Адрес", "Телефон", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Добавить клиента")
        self.btn_refresh = QPushButton("🔄 Обновить")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.open_add_dialog)
        self.btn_refresh.clicked.connect(self.load_customers)
        self.btn_search.clicked.connect(self.search_customers)

    def load_customers(self):
        try:
            from controllers.customer_controller import CustomerController
            cc = CustomerController()
            customers = cc.get_all_customers()
            self.table.setRowCount(0)

            for c in customers:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
                self.table.setItem(row, 1, QTableWidgetItem(c.name))
                self.table.setItem(row, 2, QTableWidgetItem(c.inn))
                self.table.setItem(row, 3, QTableWidgetItem(c.address))
                self.table.setItem(row, 4, QTableWidgetItem(c.phone))

                btn_del = QPushButton("🗑️")
                btn_del.clicked.connect(lambda _, cid=c.id: self.delete_customer(cid))
                self.table.setCellWidget(row, 5, btn_del)

            cc.close()
        except Exception as e:
            import traceback
            print("Ошибка загрузки клиентов:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить клиентов:\n{e}")

    def search_customers(self):
        query = self.search_input.text().strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and query not in item.text().lower():
                self.table.setRowHidden(row, True)
            else:
                self.table.setRowHidden(row, False)

    def open_add_dialog(self):
        dialog = CustomerForm(on_saved=self.load_customers)
        dialog.exec()

    def delete_customer(self, customer_id):
        reply = QMessageBox.question(self, "Подтверждение", "Удалить этого клиента?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from controllers.customer_controller import CustomerController
                cc = CustomerController()
                cc.delete_customer(customer_id)
                cc.close()
                self.load_customers()
                QMessageBox.information(self, "Успех", "Клиент удалён.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {e}")