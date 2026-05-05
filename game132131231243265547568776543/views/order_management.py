from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox
)
from .order_form import OrderForm
from controllers.order_controller import OrderController
from models import Order


class EditOrderDialog(QDialog):
    def __init__(self, order, parent=None):
        super().__init__(parent)
        self.order = order
        self.setWindowTitle(f"Редактировать заказ №{order.id}")
        self.resize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.customer_id_input = QLineEdit(str(self.order.customer_id))
        self.customer_id_input.setReadOnly(True)
        layout.addRow("ID клиента:", self.customer_id_input)

        self.status_input = QComboBox()
        self.status_input.addItems(["Новый", "В обработке", "Отправлен", "Доставлен", "Отменён"])
        self.status_input.setCurrentText(self.order.status)
        layout.addRow("Статус:", self.status_input)

        buttons = QHBoxLayout()
        self.btn_save = QPushButton("✅ Сохранить")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("❌ Отмена")
        self.btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)
        layout.addRow(buttons)

        self.setLayout(layout)


class OrderManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 Управление заказами")
        self.resize(900, 500)
        self.selected_order_id = None
        self.order_form = None
        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ Создать заказ")
        self.btn_add.clicked.connect(self.create_order)

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self.load_orders)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Клиент ID", "Дата", "Сумма", "Статус", "Действия"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        action_layout = QHBoxLayout()
        self.btn_delete = QPushButton("🗑️ Удалить заказ")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.delete_order)

        action_layout.addStretch()
        action_layout.addWidget(self.btn_delete)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def create_order(self):
        """Открыть форму создания заказа."""
        if self.order_form is None or not self.order_form.isVisible():
            self.order_form = OrderForm()
            self.order_form.saved.connect(self.on_order_saved)
            self.order_form.show()
        else:
            self.order_form.raise_()
            self.order_form.activateWindow()

    def on_order_saved(self):
        """Обновляем список после сохранения заказа."""
        self.load_orders()

    def load_orders(self):
        self.table.setRowCount(0)
        controller = OrderController()
        try:
            orders = controller.get_orders()
            for order in orders:
                row = self.table.rowCount()
                self.table.insertRow(row)

                self.table.setItem(row, 0, QTableWidgetItem(str(order.id)))
                self.table.setItem(row, 1, QTableWidgetItem(str(order.customer_id)))
                self.table.setItem(row, 2, QTableWidgetItem(order.order_date.strftime("%d.%m.%Y %H:%M")))
                self.table.setItem(row, 3, QTableWidgetItem(f"{order.total_amount:.2f} руб"))
                self.table.setItem(row, 4, QTableWidgetItem(order.status))

                btn_edit = QPushButton("✏️ Редактировать")
                btn_edit.setFixedSize(100, 30)
                btn_edit.clicked.connect(lambda _, oid=order.id: self.edit_order(oid))
                self.table.setCellWidget(row, 5, btn_edit)
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось загрузить заказы:\n{str(e)}")
        finally:
            controller.close()

    def on_selection_changed(self):
        """Обновляем состояние кнопки удаления при выборе строки."""
        selected_row = self.table.currentRow()
        self.selected_order_id = None
        self.btn_delete.setEnabled(False)

        if selected_row >= 0:
            item = self.table.item(selected_row, 0)
            if item and item.text().isdigit():
                self.selected_order_id = int(item.text())
                self.btn_delete.setEnabled(True)

    def edit_order(self, order_id):
        """Редактирование статуса заказа."""
        controller = OrderController()
        try:
            order = controller.db_session.query(controller.model).get(order_id)
            if not order:
                QMessageBox.warning(self, "⚠️ Ошибка", "Заказ не найден.")
                return

            dialog = EditOrderDialog(order, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                order.status = dialog.status_input.currentText()
                try:
                    controller.db_session.commit()
                    QMessageBox.information(self, "✅ Успех", f"Статус заказа №{order.id} обновлён.")
                    self.load_orders()
                except Exception as e:
                    controller.db_session.rollback()
                    QMessageBox.critical(self, "❌ Ошибка", f"Не удалось сохранить изменения:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Ошибка при редактировании заказа:\n{str(e)}")
        finally:
            controller.close()

    def delete_order(self):
        """Удаление выбранного заказа."""
        if not self.selected_order_id:
            QMessageBox.warning(self, "⚠️ Нет выбора", "Выберите заказ для удаления.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить заказ №{self.selected_order_id}?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        controller = OrderController()
        try:
            order = controller.db_session.query(controller.model).get(self.selected_order_id)
            if not order:
                QMessageBox.warning(self, "⚠️ Ошибка", "Заказ не найден.")
                return

            controller.db_session.delete(order)
            controller.db_session.commit()
            QMessageBox.information(self, "✅ Успех", f"Заказ №{self.selected_order_id} успешно удалён.")
            self.load_orders()
            self.selected_order_id = None
            self.btn_delete.setEnabled(False)
        except Exception as e:
            controller.db_session.rollback()
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось удалить заказ:\n{str(e)}")
        finally:
            controller.close()