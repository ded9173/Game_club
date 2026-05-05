from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
from controllers.order_controller import OrderController


class OrderListWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 Список заказов")
        self.resize(900, 400)
        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Клиент", "Дата", "Сумма", "Статус"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self.load_orders)
        layout.addWidget(self.btn_refresh)

        self.setLayout(layout)

    def load_orders(self):
        self.table.setRowCount(0)
        controller = OrderController()
        orders = controller.get_orders()
        try:
            for order in orders:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(order.id)))
                self.table.setItem(row, 1, QTableWidgetItem(str(order.customer_id)))
                self.table.setItem(row, 2, QTableWidgetItem(order.order_date.strftime("%d.%m.%Y %H:%M")))
                self.table.setItem(row, 3, QTableWidgetItem(f"{order.total_amount:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(order.status))
        finally:
            controller.close()